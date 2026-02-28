package main

import (
    "encoding/json"
    "log"
    "net/http"
    "time"
    
    "github.com/gorilla/mux"
    "github.com/nats-io/nats.go"
)

type DocumentRequest struct {
    Content  string                 `json:"content"`
    Metadata map[string]interface{} `json:"metadata"`
}

type DocumentResponse struct {
    ID     string `json:"id"`
    Status string `json:"status"`
    TaskID string `json:"task_id"`
}

type StatusResponse struct {
    Agents struct {
        Total  int `json:"total"`
        Active int `json:"active"`
        Dead   int `json:"dead"`
    } `json:"agents"`
    Tasks struct {
        Pending    int `json:"pending"`
        Processing int `json:"processing"`
        Completed  int `json:"completed"`
    } `json:"tasks"`
    Documents int `json:"documents"`
    Uptime    int `json:"uptime"`
}

var nc *nats.Conn
var startTime = time.Now()

func main() {
    var err error
    nc, err = nats.Connect("nats://nats:4222")
    if err != nil {
        log.Fatal("Failed to connect to NATS:", err)
    }
    defer nc.Close()
    log.Println("Connected to NATS")

    r := mux.NewRouter()
    
    r.HandleFunc("/api/v1/documents", createDocument).Methods("POST")
    r.HandleFunc("/api/v1/documents/{id}", getDocument).Methods("GET")
    r.HandleFunc("/api/v1/documents/{id}/similar", findSimilar).Methods("GET")
    r.HandleFunc("/api/v1/graph/{id}", getGraph).Methods("GET")
    r.HandleFunc("/api/v1/status", getStatus).Methods("GET")
    r.HandleFunc("/health", healthCheck).Methods("GET")
    
    log.Println("API Gateway listening on :8080")
    log.Fatal(http.ListenAndServe(":8080", r))
}

func createDocument(w http.ResponseWriter, r *http.Request) {
    var req DocumentRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, `{"error":"Invalid request"}`, http.StatusBadRequest)
        return
    }
    
    docID := generateUUID()
    log.Printf("Creating document: %s", docID)
    
    data := map[string]interface{}{
        "id":       docID,
        "content":  req.Content,
        "metadata": req.Metadata,
    }
    jsonData, _ := json.Marshal(data)
    nc.Publish("document.ingest", jsonData)
    
    resp := DocumentResponse{
        ID:     docID,
        Status: "processing",
        TaskID: generateUUID(),
    }
    
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusAccepted)
    json.NewEncoder(w).Encode(resp)
}

func getDocument(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    docID := vars["id"]
    log.Printf("Getting document: %s", docID)
    w.Write([]byte(`{"id":"` + docID + `","content":"test"}`))
}

func findSimilar(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    docID := vars["id"]
    log.Printf("Finding similar documents for: %s", docID)
    w.Write([]byte(`{"documents":[]}`))
}

func getGraph(w http.ResponseWriter, r *http.Request) {
    vars := mux.Vars(r)
    docID := vars["id"]
    log.Printf("Getting graph for document: %s", docID)
    w.Write([]byte(`{"nodes":[],"edges":[]}`))
}

func getStatus(w http.ResponseWriter, r *http.Request) {
    var status StatusResponse
    
    status.Agents.Total = 5
    status.Agents.Active = 3
    status.Agents.Dead = 2
    
    status.Tasks.Pending = 12
    status.Tasks.Processing = 3
    status.Tasks.Completed = 1245
    
    status.Documents = 1250
    status.Uptime = int(time.Since(startTime).Seconds())
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(status)
}

func healthCheck(w http.ResponseWriter, r *http.Request) {
    w.Write([]byte(`{"status":"ok"}`))
}

func generateUUID() string {
    return "doc_" + time.Now().Format("20060102150405")
}
