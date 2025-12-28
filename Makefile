up:
	docker compose up -d --build

down:
	docker compose down -v

logs:
	docker compose logs -f api

test:
	# Add manual curl commands or pytest here
	@echo "Running health check..."
	curl -v http://localhost:8000/health/live