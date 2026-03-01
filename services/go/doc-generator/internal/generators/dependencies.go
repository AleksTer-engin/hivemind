package generators

import (
    "fmt"
    "os"
    "path/filepath"
    "strings"
    
    "github.com/welem/hivemind/doc-generator/internal/contracts"
)

func GenerateDependencies(contracts *contracts.ContractData, outputPath, timestamp string) error {
    var content strings.Builder
    
    content.WriteString("# 📦 Зависимости HiveMind\n\n")
    content.WriteString(fmt.Sprintf("*Обновлено: %s*\n\n", timestamp))
    
    content.WriteString("## 🔧 Базовые зависимости\n\n")
    content.WriteString("| Компонент | Версия |\n")
    content.WriteString("|-----------|--------|\n")
    content.WriteString("| Docker | 24.0+ |\n")
    content.WriteString("| Docker Compose | 2.20+ |\n")
    content.WriteString("| Go | 1.23+ |\n")
    content.WriteString("| Python | 3.11+ |\n")
    content.WriteString("| Poetry | 1.6+ |\n\n")
    
    content.WriteString("## 🐳 Docker-образы\n\n")
    content.WriteString("| Сервис | Базовый образ |\n")
    content.WriteString("|--------|---------------|\n")
    
    for name, svc := range contracts.Services {
        lang := svc.Service.Language
        if lang == "go" {
            content.WriteString(fmt.Sprintf("| %s | golang:1.23-alpine |\n", name))
        } else if lang == "python" {
            content.WriteString(fmt.Sprintf("| %s | python:3.11-slim |\n", name))
        }
    }
    
    return os.WriteFile(filepath.Join(outputPath, "DEPENDENCIES.md"), []byte(content.String()), 0644)
}