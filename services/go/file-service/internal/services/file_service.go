// internal/services/file_service.go
package services

import (
    "fmt"
    "os"
    "path/filepath"
    "strings"
    
    "github.com/google/uuid"
    
    "github.com/welem/hivemind/services/file-service/internal/models"
)

type FileService struct {
    basePath string
}

func NewFileService(basePath string) *FileService {
    // Создаём базовую директорию, если нет
    os.MkdirAll(basePath, 0755)
    
    return &FileService{
        basePath: basePath,
    }
}

func (s *FileService) safePath(path string) (string, error) {
    fullPath := filepath.Join(s.basePath, path)
    
    // Защита от path traversal
    if !strings.HasPrefix(fullPath, s.basePath) {
        return "", fmt.Errorf("access denied: path outside base directory")
    }
    
    return fullPath, nil
}

func (s *FileService) Write(req models.WriteRequest) (*models.FileInfo, error) {
    fullPath, err := s.safePath(req.Path)
    if err != nil {
        return nil, err
    }
    
    // Создаём директорию, если нужно
    dir := filepath.Dir(fullPath)
    if err := os.MkdirAll(dir, 0755); err != nil {
        return nil, fmt.Errorf("failed to create directory: %w", err)
    }
    
    // Проверка на существование
    if _, err := os.Stat(fullPath); err == nil && !req.Overwrite {
        return nil, fmt.Errorf("file already exists (use overwrite=true to force)")
    }
    
    // Запись файла
    if err := os.WriteFile(fullPath, []byte(req.Content), 0644); err != nil {
        return nil, fmt.Errorf("failed to write file: %w", err)
    }
    
    // Получаем информацию о файле
    info, err := os.Stat(fullPath)
    if err != nil {
        return nil, fmt.Errorf("failed to stat file: %w", err)
    }
    
    fileInfo := models.FileInfoFromOS(req.Path, info)
    fileInfo.ID = uuid.New().String()
    fileInfo.Type = req.Type
    
    return &fileInfo, nil
}

func (s *FileService) Read(path string) (*models.FileContent, error) {
    fullPath, err := s.safePath(path)
    if err != nil {
        return nil, err
    }
    
    info, err := os.Stat(fullPath)
    if err != nil {
        if os.IsNotExist(err) {
            return nil, fmt.Errorf("file not found")
        }
        return nil, fmt.Errorf("failed to stat file: %w", err)
    }
    
    if info.IsDir() {
        return nil, fmt.Errorf("path is a directory, use List instead")
    }
    
    content, err := os.ReadFile(fullPath)
    if err != nil {
        return nil, fmt.Errorf("failed to read file: %w", err)
    }
    
    fileInfo := models.FileInfoFromOS(path, info)
    
    return &models.FileContent{
        FileInfo: fileInfo,
        Content:  string(content),
    }, nil
}

func (s *FileService) List(path string) ([]models.FileInfo, error) {
    fullPath, err := s.safePath(path)
    if err != nil {
        return nil, err
    }
    
    entries, err := os.ReadDir(fullPath)
    if err != nil {
        return nil, fmt.Errorf("failed to read directory: %w", err)
    }
    
    var files []models.FileInfo
    for _, entry := range entries {
        info, err := entry.Info()
        if err != nil {
            continue
        }
        
        relPath := filepath.Join(path, entry.Name())
        fileInfo := models.FileInfoFromOS(relPath, info)
        
        files = append(files, fileInfo)
    }
    
    return files, nil
}

func (s *FileService) Delete(req models.DeleteRequest) error {
    fullPath, err := s.safePath(req.Path)
    if err != nil {
        return err
    }
    
    info, err := os.Stat(fullPath)
    if err != nil {
        if os.IsNotExist(err) {
            return fmt.Errorf("file not found")
        }
        return fmt.Errorf("failed to stat file: %w", err)
    }
    
    if info.IsDir() {
        if !req.Force {
            // Проверяем, пустая ли директория
            entries, _ := os.ReadDir(fullPath)
            if len(entries) > 0 {
                return fmt.Errorf("directory not empty (use force=true to delete anyway)")
            }
        }
        if err := os.RemoveAll(fullPath); err != nil {
            return fmt.Errorf("failed to remove directory: %w", err)
        }
    } else {
        if err := os.Remove(fullPath); err != nil {
            return fmt.Errorf("failed to remove file: %w", err)
        }
    }
    
    return nil
}

func (s *FileService) Move(req models.MoveRequest) error {
    srcFull, err := s.safePath(req.Source)
    if err != nil {
        return err
    }
    
    dstFull, err := s.safePath(req.Dest)
    if err != nil {
        return err
    }
    
    if err := os.Rename(srcFull, dstFull); err != nil {
        return fmt.Errorf("failed to move file: %w", err)
    }
    
    return nil
}

func (s *FileService) Exists(path string) (bool, error) {
    fullPath, err := s.safePath(path)
    if err != nil {
        return false, err
    }
    
    _, err = os.Stat(fullPath)
    if err == nil {
        return true, nil
    }
    if os.IsNotExist(err) {
        return false, nil
    }
    return false, err
}