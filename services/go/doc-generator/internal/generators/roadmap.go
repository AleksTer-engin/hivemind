package generators

import (
    "fmt"
    "os"
    "path/filepath"
    "strings"
)

func GenerateRoadmap(outputPath, timestamp string) error {
    var content strings.Builder
    
    content.WriteString("# 🗺️ Дорожная карта HiveMind\n\n")
    content.WriteString(fmt.Sprintf("*Обновлено: %s*\n\n", timestamp))
    
    content.WriteString("## ✅ Завершено\n\n")
    content.WriteString("- [x] API Gateway (Go)\n")
    content.WriteString("- [x] Classifier (Python)\n")
    content.WriteString("- [x] Embedder (Python)\n")
    content.WriteString("- [x] Linker (Python)\n")
    content.WriteString("- [x] HiveMind UI (Python)\n")
    content.WriteString("- [x] NATS event bus\n")
    content.WriteString("- [x] Базы данных (Postgres, Neo4j, Qdrant, Redis)\n")
    content.WriteString("- [x] File Service (Go)\n")
    content.WriteString("- [x] Goals UI\n\n")
    
    content.WriteString("## 🚧 В разработке\n\n")
    content.WriteString("- [ ] Документация (автоматическая)\n")
    content.WriteString("- [ ] LLM Service (Go)\n")
    content.WriteString("- [ ] Оркестратор (Go)\n")
    content.WriteString("- [ ] Лаборатория (Python)\n")
    content.WriteString("- [ ] Тесты и CI/CD\n\n")
    
    content.WriteString("## 🔮 В планах\n\n")
    content.WriteString("- [ ] Рефлексия системы\n")
    content.WriteString("- [ ] Самообучение\n")
    content.WriteString("- [ ] Мульти-инстансность\n")
    content.WriteString("- [ ] Интеграция с внешними сервисами\n")
    
    return os.WriteFile(filepath.Join(outputPath, "ROADMAP.md"), []byte(content.String()), 0644)
}