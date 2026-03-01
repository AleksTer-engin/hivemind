package generators

import (
    "fmt"
    "os"
    "path/filepath"
    "sort"
    "strings"
    
    "github.com/welem/hivemind/doc-generator/internal/contracts"
    "github.com/welem/hivemind/doc-generator/internal/services"
)

func GenerateAPIContracts(contracts *contracts.ContractData, statuses map[string]services.ServiceStatus, outputPath, timestamp string) error {
    var content strings.Builder
    
    content.WriteString("# 📜 API Контракты HiveMind\n\n")
    content.WriteString(fmt.Sprintf("*Обновлено: %s*\n\n", timestamp))
    content.WriteString("## 📋 Сводка\n\n")
    
    // Сводка по сервисам
    content.WriteString("| Сервис | Статус | Язык | Версия |\n")
    content.WriteString("|--------|--------|------|--------|\n")
    
    var names []string
    for name := range contracts.Services {
        names = append(names, name)
    }
    sort.Strings(names)
    
    for _, name := range names {
        svc := contracts.Services[name]
        status := "❌ не работает"
        emoji := "❌"
        
        if s, ok := statuses[name]; ok && s.Running {
            status = "✅ работает"
            emoji = "✅"
        }
        
        content.WriteString(fmt.Sprintf("| %s | %s %s | %s | %s |\n",
            name, emoji, status, svc.Service.Language, svc.Service.Version))
    }
    
    // API Endpoints
    content.WriteString("\n## 🔌 API Endpoints\n\n")
    content.WriteString("| Метод | Путь | Описание |\n")
    content.WriteString("|-------|------|----------|\n")
    
    sort.Slice(contracts.APIs, func(i, j int) bool {
        return contracts.APIs[i].Path < contracts.APIs[j].Path
    })
    
    for _, api := range contracts.APIs {
        content.WriteString(fmt.Sprintf("| %s | `%s` | %s |\n",
            api.Method, api.Path, api.Description))
    }
    
    // NATS Events
    content.WriteString("\n## 📨 NATS Events\n\n")
    content.WriteString("| Топик | Описание |\n")
    content.WriteString("|-------|----------|\n")
    
    sort.Slice(contracts.Events, func(i, j int) bool {
        return contracts.Events[i].Topic < contracts.Events[j].Topic
    })
    
    for _, event := range contracts.Events {
        content.WriteString(fmt.Sprintf("| `%s` | %s |\n",
            event.Topic, event.Description))
    }
    
    return os.WriteFile(filepath.Join(outputPath, "API_CONTRACTS.md"), []byte(content.String()), 0644)
}