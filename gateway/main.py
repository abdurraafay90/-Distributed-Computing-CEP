from fastapi.middleware.cors import CORSMiddleware
import os
import asyncio
from dotenv import load_dotenv
import datetime
import httpx
import boto3
from boto3.dynamodb.conditions import Key
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

@app.get("/history/{user_id}")
async def get_task_history(user_id: str):
    """Retrieves all past research tasks for a specific user."""
    try:
        # Query items with user_id, ScanIndexForward=False sorts by newest first
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            ScanIndexForward=False 
        )
        return {"status": "success", "history": response.get('Items', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TaskRequest(BaseModel):
    user_id: str
    prompt: str

@app.post("/task")
async def handle_task(request: TaskRequest):
    timestamp = datetime.datetime.now().isoformat()
    
    async with httpx.AsyncClient() as client:
        # 1. Generate a Short Title (Subject) using Gemma:2b
        generated_title = "New Research"
        try:
            title_payload = {
                "model": "gemma:2b",
                "prompt": f"Summarize this topic into a 3-word title. No punctuation. TOPIC: {request.prompt}\nTITLE:",
                "stream": False,
                "options": {"temperature": 0.3}
            }
            # Fast call to EC2 for the title
            title_resp = await client.post(SUMMARIZER_URL, json=title_payload, timeout=10.0)
            generated_title = title_resp.json().get("response", "New Research").strip().replace("\n", "")
        except Exception:
            generated_title = request.prompt[:30] + "..." # Fallback

        # 2. Log to DynamoDB with the new 'title' field
        try:
            table.put_item(
                Item={
                    'user_id': request.user_id,
                    'task_timestamp': timestamp,
                    'prompt': request.prompt,
                    'title': generated_title, # New Field!
                    'status': 'IN_PROGRESS'
                }
            )
        except Exception as e:
            print(f"DynamoDB Error: {e}")

        # 3. Call Researcher Agent (Now using Tavily)
        try:
            research_resp = await client.post(RESEARCHER_URL, json={"query": request.prompt}, timeout=30.0)
            research_data = research_resp.json().get("results", "No research found.")
            
            # Prepare context for Summarizer
            aggregated_context = f"NEWS AND RESEARCH DATA:\n{research_data}"
        except Exception as e:
            research_data = f"Research failed: {str(e)}"
            aggregated_context = research_data

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
