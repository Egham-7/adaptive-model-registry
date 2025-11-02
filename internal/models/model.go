package models

import (
	"time"

	"gorm.io/datatypes"
)

// Model captures metadata persisted for each LLM entry.
type Model struct {
	ID                  int64          `json:"id" gorm:"primaryKey;autoIncrement"`
	OpenrouterID        string         `json:"openrouter_id" gorm:"column:openrouter_id"`
	Provider            string         `json:"provider"`
	ModelName           string         `json:"model_name" gorm:"column:model_name;uniqueIndex"`
	DisplayName         string         `json:"display_name" gorm:"column:display_name"`
	Description         string         `json:"description"`
	ContextLength       int32          `json:"context_length" gorm:"column:context_length"`
	Pricing             datatypes.JSON `json:"pricing" gorm:"type:jsonb"`
	Architecture        datatypes.JSON `json:"architecture" gorm:"type:jsonb"`
	TopProvider         datatypes.JSON `json:"top_provider" gorm:"column:top_provider;type:jsonb"`
	SupportedParameters datatypes.JSON `json:"supported_parameters" gorm:"column:supported_parameters;type:jsonb"`
	DefaultParameters   datatypes.JSON `json:"default_parameters" gorm:"column:default_parameters;type:jsonb"`
	Endpoints           datatypes.JSON `json:"endpoints" gorm:"type:jsonb"`
	CreatedAt           time.Time      `json:"created_at" gorm:"column:created_at;autoCreateTime"`
	LastUpdated         time.Time      `json:"last_updated" gorm:"column:last_updated;autoUpdateTime"`
}

// TableName ensures GORM uses the expected table name.
func (Model) TableName() string {
	return "llm_models"
}
