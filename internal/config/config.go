package config

import (
	"errors"
	"fmt"
	"os"
	"strings"
	"time"
)

// Config captures runtime configuration for the service.
type Config struct {
	Port            string
	DatabaseURL     string
	ReadTimeout     time.Duration
	WriteTimeout    time.Duration
	ShutdownTimeout time.Duration
}

// Load reads configuration from environment variables, applying sensible defaults.
func Load() (Config, error) {
	cfg := Config{
		Port:            getEnvDefault("PORT", "3000"),
		DatabaseURL:     os.Getenv("DATABASE_URL"),
		ReadTimeout:     durationFromEnv("READ_TIMEOUT", 5*time.Second),
		WriteTimeout:    durationFromEnv("WRITE_TIMEOUT", 5*time.Second),
		ShutdownTimeout: durationFromEnv("SHUTDOWN_TIMEOUT", 10*time.Second),
	}

	if cfg.DatabaseURL == "" {
		return Config{}, errors.New("DATABASE_URL is required")
	}

	return cfg, nil
}

// MustLoad panics when configuration cannot be loaded.
func MustLoad() Config {
	cfg, err := Load()
	if err != nil {
		panic(fmt.Sprintf("load config: %v", err))
	}
	return cfg
}

// ListenAddr returns the Fiber listen address derived from the configured port.
func (c Config) ListenAddr() string {
	if strings.HasPrefix(c.Port, ":") {
		return c.Port
	}
	return ":" + c.Port
}

func getEnvDefault(key, fallback string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return fallback
}

func durationFromEnv(key string, fallback time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if parsed, err := time.ParseDuration(value); err == nil {
			return parsed
		}
	}
	return fallback
}
