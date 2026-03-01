package docker

import (
    "fmt"
    "io/ioutil"
    
    "gopkg.in/yaml.v3"
)

type ComposeService struct {
    Build       interface{}         `yaml:"build,omitempty"`
    Image       string            `yaml:"image"`
    Ports       []string          `yaml:"ports"`
    Environment interface{}         `yaml:"environment,omitempty"`
    DependsOn   interface{}         `yaml:"depends_on,omitempty"`
    Networks    interface{}         `yaml:"networks,omitempty"`
}

type ComposeData struct {
    Services map[string]ComposeService `yaml:"services"`
    Networks map[string]interface{}     `yaml:"networks"`
    Volumes  map[string]interface{}     `yaml:"volumes"`
}

func ParseCompose(path string) (*ComposeData, error) {
    content, err := ioutil.ReadFile(path)
    if err != nil {
        return nil, fmt.Errorf("failed to read docker-compose: %w", err)
    }
    
    var data ComposeData
    if err := yaml.Unmarshal(content, &data); err != nil {
        return nil, fmt.Errorf("failed to parse docker-compose: %w", err)
    }
    
    return &data, nil
}