package api

import (
	"github.com/adaptive/adaptive-model-registry/internal/models"
	"github.com/adaptive/adaptive-model-registry/internal/services"
	"github.com/gofiber/fiber/v2"
)

// ProviderHandler handles provider-related HTTP requests.
type ProviderHandler struct {
	service *services.ProviderService
}

// NewProviderHandler constructs a ProviderHandler.
func NewProviderHandler(service *services.ProviderService) *ProviderHandler {
	return &ProviderHandler{service: service}
}

// List returns providers matching optional filter criteria.
// Query parameters:
//   - tags: comma-separated list of tags to filter by
//   - status: endpoint status filter (integer)
//   - input_modalities: comma-separated list of input modalities
//   - output_modalities: comma-separated list of output modalities
//   - min_context_length: minimum context length (integer)
//   - has_pricing: filter by pricing availability (true/false)
//   - quantizations: comma-separated list of quantizations
func (h *ProviderHandler) List(c *fiber.Ctx) error {
	filter := models.ProviderFilter{
		Tags:             parseQueryArray(c, "tags"),
		Status:           parseQueryInt(c, "status"),
		InputModalities:  parseQueryArray(c, "input_modalities"),
		OutputModalities: parseQueryArray(c, "output_modalities"),
		MinContextLength: parseQueryInt(c, "min_context_length"),
		HasPricing:       parseQueryBool(c, "has_pricing"),
		Quantizations:    parseQueryArray(c, "quantizations"),
	}

	providers, err := h.service.List(c.Context(), filter)
	if err != nil {
		return c.Status(fiber.StatusInternalServerError).JSON(fiber.Map{
			"error": "Failed to list providers",
		})
	}

	return c.JSON(providers)
}
