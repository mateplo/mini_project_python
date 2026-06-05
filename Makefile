.PHONY: init dev up down logs test lint build clean

# Install Python dependencies
init:
	pip install -r requirements.txt

# Run API and dashboard locally without Docker (dev)
dev:
	uvicorn api.main:app --reload --port 8000 & \
	streamlit run dashboard/app.py

# Build images and start the full stack
up:
	docker compose up --build -d

# Stop the stack and remove volumes
down:
	docker compose down -v

# Follow the container logs
logs:
	docker compose logs -f

# Run the test suite (fails under 75% coverage)
test:
	pytest tests/ -v --cov=api --cov-fail-under=75

# Lint the code
lint:
	flake8 api/ dashboard/ tests/

# Build the Docker images
build:
	docker compose build

# Stop and remove containers, networks and images
clean:
	docker compose down --rmi all --volumes
