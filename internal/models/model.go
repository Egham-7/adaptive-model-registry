package models

import (
	"time"
)

// ModelPricing represents model pricing (database entity and API response)
type ModelPricing struct {
	ID                    int64  `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	ModelID               int64  `json:"model_id,omitzero" gorm:"column:model_id;uniqueIndex"`
	PromptCost            string `json:"prompt_cost" gorm:"column:prompt_cost"`
	CompletionCost        string `json:"completion_cost" gorm:"column:completion_cost"`
	RequestCost           string `json:"request_cost,omitzero" gorm:"column:request_cost"`
	ImageCost             string `json:"image_cost,omitzero" gorm:"column:image_cost"`
	WebSearchCost         string `json:"web_search_cost,omitzero" gorm:"column:web_search_cost"`
	InternalReasoningCost string `json:"internal_reasoning_cost,omitzero" gorm:"column:internal_reasoning_cost"`
}

func (ModelPricing) TableName() string {
	return "model_pricing"
}

// ModelArchitecture represents model architecture (database entity and API response)
type ModelArchitecture struct {
	ID           int64  `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	ModelID      int64  `json:"model_id,omitzero" gorm:"column:model_id;uniqueIndex"`
	Modality     string `json:"modality" gorm:"column:modality"`
	Tokenizer    string `json:"tokenizer" gorm:"column:tokenizer"`
	InstructType string `json:"instruct_type,omitzero" gorm:"column:instruct_type"`

	// Relationships
	Modalities []ModelArchitectureModality `json:"modalities,omitzero" gorm:"foreignKey:ArchitectureID"`
}

func (ModelArchitecture) TableName() string {
	return "model_architecture"
}

// ModelArchitectureModality represents input/output modalities
type ModelArchitectureModality struct {
	ID             int64  `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	ArchitectureID int64  `json:"architecture_id,omitzero" gorm:"column:architecture_id;index"`
	ModalityType   string `json:"modality_type" gorm:"column:modality_type"` // "input" or "output"
	ModalityValue  string `json:"modality_value" gorm:"column:modality_value"`
}

func (ModelArchitectureModality) TableName() string {
	return "model_architecture_modalities"
}

// ModelTopProvider represents top provider metadata (database entity and API response)
type ModelTopProvider struct {
	ID                  int64  `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	ModelID             int64  `json:"model_id,omitzero" gorm:"column:model_id;uniqueIndex"`
	ContextLength       *int   `json:"context_length,omitzero" gorm:"column:context_length"`
	MaxCompletionTokens *int   `json:"max_completion_tokens,omitzero" gorm:"column:max_completion_tokens"`
	IsModerated         string `json:"is_moderated,omitzero" gorm:"column:is_moderated"` // stored as string "true"/"false"
}

func (ModelTopProvider) TableName() string {
	return "model_top_provider"
}

// ModelEndpoint represents a provider endpoint for the model (database entity and API response)
type ModelEndpoint struct {
	ID                      int64  `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	ModelID                 int64  `json:"model_id,omitzero" gorm:"column:model_id;index"`
	Name                    string `json:"name" gorm:"column:name"`
	EndpointModelName       string `json:"endpoint_model_name" gorm:"column:endpoint_model_name"`
	ContextLength           int    `json:"context_length" gorm:"column:context_length"`
	ProviderName            string `json:"provider_name" gorm:"column:provider_name;index"`
	Tag                     string `json:"tag" gorm:"column:tag"`
	Quantization            string `json:"quantization,omitzero" gorm:"column:quantization"`
	MaxCompletionTokens     *int   `json:"max_completion_tokens,omitzero" gorm:"column:max_completion_tokens"`
	MaxPromptTokens         *int   `json:"max_prompt_tokens,omitzero" gorm:"column:max_prompt_tokens"`
	Status                  int    `json:"status" gorm:"column:status"`
	UptimeLast30m           string `json:"uptime_last_30m,omitzero" gorm:"column:uptime_last_30m"`
	SupportsImplicitCaching string `json:"supports_implicit_caching,omitzero" gorm:"column:supports_implicit_caching"` // stored as string "true"/"false"

	// Relationships
	Pricing *ModelEndpointPricing `json:"pricing,omitzero" gorm:"foreignKey:EndpointID"`
}

func (ModelEndpoint) TableName() string {
	return "model_endpoints"
}

// ModelEndpointPricing represents endpoint-specific pricing
type ModelEndpointPricing struct {
	ID             int64  `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	EndpointID     int64  `json:"endpoint_id,omitzero" gorm:"column:endpoint_id;uniqueIndex"`
	PromptCost     string `json:"prompt_cost,omitzero" gorm:"column:prompt_cost"`
	CompletionCost string `json:"completion_cost,omitzero" gorm:"column:completion_cost"`
	RequestCost    string `json:"request_cost,omitzero" gorm:"column:request_cost"`
	ImageCost      string `json:"image_cost,omitzero" gorm:"column:image_cost"`
}

func (ModelEndpointPricing) TableName() string {
	return "model_endpoint_pricing"
}

// ModelSupportedParameter represents supported parameters (many-to-many with Model)
type ModelSupportedParameter struct {
	ID            int64  `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	ModelID       int64  `json:"model_id,omitzero" gorm:"column:model_id;index"`
	ParameterName string `json:"parameter_name" gorm:"column:parameter_name"`
}

func (ModelSupportedParameter) TableName() string {
	return "model_supported_parameters"
}

// ModelDefaultParameters represents default parameters (one-to-one with Model, stored as JSON for flexibility)
type ModelDefaultParameters struct {
	ID         int64          `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	ModelID    int64          `json:"model_id,omitzero" gorm:"column:model_id;uniqueIndex"`
	Parameters map[string]any `json:"parameters" gorm:"column:parameters;type:jsonb;serializer:json"`
}

func (ModelDefaultParameters) TableName() string {
	return "model_default_parameters"
}

// Model represents the core LLM model with normalized relationships
type Model struct {
	ID            int64     `json:"id" gorm:"primaryKey;autoIncrement"`
	Provider      string    `json:"provider" gorm:"column:provider;index;uniqueIndex:idx_provider_model"`
	ModelName     string    `json:"model_name" gorm:"column:model_name;index;uniqueIndex:idx_provider_model"`
	DisplayName   string    `json:"display_name,omitzero" gorm:"column:display_name"`
	Description   string    `json:"description,omitzero" gorm:"column:description"`
	ContextLength int       `json:"context_length,omitzero" gorm:"column:context_length"`
	CreatedAt     time.Time `json:"created_at" gorm:"column:created_at"`
	LastUpdated   time.Time `json:"last_updated" gorm:"column:last_updated"`

	// Normalized relationships
	Pricing             *ModelPricing             `json:"pricing,omitzero" gorm:"foreignKey:ModelID"`
	Architecture        *ModelArchitecture        `json:"architecture,omitzero" gorm:"foreignKey:ModelID"`
	TopProvider         *ModelTopProvider         `json:"top_provider,omitzero" gorm:"foreignKey:ModelID"`
	SupportedParameters []ModelSupportedParameter `json:"supported_parameters,omitzero" gorm:"foreignKey:ModelID"`
	DefaultParameters   *ModelDefaultParameters   `json:"default_parameters,omitzero" gorm:"foreignKey:ModelID"`
	Endpoints           []ModelEndpoint           `json:"endpoints,omitzero" gorm:"foreignKey:ModelID"`
}

func (Model) TableName() string {
	return "llm_models"
}
