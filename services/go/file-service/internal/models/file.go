// internal/models/file.go
package models

import (
    "time"
    "os"
)

type FileType string

const (
    TypeRaw       FileType = "raw"
    TypeCard      FileType = "card"
    TypeNote      FileType = "note"
    TypeArticle   FileType = "article"
)

type FileInfo struct {
    ID         string    `json:"id"`
    Path       string    `json:"path"`
    Name       string    `json:"name"`
    Type       FileType  `json:"type"`
    Size       int64     `json:"size"`
    Modified   time.Time `json:"modified"`
    IsDir      bool      `json:"is_dir"`
    Extension  string    `json:"extension,omitempty"`
    MimeType   string    `json:"mime_type,omitempty"`
}

type FileContent struct {
    FileInfo
    Content string `json:"content,omitempty"`
}

type WriteRequest struct {
    Path     string   `json:"path"`
    Content  string   `json:"content"`
    Type     FileType `json:"type,omitempty"`
    Overwrite bool    `json:"overwrite"`
}

type ReadRequest struct {
    Path string `json:"path"`
}

type ListRequest struct {
    Path string `json:"path"`
}

type DeleteRequest struct {
    Path string `json:"path"`
    Force bool  `json:"force"`
}

type MoveRequest struct {
    Source string `json:"source"`
    Dest   string `json:"dest"`
}

func FileInfoFromOS(path string, info os.FileInfo) FileInfo {
    return FileInfo{
        Path:      path,
        Name:      info.Name(),
        Size:      info.Size(),
        Modified:  info.ModTime(),
        IsDir:     info.IsDir(),
    }
}