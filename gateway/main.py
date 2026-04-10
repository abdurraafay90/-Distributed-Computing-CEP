from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import datetime
import httpx
import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from boto3.dynamodb.conditions import Key
import asyncio

load_dotenv()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DynamoDB Configuration
DYNAMODB_TABLE = "CS432_Tasks"
dynamodb = boto3.resource(
    'dynamodb',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)
table = dynamodb.Table(DYNAMODB_TABLE)

RESEARCHER_URL = "http://localhost:8001/research"
SUMMARIZER_URL = "http://13.60.182.213:11434/api/generate"

class TaskRequest(BaseModel):
    user_id: str
    prompt: str

@app.get("/history/{user_id}")
async def get_task_history(user_id: str):
    """Retrieves all past research tasks for the sidebar."""
    try:
        response = table.query(
            KeyConditionExpression=Key('user_id').eq(user_id),
            ScanIndexForward=False 
        )
        return {"status": "success", "history": response.get('Items', [])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/task")
async def handle_task(request: TaskRequest):
    timestamp = datetime.datetime.now().isoformat()
    
    # Initialize variables to prevent NameError
    generated_title = "New Research"
    research_data = ""
    summary = "No summary generated."

    async with httpx.AsyncClient() as client:
        # 1. Generate Subject Title
        try:
            title_resp = await client.post(SUMMARIZER_URL, json={
                "model": "gemma:2b",
                "prompt": f"Summarize this topic into a 3-word title. No punctuation. TOPIC: {request.prompt}\nTITLE:",
                "stream": False
            }, timeout=10.0)
            generated_title = title_resp.json().get("response", "New Research").strip()
        except:
            generated_title = request.prompt[:30] + "..."

        # 2. Log Initial Task to DynamoDB
        table.put_item(Item={
            'user_id': request.user_id,
            'task_timestamp': timestamp,
            'prompt': request.prompt,
            'title': generated_title,
            'status': 'IN_PROGRESS'
        })

        # 3. Call Researcher Agent (Tavily)
        try:
            research_resp = await client.post(RESEARCHER_URL, json={"query": request.prompt}, timeout=30.0)
            research_data = research_resp.json().get("results", "No research found.")
        except Exception as e:
            research_data = f"Research failed: {str(e)}"

        # 4. Call Summarizer Agent (Improved Prompt for More Detail)
        try:
            ai_prompt = (
                f"Act as a Technical Journalist. Write a multi-paragraph, comprehensive news report based on the following data. "
                f"Include specific incidents, technical details, and anecdotes mentioned in the text. "
                f"Ensure you discuss the implications of the findings. Use bullet points for key technical facts.\n\n"
                f"RESEARCH DATA:\n{research_data[:4000]}\n\n" # Increased context window
                f"DETAILED NEWS REPORT:"
            )
            
            summary_payload = {
                "model": "gemma:2b",
                "prompt": ai_prompt,
                "stream": False,
                "options": {
                    "num_predict": 1024, # Request a longer response
                    "temperature": 0.4,   # Balance creativity and accuracy
                    "top_p": 0.9
                }
            }
            summary_resp = await client.post(SUMMARIZER_URL, json=summary_payload, timeout=120.0)
            summary = summary_resp.json().get("response", "Summarization failed.")
        except Exception as e:
            summary = f"Summarizer error: {str(e)}"

    # 5. Finalize DynamoDB record
    table.update_item(
        Key={'user_id': request.user_id, 'task_timestamp': timestamp},
        UpdateExpression="set #s = :s, summary = :sum",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': 'COMPLETED', ':sum': summary}
    )

    return {
        "status": "COMPLETED",
        "title": generated_title,
        "research": research_data,
        "summary": summary
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
