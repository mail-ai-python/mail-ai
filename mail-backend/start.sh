#!/bin/bash

# The application now runs as a single web process.
# The event processor logic is triggered by the /api/notifications webhook.

echo "Starting web service..."
uvicorn services.auth_service.main:app --host 0.0.0.0 --port $PORT
