#!/bin/bash

# Start the event processor in the background
echo "Starting event processor..."
python -u services/event_processor/main.py &

# Start the FastAPI server in the foreground
echo "Starting auth service..."
uvicorn services.auth_service.main:app --host 0.0.0.0 --port $PORT
