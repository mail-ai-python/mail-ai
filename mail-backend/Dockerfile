FROM python:3.9-slim

WORKDIR /app

# Set the port Render will use
ENV PORT 8000

# Install all dependencies from the consolidated requirements file
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project code into the container
COPY . .

# Copy the startup script and make it executable
COPY start.sh .
RUN chmod +x ./start.sh

# Command to run the startup script
CMD ["./start.sh"]
