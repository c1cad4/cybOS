# Единая установка и запуск

Один вход для реализованных компонентов — `python3 cyb.py` из корня `cybOS`.
Требуются Python 3.12+ и Git. Установка получает исходники с GitHub и зависимости
из стандартных реестров пакетов. Существующие checkout и изменения сохраняются;
несовпадение HEAD с lock-файлом останавливает воспроизводимую установку.

## Агенты и локальный API

```bash
git clone https://github.com/c1cad4/cybOS.git
cd cybOS
python3 cyb.py setup --profile core
python3 cyb.py doctor --profile core
python3 cyb.py test --profile core
python3 cyb.py run CybCore
```

Откройте http://127.0.0.1:8010. Launcher создаёт отдельную `.venv` в CybCore,
устанавливает `requirements.lock.txt` и использует её при запуске и тестировании.
Активация окружения вручную не требуется. Для модели нужен отдельно работающий
OpenAI-совместимый сервер на loopback; по умолчанию используется 127.0.0.1:8080.
Без него доступны регистрация агентов, сохранение и поиск знаний.

## Нативный рабочий стол

Нужны Rust/Cargo и системный C/C++ linker. Для macOS установите Xcode Command
Line Tools; для Linux — зависимости оконной системы из инструкции CybOS-demo.

```bash
python3 cyb.py setup --profile desktop
python3 cyb.py test --profile desktop
python3 cyb.py run CybOS-demo
```

Все десять библиотек устанавливаются до сборки приложения. Запускается нативный
Rust/egui runtime. Для выбора каталога данных используйте `CYBOS_DATA_DIR`.

## Вся экосистема

```bash
python3 cyb.py list
python3 cyb.py setup --profile all
python3 cyb.py doctor --profile all
python3 cyb.py test --profile all
```

Профиль `all` включает реализованные проекты и их зависимости. Для Rust нужен
Cargo, для JavaScript — Node.js 24+ (npm нужен только проектам с пакетными зависимостями), для исторического go-cyber — совместимый
Go toolchain (в документации компонента указан Go 1.17.8). cybchat требует Apple SDK,
расширение Price Tracker — ручной загрузки в браузер. Эти ограничения выводятся
отдельно. `planned` проекты видны в `list`, но не считаются работающими приложениями.

Если нужны только исходники без компиляции Rust и Go:

```bash
python3 cyb.py setup --profile all --no-build
```

Это подготовка исходников и пакетных окружений, а не проверка готовности runtime.

## Отдельный компонент

```bash
python3 cyb.py setup --component CybMemory
python3 cyb.py test --component CybMemory
python3 cyb.py serve cybOS --port 8004
python3 cyb.py serve Robotcyb-game --port 8005
```

`--component` также включает зависимости. Библиотеки проверяются через `test`,
статические страницы запускаются через `serve`. `run` использует только явно
объявленную команду процесса. Launcher не создаёт фиктивный запуск для planned
компонентов, библиотек, цепочки блоков или расширений.

## Что проверяет doctor

Наличие checkout и точную ревизию, необходимые исполняемые инструменты,
целостность Python-зависимостей и импорт API. Это не заменяет `test`, браузерную
проверку, запуск приложения или проверку оборудования. При ошибках команды
возвращают ненулевой код; установка не делает reset существующих папок.

## Устранение проблем

- `checkout differs`: сохраните свою работу; используйте чистую соседнюю папку
  через `python3 cyb.py --root /path/to/components setup --profile core`.
- `Python environment missing`: повторите `setup --profile core`.
- `node/cargo/go is missing`: установите инструмент для выбранного компонента
  и повторите setup. `core` не требует Rust, Go или Node.
- Модель offline: проверьте `/v1/models` вашего сервера и `CYBMODEL_URL`;
  сведения и ограничения адаптера находятся в README CybCore.

Исходники реализации окружений: [Python venv](https://docs.python.org/3/library/venv.html).
Серверы модели: [MLX-LM](https://github.com/ml-explore/mlx-lm),
[llama.cpp](https://github.com/ggml-org/llama.cpp/tree/master/tools/server).
