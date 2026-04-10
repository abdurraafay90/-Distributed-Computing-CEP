from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from boto3.dynamodb.conditions import Key
import os, datetime, httpx, boto3, json
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

app = FastAPI()

# CORS Middleware for Frontend Communication
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# --- CONFIGURATION ---
# Verified Model: llama3.2:3b
# Verified IP: 13.60.182.213
MODEL_NAME = "llama3.2:3b" 
RESEARCHER_URL = "http://localhost:8001/research"
SUMMARIZER_URL = "http://13.60.182.213:11434/api/generate"

# DynamoDB Configuration
DYNAMODB_TABLE = "CS432_Tasks"
dynamodb = boto3.resource(
    'dynamodb', 
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)
table = dynamodb.Table(DYNAMODB_TABLE)

class TaskRequest(BaseModel):
    user_id: str
    prompt: str

@app.get("/history/{user_id}")
async def get_task_history(user_id: str):
    """Retrieves all past research tasks for the user sidebar."""
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
    print(f"\n🚀 [TASK RECEIVED] {request.prompt}")
    
    generated_title = "Research Result"
    research_results = []
    summary = "Error: Processing Failed"

    async with httpx.AsyncClient() as client:
        # 1. Generate Title (Fast call to EC2)
        try:
            print("      ↳ [1/4] Generating Title...")
            t_resp = await client.post(SUMMARIZER_URL, json={
                "model": MODEL_NAME, 
                "prompt": f"Summarize into a 3-word title: {request.prompt}\nTITLE:", 
                "stream": False
            }, timeout=15.0)
            
            if t_resp.status_code == 200:
                generated_title = t_resp.json().get("response", "New Research").strip().replace('"', '')
                print(f"      ✔ Title: {generated_title}")
        except Exception as e: 
            print(f"      ✖ Title Gen Failed: {e}")
            generated_title = request.prompt[:30]

        # 2. Initial Log to DynamoDB
        print("      ↳ [2/4] Logging 'IN_PROGRESS' to DynamoDB...")
        table.put_item(Item={
            'user_id': request.user_id, 
            'task_timestamp': timestamp,
            'prompt': request.prompt, 
            'title': generated_title, 
            'status': 'IN_PROGRESS'
        })

        # 3. Research Phase (Tavily Agent)
        try:
            print("      ↳ [3/4] Calling Researcher Agent...")
            r_resp = await client.post(RESEARCHER_URL, json={"query": request.prompt}, timeout=45.0)
            research_results = r_resp.json().get("results", [])
            print(f"      ✔ Research gathered ({len(research_results)} sources)")
        except Exception as e:
            print(f"      ✖ Researcher Agent Failed: {e}")
            research_results = f"Researcher error: {str(e)}"

        # 4. Summarization Phase (OPTIMIZED FOR SPEED & TYPE-SAFETY)
        if research_results:
            try:
                # TYPE-SAFE DATA JOIN: Prevents AttributeError if results are a string
                if isinstance(research_results, str):
                    raw_text = research_results
                else:
                    raw_text = "\n\n".join([
                        r.get("content", "") if isinstance(r, dict) else str(r) 
                        for r in research_results
                    ])
                
                # LIMIT TO 3,500 CHARS: Fast ingestion for CPU-based inference
                clean_context = raw_text[:300] 
                
                print(f"      ↳ [4/4] Generating Quick Summary (Target: < 100s)...")

                prompt = (
                    f"System: You are a concise technical reporter. Summarize this data "
                    f"in 3 bullet points. Be brief and factual.\n\n"
                    f"DATA:\n{clean_context}\n\n"
                    f"REPORT:"
                )

                s_resp = await client.post(SUMMARIZER_URL, json={
                    "model": MODEL_NAME, 
                    "prompt": prompt, 
                    "stream": False,
                    "options": {
                        "num_ctx": 1024,      # Smaller context = faster RAM access
                        "num_predict": 200,    # Limits output length to prevent timeout
                        "temperature": 0.3,
                        "num_thread": 2        # Uses both vCPUs on m7i.large
                    }
                }, timeout=150.0)
                
                if s_resp.status_code == 200:
                    summary = s_resp.json().get("response", "Model returned no content.")
                    print("      ✔ Summary Complete.")
                else:
                    summary = f"EC2 Error {s_resp.status_code}: {s_resp.text}"
                    print(f"      ✖ EC2 returned status {s_resp.status_code}")
            
            except Exception as e:
                summary = f"Summarizer Error: {type(e).__name__} - {str(e)}"
                print(f"      ✖ Summarizer Exception: {e}")

    # 5. Finalize DynamoDB Entry
    print("      ↳ Finalizing DynamoDB entry...")
    try:
        table.update_item(
            Key={'user_id': request.user_id, 'task_timestamp': timestamp},
            UpdateExpression="set #s = :s, summary = :sum, research = :res",
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={
                ':s': 'COMPLETED', 
                ':sum': summary, 
                ':res': json.dumps(research_results) 
            }
        )
    except Exception as e:
        print(f"      ✖ Final DB Update Failed: {e}")

    print("✨ [TASK FINISHED]\n")
    return {"status": "COMPLETED", "title": generated_title, "summary": summary}

if __name__ == "__main__":
    import uvicorn
    # Listening on local port 8000
    uvicorn.run(app, host="0.0.0.0", port=8000)