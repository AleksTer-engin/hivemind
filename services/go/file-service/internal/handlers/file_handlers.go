// internal/handlers/file_handlers.go
package handlers

import (
    "encoding/json"
    "net/http"
    
    "github.com/gorilla/mux"
    "github.com/nats-io/nats.go"
    
    "github.com/welem/hivemind/services/file-service/internal/models"
    "github.com/welem/hivemind/services/file-service/internal/services"
)

type FileHandlers struct {
    service *services.FileService
    nc      *nats.Conn
}

func NewFileHandlers(service *services.FileService, nc *nats.Conn) *FileHandlers {
    return &FileHandlers{
        service: service,
        nc:      nc,
    }
}

func (h *FileHandlers) RegisterRoutes(r *mux.Router) {
    api := r.PathPrefix("/api/v1/files").Subrouter()
    
    api.HandleFunc("/write", h.handleWrite).Methods("POST")
    api.HandleFunc("/read", h.handleRead).Methods("POST")
    api.HandleFunc("/list", h.handleList).Methods("POST")
    api.HandleFunc("/delete", h.handleDelete).Methods("POST")
    api.HandleFunc("/move", h.handleMove).Methods("POST")
    
    api.HandleFunc("/health", h.handleHealth).Methods("GET")
}

func (h *FileHandlers) RegisterNatsHandlers() error {
    // Подписка на NATS для асинхронных операций
    _, err := h.nc.Subscribe("file.write", func(msg *nats.Msg) {
        var req models.WriteRequest
        if err := json.Unmarshal(msg.Data, &req); err != nil {
            h.nc.Publish(msg.Reply, []byte(`{"error":"invalid request"}`))
            return
        }
        
        info, err := h.service.Write(req)
        if err != nil {
            h.nc.Publish(msg.Reply, []byte(`{"error":"`+err.Error()+`"}`))
            return
        }
        
        resp, _ := json.Marshal(info)
        h.nc.Publish(msg.Reply, resp)
    })
    
    return err
}

func (h *FileHandlers) handleWrite(w http.ResponseWriter, r *http.Request) {
    var req models.WriteRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    
    info, err := h.service.Write(req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(info)
}

func (h *FileHandlers) handleRead(w http.ResponseWriter, r *http.Request) {
    var req models.ReadRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    
    content, err := h.service.Read(req.Path)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(content)
}

func (h *FileHandlers) handleList(w http.ResponseWriter, r *http.Request) {
    var req models.ListRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    
    files, err := h.service.List(req.Path)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(files)
}

func (h *FileHandlers) handleDelete(w http.ResponseWriter, r *http.Request) {
    var req models.DeleteRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    
    if err := h.service.Delete(req); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    w.WriteHeader(http.StatusNoContent)
}

func (h *FileHandlers) handleMove(w http.ResponseWriter, r *http.Request) {
    var req models.MoveRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    
    if err := h.service.Move(req); err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    w.WriteHeader(http.StatusNoContent)
}

func (h *FileHandlers) handleHealth(w http.ResponseWriter, r *http.Request) {
    w.Write([]byte(`{"status":"ok"}`))
}