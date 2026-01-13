# AIplay Project

This project is a mail AI application with a React frontend and a Python backend using microservices architecture.

## Build Instructions

To build and run the AIplay project on Windows:

1. Ensure you have Docker Desktop installed and running.
2. Ensure you have Node.js and npm installed.
3. Ensure you have Python installed.
4. Navigate to the aiplay directory: `cd aiplay`
5. For the backend:
   - Navigate to mail-ai-backend: `cd mail-ai-backend`
   - Run `docker-compose up --build` to build and start the services.
6. For the frontend:
   - Navigate to frontend: `cd frontend`
   - Run `npm install` to install dependencies.
   - Run `npm start` to start the development server.

## File Descriptions

- ReadMe.md: This file, providing project overview and instructions.
- TODO.md: Task tracking file.
- frontend/package.json: Defines frontend dependencies and scripts.
- frontend/package-lock.json: Locks frontend dependency versions.
- frontend/README.md: Frontend-specific documentation.
- frontend/.gitignore: Specifies files to ignore in frontend Git.
- frontend/public/: Static assets for the React app.
  - index.html: Main HTML template.
  - manifest.json: App manifest for PWA.
  - robots.txt: Instructions for web crawlers.
  - favicon.ico, logo192.png, logo512.png: App icons.
- frontend/src/: Source code for the React app.
  - App.js: Main application component.
  - App.css: Styles for the main app.
  - index.js: Entry point for the React app.
  - index.css: Global styles.
  - Login.js: Login component.
  - Dashboard.js: Dashboard component.
  - Success.js: Success component.
  - logo.svg: App logo.
  - reportWebVitals.js: Performance monitoring.
  - App.test.js: Tests for App component.
  - setupTests.js: Test setup.
- mail-ai-backend/docker-compose.yml: Defines backend services and their configurations.
- mail-ai-backend/common/: Shared code across services.
  - __init__.py: Initializes the common module.
  - ai_factory.py: Factory for AI models.
  - database.py: Database connection and operations.
  - email_repository.py: Repository for email data.
  - interfaces.py: Interface definitions.
  - models.py: Data models.
  - user_repository.py: Repository for user data.
  - utils.py: Utility functions.
- mail-ai-backend/core/: Core configurations.
  - config.py: Configuration settings.
  - dependencies.py: Dependency injection.
- mail-ai-backend/k8s/: Kubernetes deployment files.
  - auth-deployment.yaml: Deployment for auth service.
  - processor-deployment.yaml: Deployment for processor service.
- mail-ai-backend/services/: Individual services.
  - __init__.py: Initializes the services module.
  - auth/: Auth service.
    - auth_service.py: Auth service implementation.
    - main.py: Entry point for auth service.
  - auth_service/: Auth service directory.
    - __init__.py: Initializes auth service.
    - client_secret.json: OAuth client secrets.
    - DockerFile: Dockerfile for auth service.
    - main.py: Main application for auth service.
    - requirement.txt: Python dependencies for auth service.
    - routes.py: API routes for auth service.
  - email_processor/: Email processing service.
    - deduplicator.py: Removes duplicate emails.
    - email_parser.py: Parses email content.
    - email_validator.py: Validates email data.
    - main.py: Entry point for email processor.
    - processor.py: Main processing logic.
    - summarizer.py: Summarizes email content.
  - event_processor/: Event processing service.
    - __init__.py: Initializes event processor.
    - context_engine.py: Manages context for processing.
    - Dockerfile: Dockerfile for event processor.
    - main.py: Entry point for event processor.
    - processor.py: Main processing logic.
    - prompt_builder.py: Builds prompts for AI.
    - requirement.txt: Python dependencies for event processor.
    - service_account.json: Service account credentials.
    - worker.py: Worker for processing tasks.

## UML Diagram

```
+----------------+     +-----------------+
|   Frontend     |     |   Auth Service  |
|   (React)      | --> |   (FastAPI)     |
+----------------+     +-----------------+
                              |
                              | (depends on)
                              v
+----------------+     +-----------------+
|   MongoDB      | <-- | Event Processor |
|   (Database)   |     |   (Worker)      |
+----------------+     +-----------------+
```

This diagram shows the relationships between the services: Frontend communicates with Auth Service, both Auth Service and Event Processor depend on MongoDB.
