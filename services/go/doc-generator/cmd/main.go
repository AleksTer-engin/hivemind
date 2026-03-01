package main

import (
    "log"
    "path/filepath"
    "time"
    
    "github.com/spf13/viper"
    "github.com/welem/hivemind/doc-generator/internal/contracts"
    "github.com/welem/hivemind/doc-generator/internal/docker"
    "github.com/welem/hivemind/doc-generator/internal/generators"
    "github.com/welem/hivemind/doc-generator/internal/services"
)

type Config struct {
    HiveMindPath string `mapstructure:"hivemind_path"`
    OutputPath   string `mapstructure:"output_path"`
}

func main() {
    log.Println("🚀 Doc Generator starting...")
    
    // Загрузка конфига
    var cfg Config
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath(".")
    viper.AddConfigPath("./configs")
    
    if err := viper.ReadInConfig(); err != nil {
        log.Printf("⚠️ No config file found, using defaults: %v", err)
        cfg.HiveMindPath = "/home/welem/hivemind"
        cfg.OutputPath = "/home/welem/hivemind/docs"
    } else {
        if err := viper.Unmarshal(&cfg); err != nil {
            log.Fatalf("❌ Failed to parse config: %v", err)
        }
    }
    
    log.Printf("📁 HiveMind path: %s", cfg.HiveMindPath)
    log.Printf("📁 Output path: %s", cfg.OutputPath)
    
    // Загрузка контрактов
    contractsPath := filepath.Join(cfg.HiveMindPath, "contracts")
    contractData, err := contracts.LoadAll(contractsPath)
    if err != nil {
        log.Fatalf("❌ Failed to load contracts: %v", err)
    }
    log.Printf("✅ Loaded %d service contracts", len(contractData.Services))
    log.Printf("✅ Loaded %d API contracts", len(contractData.APIs))
    log.Printf("✅ Loaded %d event contracts", len(contractData.Events))
    
    // Анализ docker-compose
    composePath := filepath.Join(cfg.HiveMindPath, "docker-compose.yml")
    composeData, err := docker.ParseCompose(composePath)
    if err != nil {
        log.Printf("⚠️ Failed to parse docker-compose: %v", err)
    } else {
        log.Printf("✅ Parsed docker-compose with %d services", len(composeData.Services))
    }
    
    // Проверка статусов сервисов
    var serviceStatuses map[string]services.ServiceStatus
	if composeData != nil {
		serviceStatuses = services.CheckAll(composeData)
	} else {
		serviceStatuses = make(map[string]services.ServiceStatus)
		log.Println("⚠️ Compose data is nil, skipping service checks")
	}
    running := 0
    for _, status := range serviceStatuses {
        if status.Running {
            running++
        }
    }
    log.Printf("✅ Checked %d services (%d running)", len(serviceStatuses), running)
    
    // Генерация документации
    timestamp := time.Now().Format("2006-01-02 15:04:05")
    
    // 1. API_CONTRACTS.md
    if err := generators.GenerateAPIContracts(contractData, serviceStatuses, cfg.OutputPath, timestamp); err != nil {
        log.Printf("❌ Failed to generate API contracts: %v", err)
    } else {
        log.Println("✅ Generated API_CONTRACTS.md")
    }
    
    // 2. ARCHITECTURE_IDEAL.md
    if err := generators.GenerateArchitecture(contractData, composeData, cfg.OutputPath, timestamp); err != nil {
        log.Printf("❌ Failed to generate architecture: %v", err)
    } else {
        log.Println("✅ Generated ARCHITECTURE_IDEAL.md")
    }
    
    // 3. CURRENT_CONTEXT.md
    if err := generators.GenerateCurrentContext(serviceStatuses, cfg.OutputPath, timestamp); err != nil {
        log.Printf("❌ Failed to generate current context: %v", err)
    } else {
        log.Println("✅ Generated CURRENT_CONTEXT.md")
    }
    
    // 4. DEPENDENCIES.md
    if err := generators.GenerateDependencies(contractData, cfg.OutputPath, timestamp); err != nil {
        log.Printf("❌ Failed to generate dependencies: %v", err)
    } else {
        log.Println("✅ Generated DEPENDENCIES.md")
    }
    
    // 5. KNOWLEDGE_GRAPH.json
    if err := generators.GenerateKnowledgeGraph(contractData, serviceStatuses, cfg.OutputPath, timestamp); err != nil {
        log.Printf("❌ Failed to generate knowledge graph: %v", err)
    } else {
        log.Println("✅ Generated KNOWLEDGE_GRAPH.json")
    }
    
    // 6. ROADMAP.md
    if err := generators.GenerateRoadmap(cfg.OutputPath, timestamp); err != nil {
        log.Printf("❌ Failed to generate roadmap: %v", err)
    } else {
        log.Println("✅ Generated ROADMAP.md")
    }
    
    log.Println("🎉 Documentation generation complete!")
}