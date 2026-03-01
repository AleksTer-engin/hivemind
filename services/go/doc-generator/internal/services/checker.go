package services

import (
    "context"
    "fmt"
    "net"
    "strings"
    "time"
    
    "github.com/docker/docker/api/types"
    "github.com/docker/docker/api/types/container"
    "github.com/docker/docker/client"
    
    "github.com/welem/hivemind/doc-generator/internal/docker"
)

type ServiceStatus struct {
    Name      string
    Running   bool
    Status    string
    Ports     []string
    UpdatedAt string
}

func CheckAll(compose *docker.ComposeData) map[string]ServiceStatus {
    statuses := make(map[string]ServiceStatus)
    
    // Пробуем подключиться к Docker
    cli, err := client.NewClientWithOpts(client.FromEnv, client.WithAPIVersionNegotiation())
    if err != nil {
        // Если Docker недоступен, просто возвращаем имена сервисов из compose
        for name := range compose.Services {
            statuses[name] = ServiceStatus{
                Name:    name,
                Running: false,
                Status:  "unknown (docker not available)",
            }
        }
        return statuses
    }
    
    ctx := context.Background()
    containers, err := cli.ContainerList(ctx, container.ListOptions{All: true})
    if err != nil {
        for name := range compose.Services {
            statuses[name] = ServiceStatus{
                Name:    name,
                Running: false,
                Status:  fmt.Sprintf("error: %v", err),
            }
        }
        return statuses
    }
    
    // Создаем карту контейнеров по имени
    containerMap := make(map[string]types.Container)
    for _, c := range containers {
        for _, name := range c.Names {
            cleanName := strings.TrimPrefix(name, "/")
            containerMap[cleanName] = c
        }
    }
    
    // Проверяем каждый сервис из compose
    for name := range compose.Services {
        // Ищем контейнер по разным вариантам имени
        possibleNames := []string{
            fmt.Sprintf("hivemind-%s-1", name),
            fmt.Sprintf("%s-1", name),
            name,
        }
        
        var found bool
        for _, pName := range possibleNames {
            if c, ok := containerMap[pName]; ok {
                statuses[name] = ServiceStatus{
                    Name:      name,
                    Running:   c.State == "running",
                    Status:    c.Status,
                    Ports:     extractPorts(c.Ports),
                    UpdatedAt: time.Now().Format("2006-01-02 15:04:05"),
                }
                found = true
                break
            }
        }
        
        if !found {
            statuses[name] = ServiceStatus{
                Name:    name,
                Running: false,
                Status:  "not running",
            }
        }
    }
    
    return statuses
}

func extractPorts(ports []types.Port) []string {
    var result []string
    for _, p := range ports {
        if p.PublicPort > 0 {
            result = append(result, fmt.Sprintf("%d:%d", p.PublicPort, p.PrivatePort))
        }
    }
    return result
}

func CheckNATS() bool {
    conn, err := net.DialTimeout("tcp", "localhost:4222", 2*time.Second)
    if err != nil {
        return false
    }
    conn.Close()
    return true
}