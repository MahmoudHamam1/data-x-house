#!/bin/bash

# DX House Services Deployment Script

set -e

echo "Deploying DX House services..."

# Check environment variables
required_vars=("HIVE_DB_PASSWORD" "DB_ROOT_PASSWORD" "RANGER_ADMIN_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Environment variable $var is not set"
        exit 1
    fi
done

# Deploy database first
echo "Deploying MySQL database..."
docker run -d --name dx-database --hostname dx-database \
  --network dxhouse-net \
  -e MYSQL_ROOT_PASSWORD=${DB_ROOT_PASSWORD} \
  -e MYSQL_DATABASE=metastore \
  -e MYSQL_USER=hive \
  -e MYSQL_PASSWORD=${HIVE_DB_PASSWORD} \
  mysql/mysql-server:8.0

# Wait for database to be ready
echo "Waiting for database to be ready..."
sleep 30

# Deploy core services
echo "Deploying DX House cluster..."
docker run -itd --name dx-master --hostname dx-master \
  --network dxhouse-net \
  -p 9870:9870 -p 8088:8088 -p 10000:10000 -p 9083:9083 -p 7077:7077 -p 4040:4040 \
  dxhouse-cls:latest

echo "Services deployment completed!"
echo "Access points:"
echo "- HDFS NameNode: http://localhost:9870"
echo "- YARN ResourceManager: http://localhost:8088"
echo "- Spark Master: http://localhost:4040"