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
	IsZDR                   string `json:"is_zdr,omitzero" gorm:"column:is_zdr"`                                       // stored as string "true"/"false"

	// Relationships
	Pricing *ModelEndpointPricing `json:"pricing,omitzero" gorm:"foreignKey:EndpointID"`
}

func (ModelEndpoint) TableName() string {
	return "model_endpoints"
}

// ModelEndpointPricing represents endpoint-specific pricing
type ModelEndpointPricing struct {
	ID                  int64  `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	EndpointID          int64  `json:"endpoint_id,omitzero" gorm:"column:endpoint_id;uniqueIndex"`
	PromptCost          string `json:"prompt_cost,omitzero" gorm:"column:prompt_cost"`
	CompletionCost      string `json:"completion_cost,omitzero" gorm:"column:completion_cost"`
	RequestCost         string `json:"request_cost,omitzero" gorm:"column:request_cost"`
	ImageCost           string `json:"image_cost,omitzero" gorm:"column:image_cost"`
	ImageOutputCost     string `json:"image_output_cost,omitzero" gorm:"column:image_output_cost"`
	AudioCost           string `json:"audio_cost,omitzero" gorm:"column:audio_cost"`
	InputAudioCacheCost string `json:"input_audio_cache_cost,omitzero" gorm:"column:input_audio_cache_cost"`
	InputCacheReadCost  string `json:"input_cache_read_cost,omitzero" gorm:"column:input_cache_read_cost"`
	InputCacheWriteCost string `json:"input_cache_write_cost,omitzero" gorm:"column:input_cache_write_cost"`
	Discount            string `json:"discount,omitzero" gorm:"column:discount"`
}

func (ModelEndpointPricing) TableName() string {
	return "model_endpoint_pricing"
}

// ModelSupportedParameter represents supported parameters (many-to-many with Model)
type ModelSupportedParameter struct {
	ID            int64              `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	ModelID       int64              `json:"model_id,omitzero" gorm:"column:model_id;index"`
	ParameterName SupportedParameter `json:"parameter_name" gorm:"column:parameter_name"`
}

func (ModelSupportedParameter) TableName() string {
	return "model_supported_parameters"
}

// ModelDefaultParameters represents default parameters (one-to-one with Model, stored as JSON for flexibility)
type ModelDefaultParameters struct {
	ID         int64                   `json:"id,omitzero" gorm:"primaryKey;autoIncrement"`
	ModelID    int64                   `json:"model_id,omitzero" gorm:"column:model_id;uniqueIndex"`
	Parameters DefaultParametersValues `json:"parameters" gorm:"column:parameters;type:jsonb;serializer:json"`
}

// DefaultParametersValues contains the strongly typed default parameter values
// This includes all parameters that can potentially have default values
type DefaultParametersValues struct {
	// Sampling parameters
	Temperature *float64 `json:"temperature,omitzero"`
	TopP        *float64 `json:"top_p,omitzero"`
	TopK        *float64 `json:"top_k,omitzero"`
	MinP        *float64 `json:"min_p,omitzero"`
	TopA        *float64 `json:"top_a,omitzero"`

	// Penalty parameters
	FrequencyPenalty *float64 `json:"frequency_penalty,omitzero"`

	// Token and output parameters
	MaxTokens           *float64 `json:"max_tokens,omitzero"`
	MaxCompletionTokens *float64 `json:"max_completion_tokens,omitzero"`
	TopLogprobs         *float64 `json:"top_logprobs,omitzero"`
	Seed                *float64 `json:"seed,omitzero"`

	// Control parameters
	N                 *float64  `json:"n,omitzero"`
	StopSequences     *[]string `json:"stop_sequences,omitzero"`
	ParallelToolCalls *bool     `json:"parallel_tool_calls,omitzero"`
	Store             *bool     `json:"store,omitzero"`
	Logprobs          *bool     `json:"logprobs,omitzero"`
}

func (ModelDefaultParameters) TableName() string {
	return "model_default_parameters"
}

// Model represents the core LLM model with normalized relationships
type Model struct {
	ID            int64     `json:"id" gorm:"primaryKey;autoIncrement"`
	Author        string    `json:"author" gorm:"column:author;index;uniqueIndex:idx_author_model"`
	ModelName     string    `json:"model_name" gorm:"column:model_name;index;uniqueIndex:idx_author_model"`
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
	Providers           []ModelEndpoint           `json:"providers,omitzero" gorm:"foreignKey:ModelID"`
}

func (Model) TableName() string {
	return "llm_models"
}

// Provider represents aggregated provider metadata from model endpoints
type Provider struct {
	Name          string   `json:"name"`           // Provider name (e.g., "openai", "anthropic")
	Tags          []string `json:"tags"`           // Unique tags across all endpoints
	ModelCount    int      `json:"model_count"`    // Number of unique models
	EndpointCount int      `json:"endpoint_count"` // Total number of endpoints
	ActiveCount   int      `json:"active_count"`   // Number of active endpoints (status = 0)
	Quantizations []string `json:"quantizations"`  // Unique quantizations available
}
