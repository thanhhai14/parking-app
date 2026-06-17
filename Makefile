.PHONY: dev-infra stop-infra build-api run-api migrate-create migrate-up

# Start local infrastructure
dev-infra:
	docker compose up -d postgres redis minio

# Stop local infrastructure
stop-infra:
	docker compose down

# Build backend API docker image
build-api:
	docker compose build parking-api

# Run api locally
run-api:
	cd apps/parking-api && uvicorn main:app --reload --port 8000

# Create a new alembic migration (requires message e.g. MSG="create users")
migrate-create:
	cd apps/parking-api && alembic revision --autogenerate -m "$(MSG)"

# Upgrade database to head migration
migrate-up:
	cd apps/parking-api && alembic upgrade head
