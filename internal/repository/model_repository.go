package repository

import (
	"context"
	"errors"
	"time"

	"github.com/adaptive/adaptive-model-registry/internal/models"
	"gorm.io/gorm"
)

// ErrNotFound signals that no record matched the query.
var ErrNotFound = gorm.ErrRecordNotFound

// ModelRepository defines persistence operations for model metadata.
type ModelRepository interface {
	List(ctx context.Context, filter models.ModelFilter) ([]models.Model, error)
	GetByProviderAndName(ctx context.Context, provider, name string) (*models.Model, error)
	Upsert(ctx context.Context, model *models.Model) (*models.Model, error)
}

type modelRepository struct {
	db *gorm.DB
}

// NewModelRepository constructs a ModelRepository backed by Postgres via GORM.
func NewModelRepository(db *gorm.DB) ModelRepository {
	return &modelRepository{db: db}
}

func (r *modelRepository) List(ctx context.Context, filter models.ModelFilter) ([]models.Model, error) {
	var items []models.Model
	query := r.db.WithContext(ctx).
		Joins("Pricing").
		Joins("Architecture").
		Joins("TopProvider").
		Joins("DefaultParameters").
		Preload("Architecture.Modalities").
		Preload("SupportedParameters").
		Preload("Providers").
		Preload("Providers.Pricing").
		Order("model_name")

	// Filter by authors (OR logic - match any)
	if len(filter.Authors) > 0 {
		query = query.Where("author IN ?", filter.Authors)
	}

	// Filter by model names (OR logic - match any)
	if len(filter.ModelNames) > 0 {
		query = query.Where("model_name IN ?", filter.ModelNames)
	}

	// Filter by endpoint tags and/or providers (OR logic within each, AND between them)
	if len(filter.EndpointTags) > 0 || len(filter.Providers) > 0 {
		subQuery := query.Session(&gorm.Session{NewDB: true}).
			Select("llm_models.id").
			Joins("JOIN model_endpoints ON model_endpoints.model_id = llm_models.id").
			Where("model_endpoints.status = 0")

		if len(filter.EndpointTags) > 0 {
			subQuery = subQuery.Where("model_endpoints.tag IN ?", filter.EndpointTags)
		}
		if len(filter.Providers) > 0 {
			subQuery = subQuery.Where("model_endpoints.provider_name IN ?", filter.Providers)
		}

		query = query.Where("llm_models.id IN (?)", subQuery).Distinct()
	}

	// Filter by input modalities
	if len(filter.InputModalities) > 0 {
		subQuery := query.Session(&gorm.Session{NewDB: true}).
			Select("llm_models.id").
			Joins("JOIN model_architecture ON model_architecture.model_id = llm_models.id").
			Joins("JOIN model_architecture_modalities ON model_architecture_modalities.architecture_id = model_architecture.id").
			Where("model_architecture_modalities.modality_type = ?", "input").
			Where("model_architecture_modalities.modality_value IN ?", filter.InputModalities)

		query = query.Where("llm_models.id IN (?)", subQuery).Distinct()
	}

	// Filter by output modalities
	if len(filter.OutputModalities) > 0 {
		subQuery := query.Session(&gorm.Session{NewDB: true}).
			Select("llm_models.id").
			Joins("JOIN model_architecture ON model_architecture.model_id = llm_models.id").
			Joins("JOIN model_architecture_modalities ON model_architecture_modalities.architecture_id = model_architecture.id").
			Where("model_architecture_modalities.modality_type = ?", "output").
			Where("model_architecture_modalities.modality_value IN ?", filter.OutputModalities)

		query = query.Where("llm_models.id IN (?)", subQuery).Distinct()
	}

	// Filter by minimum context length
	if filter.MinContextLength != nil {
		query = query.Where("context_length >= ?", *filter.MinContextLength)
	}

	// Filter by maximum prompt cost
	if filter.MaxPromptCost != nil {
		query = query.Joins("LEFT JOIN model_pricing ON model_pricing.model_id = llm_models.id").
			Where("model_pricing.prompt_cost <= ?", *filter.MaxPromptCost)
	}

	// Filter by maximum completion cost
	if filter.MaxCompletionCost != nil {
		query = query.Joins("LEFT JOIN model_pricing ON model_pricing.model_id = llm_models.id").
			Where("model_pricing.completion_cost <= ?", *filter.MaxCompletionCost)
	}

	// Filter by supported parameters
	if len(filter.SupportedParams) > 0 {
		for _, param := range filter.SupportedParams {
			subQuery := query.Session(&gorm.Session{NewDB: true}).
				Select("llm_models.id").
				Joins("JOIN model_supported_parameters ON model_supported_parameters.model_id = llm_models.id").
				Where("model_supported_parameters.parameter_name = ?", param)

			query = query.Where("llm_models.id IN (?)", subQuery)
		}
	}

	// Filter by endpoint status
	if filter.Status != nil {
		subQuery := query.Session(&gorm.Session{NewDB: true}).
			Select("llm_models.id").
			Joins("JOIN model_endpoints ON model_endpoints.model_id = llm_models.id").
			Where("model_endpoints.status = ?", *filter.Status)

		query = query.Where("llm_models.id IN (?)", subQuery).Distinct()
	}

	// Filter by quantizations
	if len(filter.Quantizations) > 0 {
		subQuery := query.Session(&gorm.Session{NewDB: true}).
			Select("llm_models.id").
			Joins("JOIN model_endpoints ON model_endpoints.model_id = llm_models.id").
			Where("model_endpoints.quantization IN ?", filter.Quantizations)

		query = query.Where("llm_models.id IN (?)", subQuery).Distinct()
	}

	if err := query.Find(&items).Error; err != nil {
		return nil, err
	}
	return items, nil
}

func (r *modelRepository) GetByProviderAndName(ctx context.Context, provider, name string) (*models.Model, error) {
	var m models.Model
	if err := r.db.WithContext(ctx).
		Preload("Pricing").
		Preload("Architecture").
		Preload("Architecture.Modalities").
		Preload("TopProvider").
		Preload("SupportedParameters").
		Preload("DefaultParameters").
		Preload("Providers").
		Preload("Providers.Pricing").
		Where("author = ? AND model_name = ?", provider, name).
		First(&m).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrNotFound
		}
		return nil, err
	}
	return &m, nil
}

func (r *modelRepository) Upsert(ctx context.Context, input *models.Model) (*models.Model, error) {
	now := time.Now().UTC()

	var existing models.Model
	err := r.db.WithContext(ctx).
		Where("author = ? AND model_name = ?", input.Author, input.ModelName).
		First(&existing).Error
	switch {
	case errors.Is(err, gorm.ErrRecordNotFound):
		// Create new model with all relationships
		input.CreatedAt = now
		input.LastUpdated = now

		// Use transaction to ensure atomicity
		return input, r.db.WithContext(ctx).Transaction(func(tx *gorm.DB) error {
			// Create core model
			if err := tx.Create(input).Error; err != nil {
				return err
			}

			// Set model_id for all relationships
			if input.Pricing != nil {
				input.Pricing.ModelID = input.ID
				if err := tx.Create(input.Pricing).Error; err != nil {
					return err
				}
			}

			if input.Architecture != nil {
				input.Architecture.ModelID = input.ID
				if err := tx.Create(input.Architecture).Error; err != nil {
					return err
				}

				// Create modalities
				for i := range input.Architecture.Modalities {
					input.Architecture.Modalities[i].ArchitectureID = input.Architecture.ID
				}
				if len(input.Architecture.Modalities) > 0 {
					if err := tx.Create(&input.Architecture.Modalities).Error; err != nil {
						return err
					}
				}
			}

			if input.TopProvider != nil {
				input.TopProvider.ModelID = input.ID
				if err := tx.Create(input.TopProvider).Error; err != nil {
					return err
				}
			}

			if len(input.SupportedParameters) > 0 {
				for i := range input.SupportedParameters {
					input.SupportedParameters[i].ModelID = input.ID
				}
				if err := tx.Create(&input.SupportedParameters).Error; err != nil {
					return err
				}
			}

			if input.DefaultParameters != nil {
				input.DefaultParameters.ModelID = input.ID
				if err := tx.Create(input.DefaultParameters).Error; err != nil {
					return err
				}
			}

			if len(input.Providers) > 0 {
				for i := range input.Providers {
					input.Providers[i].ModelID = input.ID
				}
				if err := tx.Create(&input.Providers).Error; err != nil {
					return err
				}

				// Create provider pricing
				for i := range input.Providers {
					if input.Providers[i].Pricing != nil {
						input.Providers[i].Pricing.EndpointID = input.Providers[i].ID
						if err := tx.Create(input.Providers[i].Pricing).Error; err != nil {
							return err
						}
					}
				}
			}

			return nil
		})

	case err != nil:
		return nil, err

	default:
		// For now, updates are not supported in the normalized schema
		// The sync script only inserts new models
		return nil, errors.New("model updates not yet implemented for normalized schema")
	}
}
