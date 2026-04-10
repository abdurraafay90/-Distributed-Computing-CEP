"use client";

import { useState, useEffect } from 'react';
import { 
  Menu, 
  PanelLeftClose, 
  PanelLeftOpen, 
  Send, 
  History, 
  Cpu, 
  Moon, 
  Sun,
  Plus,
  Database
} from 'lucide-react';

export default function Home() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [darkMode, setDarkMode] = useState(false);
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const [history, setHistory] = useState<any[]>([]);

  const userId = 'test_user_123';
  const gatewayUrl = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000';

  // Toggle Dark Mode Class on Document
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Fetch DynamoDB History
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

  const handleSelectHistory = (item: any) => {
    // Clear current messages and load the historical data
    setMessages([
      { role: 'user', content: item.prompt },
      { 
        role: 'assistant', 
        summary: item.summary, 
        research: item.research,
        status: 'COMPLETED' 
      }
    ]);
    
    // Optional: Close sidebar on mobile after selection
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || loading) return;

    const userMsg = { role: 'user', content: prompt };
    setMessages(prev => [...prev, userMsg]);
    setLoading(true);
    setPrompt('');

    try {
      const response = await fetch(`${gatewayUrl}/task`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'ngrok-skip-browser-warning': 'true' 
        },
        body: JSON.stringify({ user_id: userId, prompt: userMsg.content }),
      });
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', ...data }]);
      fetchHistory();
    } catch (error) {
      setMessages(prev => [...prev, { role: 'error', content: "Gateway connection failed." }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-white dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 transition-colors duration-300 overflow-hidden font-sans">
      
      {/* Retractable Sidebar */}
      <aside className={`${isSidebarOpen ? 'w-72' : 'w-0'} transition-all duration-300 ease-in-out bg-zinc-50 dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 flex flex-col relative overflow-hidden shrink-0`}>
        <div className={`p-4 flex items-center justify-between transition-opacity duration-300 ${isSidebarOpen ? 'opacity-100' : 'opacity-0 pointer-events-none'}`}>
          <button 
            onClick={() => setMessages([])}
            className="flex items-center gap-2 w-full p-2 border border-zinc-300 dark:border-zinc-700 rounded-lg hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors"
          >
            <Plus size={18} /> <span className="text-sm font-medium">New Research</span>
          </button>
        </div>

        <div className={`flex-1 overflow-y-auto p-2 space-y-1 ${isSidebarOpen ? 'opacity-100' : 'opacity-0'}`}>
          <div className="px-3 py-2 text-xs font-bold text-zinc-500 uppercase tracking-wider">Recent History</div>
          {history.length === 0 ? (
            <p className="px-3 py-4 text-xs italic text-zinc-400">No past tasks found.</p>
          ) : (
            history.map((item, i) => (
              <button 
                key={i} 
                onClick={() => handleSelectHistory(item)}
                className="w-full text-left p-3 text-sm hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded-xl truncate transition-colors group relative"
                title={item.prompt} // Show full prompt on hover
              >
                <div className="flex items-center gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-blue-500 opacity-50"></div>
                  {/* Use the new title field, or fall back to prompt */}
                  <span className="truncate">{item.title || item.prompt}</span>
                </div>
              </button>
            ))
          )}
        </div>

        {/* Sidebar Footer Controls */}
        <div className={`p-4 border-t dark:border-zinc-800 ${isSidebarOpen ? 'opacity-100' : 'opacity-0'}`}>
          <button 
            onClick={() => setDarkMode(!darkMode)}
            className="flex items-center gap-3 w-full p-2 hover:bg-zinc-200 dark:hover:bg-zinc-800 rounded-lg transition-colors"
          >
            {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            <span className="text-sm font-medium">{darkMode ? 'Light Mode' : 'Dark Mode'}</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        
        {/* Top Header */}
        <header className="p-4 flex items-center gap-4 border-b dark:border-zinc-900 shrink-0">
          <button 
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 hover:bg-zinc-100 dark:hover:bg-zinc-900 rounded-lg text-zinc-500"
          >
            {isSidebarOpen ? <PanelLeftClose size={22} /> : <PanelLeftOpen size={22} />}
          </button>
          <div className="font-bold flex items-center gap-2">
            <Cpu size={20} className="text-blue-600" />
            <span className="tracking-tight uppercase">Neuraid System</span>
          </div>
        </header>

        {/* Message Feed */}
        <div className="flex-1 overflow-y-auto scroll-smooth">
          <div className="max-w-3xl mx-auto p-6 space-y-8 pb-40">
            {messages.length === 0 && (
              <div className="h-[60vh] flex flex-col items-center justify-center text-center">
                <div className="p-4 bg-blue-100 dark:bg-blue-900/30 rounded-full mb-4">
                  <Cpu size={40} className="text-blue-600 dark:text-blue-400" />
                </div>
                <h1 className="text-3xl font-bold tracking-tight mb-2">How can I assist your research?</h1>
                <p className="text-zinc-500 max-w-sm">Ask anything. Neuraid will gather live data via Tavily and summarize it for you using Gemma on AWS.</p>
              </div>
            )}
            
            {messages.map((msg, i) => (
              <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-full bg-blue-600 flex-shrink-0 flex items-center justify-center text-white">
                    <Cpu size={16} />
                  </div>
                )}
                <div className={`max-w-[85%] p-4 rounded-2xl ${
                  msg.role === 'user' 
                    ? 'bg-zinc-100 dark:bg-zinc-800' 
                    : ''
                }`}>
                  {msg.role === 'assistant' ? (
                    <div className="space-y-6">
                      <div className="leading-relaxed text-lg whitespace-pre-wrap">
                        {msg.summary}
                      </div>
                      <div className="pt-4 border-t border-zinc-200 dark:border-zinc-800">
                        <details className="group">
                          <summary className="text-xs font-bold text-zinc-400 cursor-pointer list-none flex items-center gap-2 hover:text-blue-500 transition-colors">
                            <Database size={12} /> VIEW RAW RESEARCH SOURCES
                          </summary>
                          <div className="mt-4 p-4 bg-zinc-50 dark:bg-zinc-900 rounded-xl border dark:border-zinc-800 text-xs font-mono whitespace-pre-wrap opacity-80 overflow-x-auto">
                            {msg.research}
                          </div>
                        </details>
                      </div>
                    </div>
                  ) : (
                    <p className="text-lg">{msg.content}</p>
                  )}
                  {msg.role === 'error' && (
                    <p className="text-red-500 font-medium">{msg.content}</p>
                  )}
                </div>
              </div>
            ))}
            
            {loading && (
              <div className="flex gap-4 items-center text-blue-600 dark:text-blue-400">
                <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                  <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                </div>
                <span className="text-sm font-medium">Gathering intelligence...</span>
              </div>
            )}
          </div>
        </div>

        {/* Center-Bottom Input Bar */}
        <div className="absolute bottom-0 w-full p-4 bg-gradient-to-t from-white dark:from-zinc-950 via-white dark:via-zinc-950 to-transparent shrink-0">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative group">
            <div className="relative flex items-center bg-zinc-100 dark:bg-zinc-900 rounded-2xl border-2 border-transparent focus-within:border-blue-500/50 transition-all shadow-xl">
              <input
                className="w-full p-5 pr-14 bg-transparent outline-none text-zinc-900 dark:text-white placeholder-zinc-500"
                placeholder="What do you want to research today?"
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                disabled={loading}
              />
              <button 
                type="submit" 
                disabled={loading || !prompt.trim()}
                className="absolute right-3 p-2.5 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-xl hover:scale-105 disabled:opacity-20 disabled:scale-100 transition-all shadow-lg"
              >
                <Send size={18} />
              </button>
            </div>
            <p className="mt-3 text-[10px] text-center text-zinc-500 font-medium">
              CS-432 Distributed Systems Project • Powered by Tavily & Gemma:2b
            </p>
          </form>
        </div>
      </main>
    </div>
  );
}
