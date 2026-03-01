FROM golang:1.23-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o file-service ./cmd/main.go

FROM alpine:latest

RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/file-service .
COPY --from=builder /app/configs/config.yaml ./configs/

# Монтируем data сюда
VOLUME ["/app/data"]

EXPOSE 8081

CMD ["./file-service"]