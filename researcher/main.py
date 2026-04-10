from fastapi import FastAPI
from pydantic import BaseModel
from tavily import TavilyClient
import os
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

# Ensure TAVILY_API_KEY is in your .env
tavily_key = os.getenv("TAVILY_API_KEY")
if not tavily_key:
    print("WARNING: TAVILY_API_KEY not found in .env")

tavily = TavilyClient(api_key=tavily_key)

class ResearchRequest(BaseModel):
    query: str

@app.post("/research")
async def do_research(request: ResearchRequest):
    """
    Uses Tavily's AI-optimized search to find recent news.
    """
    print(f"Researcher received query: {request.query}")
    try:
        # 'topic="news"' filters for recent events; 'search_depth="advanced"' gets better context
        response = tavily.search(
            query=request.query,
            topic="news",
            search_depth="advanced",
            max_results=3
        )
        
        results_list = []
        for r in response.get('results', []):
            results_list.append(f"Source: {r['url']}\nContent: {r['content']}")
        
        combined_report = "\n\n".join(results_list)
        return {"status": "success", "results": combined_report}
    except Exception as e:
        print(f"Tavily Error: {e}")
        return {"status": "error", "results": f"Tavily Search failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
