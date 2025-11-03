package models

import (
	"database/sql/driver"
	"encoding/json"
	"errors"
	"time"
)

// Pricing represents the cost structure for model usage
type Pricing struct {
	Prompt            string  `json:"prompt,omitzero"`             // Cost per token for input
	Completion        string  `json:"completion,omitzero"`         // Cost per token for output
	Request           *string `json:"request,omitzero"`            // Cost per request (optional)
	Image             *string `json:"image,omitzero"`              // Cost per image (optional)
	ImageOutput       *string `json:"image_output,omitzero"`       // Cost per output image (optional)
	WebSearch         *string `json:"web_search,omitzero"`         // Cost for web search (optional)
	InternalReasoning *string `json:"internal_reasoning,omitzero"` // Cost for reasoning (optional)
	Discount          float64 `json:"discount,omitzero"`           // Discount percentage (optional)
}

// Architecture represents the model's architecture and capabilities
type Architecture struct {
	Modality         string   `json:"modality,omitzero"`          // e.g., "text+image->text"
	InputModalities  []string `json:"input_modalities,omitzero"`  // e.g., ["text", "image"]
	OutputModalities []string `json:"output_modalities,omitzero"` // e.g., ["text"]
	Tokenizer        string   `json:"tokenizer,omitzero"`         // e.g., "Nova", "Llama3"
	InstructType     *string  `json:"instruct_type"`              // e.g., "chatml", null
}

// TopProvider represents the top provider's configuration for the model
type TopProvider struct {
	ContextLength       *int `json:"context_length,omitzero"`        // Maximum context length
	MaxCompletionTokens *int `json:"max_completion_tokens,omitzero"` // Maximum completion tokens
	IsModerated         bool `json:"is_moderated,omitzero"`          // Whether content is moderated
}

// Endpoint represents a provider endpoint for the model
type Endpoint struct {
	Name                    string   `json:"name"`                               // Full endpoint name
	ModelName               string   `json:"model_name"`                         // Display model name
	ContextLength           int      `json:"context_length"`                     // Context length for this endpoint
	Pricing                 Pricing  `json:"pricing"`                            // Pricing specific to this endpoint
	ProviderName            string   `json:"provider_name"`                      // Provider name
	Tag                     string   `json:"tag"`                                // Provider tag/slug
	Quantization            *string  `json:"quantization,omitzero"`              // Quantization level (e.g., "int8")
	MaxCompletionTokens     *int     `json:"max_completion_tokens,omitzero"`     // Max completion tokens
	MaxPromptTokens         *int     `json:"max_prompt_tokens,omitzero"`         // Max prompt tokens
	SupportedParameters     []string `json:"supported_parameters,omitzero"`      // Supported parameters for this endpoint
	UptimeLast30m           *float64 `json:"uptime_last_30m,omitzero"`           // Uptime percentage in last 30 minutes
	SupportsImplicitCaching bool     `json:"supports_implicit_caching,omitzero"` // Whether implicit caching is supported
}

// DefaultParameters represents default parameter values for a model
type DefaultParameters map[string]any

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
	SupportedParameters []string          `json:"supported_parameters,omitzero" gorm:"column:supported_parameters;type:jsonb;serializer:json"`
	DefaultParameters   DefaultParameters `json:"default_parameters,omitzero" gorm:"column:default_parameters;type:jsonb;serializer:json"`
	Endpoints           []Endpoint        `json:"endpoints,omitzero" gorm:"type:jsonb;serializer:json"`
	CreatedAt           time.Time         `json:"created_at" gorm:"column:created_at;autoCreateTime"`
	LastUpdated         time.Time         `json:"last_updated" gorm:"column:last_updated;autoUpdateTime"`
}

// TableName ensures GORM uses the expected table name.
func (Model) TableName() string {
	return "llm_models"
}

// Scan implements sql.Scanner for JSONB fields
func (p *Pricing) Scan(value any) error {
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
func (a *Architecture) Scan(value any) error {
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
func (t *TopProvider) Scan(value any) error {
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
func (d *DefaultParameters) Scan(value any) error {
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
