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
	GetByName(ctx context.Context, name string) (*models.Model, error)
	GetByOpenrouterID(ctx context.Context, openrouterID string) (*models.Model, error)
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
	query := r.db.WithContext(ctx).Order("model_name")

	if filter.Provider != "" {
		query = query.Where("provider = ?", filter.Provider)
	}
	if filter.ModelName != "" {
		query = query.Where("model_name = ?", filter.ModelName)
	}
	if filter.OpenrouterID != "" {
		query = query.Where("openrouter_id = ?", filter.OpenrouterID)
	}

	if err := query.Find(&items).Error; err != nil {
		return nil, err
	}
	return items, nil
}

func (r *modelRepository) GetByName(ctx context.Context, name string) (*models.Model, error) {
	var m models.Model
	if err := r.db.WithContext(ctx).Where("model_name = ?", name).First(&m).Error; err != nil {
		if errors.Is(err, gorm.ErrRecordNotFound) {
			return nil, ErrNotFound
		}
		return nil, err
	}
	return &m, nil
}

func (r *modelRepository) GetByOpenrouterID(ctx context.Context, openrouterID string) (*models.Model, error) {
	var m models.Model
	if err := r.db.WithContext(ctx).Where("openrouter_id = ?", openrouterID).First(&m).Error; err != nil {
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
	err := r.db.WithContext(ctx).Where("model_name = ?", input.ModelName).First(&existing).Error
	switch {
	case errors.Is(err, gorm.ErrRecordNotFound):
		input.CreatedAt = now
		input.LastUpdated = now
		if err := r.db.WithContext(ctx).Create(input).Error; err != nil {
			return nil, err
		}
		return input, nil
	case err != nil:
		return nil, err
	default:
		existing.OpenrouterID = input.OpenrouterID
		existing.Provider = input.Provider
		existing.DisplayName = input.DisplayName
		existing.Description = input.Description
		existing.ContextLength = input.ContextLength
		existing.Pricing = input.Pricing
		existing.Architecture = input.Architecture
		existing.TopProvider = input.TopProvider
		existing.SupportedParameters = input.SupportedParameters
		existing.DefaultParameters = input.DefaultParameters
		existing.Endpoints = input.Endpoints
		existing.LastUpdated = now

		if err := r.db.WithContext(ctx).Save(&existing).Error; err != nil {
			return nil, err
		}
		return &existing, nil
	}
}
