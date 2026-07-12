# План безопасного рефакторинга TIMER

## Границы текущего этапа

Текущий этап намеренно ограничен изолированными изменениями, для которых можно
зафиксировать поведение без запуска Crossout. Полный рефакторинг приложения на
этом этапе не выполнялся.

Эталон перед началом работ:

- ветка `refactor-structure`, `HEAD` — `bf6c4ac`;
- рабочее дерево было чистым;
- `timer_app/app.py` содержал 4484 строки и 207 функций;
- `main.py` и `timer.py` запускали один и тот же `timer_app.app.main`;
- автоматических тестов не было.

Удаление `Tools/market_sell_reader_fast.py`, присутствующее в текущем рабочем
дереве, не относится к этому рефакторингу. Файл намеренно не восстанавливался
и не изменялся.

## Что уже изменено

### 1. Зафиксировано текущее поведение

Добавлен набор `unittest`-тестов без новых зависимостей. Он проверяет:

- импорт модулей без запуска GUI и фоновых потоков;
- загрузку и слияние настроек;
- текущий пиксельный формат всех 36 координат и legacy-разрешение точек;
- парсинг данных CrossoutCore и существующие экономические формулы;
- построение и форматирование строк Picker;
- чтение и запись Picker-кэша;
- переходы состояния рыночных действий;
- stop/cancel helpers разбора;
- точные ID горячих клавиш и VK-коды;
- парсинг рыночной цены из буфера обмена;
- успешную последовательность safe-buy с восстановлением буфера;
- один полный контролируемый цикл разбора, cleanup и финальный `LEFTUP`;
- выбор верхнего/нижнего пункта разбора, timeout/fallback и stop-ветви
  context probe;
- confirm polling, включая нулевое ожидание, ограничение sleep оставшимся
  deadline, потерю игрового окна и отмену ожидания;
- order-complete probe: продление deadline при удержании, потерю и
  восстановление focus, timeout, два `ESC` и lifecycle при исключении;
- single-flight двух конкурентных запусков order-complete probe и текущее
  состояние после ошибки `Thread.start()`;
- pending Picker selection: token-инвалидацию, daemon waiter, `root.after`,
  stale callback, wait failure и success-порядок reset/paste;
- форматирование и цикл фонового таймера;
- владение памятью и закрытие Win32 clipboard на успешных и ошибочных путях;
- потокобезопасность логирования и single-flight кэша фильтров.

Тесты не вызывают реальный WinAPI, Tkinter GUI, сеть, Chrome LevelDB, игровые
клики или OCR экрана.

### 2. Выделен pipeline данных Picker

Создан `timer_app/picker/data.py`:

- `PickerDataService` содержит прежнюю последовательность параллельной загрузки,
  parsing, fallback, расчёта элементов, профилирования и повторных попыток;
- зависимости передаются явно и не импортируют `app.py`;
- `PickerRefreshState` объединяет элементы, метаданные обновления и два lock;
- прежние функции в `app.py` оставлены тонкими совместимыми обёртками;
- интервалы обновления, количество worker-потоков executor и порядок ожидания
  результатов не менялись.

Дополнительно гарантировано освобождение refresh-lock, если планирование
Tk-обновления завершится исключением.

### 3. Выделен таймер

Создан `timer_app/timer.py`:

- чистые функции parsing/formatting;
- `TimerState` для очереди и сглаживаемого значения времени;
- прежний бесконечный worker с явными callback-зависимостями;
- в `app.py` сохранены прежние имена функций-обёрток.

Формат времени, интервалы `0.05`, `0.2`, `1` и `3` секунды, границы alert и
payload очереди не менялись.

### 4. Выделена низкоуровневая работа с буфером обмена

Создан `timer_app/clipboard.py`. В него буквально перенесены Win32 get/set
операции с сохранением:

- `CF_UNICODETEXT = 13`;
- `GMEM_MOVEABLE = 0x0002`;
- порядка `OpenClipboard` / allocation / lock / copy / `SetClipboardData`;
- передачи владения памятью Windows после успешного `SetClipboardData`;
- прежнего Tkinter fallback в `app.py`.

### 5. Небольшие исправления надёжности

- Запись, ротация и rate-limit лога защищены общим `RLock`; формат строки,
  размер 512 KiB и интервал 30 секунд не менялись.
- Picker-кэш теперь безопасно отклоняет JSON с корнем не-объектом.
- Одновременные cache miss фильтров CrossoutCore выполняют одно чтение; время
  жизни кэша отсчитывается после завершения чтения.

### 6. Расширены characterization-тесты критичных сценариев

Отдельно зафиксированы:

- success и timeout order-complete probe, включая точные два `ESC`;
- все основные ошибочные ветви safe-buy с одним или четырьмя `ESC`;
- полная последовательность paste с восстановлением курсора;
- короткое и длинное нажатие End;
- market details/lots, удержание и отпускание кнопки ордера;
- stop, finish-current-cycle, restart и запуск salvage.

### 7. Централизовано runtime-состояние salvage

В `timer_app/actions/salvage.py` добавлен `SalvageRuntimeState`. Он объединяет
прежние разрозненные runtime-флаги, `Event`, HWND, состояние курсора и общий
`RLock` жизненного цикла.

- check/setup запуска и `Thread.start()` теперь являются одной single-flight
  операцией;
- два конкурентных запуска создают ровно один worker;
- ошибка создания/запуска потока полностью откатывает состояние;
- stop/finish согласованно обновляют флаги под lock, сохраняя прежний контракт
  `running` во время cleanup;
- reset выполняется даже при исключении cleanup;
- restart планируется только после полного reset;
- порядок игровых действий, задержек и обязательного `LEFTUP` не менялся.

### 8. Выделена orchestration цикла salvage

В `timer_app/actions/salvage.py` добавлены:

- `SalvageWorkflowConfig` с пятью прежними значениями таймингов;
- `SalvageWorkflowDependencies` с явными callback-зависимостями;
- `SalvageWorkflow`, содержащий последовательность named clicks, hold,
  stop/finish, cleanup, reset и restart.

`app.run_salvage_loop()` сохранён как совместимая тонкая обёртка. WinAPI,
`GameActions`, Tk, focus и pixel helpers остаются на стороне приложения и
передаются workflow явно. Это исключает обратный импорт `app.py` и сохраняет
существующие hotkey/start callers.

`timer_app/app.py` после текущего этапа содержит 4267 строк. Большая часть
приложения намеренно остаётся в нём до отдельных characterization-этапов.

### 9. Выделены salvage decision и polling helpers

В `timer_app/actions/salvage.py` перенесены только решения, не выполняющие
реальный ввод или чтение экрана:

- проверка светлого пикселя контекстного меню;
- выбор верхнего/нижнего пункта разбора с прежним fallback;
- ожидание доступности кнопки подтверждения.

В `app.py` сохранены прежние публичные функции-обёртки, чтение пикселей,
получение HWND, клики, guarded sleep и запрос finish-current-cycle. Все
изменяемые значения и app-callbacks читаются через late-binding функции в тех
же точках цикла, что и раньше.

Characterization-тесты отдельно фиксируют:

- чтение обеих context-проб до выбора и приоритет верхней;
- последний RGB в fallback-логе и существующий двойной пробел без проб;
- возврат `None` без fallback при отменённом guarded sleep;
- сохранение fallback при заранее установленном stop и потерянном окне;
- confirm probe до deadline-check, в том числе при нулевом ожидании;
- минимальный context poll `0.001` и ограничение обоих poll оставшимся
  временем;
- обязательные logging, cleanup и reset при исключении основного workflow.

После этого шага `timer_app/app.py` содержит 4243 строки. Низкоуровневые
WinAPI/GameActions/pixel/focus helpers намеренно не переносились.

### 10. Вынесено polling/ESC-тело order-complete probe

В `timer_app/actions/market.py` добавлены
`OrderCompleteProbeDependencies` и `run_order_complete_probe()`. В модуль
перенесена прежняя последовательность:

- расчёт и продление deadline во время удержания кнопки ордера;
- ожидание и однократное логирование отсутствующего focus;
- чтение результата probe и сохранение последнего RGB;
- необязательный `LEFTUP`, reset рыночной стадии и повторное восстановление
  focus;
- два `ESC` с прежними задержками;
- timeout-лог.

В `app.py` намеренно оставлены `Lock`, `Event`, флаг running, запуск daemon
worker, общий `right_shift_order_down`, чтение пикселей, focus recovery и
низкоуровневый ввод. App-level `try/finally` по-прежнему сбрасывает running и
устанавливает Event при любом исключении.

Characterization-тесты дополнительно фиксируют:

- продолжение probe после внешнего отпускания кнопки;
- продление deadline при удержании;
- отсутствие pixel-read без focus и однократный wait-лог;
- возобновление polling после восстановления focus;
- потерю focus после hit, когда стадия уже сброшена, но `ESC` пропускаются;
- точный wait-контракт `Event.wait(2.25)`;
- обязательный lifecycle cleanup при исключении reader.

Состояние потока не переносилось в тот же шаг: это могло бы незаметно изменить
существующие Event-generation/TOCTOU races и поведение при ошибке
`Thread.start()`. После этого шага `timer_app/app.py` содержит 4235 строк.

### 11. Централизовано lifecycle-состояние order-complete probe

В `timer_app/actions/market.py` добавлен простой `OrderCompleteProbeState`,
объединяющий прежние три globals:

- running-флаг;
- обычный `threading.Lock`;
- completion `Event`, установленный в начальном состоянии.

Методы state буквально сохраняют прежние критические секции:

- `try_begin()` — check running, затем `running=True` и `Event.clear()`;
- `finish()` — `running=False`, затем `Event.set()`;
- `is_running()` — только чтение под lock;
- `wait(timeout)` — прямой `Event.wait()` без дополнительного lock или
  повторной проверки running.

App-функции запуска, worker, проверки и ожидания сохранили прежние имена и
контракты. `Thread` по-прежнему создаётся после выхода из lock. Ошибка
`Thread.start()` намеренно не получила rollback: исключение выходит наружу, а
state остаётся running с очищенным Event, как в эталонной реализации.

Два синхронизированных caller-потока теперь проверяют реальный single-flight:
пока первый заблокирован внутри fake `Thread.start()`, второй возвращается без
создания worker. Отдельно проверены независимость экземпляров state, начальный
Event, повторный `try_begin()` и release waiters после `finish()`.

После этого шага `timer_app/app.py` содержит 4223 строки.

### 12. Зафиксирован deferred-выбор строки Picker

Добавлены app-level characterization-тесты текущего pending selection flow без
изменения production-кода. Они фиксируют:

- отсутствие изменений, если order-complete probe уже не работает;
- порядок token increment → pending row → redraw → daemon Thread;
- передачу захваченных token, row, item name и результата wait через
  `root.after(0, callback)`;
- отсутствие rollback token/row при ошибке `Thread.start()`;
- сохранение pending marker при исключении `root.after`;
- cancel-инвалидацию waiter-а и полностью тихий stale callback даже при
  `wait_ok=False`;
- очистку pending row и redraw до проверок wait/result/market readiness;
- exact failure-log при timeout ожидания;
- остановку при смене выбранной строки или невозможности восстановить рынок;
- success-порядок redraw → ensure market → reset stage → paste captured name.

В этом шаге намеренно не переносились token/row state, waiter Thread, Tk,
market navigation или paste. Теперь два globals pending selection можно
заменить простым state отдельным механическим этапом с уже готовой защитой от
регрессий. `timer_app/app.py` остаётся на 4223 строках.

## Выполненные проверки

На исходном состоянии и после логических шагов выполнялись:

```powershell
py -c "import ast, pathlib; [ast.parse(p.read_text(encoding='utf-8')) for p in pathlib.Path('.').rglob('*.py')]; print('syntax ok')"
py -m unittest discover -s tests -v
py -m json.tool settings.json
py -m json.tool coordinates.json
```

Также выполнялись:

- импорт всех пакетов `timer_app` и совместимых точек входа `main`, `timer`,
  `timer_settings`;
- `git diff --check`;
- отдельные проверки загрузки настроек и разрешения всех координат;
- проверка, что импорт не создаёт Tk-окна и не запускает фоновые потоки;
- проверка, что `settings.json`, `coordinates.json`, `main.py` и `timer.py` не
  изменены.

Текущий результат тестов: 140 тестов, все успешно.

## Что осталось сделать

Основной цикл зависимостей пока не разорван:

```text
Picker selection
    -> ожидание order-complete
    -> восстановление market view
    -> paste выбранного имени
    -> обновление selection и повторная отрисовка Picker
```

Из-за этого нельзя безопасно одним переносом разделить Picker UI, market,
focus и обработку клавиш. Следующие этапы должны выполняться отдельно.

## Следующие независимые этапы

### Этап 1 (выполнен). Дополнить characterization критичных state machine

Только тесты, без архитектурных изменений:

- успешный и timeout-путь order-complete probe с точными двумя `ESC`;
- ошибки safe-buy: один `ESC`, четыре `ESC`, mismatch и clipboard timeout;
- paste: click, `Ctrl+A`, Backspace, `Ctrl+V`, cursor restore, Enter;
- короткое и долгое нажатие End;
- stop/restart/finish-current-cycle для разбора;
- переключение details/lots и long Right hold/release.

### Этап 2 (выполнен). Извлечь salvage workflow и решения

- Состояние, single-flight lifecycle и orchestration основного цикла
  централизованы в `timer_app/actions/salvage.py`.
- Polling выбора context-disassemble и ожидания confirm вынесен с явными
  callback-зависимостями.
- В `app.py` оставлены разрешение HWND, реальные клики, cursor/pixel reads,
  hotkeys и Tk scheduling.
- Порядок named clicks, проверок пикселей, hold, sleep и обязательного
  `LEFTUP` в `finally` зафиксирован тестами.
- Область lifecycle-lock не расширялась на клики, ожидания, WinAPI или
  Tk-вызовы.

Не объединять этот этап с market или Picker UI.

### Этап 3 (частично выполнен). Извлечь order-complete и market navigation

Выполнено:

- Polling/ESC-тело order-complete probe вынесено в `actions/market.py`.
- Lifecycle-state probe объединён в `OrderCompleteProbeState` без изменения
  lock/Event semantics.
- Сохранены poll `0.005`, продлеваемое окно ожидания, mouse-up, reset стадии и
  два `ESC`.
- WinAPI, focus, pixel reader, создание Thread и callers оставлены в `app.py`;
  state владеет только lock/Event-переходами.

Следующие части выполнять отдельно:

- Исправление poisoned-state после ошибки `Thread.start()` выполнять только
  как отдельное намеренное reliability-изменение.
- Устранение Event-generation/TOCTOU race требует отдельного контракта и не
  должно объединяться с Picker navigation.
- Pending Picker selection теперь покрыт characterization-тестами; следующим
  отдельным шагом объединить только token и pending row в простой state без
  lock и без переноса Thread/Tk/navigation/paste.
- После state-переноса отдельно оставить Picker один callback
  `ensure_market_ready`.
- Market details/lots/back navigation переносить после Picker-wait seam, не в
  одном изменении с состоянием probe.
- Safe-buy на этом этапе не переносить.

### Этап 4. Извлечь safe-buy

- Выполнять только после тестов всех ошибочных ветвей.
- Сохранить lock, флаг одной попытки на карточку, OCR, sentinel буфера,
  проверку цены/количества, один или четыре `ESC` и восстановление буфера.
- Не менять OCR-пороги, шаблоны, координаты или polling.

### Этап 5. Отделить выбранный предмет и paste-состояние

- Вынести поиск строки по имени, pending selection и refresh-paste state.
- Не переносить Tk-рисование в тот же этап.
- Явно запретить несколько одновременно активных paste-сценариев только после
  characterization текущей реакции на быстрый выбор разных строк.

### Этап 6. Извлечь Picker UI

- Перенести создание окна, layout, canvas drawing и navigation в один крупный,
  понятный модуль, а не в множество мелких файлов.
- Сохранить размеры, цвета, шрифты, положения, высоты строк и поведение hover.
- После переноса отдельно оптимизировать поиск строки и лишние redraw.

### Этап 7. Централизовать ввод и UI-dispatch

- Объединить флаги End/стрелок/Delete в простой state-класс.
- Сохранить все hotkey IDs, VK-коды, hold/release правила и polling.
- Перенаправить Tk-вызовы фоновых потоков через одну очередь UI-команд.
- Добавить штатное завершение постоянных worker-потоков и unregister hotkeys.

### Этап 8. Контекст игрового окна и безопасные оптимизации WinAPI

- После тестов focus recovery выделить контекст HWND/foreground.
- Пакетно читать пиксели в рамках одной проверки, не создавая долговременный
  кэш динамических цветов.
- Переиспользовать геометрию только внутри одного атомарного probe.
- Не кэшировать foreground между poll-итерациями без проверки live-window.

### Этап 9. Ошибки и статический анализ

- По одному модулю сужать только доказанно широкие `except Exception`.
- Не менять WinAPI fallback, если набор возможных исключений не подтверждён.
- Добавлять rate-limited logging там, где ошибка сейчас теряется молча.
- Запустить внешний статический анализ только если инструмент уже установлен;
  не добавлять зависимость ради этого этапа.

## Что нельзя проверить без запущенной игры

- реальные координаты кликов на текущем разрешении и масштабе Windows;
- фактические цвета/переходы пикселей кнопок рынка и разбора;
- OCR цен на реальном изображении списка предложений;
- готовность диалогов между существующими задержками;
- удержание/отпускание мыши и клавиш в Crossout;
- восстановление, сворачивание и foreground игрового окна;
- регистрацию и конфликт системных горячих клавиш;
- поведение короткого/долгого End и стрелок при реальном вводе;
- внешний вид, click-through и topmost оверлеев на нескольких мониторах;
- полный safe-buy, order-complete и salvage на живом интерфейсе;
- корректное восстановление системного буфера обмена при вмешательстве другого
  приложения во время сценария.

## Оставшиеся риски

- Tkinter местами вызывается из фоновых потоков.
- Paste, safe-buy, salvage, order probe и ручная навигация пока не имеют общего
  guard для мыши, клавиатуры, foreground и clipboard.
- Paste может создать несколько потоков для быстро выбранных разных имён.
- Каждый быстрый pending-выбор Picker создаёт отдельный waiter Thread; token
  отменяет только UI-callback, но не само ожидание.
- Ошибка запуска waiter-а или `root.after` оставляет pending marker; это
  сохранено как текущее поведение.
- Ошибка `Thread.start()` order-complete probe оставляет running-флаг и
  очищенный Event; это сохранено намеренно до отдельного reliability-этапа.
- Waiter order-complete probe не различает поколения Event и имеет TOCTOU между
  проверкой running и ожиданием.
- `right_shift_order_down` разделяется input-worker и probe без общего lock.
- Координаты курсора и cooldown right-click остаются worker-owned; это нужно
  сохранить при будущем переносе сценария.
- Постоянные daemon-worker не имеют штатного shutdown.
- На каждое обновление Picker создаётся новый `ThreadPoolExecutor`.
- Hover полностью перестраивает canvas.
- Некоторые WinAPI geometry/pixel вызовы повторяются в пределах одного probe.

Эти риски зафиксированы, но намеренно не исправлялись в текущем этапе: такое
изменение могло бы поменять реальное временное поведение автоматизации.

## Инварианты текущего этапа

Намеренно не менялись:

- пользовательские функции и сценарии;
- алгоритмы рынка, safe-buy, Picker, таймера и разбора;
- URL, parser rules, OCR и экономические формулы;
- hotkey IDs, VK-коды и правила нажатия/удержания/отпускания;
- числовые значения координат и формат `coordinates.json`;
- значения задержек, polling и `root.after`;
- внешний вид, размеры, положение и поведение окон/оверлеев;
- форматы `settings.json` и Picker-кэша;
- точки входа `main.py` и `timer.py`.
