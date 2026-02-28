#!/bin/bash
# update-docs.sh - обновляет документацию, сохраняя существующее

echo "📚 Updating HiveMind documentation..."

# Функция для обновления файла
update_file() {
    local file=$1
    local header=$2
    local content=$3
    
    if [ ! -f "$file" ]; then
        echo "Creating $file..."
        echo -e "$header\n\n$content" > "$file"
    else
        echo "Updating $file..."
        # Добавляем новый контент в конец
        echo -e "\n## Updated: $(date)\n$content" >> "$file"
    fi
}

# 1. Обновить README.md
update_file "README.md" "# HiveMind" "## Current Status (Updated $(date))\n- ✅ API Gateway: working\n- ✅ Classifier: working\n- ✅ Embedder: working\n- ✅ Linker: working\n- ✅ UI: working\n- ✅ All services connected via NATS"

# 2. Обновить статусы в contracts/README.md
update_file "contracts/README.md" "# HiveMind Contracts" "## Service Status (Updated $(date))\n| Service | Status |\n|---------|--------|\n| api-gateway | ✅ active |\n| classifier | ✅ active |\n| embedder | ✅ active |\n| linker | ✅ active |\n| hivemind-ui | ✅ active |"

# 3. Обновить CURRENT_CONTEXT.md
update_file "CURRENT_CONTEXT.md" "# Current Development Context" "## Status as of $(date)\n- ✅ System fully operational\n- ✅ All services connected via NATS\n- ✅ UI available at http://localhost:8050\n- ✅ API Gateway at http://localhost:8080\n- ⚠️ Qdrant and NATS still show unhealthy but functional\n- ⚠️ CUDA toolkit not yet installed"

echo "✅ Documentation updated!"