package server

import (
	"context"

	"github.com/gofiber/fiber/v2"
	"gorm.io/gorm"

	"github.com/adaptive/adaptive-model-registry/internal/api"
	"github.com/adaptive/adaptive-model-registry/internal/config"
	"github.com/adaptive/adaptive-model-registry/internal/repository"
	"github.com/adaptive/adaptive-model-registry/internal/services"
)

// Server wraps the Fiber application and related dependencies.
type Server struct {
	cfg config.Config
	app *fiber.App
}

// New constructs a Server instance with routes registered.
func New(cfg config.Config, db *gorm.DB, repo repository.ModelRepository) (*Server, error) {
	app := fiber.New(fiber.Config{
		Immutable:     true,
		CaseSensitive: true,
		StrictRouting: true,
		ReadTimeout:   cfg.ReadTimeout,
		WriteTimeout:  cfg.WriteTimeout,
	})

	modelService := services.NewModelService(repo)

	api.Register(app, api.Deps{
		Config: cfg,
		DB:     db,
		Models: modelService,
	})

	return &Server{
		cfg: cfg,
		app: app,
	}, nil
}

// Listen starts the Fiber server.
func (s *Server) Listen() error {
	return s.app.Listen(s.cfg.ListenAddr())
}

// Shutdown gracefully stops the server.
func (s *Server) Shutdown(ctx context.Context) error {
	return s.app.ShutdownWithContext(ctx)
}
