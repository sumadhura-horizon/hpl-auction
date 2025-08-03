# Badminton League Auction System - Simplified Makefile

# Variables
PYTHON := python3
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
STREAMLIT := $(VENV_DIR)/bin/streamlit
APP_FILE := app.py
PORT := 8501

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
RESET := \033[0m

# Default target
.DEFAULT_GOAL := help

.PHONY: help setup run clean init-db reset-db test info

help: ## Show available commands
	@echo "$(BLUE)🏸 Badminton League Auction System$(RESET)"
	@echo ""
	@echo "$(YELLOW)Essential Commands:$(RESET)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Usage Examples:$(RESET)"
	@echo "  make setup     # First time setup"
	@echo "  make run       # Start the application"
	@echo "  make clean     # Clean and start fresh"
	@echo ""

setup: $(VENV_DIR) install init-db ## Complete setup (run this first)
	@echo "$(GREEN)✅ Setup complete! Run 'make run' to start.$(RESET)"

$(VENV_DIR): ## Create virtual environment
	@echo "$(BLUE)🔧 Creating virtual environment...$(RESET)"
	$(PYTHON) -m venv $(VENV_DIR)

install: $(VENV_DIR) ## Install dependencies
	@echo "$(BLUE)📦 Installing dependencies...$(RESET)"
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed$(RESET)"

run: $(VENV_DIR) ## Start the application
	@echo "$(BLUE)🚀 Starting application on http://localhost:$(PORT)$(RESET)"
	@echo "$(YELLOW)Press Ctrl+C to stop$(RESET)"
	$(STREAMLIT) run $(APP_FILE) --server.port $(PORT)

init-db: $(VENV_DIR) ## Initialize database with sample data
	@echo "$(BLUE)📊 Initializing database...$(RESET)"
	cd $(shell pwd) && $(VENV_PYTHON) scripts/upload_data.py init
	@echo "$(GREEN)✅ Database initialized$(RESET)"

reset-db: $(VENV_DIR) ## Reset database (deletes all data!)
	@echo "$(YELLOW)⚠️  This will delete all auction data!$(RESET)"
	@read -p "Continue? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	cd $(shell pwd) && $(VENV_PYTHON) scripts/upload_data.py reset
	@echo "$(GREEN)✅ Database reset$(RESET)"

test: $(VENV_DIR) ## Test the application
	@echo "$(BLUE)🧪 Testing application...$(RESET)"
	$(VENV_PYTHON) -c "from app import AuctionApp; print('✅ App can be imported'); app = AuctionApp(); print('✅ App initializes correctly')"

clean: ## Remove virtual environment and start fresh
	@echo "$(YELLOW)🧹 Cleaning up...$(RESET)"
	rm -rf $(VENV_DIR)
	rm -rf __pycache__ src/__pycache__ src/*/__pycache__
	find . -name "*.pyc" -delete
	@echo "$(GREEN)✅ Cleaned up$(RESET)"

info: ## Show system information
	@echo "$(BLUE)📋 System Info:$(RESET)"
	@echo "Python: $(shell $(PYTHON) --version 2>/dev/null || echo 'Not found')"
	@echo "Virtual env: $(shell [ -d $(VENV_DIR) ] && echo 'Exists' || echo 'Missing')"
	@echo "Database: $(shell [ -f auction.db ] && echo 'Exists' || echo 'Missing')"
	@echo "Port: $(PORT)"
