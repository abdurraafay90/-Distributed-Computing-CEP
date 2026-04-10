from fastapi import FastAPI
from pydantic import BaseModel
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Initialize Tavily (Requires TAVILY_API_KEY in .env)
tavily_api_key = os.getenv("TAVILY_API_KEY")
if not tavily_api_key:
    print("WARNING: TAVILY_API_KEY not found in .env")

tavily = TavilyClient(api_key=tavily_api_key)

class ResearchRequest(BaseModel):
    query: str

@app.post("/research")
async def do_research(request: ResearchRequest):
    print(f"Researcher received query: {request.query}")
    try:
        # topic="news" filters for recent events to solve the 'latest news' issue
        response = tavily.search(
            query=request.query,
            topic="news",
            search_depth="advanced",
            max_results=3
        )
        
        results_list = []
        for r in response.get('results', []):
            results_list.append(f"Source: {r['url']}\nContent: {r['content']}")
        
        return {
            "status": "success", 
            "results": "\n\n".join(results_list)
        }
    except Exception as e:
        print(f"Tavily Error: {e}")
        return {"status": "error", "results": f"Tavily Search failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
