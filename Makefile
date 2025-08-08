# HPL Auction System - Platform Dispatcher Makefile

# Colors
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
RED := \033[0;31m
RESET := \033[0m

# Detect platform
UNAME_S := $(shell uname -s)
IS_MACOS := $(shell [ "$(UNAME_S)" = "Darwin" ] && echo true || echo false)
IS_LINUX := $(shell [ "$(UNAME_S)" = "Linux" ] && echo true || echo false)
IS_UBUNTU := $(shell [ -f /etc/lsb-release ] && grep -q "Ubuntu" /etc/lsb-release && echo true || echo false)

# Default target
.DEFAULT_GOAL := help

.PHONY: help macos-setup ubuntu-setup setup run clean info

help: ## Show available commands
	@echo "$(BLUE)🏸 HPL Auction System$(RESET)"
	@echo ""
	@echo "$(YELLOW)Platform: $(shell uname -s)$(RESET)"
	@echo ""
	@echo "$(YELLOW)Quick Setup Commands:$(RESET)"
	@if [ "$(IS_MACOS)" = "true" ]; then \
		echo "  $(GREEN)make macos-setup$(RESET)   # Complete macOS development setup (ONE COMMAND!)"; \
	elif [ "$(IS_UBUNTU)" = "true" ]; then \
		echo "  $(GREEN)make ubuntu-setup$(RESET)  # Complete Ubuntu server setup (ONE COMMAND!)"; \
	else \
		echo "  $(YELLOW)Platform not detected. Use platform-specific commands:$(RESET)"; \
		echo "  $(GREEN)make -f Makefile.macos macos-setup$(RESET)   # For macOS"; \
		echo "  $(GREEN)make -f Makefile.ubuntu ubuntu-setup$(RESET) # For Ubuntu"; \
	fi
	@echo ""
	@echo "$(YELLOW)Other Commands:$(RESET)"
	@echo "  $(GREEN)make setup$(RESET)         # Application setup only (after system dependencies)"
	@echo "  $(GREEN)make run$(RESET)           # Start the application"
	@echo "  $(GREEN)make clean$(RESET)         # Clean application only"
	@echo "  $(GREEN)make clean-all$(RESET)     # Clean application and reset database (⚠️  DELETES ALL DATA!)"
	@echo "  $(GREEN)make info$(RESET)          # Show system information"
	@echo ""
	@echo "$(YELLOW)Platform-Specific Commands:$(RESET)"
	@echo "  $(GREEN)make -f Makefile.macos help$(RESET)   # macOS commands"
	@echo "  $(GREEN)make -f Makefile.ubuntu help$(RESET)  # Ubuntu commands"
	@echo ""

macos-setup: ## Complete macOS development setup
	@if [ "$(IS_MACOS)" = "true" ]; then \
		$(MAKE) -f Makefile.macos macos-setup; \
	else \
		echo "$(RED)❌ This is not a macOS system$(RESET)"; \
		exit 1; \
	fi

ubuntu-setup: ## Complete Ubuntu server setup
	@if [ "$(IS_UBUNTU)" = "true" ]; then \
		$(MAKE) -f Makefile.ubuntu ubuntu-setup; \
	else \
		echo "$(RED)❌ This is not an Ubuntu system$(RESET)"; \
		exit 1; \
	fi

setup: ## Application setup (after system dependencies)
	@if [ "$(IS_MACOS)" = "true" ]; then \
		$(MAKE) -f Makefile.macos setup; \
	elif [ "$(IS_UBUNTU)" = "true" ]; then \
		$(MAKE) -f Makefile.ubuntu setup; \
	else \
		echo "$(RED)❌ Platform not supported automatically$(RESET)"; \
		echo "$(YELLOW)Use: make -f Makefile.macos setup (for macOS)$(RESET)"; \
		echo "$(YELLOW)Use: make -f Makefile.ubuntu setup (for Ubuntu)$(RESET)"; \
		exit 1; \
	fi

run: ## Start the application
	@if [ "$(IS_MACOS)" = "true" ]; then \
		$(MAKE) -f Makefile.macos run; \
	elif [ "$(IS_UBUNTU)" = "true" ]; then \
		$(MAKE) -f Makefile.ubuntu run; \
	else \
		echo "$(RED)❌ Platform not supported automatically$(RESET)"; \
		echo "$(YELLOW)Use: make -f Makefile.macos run (for macOS)$(RESET)"; \
		echo "$(YELLOW)Use: make -f Makefile.ubuntu run (for Ubuntu)$(RESET)"; \
		exit 1; \
	fi

clean: ## Remove virtual environment and start fresh
	@if [ "$(IS_MACOS)" = "true" ]; then \
		$(MAKE) -f Makefile.macos clean; \
	elif [ "$(IS_UBUNTU)" = "true" ]; then \
		$(MAKE) -f Makefile.ubuntu clean; \
	else \
		echo "$(YELLOW)🧹 Cleaning up (generic)...$(RESET)"; \
		rm -rf .venv; \
		rm -rf __pycache__ src/__pycache__ src/*/__pycache__; \
		find . -name "*.pyc" -delete; \
		echo "$(GREEN)✅ Cleaned up$(RESET)"; \
	fi

info: ## Show system information
	@echo "$(BLUE)📋 System Information:$(RESET)"
	@echo "OS: $(shell uname -s)"
	@if [ "$(IS_UBUNTU)" = "true" ]; then \
		echo "Distribution: $(shell lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown')"; \
	elif [ "$(IS_MACOS)" = "true" ]; then \
		echo "Version: $(shell sw_vers -productVersion 2>/dev/null || echo 'Unknown')"; \
	fi
	@echo "Platform detected: $(if $(IS_MACOS),macOS,$(if $(IS_UBUNTU),Ubuntu,Unknown))"
	@echo ""
	@if [ "$(IS_MACOS)" = "true" ]; then \
		$(MAKE) -f Makefile.macos info; \
	elif [ "$(IS_UBUNTU)" = "true" ]; then \
		$(MAKE) -f Makefile.ubuntu info; \
	else \
		echo "$(YELLOW)Use platform-specific Makefiles for detailed info$(RESET)"; \
	fi

# Direct delegation targets
init-db reset-db test postgres-status postgres-start postgres-stop postgres-restart fix-postgres-auth clean-all:
	@if [ "$(IS_MACOS)" = "true" ]; then \
		$(MAKE) -f Makefile.macos $@; \
	elif [ "$(IS_UBUNTU)" = "true" ]; then \
		$(MAKE) -f Makefile.ubuntu $@; \
	else \
		echo "$(RED)❌ Platform not supported automatically for target: $@$(RESET)"; \
		echo "$(YELLOW)Use: make -f Makefile.macos $@ (for macOS)$(RESET)"; \
		echo "$(YELLOW)Use: make -f Makefile.ubuntu $@ (for Ubuntu)$(RESET)"; \
		exit 1; \
	fi
