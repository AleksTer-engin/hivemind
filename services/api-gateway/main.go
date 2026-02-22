package main

import (
    "encoding/json"
    "log"
    "net/http"
)

type Request struct {
    Text string `json:"text"`
}

type Response struct {
    Status  string `json:"status"`
    Result  string `json:"result,omitempty"`
    Error   string `json:"error,omitempty"`
}

func main() {
    // Простой обработчик
    http.HandleFunc("/classify", func(w http.ResponseWriter, r *http.Request) {
        if r.Method != http.MethodPost {
            http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
            return
        }

        var req Request
        if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
            http.Error(w, "Bad request", http.StatusBadRequest)
            return
        }

        log.Printf("Received: %s", req.Text)

        // Отвечаем заглушкой
        response := Response{
            Status: "ok",
            Result: "Принято в обработку: " + req.Text,
        }

        w.Header().Set("Content-Type", "application/json")
        json.NewEncoder(w).Encode(response)
    })

    http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte(`{"status":"ok"}`))
    })

    log.Println("API Gateway listening on :8080")
    log.Fatal(http.ListenAndServe(":8080", nil))
}
