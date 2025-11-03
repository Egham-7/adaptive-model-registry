package models

// Pricing represents the cost structure for model usage
type Pricing struct {
	Prompt            string  `json:"prompt"`                       // Cost per token for input
	Completion        string  `json:"completion"`                   // Cost per token for output
	Request           *string `json:"request,omitempty"`            // Cost per request (optional)
	Image             *string `json:"image,omitempty"`              // Cost per image (optional)
	ImageOutput       *string `json:"image_output,omitempty"`       // Cost per output image (optional)
	WebSearch         *string `json:"web_search,omitempty"`         // Cost for web search (optional)
	InternalReasoning *string `json:"internal_reasoning,omitempty"` // Cost for reasoning (optional)
	Discount          *int    `json:"discount,omitempty"`           // Discount percentage (optional)
}

// Architecture represents the model's architecture and capabilities
type Architecture struct {
	Modality         string   `json:"modality"`          // e.g., "text+image->text"
	InputModalities  []string `json:"input_modalities"`  // e.g., ["text", "image"]
	OutputModalities []string `json:"output_modalities"` // e.g., ["text"]
	Tokenizer        string   `json:"tokenizer"`         // e.g., "Nova", "Llama3"
	InstructType     *string  `json:"instruct_type"`     // e.g., "chatml", null
}

// TopProvider represents the top provider's configuration for the model
type TopProvider struct {
	ContextLength       *int `json:"context_length"`        // Maximum context length
	MaxCompletionTokens *int `json:"max_completion_tokens"` // Maximum completion tokens
	IsModerated         bool `json:"is_moderated"`          // Whether content is moderated
}

// Endpoint represents a provider endpoint for the model
type Endpoint struct {
	Name                    string   `json:"name"`                      // Full endpoint name
	ModelName               string   `json:"model_name"`                // Display model name
	ContextLength           int      `json:"context_length"`            // Context length for this endpoint
	Pricing                 Pricing  `json:"pricing"`                   // Pricing specific to this endpoint
	ProviderName            string   `json:"provider_name"`             // Provider name
	Tag                     string   `json:"tag"`                       // Provider tag/slug
	Quantization            *string  `json:"quantization"`              // Quantization level (e.g., "int8")
	MaxCompletionTokens     *int     `json:"max_completion_tokens"`     // Max completion tokens
	MaxPromptTokens         *int     `json:"max_prompt_tokens"`         // Max prompt tokens
	SupportedParameters     []string `json:"supported_parameters"`      // Supported parameters for this endpoint
	Status                  int      `json:"status"`                    // Status code (0 = active)
	UptimeLast30m           *float64 `json:"uptime_last_30m"`           // Uptime percentage in last 30 minutes
	SupportsImplicitCaching bool     `json:"supports_implicit_caching"` // Whether implicit caching is supported
}

// DefaultParameters represents default parameter values for a model
type DefaultParameters map[string]interface{}
