package contracts

import (
    "fmt"
    "io/ioutil"
    "path/filepath"
    "strings"
    
    "gopkg.in/yaml.v3"
)

type ServiceContract struct {
    Service struct {
        Name        string `yaml:"name"`
        Language    string `yaml:"language"`
        Version     string `yaml:"version"`
        Description string `yaml:"description"`
    } `yaml:"service"`
    Status string `yaml:"status,omitempty"`
}

type APIContract struct {
    Name        string
    Path        string
    Method      string
    Description string
}

type EventContract struct {
    Name        string
    Topic       string
    Description string
}

type ContractData struct {
    Services map[string]ServiceContract
    APIs     []APIContract
    Events   []EventContract
}

func LoadAll(contractsPath string) (*ContractData, error) {
    data := &ContractData{
        Services: make(map[string]ServiceContract),
        APIs:     []APIContract{},
        Events:   []EventContract{},
    }
    
    // Загрузка сервисов
    servicesPath := filepath.Join(contractsPath, "services")
    files, err := ioutil.ReadDir(servicesPath)
    if err != nil {
        return nil, fmt.Errorf("failed to read services dir: %w", err)
    }
    
    for _, file := range files {
        if !strings.HasSuffix(file.Name(), ".yaml") && !strings.HasSuffix(file.Name(), ".yml") {
            continue
        }
        
        content, err := ioutil.ReadFile(filepath.Join(servicesPath, file.Name()))
        if err != nil {
            return nil, fmt.Errorf("failed to read %s: %w", file.Name(), err)
        }
        
        var contract ServiceContract
        if err := yaml.Unmarshal(content, &contract); err != nil {
            return nil, fmt.Errorf("failed to parse %s: %w", file.Name(), err)
        }
        
        name := strings.TrimSuffix(file.Name(), filepath.Ext(file.Name()))
        data.Services[name] = contract
    }
    
    // Загрузка API
    apiPath := filepath.Join(contractsPath, "api")
    if files, err := ioutil.ReadDir(apiPath); err == nil {
        for _, file := range files {
            if !strings.HasSuffix(file.Name(), ".yaml") && !strings.HasSuffix(file.Name(), ".yml") {
                continue
            }
            
            content, err := ioutil.ReadFile(filepath.Join(apiPath, file.Name()))
            if err != nil {
                continue
            }
            
            var api struct {
                Method string `yaml:"method"`
                Path   string `yaml:"path"`
                Description string `yaml:"description"`
            }
            
            if err := yaml.Unmarshal(content, &api); err == nil {
                data.APIs = append(data.APIs, APIContract{
                    Name:        strings.TrimSuffix(file.Name(), filepath.Ext(file.Name())),
                    Path:        api.Path,
                    Method:      api.Method,
                    Description: api.Description,
                })
            }
        }
    }
    
    // Загрузка событий
    eventsPath := filepath.Join(contractsPath, "events")
    if files, err := ioutil.ReadDir(eventsPath); err == nil {
        for _, file := range files {
            if !strings.HasSuffix(file.Name(), ".yaml") && !strings.HasSuffix(file.Name(), ".yml") {
                continue
            }
            
            content, err := ioutil.ReadFile(filepath.Join(eventsPath, file.Name()))
            if err != nil {
                continue
            }
            
            var event struct {
                Topic       string `yaml:"topic"`
                Description string `yaml:"description"`
            }
            
            if err := yaml.Unmarshal(content, &event); err == nil {
                data.Events = append(data.Events, EventContract{
                    Name:        strings.TrimSuffix(file.Name(), filepath.Ext(file.Name())),
                    Topic:       event.Topic,
                    Description: event.Description,
                })
            }
        }
    }
    
    return data, nil
}