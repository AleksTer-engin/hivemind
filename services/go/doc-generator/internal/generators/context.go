package generators

import (
    "fmt"
    "os"
    "path/filepath"
    "strings"
        
    "github.com/welem/hivemind/doc-generator/internal/services"
)

func GenerateCurrentContext(statuses map[string]services.ServiceStatus, outputPath, timestamp string) error {
    var content strings.Builder
    
    content.WriteString("# 📊 Текущий контекст разработки\n\n")
    content.WriteString(fmt.Sprintf("**Обновлено**: %s\n\n", timestamp))
    
    content.WriteString("## 🚦 Статус сервисов\n\n")
    
    // Считаем статистику
    total := len(statuses)
    running := 0
    for _, s := range statuses {
        if s.Running {
            running++
        }
    }
    
    content.WriteString(fmt.Sprintf("✅ **Работает**: %d/%d сервисов\n\n", running, total))
    
    content.WriteString("| Сервис | Статус | Порты |\n")
    content.WriteString("|--------|--------|-------|\n")
    
    for name, status := range statuses {
        statusEmoji := "❌"
        if status.Running {
            statusEmoji = "✅"
        }
        ports := strings.Join(status.Ports, ", ")
        content.WriteString(fmt.Sprintf("| `%s` | %s %s | %s |\n",
            name, statusEmoji, status.Status, ports))
    }
    
    content.WriteString("\n## 📅 Последние изменения\n\n")
    content.WriteString("- " + timestamp + " — автоматическое обновление документации\n")
    
    return os.WriteFile(filepath.Join(outputPath, "CURRENT_CONTEXT.md"), []byte(content.String()), 0644)
}