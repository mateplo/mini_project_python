.PHONY: init run test build down clean

# Install Python dependencies
init:
	pip install -r requirements.txt

# Build the Docker images
build:
	docker compose build

# Run the full stack (API + dashboard)
run:
	docker compose up -d

# Run the test suite with coverage
test:
	pytest tests/ -v --cov=api

# Stop the containers
down:
	docker compose down

# Stop and remove containers, networks and images
clean:
	docker compose down --rmi all --volumes
