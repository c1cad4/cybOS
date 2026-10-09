# Разработка

## Рабочая папка

Все checkout-папки находятся на одном уровне. Для облачных задач используйте существующую изолированную рабочую папку; отдельный worktree создаётся только по прямому запросу.

```bash
git clone https://github.com/c1cad4/cybOS.git
python3 cybOS/tools/bootstrap.py
python3 cybLaunch/launcher.py list
python3 cybLaunch/launcher.py test all
```

`ecosystem.lock.json` содержит точные Git-ревизии. Bootstrap клонирует отсутствующие проекты, а существующие оставляет без reset/перезаписи. `--verify` проверяет HEAD существующих папок против lock-файла. При разработке изменения в соседних библиотеках видны стенду через Cargo path dependencies.

## Инструменты

- Rust 1.99.0 и Cargo, C/C++ linker для native-зависимостей.
- Go 1.17.8 для исторического узла `go-cyber`.
- Python 3.12+, Node 24+ для CLI, проверок и статических приложений.
- Linux X11/Wayland или виртуальный Xvfb для нативного GUI.
- macOS/Xcode для `cybchat`, BLE и упаковки приложения Apple.

Значения токенов не хранятся в репозиториях. Локальная библиотечная и unit-проверка не требует платных API или кошелька.

## Запуск

```bash
python3 cybLaunch/launcher.py serve cybOS --port 8004
python3 cybLaunch/launcher.py serve Robotcyb-game --port 8005
cd CybOS-demo
python3 scripts/bootstrap_components.py
cargo test --locked -j 4
CYBOS_DATA_DIR=/path/to/local/data cargo run --locked
```

В Price Tracker используется DexScreener; требуется Chrome/Edge 120+ и разрешение загрузки распакованных расширений. Данные game и examples с меткой demo — фикстуры, а не реальные показания устройств.

## Проверки и поставка

Проверяйте каждый изменённый компонент и приложение-интегратор. CI клонирует зависимости по фиксированным SHA. При изменении API сначала публикуется библиотечный коммит, затем обновляются pins интегратора. Не смешивайте ветку рабочего прототипа с выпуском для конечных пользователей. Публикация GitHub release, моделей или hardware firmware выполняется отдельной задачей.

## Агенты и долговременная память

```bash
cd CybCore
python3 scripts/bootstrap_components.py
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python run.py
```

Порт 8010, loopback. CybCore содержит UI, `/docs`, `/health`, `/agents`, `/tasks`.
Запуск через cybLaunch: активируйте `.venv`, затем `python3 ../cybLaunch/launcher.py run CybCore`.
Знания и идемпотентные результаты хранятся в SQLite; пользовательский реестр агентов сессионный.
Другие новые компоненты имеют честный статус planned и пока не исполняются.
