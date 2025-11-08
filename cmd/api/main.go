package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/adaptive/adaptive-model-registry/internal/config"
	"github.com/adaptive/adaptive-model-registry/internal/database"
	"github.com/adaptive/adaptive-model-registry/internal/models"
	"github.com/adaptive/adaptive-model-registry/internal/repository"
	"github.com/adaptive/adaptive-model-registry/internal/server"
	"github.com/adaptive/adaptive-model-registry/internal/services"
)

func main() {
	cfg := config.MustLoad()

	db := database.MustOpen(cfg.DatabaseURL)
	defer func() {
		if err := database.Close(db); err != nil {
			log.Printf("close database: %v", err)
		}
	}()

	// Auto-migrate database schema and create indices
	if err := db.AutoMigrate(
		&models.Model{},
		&models.ModelPricing{},
		&models.ModelArchitecture{},
		&models.ModelArchitectureModality{},
		&models.ModelTopProvider{},
		&models.ModelEndpoint{},
		&models.ModelEndpointPricing{},
		&models.ModelSupportedParameter{},
		&models.ModelDefaultParameters{},
	); err != nil {
		log.Fatalf("auto-migrate database: %v", err)
	}

	// Initialize repositories
	modelRepo := repository.NewModelRepository(db)
	providerRepo := repository.NewProviderRepository(db)

	// Initialize services
	modelService := services.NewModelService(modelRepo)
	providerService := services.NewProviderService(providerRepo)

	srv, err := server.New(cfg, db, modelService, providerService)
	if err != nil {
		log.Fatalf("init server: %v", err)
	}

	errCh := make(chan error, 1)
	go func() {
		if err := srv.Listen(); err != nil {
			errCh <- err
		}
		close(errCh)
	}()

	sigCh := make(chan os.Signal, 1)
	signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)

	select {
	case err := <-errCh:
		if err != nil {
			log.Fatalf("server error: %v", err)
		}
	case sig := <-sigCh:
		log.Printf("received signal %s, initiating shutdown", sig)
		shutdownCtx, cancel := context.WithTimeout(context.Background(), cfg.ShutdownTimeout)
		defer cancel()
		if err := srv.Shutdown(shutdownCtx); err != nil {
			log.Fatalf("shutdown server: %v", err)
		}
	}
}
