package api

import (
	"time"

	"github.com/gofiber/fiber/v2"
)

// Root returns basic metadata about the service.
func Root(c *fiber.Ctx) error {
	return successResponse(c, fiber.StatusOK, fiber.Map{
		"service":     "adaptive-model-registry",
		"description": "Postgres-backed model registry built with Fiber and GORM.",
		"timestamp":   time.Now().UTC(),
	})
}
