# Load .env file
source /home/ubuntu/.env
# Stop and remove existing containers
echo "Stopping and removing existing containers..."
docker ps -q | xargs -r docker stop
docker ps -aq | xargs -r docker rm

# Remove all unused Docker images
echo "Removing all old and unused Docker images..."
docker image prune -af

# Login to AWS ECR
echo "Logging into AWS ECR..."
aws ecr get-login-password --region ${{ secrets.AWS_REGION }} | docker login --username AWS --password-stdin $IMAGE_REPO

# Pull the latest Docker images
echo "Pulling latest Docker images..."
docker pull $IMAGE_REPO/django-app:latest
docker pull $IMAGE_REPO/celery-embeddings:latest
docker pull $IMAGE_REPO/celery-queries:latest
docker pull $IMAGE_REPO/rabbitmq:latest
docker pull $IMAGE_REPO/postgres:latest
docker pull $IMAGE_REPO/weaviate:latest


# Run the containers manually
echo "Starting Django app container..."
docker run -d --name django-app -p 8000:8000 --env-file .env $IMAGE_REPO/django-app:latest

echo "Starting Celery worker (embeddings)..."
docker run -d --name celery-embeddings --env-file .env $IMAGE_REPO/celery-embeddings:latest

echo "Starting Celery worker (queries)..."
docker run -d --name celery-queries --env-file .env $IMAGE_REPO/celery-queries:latest

echo "Starting RabbitMQ..."
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 $IMAGE_REPO/rabbitmq:latest

echo "Starting PostgreSQL..."
docker run -d --name postgres -p 5432:5432 \
    -e POSTGRES_DB=${DB_NAME} \
    -e POSTGRES_USER=${DB_USER} \
    -e POSTGRES_PASSWORD=${DB_PASSWORD} \
    $IMAGE_REPO/postgres:latest

echo "Starting Weaviate..."
docker run -d --name weaviate -p 8080:8080 $IMAGE_REPO/weaviate:latest