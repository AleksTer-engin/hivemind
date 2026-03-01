// cmd/main.go
package main

import (
    "context"
    "log"
	"net/http"  // ← ЭТОГО НЕ ХВАТАЕТ!
    "os"
    "os/signal"
    "syscall"
    "time"
    
    "github.com/gorilla/mux"
    "github.com/nats-io/nats.go"
    "github.com/spf13/viper"
    
    "github.com/welem/hivemind/services/file-service/internal/handlers"
    "github.com/welem/hivemind/services/file-service/internal/services"
)

func main() {
    // Загрузка конфига
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    viper.AddConfigPath("./configs")
    viper.AddConfigPath("/app/configs")
    
    if err := viper.ReadInConfig(); err != nil {
        log.Printf("Warning: no config file found: %v", err)
    }
    
    // Настройки по умолчанию
    viper.SetDefault("server.port", 8081)
    viper.SetDefault("nats.url", "nats://nats:4222")
    viper.SetDefault("storage.path", "/app/data")
    
    // Подключение к NATS
    nc, err := nats.Connect(viper.GetString("nats.url"))
    if err != nil {
        log.Fatalf("Failed to connect to NATS: %v", err)
    }
    defer nc.Close()
    log.Println("✅ Connected to NATS")
    
    // Создание сервиса
    fileService := services.NewFileService(
        viper.GetString("storage.path"),
    )
    
    // Создание обработчиков
    fileHandlers := handlers.NewFileHandlers(fileService, nc)
    
    // Настройка HTTP сервера
    router := mux.NewRouter()
    fileHandlers.RegisterRoutes(router)
    
    // Настройка NATS подписок
    if err := fileHandlers.RegisterNatsHandlers(); err != nil {
        log.Fatalf("Failed to register NATS handlers: %v", err)
    }
    
    // Запуск HTTP сервера
    srv := &http.Server{
        Addr:         ":" + viper.GetString("server.port"),
        Handler:      router,
        ReadTimeout:  15 * time.Second,
        WriteTimeout: 15 * time.Second,
    }
    
    go func() {
        log.Printf("🚀 File service starting on port %s", viper.GetString("server.port"))
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatalf("Server failed: %v", err)
        }
    }()
    
    // Graceful shutdown
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit
    
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    if err := srv.Shutdown(ctx); err != nil {
        log.Fatalf("Server forced to shutdown: %v", err)
    }
    
    log.Println("👋 Server stopped")
}