package api

import (
	"errors"
	"net/http"
	"time"

	"github.com/gofiber/fiber/v2"

	"github.com/adaptive/adaptive-model-registry/internal/models"
	"github.com/adaptive/adaptive-model-registry/internal/repository"
	"github.com/adaptive/adaptive-model-registry/internal/services"
)

// ModelHandler exposes CRUD operations for models.
type ModelHandler struct {
	service *services.ModelService
}

// NewModelHandler constructs a ModelHandler.
func NewModelHandler(service *services.ModelService) *ModelHandler {
	return &ModelHandler{service: service}
}

// List returns all registered models.
func (h *ModelHandler) List(c *fiber.Ctx) error {
	ctx := requestContext(c)

	filter := models.ModelFilter{
		Provider:     c.Query("provider"),
		ModelName:    c.Query("model_name"),
		OpenrouterID: c.Query("openrouter_id"),
	}

	items, err := h.service.List(ctx, filter)
	if err != nil {
		return errorResponse(c, http.StatusInternalServerError, err.Error())
	}

	return successResponse(c, http.StatusOK, items)
}

// GetByName fetches the first model matching the supplied name.
func (h *ModelHandler) GetByName(c *fiber.Ctx) error {
	name := c.Params("name")
	if name == "" {
		return errorResponse(c, http.StatusBadRequest, "model name is required")
	}

	ctx := requestContext(c)
	item, err := h.service.GetByName(ctx, name)
	switch {
	case err == nil:
		return successResponse(c, http.StatusOK, item)
	case errors.Is(err, repository.ErrNotFound):
		return errorResponse(c, http.StatusNotFound, "model not found")
	default:
		return errorResponse(c, http.StatusInternalServerError, err.Error())
	}
}

// GetByOpenrouterID fetches a model by OpenRouter ID.
func (h *ModelHandler) GetByOpenrouterID(c *fiber.Ctx) error {
	openrouterID := c.Params("id")
	if openrouterID == "" {
		return errorResponse(c, http.StatusBadRequest, "openrouter id is required")
	}

	ctx := requestContext(c)
	item, err := h.service.GetByOpenrouterID(ctx, openrouterID)
	switch {
	case err == nil:
		return successResponse(c, http.StatusOK, item)
	case errors.Is(err, repository.ErrNotFound):
		return errorResponse(c, http.StatusNotFound, "model not found")
	default:
		return errorResponse(c, http.StatusInternalServerError, err.Error())
	}
}

// Upsert creates or updates a model record.
func (h *ModelHandler) Upsert(c *fiber.Ctx) error {
	var body models.Model
	if err := c.BodyParser(&body); err != nil {
		return errorResponse(c, http.StatusBadRequest, err.Error())
	}

	if err := validateModel(body); err != nil {
		return errorResponse(c, http.StatusBadRequest, err.Error())
	}

	body.ID = 0
	body.CreatedAt = time.Time{}
	body.LastUpdated = time.Time{}

	ctx := requestContext(c)
	result, err := h.service.Upsert(ctx, &body)
	if err != nil {
		return errorResponse(c, http.StatusInternalServerError, err.Error())
	}

	return successResponse(c, http.StatusCreated, result)
}

func validateModel(m models.Model) error {
	if m.ModelName == "" {
		return errors.New("model_name is required")
	}
	return nil
}
