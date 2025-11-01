package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/adaptive/adaptive-model-registry/internal/config"
	"github.com/adaptive/adaptive-model-registry/internal/database"
	"github.com/adaptive/adaptive-model-registry/internal/repository"
	"github.com/adaptive/adaptive-model-registry/internal/server"
)

func main() {
	cfg := config.MustLoad()

	db := database.MustOpen(cfg.DatabaseURL)
	defer func() {
		if err := database.Close(db); err != nil {
			log.Printf("close database: %v", err)
		}
	}()

	repo := repository.NewModelRepository(db)

	srv, err := server.New(cfg, db, repo)
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
