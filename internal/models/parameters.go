package models

// SupportedParameter represents the allowed parameter names for model configuration
type SupportedParameter string

const (
	// Sampling parameters
	SupportedParameterTemperature SupportedParameter = "temperature"
	SupportedParameterTopP        SupportedParameter = "top_p"
	SupportedParameterTopK        SupportedParameter = "top_k"
	SupportedParameterMinP        SupportedParameter = "min_p"
	SupportedParameterTopA        SupportedParameter = "top_a"

	// Penalty parameters
	SupportedParameterFrequencyPenalty SupportedParameter = "frequency_penalty"

	// Token and output parameters
	SupportedParameterTopLogprobs SupportedParameter = "top_logprobs"
	SupportedParameterSeed        SupportedParameter = "seed"

	// Response format parameters
	SupportedParameterResponseFormat    SupportedParameter = "response_format"
	SupportedParameterStructuredOutputs SupportedParameter = "structured_outputs"

	// Control parameters
	SupportedParameterStop              SupportedParameter = "stop"
	SupportedParameterTools             SupportedParameter = "tools"
	SupportedParameterToolChoice        SupportedParameter = "tool_choice"
	SupportedParameterParallelToolCalls SupportedParameter = "parallel_tool_calls"

	// Reasoning parameters
	SupportedParameterIncludeReasoning SupportedParameter = "include_reasoning"
	SupportedParameterReasoning        SupportedParameter = "reasoning"
)

// SupportedParametersList contains all valid supported parameters
var SupportedParametersList = []SupportedParameter{
	SupportedParameterTemperature,
	SupportedParameterTopP,
	SupportedParameterTopK,
	SupportedParameterMinP,
	SupportedParameterTopA,
	SupportedParameterFrequencyPenalty,
	SupportedParameterTopLogprobs,
	SupportedParameterSeed,
	SupportedParameterResponseFormat,
	SupportedParameterStructuredOutputs,
	SupportedParameterStop,
	SupportedParameterTools,
	SupportedParameterToolChoice,
	SupportedParameterParallelToolCalls,
	SupportedParameterIncludeReasoning,
	SupportedParameterReasoning,
}

// IsValidSupportedParameter checks if a parameter name is valid
func IsValidSupportedParameter(param string) bool {
	for _, validParam := range SupportedParametersList {
		if string(validParam) == param {
			return true
		}
	}
	return false
}

// DefaultParameter represents the allowed parameter names for default values
type DefaultParameter string

const (
	DefaultParameterTemperature      DefaultParameter = "temperature"
	DefaultParameterTopP             DefaultParameter = "top_p"
	DefaultParameterFrequencyPenalty DefaultParameter = "frequency_penalty"
)

// DefaultParametersList contains all valid default parameters
var DefaultParametersList = []DefaultParameter{
	DefaultParameterTemperature,
	DefaultParameterTopP,
	DefaultParameterFrequencyPenalty,
}

// IsValidDefaultParameter checks if a parameter name is valid for defaults
func IsValidDefaultParameter(param string) bool {
	for _, validParam := range DefaultParametersList {
		if string(validParam) == param {
			return true
		}
	}
	return false
}
