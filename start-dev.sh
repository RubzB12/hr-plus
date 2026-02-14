#!/bin/bash
set -e

echo "🚀 HR-Plus Development Environment Startup"
echo "==========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Docker
echo "📦 Checking Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo ""
    echo "Please start Docker Desktop first, then run this script again."
    echo ""
    echo "macOS: Open Docker Desktop from Applications"
    echo "Windows: Open Docker Desktop from Start Menu"
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"
echo ""

# Start infrastructure services
echo "🏗️  Starting infrastructure services (PostgreSQL, Redis, Elasticsearch, MinIO)..."
docker-compose up -d
echo ""

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready (~30 seconds)..."
sleep 10

# Check PostgreSQL
echo "🔍 Checking PostgreSQL..."
until docker exec hrplus-postgres pg_isready -U hrplus > /dev/null 2>&1; do
    echo "   Waiting for PostgreSQL..."
    sleep 2
done
echo -e "${GREEN}✅ PostgreSQL is ready${NC}"

# Check Redis
echo "🔍 Checking Redis..."
until docker exec hrplus-redis redis-cli ping > /dev/null 2>&1; do
    echo "   Waiting for Redis..."
    sleep 2
done
echo -e "${GREEN}✅ Redis is ready${NC}"

echo ""
echo -e "${GREEN}✅ All infrastructure services are ready!${NC}"
echo ""

# Django migrations
echo "🗄️  Running Django migrations..."
cd backend
python manage.py migrate
echo -e "${GREEN}✅ Database migrations complete${NC}"
echo ""

# Check for superuser
echo "👤 Checking for Django superuser..."
if python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); exit(0 if User.objects.filter(is_superuser=True).exists() else 1)" 2>/dev/null; then
    echo -e "${GREEN}✅ Superuser exists${NC}"
else
    echo -e "${YELLOW}⚠️  No superuser found${NC}"
    echo ""
    echo "Create a superuser to access Django admin:"
    echo "  cd backend && python manage.py createsuperuser"
fi
echo ""

# Summary
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📌 Infrastructure Services:"
echo "   • PostgreSQL:      localhost:5432"
echo "   • Redis:           localhost:6379"
echo "   • Elasticsearch:   localhost:9200"
echo "   • MinIO Console:   http://localhost:9001 (admin/minioadmin)"
echo "   • Mailpit:         http://localhost:8025"
echo ""
echo "🚀 Start the application servers:"
echo ""
echo "   Terminal 1 - Django Backend:"
echo "   $ cd backend"
echo "   $ python manage.py runserver"
echo "   → http://localhost:8000"
echo ""
echo "   Terminal 2 - Public Career Site (optional):"
echo "   $ cd apps/public-careers"
echo "   $ npm install  # first time only"
echo "   $ npm run dev"
echo "   → http://localhost:3000"
echo ""
echo "   Terminal 3 - Internal Dashboard (optional):"
echo "   $ cd apps/internal-dashboard"
echo "   $ npm install  # first time only"
echo "   $ npm run dev"
echo "   → http://localhost:3001"
echo ""
echo "📚 Quick Links:"
echo "   • Django Admin:    http://localhost:8000/admin"
echo "   • API Docs:        http://localhost:8000/api/docs/"
echo "   • API Schema:      http://localhost:8000/api/schema/"
echo ""
echo "💡 Tip: To stop infrastructure services:"
echo "   $ docker-compose down"
echo ""
