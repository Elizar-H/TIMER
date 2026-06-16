import time


STAGE_OPEN_CARD = "open_card"
STAGE_OPENING_CARD = "opening_card"
STAGE_BUY = "buy"
STAGE_OPENING_BUY_DIALOG = "opening_buy_dialog"
STAGE_QUANTITY = "quantity"


class MarketActionState:
    def __init__(self, max_age_seconds):
        self.max_age_seconds = max_age_seconds
        self.stage = STAGE_OPEN_CARD
        self.ready_at = 0
        self.updated_at = 0

    def set(self, stage, ready_at=0):
        self.stage = stage
        self.ready_at = ready_at
        self.updated_at = time.monotonic()

    def reset(self):
        self.set(STAGE_OPEN_CARD, 0)

    def get(self):
        now = time.monotonic()
        if (
            self.stage != STAGE_OPEN_CARD
            and self.updated_at
            and now - self.updated_at > self.max_age_seconds
        ):
            self.reset()
            return self.stage

        if self.stage == STAGE_OPENING_CARD and now >= self.ready_at:
            self.set(STAGE_BUY, 0)
        elif self.stage == STAGE_OPENING_BUY_DIALOG and now >= self.ready_at:
            self.set(STAGE_QUANTITY, 0)

        return self.stage
