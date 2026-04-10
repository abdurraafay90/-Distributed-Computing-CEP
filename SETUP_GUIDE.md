# 🚀 CS-432 Final Project: Setup & Recovery Guide

This guide is designed to help you set up the **Neuraid Distributed Research System** from scratch if you forget the steps before your final evaluation.

---

## 🏗️ The Architecture (How it works)
1.  **Frontend (Vercel)**: A Next.js UI that users interact with.
2.  **Ngrok Tunnel**: Bridges the internet (Vercel) to your local ThinkPad.
3.  **Gateway Agent (Port 8000)**: The "Brain." It logs to DynamoDB, calls the Researcher, and talks to the AI.
4.  **Researcher Agent (Port 8001)**: The "Seeker." It uses the Tavily API to find real-time news.
5.  **AWS EC2 (Ollama)**: The "Thinker." It runs the `gemma:2b` model to summarize research.
6.  **AWS DynamoDB**: The "Memory." It stores all research history and titles.

---

## 🔑 Phase 1: The Credentials (.env)
You **MUST** have a `.env` file in the root directory. If it's gone, recreate it with this exact structure:

```env
# AWS Credentials
AWS_ACCESS_KEY_ID=YOUR_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET
AWS_REGION=us-east-1

# Tavily Search API (Get free at tavily.com)
TAVILY_API_KEY=tvly-XXXXX

# Frontend (Only needed if running frontend locally)
NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000
```

---

## 🐍 Phase 2: Python Environment
1.  **Create Venv**: `python -m venv venv`
2.  **Activate**: `.\venv\Scripts\activate`
3.  **Install**: `pip install -r requirements.txt`

---

## ☁️ Phase 3: AWS Setup
1.  **EC2**: Ensure your instance is **Running**.
2.  **Ollama**: SSH into EC2 and run `ollama serve`. Ensure port `11434` is open in the Security Group.
3.  **DynamoDB**: Run the setup script to create the table automatically:
    ```bash
    python create_table.py
    ```

---

## 🚦 Phase 4: Running the Project (The Order Matters)

### 1. Start the Researcher (Seeker)
```powershell
.\venv\Scripts\python.exe researcher/main.py
```

### 2. Start the Gateway (Orchestrator)
**Note**: Before starting, check `gateway/main.py` and ensure the `SUMMARIZER_URL` matches your current EC2 IP.
```powershell
.\venv\Scripts\python.exe gateway/main.py
```

### 3. Start the Tunnel
```bash
ngrok http 8000
```
*Copy the `https://...` URL provided by Ngrok.*

### 4. Update Vercel
1.  Go to Vercel Project Settings > Environment Variables.
2.  Update `NEXT_PUBLIC_GATEWAY_URL` with the new Ngrok URL.
3.  **IMPORTANT**: Go to "Deployments" and click **Redeploy**.

---

## 🛠️ Common Troubleshooting
*   **"Failed to connect to Gateway"**: Usually means Ngrok has expired or the URL in Vercel doesn't match the one in your terminal.
*   **"No summary generated"**: Check if your EC2 is running and if you can ping `http://<EC2_IP>:11434`.
*   **Empty Sidebar**: Ensure the `user_id` in `page.tsx` matches the one you are querying in the Gateway.
