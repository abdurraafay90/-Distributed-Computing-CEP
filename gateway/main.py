from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
from dotenv import load_dotenv
import datetime
import httpx
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

load_dotenv()

app = FastAPI()

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DynamoDB Configuration
DYNAMODB_TABLE = "CS432_Tasks"
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)
table = dynamodb.Table(DYNAMODB_TABLE)

# Agent Endpoints
RESEARCHER_URL = "http://localhost:8001/research"
SUMMARIZER_URL = "http://13.60.182.213:11434/api/generate"

class TaskRequest(BaseModel):
    user_id: str
    prompt: str

@app.post("/task")
async def handle_task(request: TaskRequest):
    timestamp = datetime.datetime.now().isoformat()
    
    # 1. DynamoDB Logic: Initial status "IN_PROGRESS"
    try:
        table.put_item(
            Item={
                'user_id': request.user_id,
                'task_timestamp': timestamp,
                'prompt': request.prompt,
                'status': 'IN_PROGRESS'
            }
        )
    except Exception as e:
        print(f"DynamoDB Error: {e}")

    # 2. Call Researcher Agent
    async with httpx.AsyncClient() as client:
        try:
            res_resp = await client.post(RESEARCHER_URL, json={"query": request.prompt}, timeout=30.0)
            research_data = res_resp.json().get("results", "No research data found.")
            
            # Prepare context for Summarizer
            aggregated_context = f"NEWS AND RESEARCH DATA:\n{research_data}"
        except Exception as e:
            research_data = f"Research failed: {str(e)}"
            aggregated_context = research_data

        # 3. Call AWS Summarizer Agent (Ollama on EC2)
        summary = "Summary generation failed."
        try:
            summary_payload = {
                "model": "gemma:2b",
                "prompt": f"Summarize the following research data into a concise 3-paragraph report:\n\n{aggregated_context[:2500]}",
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "top_p": 0.9
                }
            }
            summary_resp = await client.post(SUMMARIZER_URL, json=summary_payload, timeout=90.0)
            summary = summary_resp.json().get("response", "No summary generated")
        except Exception as e:
            summary = f"Summarizer error: {str(e)}"

    # 4. Finalization: Update DynamoDB and Return
    try:
        table.update_item(
            Key={'user_id': request.user_id, 'task_timestamp': timestamp},
            UpdateExpression="set #s = :s, summary = :sum",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':s': 'COMPLETED', ':sum': summary}
        )
    except Exception as e:
        print(f"DynamoDB Update Error: {e}")

    return {
        "status": "COMPLETED",
        "research": research_data,
        "summary": summary
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
