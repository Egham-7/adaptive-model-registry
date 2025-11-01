package models

// ModelFilter defines optional filtering criteria when listing models.
type ModelFilter struct {
	Provider     string
	ModelName    string
	OpenrouterID string
}
