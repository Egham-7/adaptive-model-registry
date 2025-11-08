package server

import (
	"context"

	"github.com/gofiber/fiber/v2"
	"gorm.io/gorm"

	"github.com/adaptive/adaptive-model-registry/internal/api"
	"github.com/adaptive/adaptive-model-registry/internal/config"
	"github.com/adaptive/adaptive-model-registry/internal/services"
)

// Server wraps the Fiber application and related dependencies.
type Server struct {
	cfg config.Config
	app *fiber.App
}

// New constructs a Server instance with routes registered.
func New(cfg config.Config, db *gorm.DB, modelService *services.ModelService, providerService *services.ProviderService) (*Server, error) {
	app := fiber.New(fiber.Config{
		Immutable:            true,
		CaseSensitive:        true,
		StrictRouting:        true,
		AppName:              "Adaptive Model Registry",
		ReadBufferSize:       8192,
		WriteBufferSize:      8192,
		CompressedFileSuffix: ".gz",
		Prefork:              false,
		Network:              "tcp",
		ServerHeader:         "Adaptive-Model-Registry",
		ReadTimeout:          cfg.ReadTimeout,
		WriteTimeout:         cfg.WriteTimeout,
	})

	api.Register(app, api.Deps{
		Config:    cfg,
		DB:        db,
		Models:    modelService,
		Providers: providerService,
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
