#!/bin/bash
# Fix the database by recreating it with proper initialization

echo "Stopping containers..."
sudo docker compose -f /home/timseye/AirQualitySystem/docker-compose.yml down

echo "Removing the postgres volume to force re-initialization..."
sudo docker volume rm airqualitysystem_postgres_data

echo "Starting containers (database will initialize properly)..."
sudo docker compose -f /home/timseye/AirQualitySystem/docker-compose.yml up -d

echo "Waiting for database to initialize..."
sleep 10

echo "Checking database status..."
sudo docker compose -f /home/timseye/AirQualitySystem/docker-compose.yml exec db psql -U aaqis_user -d aaqis_db -c "SELECT COUNT(*) FROM unified_data;"

echo "Done! Check http://localhost:8000 to see if visualizations load."
