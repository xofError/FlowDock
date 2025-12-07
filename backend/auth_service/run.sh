#!/bin/bash
# Quick setup and run script for FlowDock Auth Service

set -e

echo "========================================="
echo "FlowDock Auth Service - Setup & Testing"
echo "========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# ==========================================
# 1. PYTHON SETUP (Local Development)
# ==========================================
echo -e "${YELLOW}[1/4] Setting up Python environment...${NC}"
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✓ Python environment ready${NC}"
echo ""

# ==========================================
# 2. RUN TESTS LOCALLY
# ==========================================
echo -e "${YELLOW}[2/4] Running tests...${NC}"
echo ""
echo "Running all tests:"
pytest app/tests/ -v

echo ""
echo "Running with coverage:"
pytest app/tests/ --cov=app --cov-report=html

echo -e "${GREEN}✓ Tests completed (HTML report: htmlcov/index.html)${NC}"
echo ""

# ==========================================
# 3. DOCKER SETUP
# ==========================================
echo -e "${YELLOW}[3/4] Docker setup information${NC}"
echo ""
echo "To run with Docker Compose:"
echo "  1. Set the Gmail app password:"
echo "     export GMAIL_PASSWORD='your-16-char-app-password'"
echo ""
echo "  2. Start all services:"
echo "     docker-compose up -d"
echo ""
echo "  3. Check logs:"
echo "     docker-compose logs -f auth_service"
echo ""
echo "  4. Stop services:"
echo "     docker-compose down"
echo ""

# ==========================================
# 4. LOCAL SERVER (Development)
# ==========================================
echo -e "${YELLOW}[4/4] Starting local development server${NC}"
echo ""
echo "Server will start at http://localhost:8000"
echo "API docs will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Export variables for local development
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/FlowDock"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="secret"
export JWT_ALGORITHM="HS256"
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="flowdockproduction@gmail.com"
export SMTP_PASSWORD="${GMAIL_PASSWORD:-your_app_password_here}"
export SMTP_FROM_EMAIL="flowdockproduction@gmail.com"
export SMTP_FROM_NAME="FlowDock"

# Start development server with reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
