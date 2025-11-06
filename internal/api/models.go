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
		Provider:  c.Query("provider"),
		ModelName: c.Query("model_name"),
	}

	items, err := h.service.List(ctx, filter)
	if err != nil {
		return errorResponse(c, http.StatusInternalServerError, err.Error())
	}

	return successResponse(c, http.StatusOK, items)
}

// GetByProviderAndName fetches a model by provider and model name.
func (h *ModelHandler) GetByProviderAndName(c *fiber.Ctx) error {
	provider := c.Params("provider")
	name := c.Params("name")
	if provider == "" || name == "" {
		return errorResponse(c, http.StatusBadRequest, "provider and model name are required")
	}

	ctx := requestContext(c)
	item, err := h.service.GetByProviderAndName(ctx, provider, name)
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
	if m.Provider == "" {
		return errors.New("provider is required")
	}
	if m.ModelName == "" {
		return errors.New("model_name is required")
	}
	return nil
}
