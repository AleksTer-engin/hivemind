package generators

import (
    "fmt"
    "os"
    "path/filepath"
	"sort"
    "strings"
    
    "github.com/welem/hivemind/doc-generator/internal/contracts"
    "github.com/welem/hivemind/doc-generator/internal/docker"
)

func GenerateArchitecture(contracts *contracts.ContractData, compose *docker.ComposeData, outputPath, timestamp string) error {
    var content strings.Builder
    
    content.WriteString("# 🏗️ Идеальная архитектура HiveMind\n\n")
    content.WriteString(fmt.Sprintf("*Обновлено: %s*\n\n", timestamp))
    
    // Диаграмма (текстовая)
    content.WriteString("```\n")
    content.WriteString("┌─────────────────────────────────────────────────────────────────┐\n")
    content.WriteString("│                         КЛИЕНТСКИЙ СЛОЙ                          │\n")
    content.WriteString("│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │\n")
    content.WriteString("│  │    Web UI    │    │  API Client  │    │  CLI Tool    │      │\n")
    content.WriteString("│  │  (Streamlit) │    │  (external)  │    │  (internal)  │      │\n")
    content.WriteString("│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘      │\n")
    content.WriteString("└─────────┼───────────────────┼───────────────────┼────────────────┘\n")
    content.WriteString("          │                   │                   │                 \n")
    content.WriteString("          ▼                   ▼                   ▼                 \n")
    content.WriteString("┌─────────────────────────────────────────────────────────────────┐\n")
    content.WriteString("│                      API GATEWAY (порт 8080)                     │\n")
    content.WriteString("└─────────────────────────────────────┬───────────────────────────┘\n")
    content.WriteString("                                      │                             \n")
    content.WriteString("                                      ▼                             \n")
    content.WriteString("┌─────────────────────────────────────────────────────────────────┐\n")
    content.WriteString("│                      NATS (событийная шина)                      │\n")
    content.WriteString("└───────────┬─────────────────┬─────────────────┬─────────────────┘\n")
    content.WriteString("            │                 │                 │                   \n")
    content.WriteString("            ▼                 ▼                 ▼                   \n")
    content.WriteString("┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐ \n")
    content.WriteString("│    Classifier     │ │     Embedder      │ │      Linker       │ \n")
    content.WriteString("│     (Python)      │ │     (Python)      │ │       (Go)        │ \n")
    content.WriteString("└─────────┬─────────┘ └─────────┬─────────┘ └─────────┬─────────┘ \n")
    content.WriteString("          │                     │                     │           \n")
    content.WriteString("          ▼                     ▼                     ▼           \n")
    content.WriteString("┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐ \n")
    content.WriteString("│     Postgres      │ │      Qdrant       │ │       Neo4j       │ \n")
    content.WriteString("│   (реляционная)   │ │    (векторная)    │ │     (графовая)    │ \n")
    content.WriteString("└───────────────────┘ └───────────────────┘ └───────────────────┘ \n")
    content.WriteString("```\n\n")
    
    // Список сервисов
    content.WriteString("## 📦 Сервисы\n\n")
    content.WriteString("| Сервис | Язык | Описание |\n")
    content.WriteString("|--------|------|----------|\n")
    
    // Сортируем имена для красоты
    var names []string
    for name := range contracts.Services {
        names = append(names, name)
    }
    sort.Strings(names)
    
    for _, name := range names {
        svc := contracts.Services[name]
        content.WriteString(fmt.Sprintf("| **%s** | %s | %s |\n",
            name, svc.Service.Language, svc.Service.Description))
    }
    
    // Сети (с проверкой compose)
    content.WriteString("\n## 🌐 Сети\n\n")
    content.WriteString("| Сеть | Драйвер |\n")
    content.WriteString("|------|---------|\n")
    
    if compose != nil && compose.Networks != nil {
        for name, network := range compose.Networks {
            driver := "bridge"
            if n, ok := network.(map[string]interface{}); ok {
                if d, ok := n["driver"].(string); ok {
                    driver = d
                }
            }
            content.WriteString(fmt.Sprintf("| `%s` | %s |\n", name, driver))
        }
    } else {
        content.WriteString("| `hivemind-net` | bridge |\n")
    }
    
    return os.WriteFile(filepath.Join(outputPath, "ARCHITECTURE_IDEAL.md"), []byte(content.String()), 0644)
}