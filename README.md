# CS-432 Final Project: Multi-Agent Research Microservices

## Architecture
- **Gateway Agent (Port 8000)**: Entry point, DynamoDB logger, and orchestrator.
- **Researcher Agent (Port 8001)**: Returns mock data for specific queries.
- **EC2 Summarizer**: Runs `gemma:2b` on Ollama (External).
- **Frontend (Vercel/Next.js)**: UI for interaction.

## Setup Instructions

### 1. Python Services
Install dependencies:
```bash
pip install -r requirements.txt
```

Run Researcher:
```bash
python researcher/main.py
```

Run Gateway (Ensure AWS Credentials in code/env are valid):
```bash
python gateway/main.py
```

### 2. Frontend
Set environment variable for the Gateway (e.g., in `.env.local` or Vercel dashboard):
```bash
NEXT_PUBLIC_GATEWAY_URL=https://your-ngrok-url.ngrok-free.app
```

Run dev server:
```bash
cd frontend
npm install
npm run dev
```

## AWS Requirements
- **DynamoDB Table**: `CS432_Tasks` (PK: `user_id`, SK: `task_timestamp`).
- **EC2 Summarizer**: Ollama installed with `gemma:2b` model pulled, port 11434 open.
