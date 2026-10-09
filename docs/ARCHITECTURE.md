# Архитектура экосистемы

cybOS — точка сборки и каталог. CybOS-demo — рабочий нативный стенд. Владельцы библиотек находятся рядом и подключаются через явные зависимости; каждый компонент можно тестировать отдельно.

```mermaid
flowchart TD
    OS[cybOS: каталог и воспроизводимая сборка] --> Launch[cybLaunch: команды разработки]
    OS --> Desktop[CybOS-demo: нативный стенд]
    Desktop --> Core[robotcyb-core: workers / Modbus / энергия]
    Desktop --> Soul[soul: память / факты / граф]
    Desktop --> Guard[cybguard: bounded actions]
    Desktop --> Replay[immunocybchain: replay identities]
    Desktop --> Net[cybnet: mesh / VPN contracts]
    Desktop --> Browser[CybBrowser: bounded document worker]
    Browser --> Web[cybweb: HTML / источники]
    Desktop --> Dex[cybdex: рынки / свечи]
    Dex --> Core
    Desktop --> Bee[cybbee: наблюдения фермы]
    Desktop --> Chain[cybchain: oracle values]
    OS --> Node[go-cyber: consensus node]
    OS --> Chat[cybchat: Apple messaging app]
    OS --> Cyb[cyb: upstream runtime]
    OS --> Experiences[robotcyb / soul-demo / Robotcyb-game / Price Tracker]
```

## Где находится источник истины

- UI, SQLite и связывание ячеек — `CybOS-demo`.
- Данные знаний и памяти — типы `soul`, сохраняемые SQLite-слоем приложения.
- Жизненный цикл worker и политика питания — `robotcyb-core`.
- Текст документа — `cybweb`; очередь запросов и bounded fetch — `CybBrowser`.
- Валидация действий — `cybguard`; выполнение остаётся явной обязанностью вызывающей стороны.
- Идентичность сообщений — `immunocybchain`; Noise-аутентификация и durable SQLite replay checks остаются в нативном CybChat.
- Наблюдения — `cybbee`; доступ к реальному устройству требует отдельного адаптера.
- Рынки — `cybdex`; транзакции и обмены не исполняются.
- Консенсус — существующий `go-cyber`; `cybchain` и `immunocybchain` не изображают новую работающую блокчейн-сеть.

## Статусы

`library` означает проверенный код библиотеки, `demo` — демонстрацию. Полный Bevy workspace `cyb` требует upstream-соседей, а `cybchat` — Apple SDK. Эти ограничения отображаются в каталоге и командах разработки.

`CybBrowser-` — дубликат, исключённый из сборки. Его удаление остаётся ручным действием владельца: доступное GitHub-подключение вернуло 403 при DELETE. Канонический проект — `CybBrowser`.
