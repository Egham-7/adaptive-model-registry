package api

import (
	"context"

	"github.com/gofiber/fiber/v2"
)

func requestContext(c *fiber.Ctx) context.Context {
	if ctx := c.UserContext(); ctx != nil {
		return ctx
	}
	return context.Background()
}

func errorResponse(c *fiber.Ctx, status int, message string) error {
	return c.Status(status).JSON(fiber.Map{
		"status":  status,
		"error":   message,
		"success": false,
	})
}

func successResponse(c *fiber.Ctx, status int, payload interface{}) error {
	if payload == nil {
		return c.SendStatus(status)
	}
	return c.Status(status).JSON(payload)
}
