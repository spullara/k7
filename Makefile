SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Use sudo only when needed
SUDO := $(shell command -v sudo >/dev/null 2>&1 && [ "$$(id -u)" -ne 0 ] && echo sudo)

# Explicit scripts (no fallbacks)
BUILD_SCRIPT := src/k7/cli/build.sh
INSTALL_SCRIPT := src/k7/cli/install.sh

.PHONY: help build install uninstall api-build-local api-run-local

help: ## Show this help message
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

build: ## Build the k7 CLI and API into .deb package
	@echo "Running: $(BUILD_SCRIPT)"
	@$(SHELL) "$(BUILD_SCRIPT)"

install: ## Install the k7 CLI from built .deb package
	@echo "Running: $(INSTALL_SCRIPT)"
	@$(SHELL) "$(INSTALL_SCRIPT)"
	@command -v k7 >/dev/null 2>&1 && echo "Installed: $$(command -v k7)" || true

uninstall: ## Uninstall the k7 CLI
	@echo "Running: $(INSTALL_SCRIPT) uninstall"
	@$(SHELL) "$(INSTALL_SCRIPT)" uninstall
	@echo "k7 uninstalled"

api-build-local: ## Build the API container locally (dev tag)
	@echo "Building local API image: k7-api:dev"
	docker build -f src/k7/api/Dockerfile.api -t k7-api:dev .

api-run-local: ## Run API using the local image (no pull)
	@echo "Starting API with local image (k7-api:dev)"
	docker pull cloudflare/cloudflared:latest || true
	K7_API_IMAGE=k7-api K7_API_TAG=dev k7 start-api --yes