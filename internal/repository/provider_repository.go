package repository

import (
	"context"

	"github.com/adaptive/adaptive-model-registry/internal/models"
	"gorm.io/gorm"
)

// ProviderRepository defines persistence operations for provider metadata.
type ProviderRepository interface {
	List(ctx context.Context, filter models.ProviderFilter) ([]models.Provider, error)
}

type providerRepository struct {
	db *gorm.DB
}

// NewProviderRepository constructs a ProviderRepository backed by Postgres via GORM.
func NewProviderRepository(db *gorm.DB) ProviderRepository {
	return &providerRepository{db: db}
}

func (r *providerRepository) List(ctx context.Context, filter models.ProviderFilter) ([]models.Provider, error) {
	var providers []models.Provider

	// Base query to get unique provider names with aggregated data
	query := r.db.WithContext(ctx).Table("model_endpoints").
		Select(`
			provider_name as name,
			ARRAY_AGG(DISTINCT tag) FILTER (WHERE tag IS NOT NULL AND tag != '') as tags,
			COUNT(DISTINCT model_id) as model_count,
			COUNT(*) as endpoint_count,
			COUNT(*) FILTER (WHERE status = 0) as active_count,
			ARRAY_AGG(DISTINCT quantization) FILTER (WHERE quantization IS NOT NULL AND quantization != '') as quantizations
		`).
		Group("provider_name").
		Order("provider_name")

	// Apply filters
	if len(filter.Tags) > 0 {
		// Filter providers that have at least one endpoint with any of the specified tags
		subQuery := r.db.WithContext(ctx).Table("model_endpoints").
			Select("DISTINCT provider_name").
			Where("tag IN ?", filter.Tags)
		query = query.Where("provider_name IN (?)", subQuery)
	}

	if filter.Status != nil {
		// Filter providers that have at least one endpoint with the specified status
		subQuery := r.db.WithContext(ctx).Table("model_endpoints").
			Select("DISTINCT provider_name").
			Where("status = ?", *filter.Status)
		query = query.Where("provider_name IN (?)", subQuery)
	}

	if len(filter.InputModalities) > 0 || len(filter.OutputModalities) > 0 {
		// Filter providers that have models with the specified modalities
		subQuery := r.db.WithContext(ctx).Table("model_endpoints").
			Select("DISTINCT model_endpoints.provider_name").
			Joins("JOIN llm_models ON llm_models.id = model_endpoints.model_id").
			Joins("JOIN model_architecture ON model_architecture.model_id = llm_models.id").
			Joins("JOIN model_architecture_modalities ON model_architecture_modalities.architecture_id = model_architecture.id")

		if len(filter.InputModalities) > 0 {
			subQuery = subQuery.Where("model_architecture_modalities.modality_type = ? AND model_architecture_modalities.modality_value IN ?", "input", filter.InputModalities)
		}
		if len(filter.OutputModalities) > 0 {
			subQuery = subQuery.Where("model_architecture_modalities.modality_type = ? AND model_architecture_modalities.modality_value IN ?", "output", filter.OutputModalities)
		}

		query = query.Where("provider_name IN (?)", subQuery)
	}

	if filter.MinContextLength != nil {
		// Filter providers that have at least one endpoint with minimum context length
		subQuery := r.db.WithContext(ctx).Table("model_endpoints").
			Select("DISTINCT provider_name").
			Where("context_length >= ?", *filter.MinContextLength)
		query = query.Where("provider_name IN (?)", subQuery)
	}

	if filter.HasPricing != nil {
		// Filter providers based on pricing availability
		if *filter.HasPricing {
			// Has pricing: at least one endpoint has pricing data
			subQuery := r.db.WithContext(ctx).Table("model_endpoints").
				Select("DISTINCT model_endpoints.provider_name").
				Joins("LEFT JOIN model_endpoint_pricing ON model_endpoint_pricing.endpoint_id = model_endpoints.id").
				Where("model_endpoint_pricing.prompt_cost IS NOT NULL OR model_endpoint_pricing.completion_cost IS NOT NULL")
			query = query.Where("provider_name IN (?)", subQuery)
		} else {
			// No pricing: no endpoints have pricing data
			subQuery := r.db.WithContext(ctx).Table("model_endpoints").
				Select("DISTINCT model_endpoints.provider_name").
				Joins("LEFT JOIN model_endpoint_pricing ON model_endpoint_pricing.endpoint_id = model_endpoints.id").
				Where("model_endpoint_pricing.prompt_cost IS NULL AND model_endpoint_pricing.completion_cost IS NULL")
			query = query.Where("provider_name IN (?)", subQuery)
		}
	}

	if len(filter.Quantizations) > 0 {
		// Filter providers that have at least one endpoint with specified quantizations
		subQuery := r.db.WithContext(ctx).Table("model_endpoints").
			Select("DISTINCT provider_name").
			Where("quantization IN ?", filter.Quantizations)
		query = query.Where("provider_name IN (?)", subQuery)
	}

	// Execute the query
	if err := query.Scan(&providers).Error; err != nil {
		return nil, err
	}

	return providers, nil
}
