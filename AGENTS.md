# Repository Guidelines

## Project Structure & Module Organization
- `cmd/api/main.go` wires config loading, database setup, the model repository, and the Fiber HTTP server.
- `internal` holds domain code by concern (`config`, `database`, `models`, `repository`, `services`, `server`); add new packages under the relevant module.
- Keep tests and fakes beside the code they cover so CI picks them up with `./...`.

## Build, Test, and Development Commands
- `go mod tidy` refreshes dependencies; run it after adding imports.
- `go run ./cmd/api` starts the registry on `http://localhost:3000`.
- `go build ./...` and `go test -race -coverprofile=coverage.txt ./...` mirror the CI build and coverage gates.
- `gofumpt -w -extra .` plus `goimports -w .` satisfy the formatting job.
- `golangci-lint run` and `gosec ./...` reproduce the lint and security workflows; treat warnings as merge blockers.

## Coding Style & Naming Conventions
- Use `gofumpt` defaults (tabs, trailing commas, sorted imports) and keep files `goimports` clean.
- Exported identifiers need doc comments; JSON tags stay `snake_case`, while Go types and services use PascalCase.
- HTTP handlers belong in `internal/server`, persistence in `internal/repository`, and orchestration or interfaces in `internal/services`.

## Testing Guidelines
- Write table-driven tests with Go’s `testing` package; name entries `Test<Thing>` in `*_test.go`.
- Prefer unit tests around repositories and services; when hitting Postgres, supply `DATABASE_URL` for the test DSN and clean up data between cases.
- Commit the coverage profile only for verification (`coverage.txt` should remain untracked).

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `chore:`) as seen in the existing log.
- PRs need a concise summary, test evidence (`go test ...` output is enough), and links to issues or tickets; add payload samples when APIs change.
- Verify CI locally after rebases by rerunning the format, lint, security, and test commands above.

## Configuration & Security Tips
- Export `DATABASE_URL` locally (e.g., `postgres://user:pass@localhost:5432/adaptive_models?sslmode=disable`) before running or testing.
- Keep secrets out of git; use git-ignored `.env` files and document required variables in README updates.
