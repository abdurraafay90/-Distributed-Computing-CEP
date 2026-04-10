from fastapi import FastAPI
from pydantic import BaseModel
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
import httpx
import asyncio

app = FastAPI()

class ResearchRequest(BaseModel):
    query: str

async def scrape_top_link(url: str):
    """Simple scraper to get main text content from a news URL."""
    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
            response = await client.get(url, headers=headers)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Remove script, style, nav, and ads
                for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    element.decompose()
                
                # Get text and clean it up (limit to first 2000 chars)
                text = soup.get_text(separator=' ')
                lines = [line.strip() for line in text.splitlines() if line.strip()]
                clean_text = ' '.join(lines)
                
                # Remove common noise words
                noise_words = ["Advertisement", "Newsletter", "Sign Up", "Join Now", "Cookies", "Privacy Policy"]
                for word in noise_words:
                    clean_text = clean_text.replace(word, "")
                
                return clean_text[:2000]
    except Exception as e:
        return f"Scraping failed: {str(e)}"
    return "No content found."

@app.post("/research")
async def do_research(request: ResearchRequest):
    """
    Search phase: Use DuckDuckGo to find top 3 results.
    Extraction phase: Scrape the top result for more context.
    """
    print(f"Researching topic: {request.query}")
    
    results_list = []
    top_link = None
    
    # 1. Search phase
    try:
        with DDGS() as ddgs:
            # Get top 3 snippets
            search_results = [r for r in ddgs.text(request.query, max_results=3)]
            for r in search_results:
                results_list.append(f"Source: {r['href']}\nSnippet: {r['body']}")
                if not top_link:
                    top_link = r['href']
    except Exception as e:
        return {"status": "error", "results": f"Search failed: {str(e)}"}

    # 2. Extraction phase (Scrape the first link)
    scraped_content = ""
    if top_link:
        print(f"Scraping top source: {top_link}")
        scraped_content = await scrape_top_link(top_link)

    # 3. Synthesis phase
    combined_report = "\n\n".join(results_list)
    if scraped_content:
        combined_report += f"\n\n--- EXTENDED DATA FROM TOP LINK ---\n{scraped_content}"

    return {
        "status": "success", 
        "results": combined_report
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
