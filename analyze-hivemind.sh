#!/usr/bin/env bash
# analyze-hivemind.sh — максимально простая версия

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✅ $1${NC}"; }
print_error()   { echo -e "${RED}❌ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
print_info()    { echo -e "${BLUE}🔍 $1${NC}"; }
print_section() { echo -e "\n${PURPLE}📋 $1${NC}"; }

# ==========================================
# Главная функция
# ==========================================

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${PURPLE}🐝 Астролябия: анализ HiveMind${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"

PROJECT_PATH="${1:-/home/welem/hivemind}"
echo "📁 $PROJECT_PATH"

# Проверка существования
if [ ! -d "$PROJECT_PATH" ]; then
    print_error "Папка не существует: $PROJECT_PATH"
    exit 1
fi

# ==========================================
# 1. Анализ корневого docker-compose.yml
# ==========================================
print_section "Анализ корневого docker-compose.yml"

if [ -f "$PROJECT_PATH/docker-compose.yml" ]; then
    print_success "Найден docker-compose.yml"
    
    # Просто покажем содержимое
    echo "   Содержит сервисы:"
    grep -E "^  [a-zA-Z0-9_-]+:" "$PROJECT_PATH/docker-compose.yml" | while read line; do
        echo "     $line"
    done
else
    print_warning "Нет docker-compose.yml"
fi

# ==========================================
# 2. Анализ init-scripts
# ==========================================
print_section "Анализ init-scripts"

if [ -d "$PROJECT_PATH/init-scripts" ]; then
    print_success "Папка init-scripts найдена"
    
    echo "   Содержимое:"
    ls -la "$PROJECT_PATH/init-scripts" | grep -v "^total" | while read line; do
        echo "     $line"
    done
else
    print_warning "Нет папки init-scripts"
fi

# ==========================================
# 3. Анализ сервисов
# ==========================================
print_section "Анализ сервисов"

if [ -d "$PROJECT_PATH/services" ]; then
    print_success "Папка services найдена"
    
    # Считаем сервисы
    service_count=0
    for service in "$PROJECT_PATH/services"/*; do
        if [ -d "$service" ]; then
            ((service_count++))
        fi
    done
    
    echo "   Всего сервисов: $service_count"
    echo ""
    
    # Анализируем каждый сервис
    for service in "$PROJECT_PATH/services"/*; do
        if [ -d "$service" ]; then
            service_name=$(basename "$service")
            echo -e "${CYAN}📦 Сервис: $service_name${NC}"
            
            # Проверяем наличие ключевых файлов
            [ -f "$service/Dockerfile" ] && echo "   ✅ Dockerfile"
            [ -f "$service/README.md" ] && echo "   ✅ README.md"
            [ -f "$service/.env" ] && echo "   ⚠️  .env файл"
            [ -f "$service/.env.example" ] && echo "   ✅ .env.example"
            [ -d "$service/tests" ] || [ -d "$service/test" ] && echo "   ✅ папка с тестами"
            
            # Определяем язык
            if [ -f "$service/package.json" ]; then
                echo "   📦 Node.js проект"
            elif [ -f "$service/pyproject.toml" ]; then
                echo "   🐍 Python (Poetry) проект"
            elif [ -f "$service/requirements.txt" ]; then
                echo "   🐍 Python (pip) проект"
            elif [ -f "$service/go.mod" ]; then
                echo "   🐹 Go проект"
            elif [ -f "$service/Cargo.toml" ]; then
                echo "   🦀 Rust проект"
            fi
            
            echo ""
        fi
    done
else
    print_warning "Нет папки services"
fi

# ==========================================
# 4. Другое содержимое
# ==========================================
print_section "Другие папки в корне"

for item in "$PROJECT_PATH"/*; do
    if [ -d "$item" ]; then
        name=$(basename "$item")
        if [ "$name" != "services" ] && [ "$name" != "init-scripts" ]; then
            echo "   📁 $name/"
        fi
    fi
done

# ==========================================
# 5. Итог
# ==========================================
print_section "Итог"

echo "📁 $PROJECT_PATH"
[ -f "$PROJECT_PATH/docker-compose.yml" ] && echo "├── docker-compose.yml"
[ -d "$PROJECT_PATH/init-scripts" ] && echo "├── init-scripts/"

if [ -d "$PROJECT_PATH/services" ]; then
    echo "├── services/ ($service_count сервисов)"
    # Покажем первые 3 сервиса
    count=0
    for service in "$PROJECT_PATH/services"/*; do
        if [ -d "$service" ] && [ $count -lt 3 ]; then
            echo "│   ├── $(basename "$service")/"
            ((count++))
        fi
    done
    if [ $service_count -gt 3 ]; then
        echo "│   └── ..."
    fi
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
print_success "Анализ завершён"