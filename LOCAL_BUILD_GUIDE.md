# PolyhedronEmu Local Build Guide


## Prerequisites

- **MongoDB**: Required for database operations
  - Install MongoDB Community Server from https://www.mongodb.com/try/download/community
  - Ensure MongoDB service is running before starting the server

## Quick Start

1. **Set up build environment:**
   ```powershell
   .\build_local.ps1 -Setup
   ```

2. **Build the project:**
   ```powershell
   .\build_local.ps1 -Build
   ```

3. **Run the built executable:**
   ```powershell
   .\build_local.ps1 -Run
   ```

## Manual Setup (Alternative)

### 1. Download Godot 4.4.1

Download the Windows 64-bit executable:
- **URL**: https://github.com/godotengine/godot/releases/tag/4.4.1-stable
- **File**: `Godot_v4.4.1-stable_win64.exe`
- **Save to**: `tools/Godot_v4.4.1-stable_win64.exe`

### 2. Download Export Templates

Download and install export templates:
- **URL**: https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_export_templates.tpz
- **Extract to**: `%APPDATA%\Godot\export_templates\4.4.1-stable\`

### 3. Manual Build Commands

```powershell
# Import resources
.\tools\Godot_v4.4.1-stable_win64.exe --headless --import

# Export project
.\tools\Godot_v4.4.1-stable_win64.exe --headless --export-release "Win64" ".builds\PolyhedronEmu_win64.exe"
```

## Troubleshooting

### Missing Export Templates
If you get "Export template not found" errors:
1. Download export templates from the Godot releases page
2. Extract to `%APPDATA%\Godot\export_templates\4.4.1-stable\`
3. Ensure the folder contains `windows_debug.exe` and `windows_release.exe`

### py4godot Issues
If Python scripts don't work:
1. Verify `pythonscript.dll` exists in `addons/py4godot/cpython-3.12.4-windows64/python/`
2. Check that `python.gdextension` is properly configured
3. Restart Godot editor after py4godot changes

### Build Failures
If export fails:
1. Try importing resources first: `--headless --import`
2. Check export preset configuration in Godot editor
3. Verify all resources are properly imported
4. Check console output for specific error messages

---

# Руководство по локальной сборке PolyhedronEmu (Русский)

## Требования

- **MongoDB**: Необходим для работы с базой данных
  - Установите MongoDB Community Server с https://www.mongodb.com/try/download/community
  - Убедитесь, что служба MongoDB запущена перед запуском сервера

## Быстрый старт

1. **Настройка среды сборки:**
   ```powershell
   .\build_local.ps1 -Setup
   ```

2. **Сборка проекта:**
   ```powershell
   .\build_local.ps1 -Build
   ```

3. **Запуск собранного исполняемого файла:**
   ```powershell
   .\build_local.ps1 -Run
   ```

## Ручная настройка (Альтернатива)

### 1. Скачать Godot 4.4.1

Скачайте исполняемый файл Windows 64-bit:
- **URL**: https://github.com/godotengine/godot/releases/tag/4.4.1-stable
- **Файл**: `Godot_v4.4.1-stable_win64.exe`
- **Сохранить в**: `tools/Godot_v4.4.1-stable_win64.exe`

### 2. Скачать export templates

Скачайте и установите export templates:
- **URL**: https://github.com/godotengine/godot/releases/download/4.4.1-stable/Godot_v4.4.1-stable_export_templates.tpz
- **Извлечь в**: `%APPDATA%\Godot\export_templates\4.4.1-stable\`

### 3. Команды ручной сборки

```powershell
# Импорт ресурсов
.\tools\Godot_v4.4.1-stable_win64.exe --headless --import

# Экспорт проекта
.\tools\Godot_v4.4.1-stable_win64.exe --headless --export-release "Win64" ".builds\PolyhedronEmu_win64.exe"
```

## Устранение неполадок

### Отсутствующие export templates
Если вы получаете ошибки "Export template not found":
1. Скачайте export templates со страницы релизов Godot
2. Извлеките в `%APPDATA%\Godot\export_templates\4.4.1-stable\`
3. Убедитесь, что папка содержит `windows_debug.exe` и `windows_release.exe`

### Проблемы с py4godot
Если Python скрипты не работают:
1. Проверьте, что `pythonscript.dll` существует в `addons/py4godot/cpython-3.12.4-windows64/python/`
2. Проверьте, что `python.gdextension` правильно настроен
3. Перезапустите редактор Godot после изменений py4godot

### Неудачи сборки
Если экспорт не удается:
1. Попробуйте сначала импортировать ресурсы: `--headless --import`
2. Проверьте конфигурацию пресета экспорта в редакторе Godot
3. Убедитесь, что все ресурсы правильно импортированы
4. Проверьте вывод консоли на предмет конкретных сообщений об ошибках