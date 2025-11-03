package models

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"time"
)

// Model captures metadata persisted for each LLM entry.
type Model struct {
	ID                  int64             `json:"id" gorm:"primaryKey;autoIncrement"`
	OpenrouterID        string            `json:"openrouter_id" gorm:"column:openrouter_id"`
	Provider            string            `json:"provider"`
	ModelName           string            `json:"model_name" gorm:"column:model_name;uniqueIndex"`
	DisplayName         string            `json:"display_name" gorm:"column:display_name"`
	Description         string            `json:"description"`
	ContextLength       int32             `json:"context_length" gorm:"column:context_length"`
	Pricing             Pricing           `json:"pricing" gorm:"type:jsonb;serializer:json"`
	Architecture        Architecture      `json:"architecture" gorm:"type:jsonb;serializer:json"`
	TopProvider         TopProvider       `json:"top_provider" gorm:"column:top_provider;type:jsonb;serializer:json"`
	SupportedParameters []string          `json:"supported_parameters" gorm:"column:supported_parameters;type:jsonb;serializer:json"`
	DefaultParameters   DefaultParameters `json:"default_parameters" gorm:"column:default_parameters;type:jsonb;serializer:json"`
	Endpoints           []Endpoint        `json:"endpoints" gorm:"type:jsonb;serializer:json"`
	CreatedAt           time.Time         `json:"created_at" gorm:"column:created_at;autoCreateTime"`
	LastUpdated         time.Time         `json:"last_updated" gorm:"column:last_updated;autoUpdateTime"`
}

// TableName ensures GORM uses the expected table name.
func (Model) TableName() string {
	return "llm_models"
}

// Scan implements sql.Scanner for JSONB fields
func (p *Pricing) Scan(value interface{}) error {
	if value == nil {
		return nil
	}
	bytes, ok := value.([]byte)
	if !ok {
		return errors.New("failed to unmarshal JSONB value for Pricing")
	}
	return json.Unmarshal(bytes, p)
}

// Value implements driver.Valuer for JSONB fields
func (p Pricing) Value() (driver.Value, error) {
	return json.Marshal(p)
}

// Scan implements sql.Scanner for JSONB fields
func (a *Architecture) Scan(value interface{}) error {
	if value == nil {
		return nil
	}
	bytes, ok := value.([]byte)
	if !ok {
		return errors.New("failed to unmarshal JSONB value for Architecture")
	}
	return json.Unmarshal(bytes, a)
}

// Value implements driver.Valuer for JSONB fields
func (a Architecture) Value() (driver.Value, error) {
	return json.Marshal(a)
}

// Scan implements sql.Scanner for JSONB fields
func (t *TopProvider) Scan(value interface{}) error {
	if value == nil {
		return nil
	}
	bytes, ok := value.([]byte)
	if !ok {
		return errors.New("failed to unmarshal JSONB value for TopProvider")
	}
	return json.Unmarshal(bytes, t)
}

// Value implements driver.Valuer for JSONB fields
func (t TopProvider) Value() (driver.Value, error) {
	return json.Marshal(t)
}

// Scan implements sql.Scanner for JSONB fields
func (d *DefaultParameters) Scan(value interface{}) error {
	if value == nil {
		*d = make(DefaultParameters)
		return nil
	}
	bytes, ok := value.([]byte)
	if !ok {
		return errors.New("failed to unmarshal JSONB value for DefaultParameters")
	}
	return json.Unmarshal(bytes, d)
}

// Value implements driver.Valuer for JSONB fields
func (d DefaultParameters) Value() (driver.Value, error) {
	return json.Marshal(d)
}
