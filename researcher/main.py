from fastapi import FastAPI
from pydantic import BaseModel
from tavily import AsyncTavilyClient # Use the Async version
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Check if API key exists
API_KEY = os.getenv("TAVILY_API_KEY")
if not API_KEY:
    print("CRITICAL ERROR: TAVILY_API_KEY not found in .env file!")

# Initialize the Async Client
tavily = AsyncTavilyClient(api_key=API_KEY)

class ResearchRequest(BaseModel):
    query: str

@app.post("/research")
async def do_research(request: ResearchRequest):
    print(f"Researching: {request.query}")
    try:
        # Use await with the async client
        response = await tavily.search(
            query=request.query,
            topic="news",
            search_depth="advanced",
            max_results=3
        )
        
        results_list = []
        for i, r in enumerate(response.get('results', []), 1):
            # Explicitly label sources so the AI sees them as separate data points
            results_list.append(f"--- NEWS SOURCE {i} ---\nURL: {r['url']}\nFACTS: {r['content']}")
        
        report = "\n\n".join(results_list)
        print(f"Research success: {len(report)} chars gathered.")
        
        return {
            "status": "success", 
            "results": report
        }
    except Exception as e:
        print(f"Tavily Error: {str(e)}")
        return {"status": "error", "results": f"Tavily Search failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
