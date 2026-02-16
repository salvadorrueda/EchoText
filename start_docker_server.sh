#!/bin/bash

# Create a docker volume for whisper models if it doesn't exist
docker volume create whisper-models > /dev/null

echo "Starting echotext-server with persisted model cache..."
echo "Model will be stored in Docker volume: whisper-models"

# Run the container with the volume mount
# We mount to /root/.cache/whisper as the container runs as root by default in python:slim
docker run --gpus all \
    -p 5000:5000 \
    -v whisper-models:/root/.cache/whisper \
    --name echotext-server-persistent \
    --rm \
    echotext-server
