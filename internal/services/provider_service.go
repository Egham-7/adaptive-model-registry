package services

import (
	"context"

	"github.com/adaptive/adaptive-model-registry/internal/models"
	"github.com/adaptive/adaptive-model-registry/internal/repository"
)

// ProviderService orchestrates business logic around provider metadata.
type ProviderService struct {
	repo repository.ProviderRepository
}

// NewProviderService constructs a ProviderService.
func NewProviderService(repo repository.ProviderRepository) *ProviderService {
	return &ProviderService{repo: repo}
}

// List returns providers matching the supplied filter ordered by name.
func (s *ProviderService) List(ctx context.Context, filter models.ProviderFilter) ([]models.Provider, error) {
	return s.repo.List(ctx, filter)
}
