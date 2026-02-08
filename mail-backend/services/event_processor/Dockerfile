FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/event_processor/requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy all project code into the container
COPY . .

# Command to run the API using uvicorn
# We'll use port 8001 for this service
CMD ["uvicorn", "services.event_processor.main:app", "--host", "0.0.0.0", "--port", "8001"]
