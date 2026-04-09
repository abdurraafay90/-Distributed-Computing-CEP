"use client";

import { useState } from 'react';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000';

    try {
      const response = await fetch(`${gatewayUrl}/task`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'test_user_123', // Static for this prototype
          prompt: prompt,
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error('Error fetching data:', error);
      setResult({ error: 'Failed to call Gateway API. Ensure the Ngrok tunnel is active.' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 bg-gray-50 flex flex-col items-center">
      <h1 className="text-3xl font-bold mb-8 text-blue-800">CS-432 Multi-Agent Research System</h1>
      
      <div className="w-full max-w-2xl bg-white p-6 rounded-lg shadow-md">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter your research topic
            </label>
            <textarea
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:outline-none h-32 text-black"
              placeholder="What do you want to research?"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-md text-white font-semibold transition-colors ${
              loading ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {loading ? 'Processing...' : 'Run Distributed Task'}
          </button>
        </form>

        {result && (
          <div className="mt-8 space-y-4 border-t pt-6">
            <h2 className="text-xl font-semibold text-gray-800">System Output</h2>
            
            <div className="bg-blue-50 p-4 rounded-md">
              <h3 className="text-sm font-bold text-blue-900 uppercase tracking-wide">Research Results</h3>
              <p className="mt-1 text-gray-700">{result.research}</p>
            </div>

            <div className="bg-green-50 p-4 rounded-md">
              <h3 className="text-sm font-bold text-green-900 uppercase tracking-wide">AI Summary (Gemma:2b)</h3>
              <p className="mt-1 text-gray-700">{result.summary}</p>
            </div>

            {result.error && (
              <div className="bg-red-50 p-4 rounded-md text-red-700">
                {result.error}
              </div>
            )}
          </div>
        )}
      </div>
      
      <footer className="mt-12 text-sm text-gray-500">
        Architecture: Gateway (8000) → Researcher (8001) → EC2 Summarizer
      </footer>
    </main>
  );
}
