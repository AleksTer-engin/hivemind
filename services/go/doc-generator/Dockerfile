FROM golang:1.23-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o doc-generator ./cmd/main.go

FROM alpine:latest

RUN apk --no-cache add docker-cli
WORKDIR /root/

COPY --from=builder /app/doc-generator .
COPY --from=builder /app/config.yaml .

ENTRYPOINT ["./doc-generator"]
