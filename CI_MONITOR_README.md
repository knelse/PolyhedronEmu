# CI Monitor for PolyhedronEmu

This script continuously monitors git commits in the repository and runs an automated CI pipeline whenever a new commit is pushed.

## Features

- **Continuous Monitoring**: Monitors git repository for new commits every 30 seconds (configurable)
- **Multi-stage Pipeline**: Runs flake8 → pytest → Godot build → archive creation
- **Build History**: Archives successful builds with timestamps and commit info
- **Persistent State**: Remembers the last processed commit across restarts
- **Detailed Logging**: Logs all activities to `logs/ci_monitor.log`
- **Build Reports**: Maintains a JSON report of all build attempts

## Prerequisites

1. **Python 3.7+** with the following standard library modules:
   - `subprocess`, `pathlib`, `zipfile`, `json`, `logging`, `datetime`
   
2. **Git** installed and repository initialized

3. **PowerShell** with execution policy allowing script execution

4. **Build script** `build_local.ps1` in the repository root

5. **Python packages** for linting and testing:
   ```bash
   pip install flake8 pytest
   ```

## Usage

### Basic Usage
```bash
python ci_monitor.py
```

### Advanced Options
```bash
# Custom repository path
python ci_monitor.py --repo-path /path/to/repo

# Custom polling interval (seconds)
python ci_monitor.py --poll-interval 60

# Custom Godot executable path
python ci_monitor.py --godot-exe "C:/Games/Godot/godot.exe"
```

## CI Pipeline Stages

### 1. Flake8 Linting
- Excludes `addons` and `.builds` folders
- Uses max line length of 100 characters
- **Stops pipeline if errors found**

### 2. Pytest Testing
- Runs tests in `tests/` directory
- Uses verbose mode with no traceback (`-v --tb=no`)
- **Stops pipeline if tests fail**

### 3. Godot Build
- Uses existing `build_local.ps1 -Build` script
- Handles cleaning, importing, exporting, and file copying automatically
- Builds for Windows 64-bit platform with all necessary runtime files
- **Stops pipeline if build fails**

### 4. Archive Creation
- Creates timestamped ZIP archive in `.build_history/` folder
- Includes all build output and commit information
- Updates build report JSON

## Directory Structure

```
PolyhedronEmu/
├── ci_monitor.py           # The CI monitor script
├── .build_history/         # Build archives and reports (created automatically)
│   ├── ci_state.json      # Last processed commit state
│   ├── build_report.json  # Historical build reports
│   └── build_*.zip        # Archived builds
├── .builds/                # Temporary build output (recreated each build)
├── logs/
│   └── ci_monitor.log     # CI monitor activity log
└── ...
```

## Archive Naming

Archives are named with the pattern: `build_YYYYMMDD_HHMMSS_COMMITHASH.zip`

Example: `build_20241211_143022_a1b2c3d4.zip`

## Build Reports

The `build_report.json` file contains an array of build attempts with:
- Timestamp
- Commit information (hash, message, author, date)  
- Success status
- Archive filename (if successful)

## Stopping the Monitor

- **Ctrl+C**: Gracefully stops the monitor
- The script will resume from the last processed commit when restarted

## Troubleshooting

### Common Issues

1. **Godot executable not found**
   - Update the path in the script or use `--godot-exe` argument
   - Ensure Godot export templates are installed

2. **Git repository not found**
   - Ensure you're running the script in a git repository
   - Use `--repo-path` to specify the correct path

3. **Python dependencies missing**
   - Install flake8: `pip install flake8`
   - Install pytest: `pip install pytest`

4. **Permission errors**
   - Ensure write permissions to the repository directory
   - Check that `.build_history` and `logs` directories can be created

### Log Files

Check `logs/ci_monitor.log` for detailed information about:
- Pipeline execution
- Build errors
- File operations
- System issues

## Configuration

The script can be customized by modifying these variables in the `CIMonitor.__init__()` method:

- `godot_exe`: Path to Godot executable
- `poll_interval`: How often to check for new commits (seconds)
- Build directory names
- Logging configuration

## Integration

To run as a service or background process:

**Windows:**
```bash
# Run in background (PowerShell)
Start-Process python -ArgumentList "ci_monitor.py" -WindowStyle Hidden

# Or use Windows Task Scheduler for automatic startup
```

**Linux/Mac:**
```bash
# Run in background
nohup python ci_monitor.py &

# Or create a systemd service
``` 

---

# CI Монитор для PolyhedronEmu (Русский)

Этот скрипт непрерывно отслеживает git коммиты в репозитории и запускает автоматизированный CI пайплайн при каждом новом коммите.

## Функции

- **Непрерывный мониторинг**: Отслеживает git репозиторий на новые коммиты каждые 30 секунд (настраивается)
- **Многоэтапный пайплайн**: Запускает flake8 → pytest → сборку Godot → создание архива
- **История сборок**: Архивирует успешные сборки с временными метками и информацией о коммитах
- **Постоянное состояние**: Запоминает последний обработанный коммит между перезапусками
- **Подробное логирование**: Записывает все действия в `logs/ci_monitor.log`
- **Отчеты о сборках**: Ведет JSON отчет обо всех попытках сборки

## Требования

1. **Python 3.7+** со следующими стандартными библиотечными модулями:
   - `subprocess`, `pathlib`, `zipfile`, `json`, `logging`, `datetime`
   
2. **Git** установлен и репозиторий инициализирован

3. **PowerShell** с политикой выполнения, разрешающей выполнение скриптов

4. **Скрипт сборки** `build_local.ps1` в корне репозитория

5. **Python пакеты** для линтинга и тестирования:
   ```bash
   pip install flake8 pytest
   ```

## Использование

### Базовое использование
```bash
python ci_monitor.py
```

### Расширенные опции
```bash
# Пользовательский путь к репозиторию
python ci_monitor.py --repo-path /path/to/repo

# Пользовательский интервал опроса (секунды)
python ci_monitor.py --poll-interval 60

# Пользовательский путь к исполняемому файлу Godot
python ci_monitor.py --godot-exe "C:/Games/Godot/godot.exe"
```

## Этапы CI пайплайна

### 1. Линтинг Flake8
- Исключает папки `addons` и `.builds`
- Использует максимальную длину строки 100 символов
- **Останавливает пайплайн при обнаружении ошибок**

### 2. Тестирование Pytest
- Запускает тесты в директории `tests/`
- Использует подробный режим без трассировки (`-v --tb=no`)
- **Останавливает пайплайн при неудачных тестах**

### 3. Сборка Godot
- Использует существующий скрипт `build_local.ps1 -Build`
- Автоматически обрабатывает очистку, импорт, экспорт и копирование файлов
- Собирает для платформы Windows 64-bit со всеми необходимыми runtime файлами
- **Останавливает пайплайн при неудачной сборке**

### 4. Создание архива
- Создает ZIP архив с временной меткой в папке `.build_history/`
- Включает весь вывод сборки и информацию о коммите
- Обновляет JSON отчет о сборке

## Структура директорий

```
PolyhedronEmu/
├── ci_monitor.py           # Скрипт CI монитора
├── .build_history/         # Архивы сборок и отчеты (создается автоматически)
│   ├── ci_state.json      # Состояние последнего обработанного коммита
│   ├── build_report.json  # Исторические отчеты о сборках
│   └── build_*.zip        # Архивированные сборки
├── .builds/                # Временный вывод сборки (пересоздается при каждой сборке)
├── logs/
│   └── ci_monitor.log     # Лог активности CI монитора
└── ...
```

## Именование архивов

Архивы именуются по шаблону: `build_YYYYMMDD_HHMMSS_COMMITHASH.zip`

Пример: `build_20241211_143022_a1b2c3d4.zip`

## Отчеты о сборках

Файл `build_report.json` содержит массив попыток сборки с:
- Временной меткой
- Информацией о коммите (хэш, сообщение, автор, дата)
- Статусом успеха
- Именем файла архива (если успешно)

## Остановка монитора

- **Ctrl+C**: Корректно останавливает монитор
- Скрипт возобновит работу с последнего обработанного коммита при перезапуске

## Устранение неполадок

### Распространенные проблемы

1. **Исполняемый файл Godot не найден**
   - Обновите путь в скрипте или используйте аргумент `--godot-exe`
   - Убедитесь, что установлены экспортные шаблоны Godot

2. **Git репозиторий не найден**
   - Убедитесь, что запускаете скрипт в git репозитории
   - Используйте `--repo-path` для указания правильного пути

3. **Отсутствуют зависимости Python**
   - Установите flake8: `pip install flake8`
   - Установите pytest: `pip install pytest`

4. **Ошибки разрешений**
   - Убедитесь в наличии прав записи в директорию репозитория
   - Проверьте, что можно создать директории `.build_history` и `logs`

### Лог файлы

Проверьте `logs/ci_monitor.log` для подробной информации о:
- Выполнении пайплайна
- Ошибках сборки
- Файловых операциях
- Системных проблемах

## Конфигурация

Скрипт можно настроить, изменив эти переменные в методе `CIMonitor.__init__()`:

- `godot_exe`: Путь к исполняемому файлу Godot
- `poll_interval`: Как часто проверять новые коммиты (секунды)
- Имена директорий сборки
- Конфигурация логирования

## Интеграция

Для запуска как сервис или фоновый процесс:

**Windows:**
```bash
# Запуск в фоне (PowerShell)
Start-Process python -ArgumentList "ci_monitor.py" -WindowStyle Hidden

# Или используйте Планировщик задач Windows для автоматического запуска
```

**Linux/Mac:**
```bash
# Запуск в фоне
nohup python ci_monitor.py &

# Или создайте systemd сервис
``` 