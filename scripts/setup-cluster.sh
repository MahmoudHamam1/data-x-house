#!/bin/bash

# DX House Cluster Setup Script
# Usage: ./setup-cluster.sh [master|worker]

set -e

ROLE=${1:-"worker"}
echo "Setting up DX House cluster node as: $ROLE"

if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

if [ "$ROLE" = "master" ]; then
    echo "Initializing Docker Swarm..."
    docker swarm init --advertise-addr $(hostname -I | awk '{print $1}') || true
    
    echo "Creating overlay network..."
    docker network create --driver overlay --attachable dxhouse-net || true
    
    echo "Getting worker join token..."
    docker swarm join-token worker
    
elif [ "$ROLE" = "worker" ]; then
    echo "Worker node setup - please run the join command provided by master node"
    echo "Example: docker swarm join --token SWMTKN-1-xxxxx MASTER_IP:2377"
fi

echo "Cluster setup for $ROLE completed!"