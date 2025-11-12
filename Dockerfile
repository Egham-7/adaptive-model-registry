# Multi-stage Dockerfile for Railway deployment
# Stage 1: Python dependencies setup
FROM python:3.12-slim AS python-setup

# Install uv package manager using the official installer
RUN pip install uv

# Copy Python project files
COPY scripts/ /app/scripts/

# Set working directory
WORKDIR /app/scripts

# Sync Python dependencies
RUN uv sync --frozen

# Stage 2: Go application build
FROM golang:1.25-alpine AS go-build

# Set working directory
WORKDIR /app

# Copy Go module files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY cmd/ ./cmd/
COPY internal/ ./internal/

# Build the Go application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o api ./cmd/api

# Stage 3: Final runtime image
FROM python:3.12-slim

# Install ca-certificates for HTTPS requests
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Copy uv and Python dependencies from python-setup stage
COPY --from=python-setup /usr/local/bin/uv /usr/local/bin/uv
COPY --from=python-setup /app/scripts /app/scripts

# Copy Go binary from go-build stage
COPY --from=go-build /app/api /app/api

# Set working directory
WORKDIR /app

# Make the Go binary executable
RUN chmod +x /app/api

# Expose port (Railway will set PORT env var)
EXPOSE 8080

# Default command (Railway will override with startCommand)
CMD ["./api"]