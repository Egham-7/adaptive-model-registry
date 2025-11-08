package api

import (
	"strings"

	"github.com/gofiber/fiber/v2"
)

// parseQueryArray extracts query parameters as a string slice.
// Supports: ?key=val1&key=val2 OR ?key=val1,val2
func parseQueryArray(c *fiber.Ctx, key string) []string {
	var results []string

	// Get all values for this key
	values := c.Context().QueryArgs().PeekMulti(key)

	for _, value := range values {
		str := string(value)
		if str != "" {
			// Split by comma to support comma-separated values
			parts := strings.SplitSeq(str, ",")
			for part := range parts {
				trimmed := strings.TrimSpace(part)
				if trimmed != "" {
					results = append(results, trimmed)
				}
			}
		}
	}

	return results
}

// parseQueryInt extracts a single integer query parameter
func parseQueryInt(c *fiber.Ctx, key string) *int {
	val := c.QueryInt(key, -1)
	if val == -1 {
		return nil
	}
	return &val
}

// parseQueryString extracts a single string query parameter
func parseQueryString(c *fiber.Ctx, key string) *string {
	val := c.Query(key)
	if val == "" {
		return nil
	}
	return &val
}

// parseQueryBool extracts a single boolean query parameter
func parseQueryBool(c *fiber.Ctx, key string) *bool {
	val := c.Query(key)
	if val == "" {
		return nil
	}

	switch val {
	case "true":
		return &[]bool{true}[0]
	case "false":
		return &[]bool{false}[0]
	default:
		return nil
	}
}
