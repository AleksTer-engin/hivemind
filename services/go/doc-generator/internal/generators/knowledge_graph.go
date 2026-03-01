package generators

import (
    "encoding/json"
    "os"
    "path/filepath"
    
    "github.com/welem/hivemind/doc-generator/internal/contracts"
    "github.com/welem/hivemind/doc-generator/internal/services"
)

type GraphNode struct {
    ID       string `json:"id"`
    Type     string `json:"type"`
    Language string `json:"language,omitempty"`
    Status   string `json:"status,omitempty"`
}

type GraphEdge struct {
    From string `json:"from"`
    To   string `json:"to"`
    Type string `json:"type"`
}

type KnowledgeGraph struct {
    Version   string      `json:"version"`
    Generated string      `json:"generated"`
    Nodes     []GraphNode `json:"nodes"`
    Edges     []GraphEdge `json:"edges"`
}

func GenerateKnowledgeGraph(contracts *contracts.ContractData, statuses map[string]services.ServiceStatus, outputPath, timestamp string) error {
    graph := KnowledgeGraph{
        Version:   "1.0",
        Generated: timestamp,
        Nodes:     []GraphNode{},
        Edges:     []GraphEdge{},
    }
    
    // Добавляем узлы сервисов
    for name, svc := range contracts.Services {
        status := "planned"
        if s, ok := statuses[name]; ok && s.Running {
            status = "active"
        }
        
        graph.Nodes = append(graph.Nodes, GraphNode{
            ID:       name,
            Type:     "service",
            Language: svc.Service.Language,
            Status:   status,
        })
    }
    
    // Добавляем узлы инфраструктуры
    infraNodes := []string{"nats", "postgres", "neo4j", "qdrant", "redis"}
    for _, name := range infraNodes {
        graph.Nodes = append(graph.Nodes, GraphNode{
            ID:   name,
            Type: "infrastructure",
        })
    }
    
    // Добавляем связи
    for name := range contracts.Services {
        graph.Edges = append(graph.Edges, GraphEdge{
            From: name,
            To:   "nats",
            Type: "uses",
        })
    }
    
    graph.Edges = append(graph.Edges, GraphEdge{
        From: "api-gateway",
        To:   "nats",
        Type: "publishes",
    })
    
    graph.Edges = append(graph.Edges, GraphEdge{
        From: "classifier",
        To:   "postgres",
        Type: "writes",
    })
    
    graph.Edges = append(graph.Edges, GraphEdge{
        From: "embedder",
        To:   "qdrant",
        Type: "writes",
    })
    
    graph.Edges = append(graph.Edges, GraphEdge{
        From: "linker",
        To:   "neo4j",
        Type: "writes",
    })
    
    data, err := json.MarshalIndent(graph, "", "  ")
    if err != nil {
        return err
    }
    
    return os.WriteFile(filepath.Join(outputPath, "KNOWLEDGE_GRAPH.json"), data, 0644)
}