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

// GetByName returns the first model record matching the name.
// Note: model names may exist across providers; this returns the first match.
func (s *ModelService) GetByName(ctx context.Context, name string) (*models.Model, error) {
	return s.repo.GetByName(ctx, name)
}

// GetByOpenrouterID retrieves a model by its OpenRouter identifier.
func (s *ModelService) GetByOpenrouterID(ctx context.Context, openrouterID string) (*models.Model, error) {
	return s.repo.GetByOpenrouterID(ctx, openrouterID)
}

// Upsert creates or updates a model entry.
func (s *ModelService) Upsert(ctx context.Context, model *models.Model) (*models.Model, error) {
	return s.repo.Upsert(ctx, model)
}
