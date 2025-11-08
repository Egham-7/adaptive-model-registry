package models

// ModelFilter defines optional filtering criteria when listing models.
// All fields support multiple values (OR logic within field, AND logic between fields).
type ModelFilter struct {
	// Existing filters
	Authors           []string `json:"authors,omitzero"`             // Filter by author(s) - OR logic
	ModelNames        []string `json:"model_names,omitzero"`         // Filter by model name(s) - OR logic
	EndpointTags      []string `json:"endpoint_tags,omitzero"`       // Filter by endpoint tag(s) - OR logic
	Providers         []string `json:"providers,omitzero"`           // Filter by provider name(s) - OR logic
	InputModalities   []string `json:"input_modalities,omitzero"`    // Filter by input modality
	OutputModalities  []string `json:"output_modalities,omitzero"`   // Filter by output modality
	MinContextLength  *int     `json:"min_context_length,omitzero"`  // Minimum context window
	MaxPromptCost     *string  `json:"max_prompt_cost,omitzero"`     // Max cost per prompt token
	MaxCompletionCost *string  `json:"max_completion_cost,omitzero"` // Max cost per completion token
	SupportedParams   []string `json:"supported_params,omitzero"`    // Required supported parameters
	Status            *int     `json:"status,omitzero"`              // Endpoint status filter
	Quantizations     []string `json:"quantizations,omitzero"`       // Filter by quantization
}
