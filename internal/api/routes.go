package api

import (
	"github.com/gofiber/fiber/v2"
	"gorm.io/gorm"

	"github.com/adaptive/adaptive-model-registry/internal/config"
	"github.com/adaptive/adaptive-model-registry/internal/services"
)

// Deps groups dependencies required by the API handlers.
type Deps struct {
	Config config.Config
	DB     *gorm.DB
	Models *services.ModelService
}

// Register mounts all API routes on the provided Fiber app.
func Register(app *fiber.App, deps Deps) {
	models := NewModelHandler(deps.Models)
	health := NewHealthHandler(deps.DB)

	app.Get("/", Root)
	app.Get("/healthz", health.Check)
	app.Get("/models", models.List)
	app.Get("/models/:provider/:name", models.GetByProviderAndName)
	app.Post("/models", models.Upsert)
}
