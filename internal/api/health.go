package api

import (
	"context"
	"net/http"
	"time"

	"github.com/gofiber/fiber/v2"
	"gorm.io/gorm"

	"github.com/adaptive/adaptive-model-registry/internal/database"
)

// HealthHandler exposes health check endpoints.
type HealthHandler struct {
	db *gorm.DB
}

// NewHealthHandler constructs a HealthHandler.
func NewHealthHandler(db *gorm.DB) *HealthHandler {
	return &HealthHandler{db: db}
}

// Check reports database health.
func (h *HealthHandler) Check(c *fiber.Ctx) error {
	ctx, cancel := context.WithTimeout(requestContext(c), 2*time.Second)
	defer cancel()

	if err := database.PingContext(ctx, h.db); err != nil {
		return errorResponse(c, http.StatusServiceUnavailable, err.Error())
	}

	return c.SendStatus(http.StatusOK)
}
