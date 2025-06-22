#!/bin/bash

# Migration script for McpEasy
# Usage: ./migrate.sh create "message" or ./migrate.sh upgrade

set -e

# Function to check if database is running
check_db() {
    if ! docker-compose ps db | grep -q "Up"; then
        echo "Database not running. Starting database..."
        docker-compose up db -d
        echo "Waiting for database to be ready..."
        sleep 5
    fi
}

# Load environment variables from .env file (before changing directory)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Change to migrations directory
cd src/migrations

case "$1" in
    "create")
        if [ -z "$2" ]; then
            echo "Usage: ./migrate.sh create \"migration message\" [--custom org_name]"
            echo "  --custom: Create a custom migration for specific organization"
            exit 1
        fi
        check_db
        
        # Check if this is a custom migration
        if [ "$3" = "--custom" ] && [ ! -z "$4" ]; then
            # Custom migration with org prefix
            org_name="$4"
            timestamp=$(date +"%Y%m%d_%H%M%S")
            migration_name="${timestamp}_custom_${org_name}_${2// /_}"
            echo "Creating custom migration for $org_name: $migration_name"
            uv run alembic revision --autogenerate -m "$migration_name"
        else
            # Core migration
            timestamp=$(date +"%Y%m%d_%H%M%S")
            migration_name="${timestamp}_core_${2// /_}"
            echo "Creating core migration: $migration_name"
            uv run alembic revision --autogenerate -m "$migration_name"
        fi
        ;;
    "upgrade")
        echo "Running migrations..."
        uv run alembic upgrade head
        ;;
    "status")
        echo "Migration status:"
        uv run alembic current
        echo "Latest available:"
        uv run alembic heads
        ;;
    "history")
        echo "Migration history:"
        uv run alembic history
        ;;
    *)
        echo "Usage: ./migrate.sh {create|upgrade|status|history}"
        echo "  create \"message\"              - Create new core migration"
        echo "  create \"message\" --custom org - Create new custom migration for organization"
        echo "  upgrade                        - Run pending migrations" 
        echo "  status                         - Show current migration status"
        echo "  history                        - Show migration history"
        echo ""
        echo "Examples:"
        echo "  ./migrate.sh create \"add user preferences\"                    # Core migration"
        echo "  ./migrate.sh create \"add invoice tables\" --custom acme        # Custom migration"
        exit 1
        ;;
esac