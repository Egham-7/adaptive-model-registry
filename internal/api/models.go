package api

import (
	"errors"
	"net/http"
	"strings"
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

// parseQueryArray extracts query parameters as a string slice.
// Supports: ?key=val1&key=val2 OR ?key=val1,val2
func parseQueryArray(c *fiber.Ctx, key string) []string {
	var results []string

	// Get all values for this key
	values := c.Context().QueryArgs().PeekMulti(key)

	for _, value := range values {
		str := string(value)
		if str != "" {
			// Split by comma to support comma-separated values
			parts := strings.Split(str, ",")
			for _, part := range parts {
				trimmed := strings.TrimSpace(part)
				if trimmed != "" {
					results = append(results, trimmed)
				}
			}
		}
	}

	return results
}

// List returns all registered models.
func (h *ModelHandler) List(c *fiber.Ctx) error {
	ctx := requestContext(c)

	filter := models.ModelFilter{
		Authors:      parseQueryArray(c, "author"),
		ModelNames:   parseQueryArray(c, "model_name"),
		EndpointTags: parseQueryArray(c, "endpoint_tag"),
		Providers:    parseQueryArray(c, "provider"),
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
	if m.Author == "" {
		return errors.New("author is required")
	}
	if m.ModelName == "" {
		return errors.New("model_name is required")
	}
	return nil
}
