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
		Preload("Endpoints").
		Preload("Endpoints.Pricing").
		Order("model_name")

	if filter.Provider != "" {
		query = query.Where("provider = ?", filter.Provider)
	}
	if filter.ModelName != "" {
		query = query.Where("model_name = ?", filter.ModelName)
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
		Preload("Endpoints").
		Preload("Endpoints.Pricing").
		Where("provider = ? AND model_name = ?", provider, name).
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
		Where("provider = ? AND model_name = ?", input.Provider, input.ModelName).
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

			if len(input.Endpoints) > 0 {
				for i := range input.Endpoints {
					input.Endpoints[i].ModelID = input.ID
				}
				if err := tx.Create(&input.Endpoints).Error; err != nil {
					return err
				}

				// Create endpoint pricing
				for i := range input.Endpoints {
					if input.Endpoints[i].Pricing != nil {
						input.Endpoints[i].Pricing.EndpointID = input.Endpoints[i].ID
						if err := tx.Create(input.Endpoints[i].Pricing).Error; err != nil {
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
