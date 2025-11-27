#!/bin/bash

echo "🚀 SmartHR Uzbekistan Backend Setup"
echo "===================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo "${GREEN}✓ .env file created${NC}"
else
    echo "${GREEN}✓ .env file already exists${NC}"
fi

# Check if using Docker
read -p "Use Docker for setup? (y/n): " use_docker

if [ "$use_docker" = "y" ]; then
    echo ""
    echo "${YELLOW}Setting up with Docker...${NC}"
    
    # Build and start containers
    docker-compose up -d --build
    
    echo "${YELLOW}Waiting for services to start...${NC}"
    sleep 10
    
    # Run migrations
    echo "${YELLOW}Running migrations...${NC}"
    docker-compose exec backend python manage.py migrate
    
    # Create superuser
    echo ""
    echo "${YELLOW}Create superuser:${NC}"
    docker-compose exec backend python manage.py createsuperuser
    
    # Create MinIO bucket
    echo "${YELLOW}Setting up MinIO...${NC}"
    docker-compose exec backend python manage.py shell << EOF
import boto3
from django.conf import settings

s3 = boto3.client(
    's3',
    endpoint_url=settings.AWS_S3_ENDPOINT_URL,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

try:
    s3.create_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
    print('MinIO bucket created')
except:
    print('MinIO bucket already exists')
EOF
    
    echo ""
    echo "${GREEN}✓ Docker setup complete!${NC}"
    echo ""
    echo "Services running:"
    echo "  - API: http://localhost:8000"
    echo "  - Admin: http://localhost:8000/admin"
    echo "  - API Docs: http://localhost:8000/api/docs"
    echo "  - MinIO Console: http://localhost:9001"
    echo ""
    echo "View logs: docker-compose logs -f"
    echo "Stop services: docker-compose down"
    
else
    echo ""
    echo "${YELLOW}Setting up manually...${NC}"
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    echo "Python version: $python_version"
    
    # Create virtual environment
    if [ ! -d "venv" ]; then
        echo "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
        echo "${GREEN}✓ Virtual environment created${NC}"
    fi
    
    # Activate virtual environment
    echo "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    
    # Install dependencies
    echo "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
    
    # Check PostgreSQL
    echo ""
    echo "${YELLOW}Make sure PostgreSQL is running and database is created${NC}"
    read -p "Press enter when ready..."
    
    # Run migrations
    echo "${YELLOW}Running migrations...${NC}"
    python manage.py migrate
    
    # Create superuser
    echo ""
    echo "${YELLOW}Create superuser:${NC}"
    python manage.py createsuperuser
    
    # Collect static files
    echo "${YELLOW}Collecting static files...${NC}"
    python manage.py collectstatic --noinput
    
    echo ""
    echo "${GREEN}✓ Manual setup complete!${NC}"
    echo ""
    echo "To start the server:"
    echo "  1. Activate venv: source venv/bin/activate"
    echo "  2. Start Redis: redis-server"
    echo "  3. Start Django: python manage.py runserver"
    echo "  4. Start Celery: celery -A config worker -l info"
    echo ""
fi

echo ""
echo "${GREEN}Setup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "  1. Update .env with your credentials"
echo "  2. Configure SMS (Twilio) settings"
echo "  3. Set up file storage (MinIO/S3)"
echo "  4. Review API documentation at /api/docs"
echo ""
echo "Happy coding! 🎉"