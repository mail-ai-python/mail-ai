FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/event_processor/requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy service code
COPY services/event_processor/ .

# Command to run the listener
CMD ["python", "-u", "services/event_processor/main.py"]