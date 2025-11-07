package models

// ModelFilter defines optional filtering criteria when listing models.
// All fields support multiple values (OR logic within field, AND logic between fields).
type ModelFilter struct {
	Authors      []string `json:"authors,omitzero"`       // Filter by author(s) - OR logic
	ModelNames   []string `json:"model_names,omitzero"`   // Filter by model name(s) - OR logic
	EndpointTags []string `json:"endpoint_tags,omitzero"` // Filter by endpoint tag(s) - OR logic
	Providers    []string `json:"providers,omitzero"`     // Filter by provider name(s) - OR logic
}
