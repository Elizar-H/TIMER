"""Picker data loading and item-building pipeline.

This module deliberately has no application or UI state.  The application
passes its existing network, parsing, settings and logging functions to
``PickerDataService``.  Keeping those dependencies explicit makes it possible
to move the pipeline out of ``app.py`` without changing its ordering or
fallback behavior.
"""

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import threading
import time


@dataclass
class PickerRefreshState:
    """Mutable Picker data shared by refresh workers and the UI thread."""

    items: list = field(default_factory=list)
    last_refresh: float = 0
    last_success_at: float | None = None
    last_refresh_ms: float | None = None
    last_item_count: int = 0
    last_refresh_note: str = "кэш"
    refreshing: bool = False
    refresh_lock: threading.Lock = field(default_factory=threading.Lock)
    fast_refresh_lock: threading.Lock = field(default_factory=threading.Lock)


class PickerDataService:
    """Loads source data and builds the rows consumed by the Picker UI."""

    def __init__(
        self,
        *,
        flash_url,
        recycling_url,
        fetch_page_html,
        fetch_market_minutes,
        read_filters,
        parse_crossout_data,
        build_flash_items,
        build_recycling_items,
        build_recycling_sale_prices,
        has_real_items,
        count_real_items,
        get_profile_refresh,
        get_empty_retry_attempts,
        get_empty_retry_delay_seconds,
        log_error,
        append_log_line,
        perf_counter=time.perf_counter,
        sleep=time.sleep,
        executor_factory=ThreadPoolExecutor,
    ):
        self.flash_url = flash_url
        self.recycling_url = recycling_url
        self.fetch_page_html = fetch_page_html
        self.fetch_market_minutes = fetch_market_minutes
        self.read_filters = read_filters
        self.parse_crossout_data = parse_crossout_data
        self.build_flash_items = build_flash_items
        self.build_recycling_items = build_recycling_items
        self.build_recycling_sale_prices = build_recycling_sale_prices
        self.has_real_items = has_real_items
        self.count_real_items = count_real_items
        self.get_profile_refresh = get_profile_refresh
        self.get_empty_retry_attempts = get_empty_retry_attempts
        self.get_empty_retry_delay_seconds = get_empty_retry_delay_seconds
        self.log_error = log_error
        self.append_log_line = append_log_line
        self.perf_counter = perf_counter
        self.sleep = sleep
        self.executor_factory = executor_factory

    def timed_call(self, label, timings, func, *args):
        """Calls ``func`` and records elapsed milliseconds even on failure."""
        started = self.perf_counter()
        try:
            return func(*args)
        finally:
            timings[label] = (self.perf_counter() - started) * 1000

    def fetch_picker_sources(self):
        """Fetches independent Picker sources with the current fallbacks."""
        timings = {}
        with self.executor_factory(max_workers=3) as executor:
            flash_future = executor.submit(
                self.timed_call,
                "flash_fetch_ms",
                timings,
                self.fetch_page_html,
                self.flash_url,
            )
            recycling_future = executor.submit(
                self.timed_call,
                "recycling_fetch_ms",
                timings,
                self.fetch_page_html,
                self.recycling_url,
            )
            market_minutes_future = executor.submit(
                self.timed_call,
                "minutes_fetch_ms",
                timings,
                self.fetch_market_minutes,
            )

            filters_started = self.perf_counter()
            filters = self.read_filters()
            timings["filters_ms"] = (
                self.perf_counter() - filters_started
            ) * 1000
            flash_html = flash_future.result()

            try:
                recycling_html = recycling_future.result()
            except Exception as error:
                self.log_error(
                    "picker_recycling_fetch",
                    f"Recycling page fetch failed: {error}",
                )
                recycling_html = None

            try:
                market_minutes = market_minutes_future.result()
            except Exception as error:
                self.log_error(
                    "picker_market_minutes_fetch",
                    f"Market minutes fetch failed: {error}",
                )
                market_minutes = {}

        return filters, flash_html, recycling_html, market_minutes, timings

    def parse_market_source(self, source_name, html):
        """Parses one market source and rejects an incomplete result."""
        items_by_id, market_data = self.parse_crossout_data(html)
        if not items_by_id or not market_data:
            raise ValueError(f"No {source_name} data parsed")
        return items_by_id, market_data

    @staticmethod
    def merge_market_sources(
        primary_items,
        primary_market,
        secondary_items,
        secondary_market,
    ):
        """Returns copies where secondary source values take precedence."""
        merged_items = dict(primary_items)
        merged_items.update(secondary_items)

        merged_market = dict(primary_market)
        merged_market.update(secondary_market)

        return merged_items, merged_market

    def log_picker_performance(self, timings, result):
        """Writes the existing compact Picker refresh performance line."""
        if not self.get_profile_refresh():
            return

        parts = [
            f"total={timings.get('total_ms', 0):.0f}ms",
            f"flash={timings.get('flash_fetch_ms', 0):.0f}ms",
            f"recycling={timings.get('recycling_fetch_ms', 0):.0f}ms",
            f"minutes={timings.get('minutes_fetch_ms', 0):.0f}ms",
            f"filters={timings.get('filters_ms', 0):.0f}ms",
            f"build={timings.get('build_ms', 0):.0f}ms",
            f"items={self.count_real_items(result)}",
        ]
        self.append_log_line("picker_refresh " + " ".join(parts))

    def build_picker_items(self):
        """Builds Picker items while preserving source and fallback order."""
        build_started = self.perf_counter()
        (
            filters,
            flash_html,
            recycling_html,
            market_minutes,
            timings,
        ) = self.fetch_picker_sources()

        parse_started = self.perf_counter()
        items_by_id, market_data = self.parse_market_source("flash", flash_html)
        timings["parse_flash_ms"] = (
            self.perf_counter() - parse_started
        ) * 1000

        try:
            if recycling_html is None:
                raise ValueError("Recycling page was not fetched")
            parse_started = self.perf_counter()
            recycling_items_by_id, recycling_market_data = (
                self.parse_market_source("recycling", recycling_html)
            )
            timings["parse_recycling_ms"] = (
                self.perf_counter() - parse_started
            ) * 1000
        except Exception as error:
            self.log_error(
                "picker_recycling_parse",
                f"Recycling page parse failed: {error}",
            )
            recycling_items_by_id = items_by_id
            recycling_market_data = market_data

        (
            merged_recycling_items_by_id,
            merged_recycling_market_data,
        ) = self.merge_market_sources(
            items_by_id,
            market_data,
            recycling_items_by_id,
            recycling_market_data,
        )

        items_started = self.perf_counter()
        flash_items = self.build_flash_items(
            items_by_id,
            market_data,
            market_minutes,
            filters,
        )
        decor_items = self.build_recycling_items(
            merged_recycling_items_by_id,
            merged_recycling_market_data,
            filters,
        )
        decor_sale_prices = self.build_recycling_sale_prices(
            merged_recycling_market_data,
            filters["recycling_rarities"],
        )
        timings["build_ms"] = (
            self.perf_counter() - items_started
        ) * 1000

        result = (
            flash_items
            + ([{"separator": True, "section": "Декор"}] if decor_items else [])
            + (
                [{"decor_prices": True, "prices": decor_sale_prices}]
                if decor_items
                else []
            )
            + decor_items
        )
        if not self.has_real_items(result):
            result = [
                {"separator": True, "section": "Предметы не найдены"}
            ]

        timings["total_ms"] = (
            self.perf_counter() - build_started
        ) * 1000
        self.log_picker_performance(timings, result)
        return result, timings

    def build_picker_items_with_retries(self):
        """Retries empty builds using the current application settings."""
        last_items = []
        last_timings = {}
        attempts = max(1, self.get_empty_retry_attempts())

        for attempt in range(attempts):
            items, timings = self.build_picker_items()
            last_items = items
            last_timings = timings
            if self.has_real_items(items):
                return items, timings, None

            if attempt + 1 < attempts:
                self.sleep(self.get_empty_retry_delay_seconds())

        return last_items, last_timings, "empty"
