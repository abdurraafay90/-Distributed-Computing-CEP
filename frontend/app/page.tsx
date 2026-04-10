"use client";

import { useState, useEffect } from 'react';
import { Search, History, Send, Database, Cpu } from 'lucide-react';

export default function Home() {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const userId = 'test_user_123'; // Persistent ID for your project
  const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000';

  // Fetch history on load
  const fetchHistory = async () => {
    try {
      const res = await fetch(`${gatewayUrl}/history/${userId}`, {
        headers: { 'ngrok-skip-browser-warning': 'true' }
      });
      const data = await res.json();
      if (data.status === "success") setHistory(data.history);
    } catch (e) { console.error("History fetch failed", e); }
  };

  useEffect(() => { fetchHistory(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    const userMessage = { role: 'user', content: prompt };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setPrompt('');

    try {
      const response = await fetch(`${gatewayUrl}/task`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'ngrok-skip-browser-warning': 'true' },
        body: JSON.stringify({ user_id: userId, prompt: userMessage.content }),
      });
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', ...data }]);
      fetchHistory(); // Refresh sidebar after new task completes
    } catch (error) {
      setMessages(prev => [...prev, { role: 'error', content: "Failed to connect to Gateway." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-white text-gray-800">
      {/* Sidebar: History */}
      <aside className="w-64 bg-gray-50 border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b flex items-center gap-2 font-bold text-blue-700">
          <History size={20} /> Research History
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {history.length === 0 ? (
            <p className="p-4 text-xs text-gray-400 italic">No research history yet.</p>
          ) : (
            history.map((item, i) => (
              <button key={i} className="w-full text-left p-2 text-sm hover:bg-gray-200 rounded truncate">
                {item.prompt}
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <main className="flex-1 flex flex-col relative">
        {/* Messages Feed */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 pb-32">
          {messages.length === 0 && (
            <div className="h-full flex flex-col items-center justify-center text-center opacity-50">
              <Cpu size={48} className="mb-4 text-blue-600" />
              <h2 className="text-xl font-semibold">How can I help with your research?</h2>
            </div>
          )}
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-3xl p-4 rounded-2xl ${
                msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 border border-gray-200'
              }`}>
                {msg.role === 'assistant' ? (
                  <div className="space-y-4 text-black">
                    <p className="font-medium">{msg.summary}</p>
                    <details className="text-xs opacity-70">
                      <summary className="cursor-pointer hover:underline">View Raw Research</summary>
                      <pre className="mt-2 whitespace-pre-wrap">{msg.research}</pre>
                    </details>
                  </div>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          {loading && <div className="text-blue-600 animate-pulse text-sm">System agents are researching...</div>}
        </div>

        {/* Sticky Input Bar */}
        <div className="absolute bottom-0 w-full p-6 bg-gradient-to-t from-white via-white to-transparent">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative">
            <input
              className="w-full p-4 pr-12 rounded-full border border-gray-300 shadow-sm focus:ring-2 focus:ring-blue-500 outline-none text-black"
              placeholder="Enter research topic..."
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              disabled={loading}
            />
            <button type="submit" className="absolute right-3 top-3 p-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 disabled:bg-gray-400">
              <Send size={20} />
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
