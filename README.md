# DeepTrace

DeepTrace is an AI-powered CI/CD failure intelligence platform that helps developers identify, analyze, and understand failures in GitHub Actions workflows.
## Webhook Test

Testing GitHub webhook integration.
## Features

- 🚀 Real-time GitHub webhook integration
- 🤖 AI-powered failure analysis
- 📊 Interactive dashboard
- 📈 CI/CD monitoring
- 🔍 Workflow insights
- 🐳 Docker-based deployment

## Tech Stack

### Frontend
- React
- Vite
- JavaScript

### Backend
- FastAPI
- Python
- PostgreSQL

### Infrastructure
- Docker
- Docker Compose
- GitHub Webhooks
- ngrok (for local development)

## Getting Started

### Clone the repository

```bash
git clone https://github.com/hahahaboi/DeepTrace.git
cd DeepTrace
```

### Start the application

```bash
docker compose up -d
```

### Open the application

- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

## Repository Structure

```
backend/
frontend/
init-db/
docker-compose.yml
README.md
```

## Roadmap

- [x] GitHub Webhook Integration
- [x] Docker Setup
- [ ] AI Failure Analysis
- [ ] Workflow Visualization
- [ ] Historical Analytics
- [ ] Notifications
- [ ] Multi-Repository Support

## License

MIT License
