# Neuraid: Distributed Multi-Agent Research System

**Course**: CS-432 Distributed Computing
**Final Project: Multi-Agent Microservice Architecture**

## 🌐 Overview
Neuraid is a distributed, agentic system designed to research real-time news and provide AI-generated summaries. It leverages a modern microservice architecture, distributed across local environments and AWS cloud.

### 🏗️ Distributed Components
*   **Next.js Frontend**: A modern, React-based user interface with a retractable sidebar, research history, and dark mode. Hosted on Vercel.
*   **Gateway Agent (FastAPI)**: Acts as the orchestrator. It manages user tasks, logs data to DynamoDB, and generates contextual titles for each research session.
*   **Researcher Agent (FastAPI)**: Specializes in web intelligence. It uses the **Tavily AI Search API** to retrieve high-quality, real-time news data.
*   **Summarizer Agent (Ollama/EC2)**: A cloud-hosted AI model (**Gemma:2b**) that processes raw research data into concise, factual summaries.
*   **AWS DynamoDB**: A schemaless NoSQL database for storing user research history, task statuses, and generated titles.

---

## 🚀 Deployment

### 1. Prerequisites
- Python 3.10+
- Node.js & npm (for frontend)
- Ngrok CLI (for tunneling)
- AWS Account with DynamoDB & EC2 (Ubuntu)

### 2. Environment Setup
Create a `.env` file with your AWS credentials and Tavily API key:
```env
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
TAVILY_API_KEY=xxx
```

### 3. Running Locally
```bash
# 1. Install Dependencies
pip install -r requirements.txt

# 2. Start Microservices
python researcher/main.py (Port 8001)
python gateway/main.py (Port 8000)

# 3. Open the Tunnel
ngrok http 8000
```

---

## 🛠️ Key Distributed Features
*   **Parallel Orchestration**: The system is designed to handle multiple research requests simultaneously.
*   **Scalable Memory**: Research history is stored in a distributed DynamoDB table, accessible from any client.
*   **Cloud Inference**: LLM processing is offloaded to an AWS EC2 instance, allowing local machines to remain lightweight.
*   **Contextual Title Generation**: Automatically summarizes the user's prompt into a 3-word title for better UX.

---

## 📄 License
This project is for educational purposes only as part of the CS-432 Final Evaluation.
