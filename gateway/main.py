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
    generated_title = "New Research"
    research_data = ""
    summary = "Summarization failed."

    async with httpx.AsyncClient() as client:
        # 1. Generate Title (Fast call)
        try:
            title_resp = await client.post(SUMMARIZER_URL, json={
                "model": "gemma:2b",
                "prompt": f"Title for: {request.prompt}\nTITLE:",
                "stream": False
            }, timeout=10.0)
            generated_title = title_resp.json().get("response", "New Research").strip()
        except Exception as e:
            print(f"Title Error: {e}")

        # 2. Initial Log to DynamoDB
        table.put_item(Item={
            'user_id': request.user_id,
            'task_timestamp': timestamp,
            'prompt': request.prompt,
            'title': generated_title,
            'status': 'IN_PROGRESS'
        })

        # 3. Call Researcher (Tavily)
        try:
            research_resp = await client.post(RESEARCHER_URL, json={"query": request.prompt}, timeout=30.0)
            research_data = research_resp.json().get("results", "")
        except Exception as e:
            research_data = f"Research failed: {str(e)}"

        # 4. Call Summarizer (FIXED FOR TIMEOUTS & OOM)
        if research_data:
            try:
                # 1. Increase the limit to 4000 chars so the AI actually sees all 3 sources
                context_for_ai = research_data[:4000] 
                
                ai_prompt = (
                    f"You are a Technical Journalist. Using ONLY the sources provided below, "
                    f"write a detailed multi-paragraph news report. "
                    f"Identify and group the main developments. "
                    f"Do not include intro fluff from the sources.\n\n"
                    f"DATA SOURCES:\n{context_for_ai}\n\n"
                    f"DETAILED REPORT:"
                )

                # INCREASED TIMEOUT: Set to 180 seconds to allow slow EC2 inference
                summary_resp = await client.post(
                    SUMMARIZER_URL, 
                    json={
                        "model": "gemma:2b", 
                        "prompt": ai_prompt, 
                        "stream": False,
                        "options": {
                            "num_predict": 1000, # Allows for a much longer, detailed response
                            "temperature": 0.3    # Lower temp = more factual
                        } 
                    }, 
                    timeout=180.0 
                )
                
                if summary_resp.status_code == 200:
                    summary = summary_resp.json().get("response", "Empty response from model.")
                else:
                    summary = f"EC2 Error: {summary_resp.status_code} - {summary_resp.text}"
            
            except httpx.ReadTimeout:
                summary = "Error: The EC2 Summarizer took too long to respond (Timeout)."
            except Exception as e:
                summary = f"Summarizer Error: {str(e)}"
                print(f"DEBUG: Summarizer failed with: {e}")

    # 5. Finalize DynamoDB
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
