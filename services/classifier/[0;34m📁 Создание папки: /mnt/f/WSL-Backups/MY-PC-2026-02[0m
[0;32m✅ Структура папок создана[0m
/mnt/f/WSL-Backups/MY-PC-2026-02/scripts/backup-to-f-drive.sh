#!/bin/bash

# backup-to-f-drive.sh - Сохранение документации WSL
# Версия: 1.2
# Дата: 2026-02-18
# Автор: welem
# Описание: Сохраняет историю установок, конфиги и документацию на диск F:

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Конфигурация - диск F:
MAILRU_PATH="/mnt/f"
BACKUP_DIR="WSL-Backups/$(hostname)-$(date +%Y-%m)"
HISTORY_FILE="$HOME/.wsl-package-history"

# Функция для вывода с цветом
print_msg() {
    local color=$1
    local msg=$2
    echo -e "${color}${msg}${NC}"
}

# Проверка доступности диска
check_cloud() {
    print_msg "$BLUE" "🔍 Проверка доступности облака Mail.ru на диске F:..."
    
    if [ ! -d "$MAILRU_PATH" ]; then
        print_msg "$RED" "❌ Диск F: не найден по пути: $MAILRU_PATH"
        return 1
    fi
    
    print_msg "$GREEN" "✅ Облако доступно: $MAILRU_PATH"
    
    # Показываем свободное место
    df -h "$MAILRU_PATH" | tail -1 | awk '{print "   Свободно: " $4}'
    
    return 0
}

# Создание структуры папок - ТЕПЕРЬ ВОЗВРАЩАЕТ ТОЛЬКО ПУТЬ
create_folders() {
    local full_path="$MAILRU_PATH/$BACKUP_DIR"
    
    print_msg "$BLUE" "📁 Создание папки: $full_path"
    
    mkdir -p "$full_path/scripts"
    mkdir -p "$full_path/snapshots"
    mkdir -p "$full_path/configs"
    mkdir -p "$full_path/docs"
    
    if [ $? -eq 0 ]; then
        print_msg "$GREEN" "✅ Структура папок создана"
        # ВОЗВРАЩАЕМ ТОЛЬКО ПУТЬ, БЕЗ ЦВЕТОВ
        echo "$full_path"
    else
        print_msg "$RED" "❌ Ошибка создания папок"
        return 1
    fi
}

# Создание README с описанием скриптов
create_readme() {
    local target_dir=$1
    
    cat > "$target_dir/README.md" << EOF
# 📚 Документация WSL-скриптов

Создано: $(date)
Хост: $(hostname)
Пользователь: $(whoami)

## 📋 Описание скриптов

### 1. \`~/wsl-audit.sh\`
**Назначение:** Аудит установленных пакетов
**Использование:** \`./wsl-audit.sh\`
**Создает:** Отчет со списком всех пакетов и их категориями

### 2. \`~/wsl-history.sh\`
**Назначение:** Логирование всех установок
**Использование:** 
- \`pkg-history\` - показать историю
- \`pkg-search\` - поиск по истории
- \`pkg-stats\` - статистика установок
- \`pkg-export\` - экспорт в CSV

### 3. \`~/backup-to-f-drive.sh\`
**Назначение:** Сохранение документации на диск F:
**Использование:** \`./backup-to-f-drive.sh\`

## 🔧 Конфигурационные файлы
- \`~/.bashrc\` - настройки bash
- \`~/.wsl-package-history\` - история установок

## 📊 Снимки системы
В папке \`snapshots/\` хранятся снимки состояния системы

---
*Автоматически создано $(date)*
EOF

    print_msg "$GREEN" "✅ README создан"
}

# Сохранение скриптов
backup_scripts() {
    local target_dir=$1
    local scripts_dir="$target_dir/scripts"
    
    print_msg "$BLUE" "💾 Копирование скриптов..."
    
    # Создаем папку для скриптов (на всякий случай)
    mkdir -p "$scripts_dir"
    
    # Копируем текущий скрипт
    if [ -f "$HOME/backup-to-f-drive.sh" ]; then
        cp "$HOME/backup-to-f-drive.sh" "$scripts_dir/"
        print_msg "$GREEN" "   ✅ backup-to-f-drive.sh"
    fi
    
    # Копируем wsl-audit.sh если есть
    if [ -f "$HOME/wsl-audit.sh" ]; then
        cp "$HOME/wsl-audit.sh" "$scripts_dir/"
        print_msg "$GREEN" "   ✅ wsl-audit.sh"
    fi
    
    # Копируем историю
    if [ -f "$HISTORY_FILE" ]; then
        cp "$HISTORY_FILE" "$scripts_dir/package-history.txt"
        print_msg "$GREEN" "   ✅ package-history.txt"
    fi
}

# Сохранение конфигов
backup_configs() {
    local target_dir=$1
    local configs_dir="$target_dir/configs"
    
    print_msg "$BLUE" "⚙️  Копирование конфигураций..."
    
    # Создаем папку для конфигов
    mkdir -p "$configs_dir"
    
    # .bashrc
    if [ -f "$HOME/.bashrc" ]; then
        cp "$HOME/.bashrc" "$configs_dir/bashrc.txt"
        print_msg "$GREEN" "   ✅ .bashrc"
    fi
    
    # wsl.conf
    if [ -f "/etc/wsl.conf" ]; then
        sudo cp "/etc/wsl.conf" "$configs_dir/wsl.conf.txt"
        print_msg "$GREEN" "   ✅ wsl.conf"
    fi
}

# Создание снимка системы
create_snapshot() {
    local target_dir=$1
    local snapshots_dir="$target_dir/snapshots"
    local snapshot_file="$snapshots_dir/system-snapshot-$(date +%Y%m%d-%H%M%S).txt"
    
    print_msg "$BLUE" "📸 Создание снимка системы..."
    
    # Создаем папку для снимков
    mkdir -p "$snapshots_dir"
    
    {
        echo "========================================="
        echo "СНИМОК СИСТЕМЫ WSL"
        echo "========================================="
        echo "Дата: $(date)"
        echo "Хост: $(hostname)"
        echo "Пользователь: $(whoami)"
        echo "Версия Ubuntu: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'N/A')"
        echo "Версия ядра: $(uname -r)"
        echo ""
        
        echo "🔧 УСТАНОВЛЕННЫЕ ПАКЕТЫ (ручные):"
        echo "-----------------------------------------"
        apt list --installed 2>/dev/null | grep -v automatic | grep -v Listing || echo "Нет ручных пакетов"
        echo ""
        
        echo "📊 ИСТОРИЯ УСТАНОВОК:"
        echo "-----------------------------------------"
        if [ -f "$HISTORY_FILE" ]; then
            cat "$HISTORY_FILE"
        else
            echo "История не найдена"
        fi
        
    } > "$snapshot_file"
    
    print_msg "$GREEN" "✅ Снимок создан: $(basename "$snapshot_file")"
}

# Главная функция
main() {
    print_msg "$BLUE" "☁️  ====== АРХИВАЦИЯ В MAIL.RU CLOUD ======"
    echo ""
    
    # Проверяем диск
    if ! check_cloud; then
        print_msg "$RED" "❌ Облако недоступно. Выход."
        exit 1
    fi
    
    echo ""
    
    # Создаем папки и получаем чистый путь
    TARGET_DIR=$(create_folders)
    if [ $? -ne 0 ]; then
        exit 1
    fi
    
    echo ""
    
    # Создаем README
    create_readme "$TARGET_DIR"
    
    echo ""
    
    # Копируем скрипты
    backup_scripts "$TARGET_DIR"
    
    echo ""
    
    # Копируем конфиги
    backup_configs "$TARGET_DIR"
    
    echo ""
    
    # Создаем снимок
    create_snapshot "$TARGET_DIR"
    
    echo ""
    print_msg "$GREEN" "✅ ====== АРХИВАЦИЯ ЗАВЕРШЕНА ======"
    print_msg "$BLUE" "📁 Все файлы сохранены в: $TARGET_DIR"
    
    # Показываем содержимое
    echo ""
    ls -la "$TARGET_DIR"
}

# Запуск
main
