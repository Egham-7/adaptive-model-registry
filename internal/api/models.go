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
		// Existing filters
		Authors:      parseQueryArray(c, "author"),
		ModelNames:   parseQueryArray(c, "model_name"),
		EndpointTags: parseQueryArray(c, "endpoint_tag"),
		Providers:    parseQueryArray(c, "provider"),

		// NEW: Advanced filters
		InputModalities:   parseQueryArray(c, "input_modality"),
		OutputModalities:  parseQueryArray(c, "output_modality"),
		MinContextLength:  parseQueryInt(c, "min_context_length"),
		MaxPromptCost:     parseQueryString(c, "max_prompt_cost"),
		MaxCompletionCost: parseQueryString(c, "max_completion_cost"),
		SupportedParams:   parseQueryArray(c, "supported_param"),
		Status:            parseQueryInt(c, "status"),
		Quantizations:     parseQueryArray(c, "quantization"),
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
