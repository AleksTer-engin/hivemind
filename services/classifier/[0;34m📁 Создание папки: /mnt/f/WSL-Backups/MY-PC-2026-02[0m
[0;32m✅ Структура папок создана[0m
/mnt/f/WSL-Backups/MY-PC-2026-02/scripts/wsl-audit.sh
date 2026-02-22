#!/bin/bash

# wsl-audit.sh - Аудит установленных пакетов в WSL
# Создает таблицу с пояснениями: что установлено и зачем

OUTPUT_FILE="$HOME/wsl-packages-audit-$(date +%Y%m%d).txt"

echo "🔍 АУДИТ ПАКЕТОВ WSL" > "$OUTPUT_FILE"
echo "=====================" >> "$OUTPUT_FILE"
echo "Дата: $(date)" >> "$OUTPUT_FILE"
echo "Система: $(lsb_release -d | cut -f2)" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Функция для категоризации пакетов
categorize_package() {
    local pkg=$1
    local desc=$2
    
    # Базовые категории на основе имени пакета и описания
    case $pkg in
        *build-essential*|*gcc*|*g++*|*make*|*cmake*)
            echo "🛠️ Инструменты разработки (компиляция)"
            ;;
        *python*|*pip*|*venv*|*conda*)
            echo "🐍 Python-экосистема"
            ;;
        *node*|*npm*|*yarn*|*javascript*)
            echo "🟩 JavaScript/Node.js"
            ;;
        *git*|*svn*|*mercurial*)
            echo "📦 Системы контроля версий"
            ;;
        *docker*|*containerd*|*podman*)
            echo "🐳 Контейнеризация"
            ;;
        *vim*|*nano*|*emacs*|*editor*)
            echo "📝 Текстовые редакторы"
            ;;
        *curl*|*wget*|*httpie*|*ftp*)
            echo "🌐 Сетевые утилиты"
            ;;
        *htop*|*top*|*iotop*|*nmon*|*glances*)
            echo "📊 Мониторинг системы"
            ;;
        *openssh*|*ssh*|*telnet*|*netcat*)
            echo "🔐 Удаленный доступ"
            ;;
        *sqlite*|*mysql*|*postgres*|*mongodb*|*redis*)
            echo "🗄️ Базы данных"
            ;;
        *firefox*|*chrome*|*browser*)
            echo "🌍 Браузеры"
            ;;
        *vlc*|*mpv*|*ffmpeg*|*gimp*|*inkscape*)
            echo "🎨 Мультимедиа/графика"
            ;;
        *zsh*|*bash*|*fish*|*shell*|*terminal*)
            echo "⌨️ Оболочки/терминалы"
            ;;
        *)
            # Если не попали в категории, пытаемся угадать по описанию
            if [[ $desc == *"library"* ]] || [[ $desc == *"shared library"* ]]; then
                echo "📚 Системные библиотеки"
            elif [[ $desc == *"utility"* ]] || [[ $desc == *"tool"* ]]; then
                echo "🔧 Системные утилиты"
            elif [[ $desc == *"font"* ]] || [[ $desc == *"theme"* ]]; then
                echo "🎯 Шрифты/темы"
            elif [[ $desc == *"documentation"* ]] || [[ $desc == *"manual"* ]]; then
                echo "📖 Документация"
            else
                echo "❓ Другое (требует ручной проверки)"
            fi
            ;;
    esac
}

echo "📦 ПАКЕТЫ, УСТАНОВЛЕННЫЕ ВРУЧНУЮ (НЕ АВТОМАТИЧЕСКИЕ):" >> "$OUTPUT_FILE"
echo "=================================================" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

# Получаем список пакетов без авто-зависимостей
apt list --installed 2>/dev/null | grep -v "automatic" | grep -v "Listing..." | while read line; do
    # Парсим строку вида "package/noble,now 1.0 amd64 [installed]"
    pkg_full=$(echo "$line" | cut -d'/' -f1)
    pkg_name=$(echo "$pkg_full" | cut -d' ' -f1)
    
    # Получаем описание пакета
    description=$(apt show "$pkg_name" 2>/dev/null | grep -m1 "Description:" | cut -d' ' -f2-)
    
    # Определяем категорию
    category=$(categorize_package "$pkg_name" "$description")
    
    # Формируем запись в таблицу
    printf "%-25s | %-35s | %s\n" "$pkg_name" "$category" "${description:0:70}" >> "$OUTPUT_FILE"
done

echo "" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"
echo "📦 ВСЕ ОСТАЛЬНЫЕ ПАКЕТЫ (СИСТЕМНЫЕ ЗАВИСИМОСТИ):" >> "$OUTPUT_FILE"
echo "=================================================" >> "$OUTPUT_FILE"
echo "Всего системных пакетов: $(apt list --installed 2>/dev/null | grep "automatic" | wc -l)" >> "$OUTPUT_FILE"
echo "Обычно это библиотеки и зависимости, необходимые для работы основных программ." >> "$OUTPUT_FILE"
echo "Их не нужно удалять вручную — это сломает систему." >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "💾 ИНФОРМАЦИЯ О ДИСКЕ:" >> "$OUTPUT_FILE"
echo "=====================" >> "$OUTPUT_FILE"
df -h / >> "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "🔧 WSL КОНФИГУРАЦИЯ:" >> "$OUTPUT_FILE"
echo "===================" >> "$OUTPUT_FILE"
if [ -f /etc/wsl.conf ]; then
    cat /etc/wsl.conf >> "$OUTPUT_FILE"
else
    echo "wsl.conf не найден (используются настройки по умолчанию)" >> "$OUTPUT_FILE"
fi

echo "" >> "$OUTPUT_FILE"
echo "✅ АУДИТ ЗАВЕРШЕН. Отчет сохранен в: $OUTPUT_FILE" >> "$OUTPUT_FILE"

# Показываем результат
cat "$OUTPUT_FILE"

# Создаем симлинк для быстрого доступа
ln -sf "$OUTPUT_FILE" "$HOME/latest-audit.txt"
echo "📎 Быстрый доступ: cat ~/latest-audit.txt"
