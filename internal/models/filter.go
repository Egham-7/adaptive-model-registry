package models

// ModelFilter defines optional filtering criteria when listing models.
type ModelFilter struct {
	Provider    string `json:"provider,omitzero"`
	ModelName   string `json:"model_name,omitzero"`
	EndpointTag string `json:"endpoint_tag,omitzero"`
}
