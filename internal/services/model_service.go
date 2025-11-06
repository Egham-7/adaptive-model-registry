package services

import (
	"context"

	"github.com/adaptive/adaptive-model-registry/internal/models"
	"github.com/adaptive/adaptive-model-registry/internal/repository"
)

// ModelService orchestrates business logic around model metadata.
type ModelService struct {
	repo repository.ModelRepository
}

// NewModelService constructs a ModelService.
func NewModelService(repo repository.ModelRepository) *ModelService {
	return &ModelService{repo: repo}
}

// List returns models matching the supplied filter ordered by name.
func (s *ModelService) List(ctx context.Context, filter models.ModelFilter) ([]models.Model, error) {
	return s.repo.List(ctx, filter)
}

// GetByProviderAndName retrieves a model by its provider and model name.
func (s *ModelService) GetByProviderAndName(ctx context.Context, provider, name string) (*models.Model, error) {
	return s.repo.GetByProviderAndName(ctx, provider, name)
}

// Upsert creates or updates a model entry.
func (s *ModelService) Upsert(ctx context.Context, model *models.Model) (*models.Model, error) {
	return s.repo.Upsert(ctx, model)
}
