import React, { useState } from 'react';
import { Bot, Loader2, Send, ShieldCheck, Sparkles, X } from 'lucide-react';
import { api, AIAssistantResponse } from '../api/client';
import { useAuth } from '../auth/AuthContext';

interface AIAssistantProps {
  cityId: string;
}

const starters = ['What is the current flood risk?', 'What should we do now?', 'Explain the top hotspot'];

export const AIAssistant: React.FC<AIAssistantProps> = ({ cityId }) => {
  const { workspace } = useAuth();
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AIAssistantResponse | null>(null);

  const ask = async (prompt = message) => {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    setMessage(prompt);
    try {
      setResponse(await api.askAIAssistant({ message: prompt, city_id: cityId }));
    } catch {
      setResponse({
        answer: 'The copilot is temporarily unavailable. Use the Command Center and official warnings for the safest next decision.',
        language: 'English',
        source: 'OFFLINE_NOTICE',
        evidence: [],
        suggested_actions: ['Open Command Center'],
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-5 right-5 z-50 w-[min(380px,calc(100vw-2.5rem))]">
      {!open ? (
          <button onClick={() => setOpen(true)} aria-label="Open help" className="flex items-center gap-2 rounded-full border border-emerald-400/50 bg-emerald-500 px-4 py-3 text-sm font-bold text-slate-950 shadow-2xl shadow-emerald-950/60 transition hover:bg-emerald-300">
          <Bot className="h-5 w-5" /> {workspace === 'citizen' ? 'Ask for help' : 'Ask Monsoon Copilot'} <Sparkles className="h-4 w-4" />
        </button>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-emerald-400/30 bg-slate-950 shadow-2xl shadow-black/50">
          <div className="flex items-center justify-between border-b border-slate-800 bg-emerald-500/10 px-4 py-3">
            <div className="flex items-center gap-2">
              <div className="rounded-lg bg-emerald-500/20 p-2 text-emerald-300"><Bot className="h-5 w-5" /></div>
              <div><p className="text-sm font-bold text-white">Monsoon Copilot</p><p className="text-[10px] text-slate-400">Grounded in current dashboard evidence</p></div>
            </div>
            <button onClick={() => setOpen(false)} aria-label="Close copilot" className="text-slate-400 hover:text-white"><X className="h-4 w-4" /></button>
          </div>
          <div className="max-h-[min(420px,55vh)] space-y-3 overflow-y-auto p-4">
            {!response && <p className="text-xs leading-relaxed text-slate-300">Ask about rainfall, hotspots, citizen reports, or the safest next operational step. English, Tamil, and Hinglish prompts are welcome.</p>}
            {response && <div className="space-y-3">
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-200">{response.answer}</p>
              <div className="rounded-lg border border-slate-800 bg-slate-900/70 p-3">
                <p className="mb-2 flex items-center gap-1 text-[10px] font-bold uppercase tracking-wide text-emerald-300"><ShieldCheck className="h-3 w-3" /> Evidence</p>
                {response.evidence.map((item) => <p key={item} className="text-[11px] text-slate-400">• {item}</p>)}
              </div>
              <div className="flex flex-wrap gap-2">{response.suggested_actions.map((item) => <button key={item} onClick={() => ask(item)} className="rounded-full border border-slate-700 px-2.5 py-1 text-[10px] text-slate-300 hover:border-emerald-400 hover:text-emerald-300">{item}</button>)}</div>
              <p className="text-[10px] text-slate-500">Source: {response.source.replaceAll('_', ' ')}</p>
            </div>}
            {!response && <div className="flex flex-wrap gap-2">{starters.map((item) => <button key={item} onClick={() => ask(item)} className="rounded-full border border-slate-700 px-2.5 py-1 text-[10px] text-slate-300 hover:border-emerald-400 hover:text-emerald-300">{item}</button>)}</div>}
          </div>
          <form onSubmit={(event) => { event.preventDefault(); void ask(); }} className="flex gap-2 border-t border-slate-800 p-3">
            <input value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Ask in English, தமிழ், or Hinglish..." className="min-w-0 flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-white outline-none focus:border-emerald-400" />
            <button disabled={loading || !message.trim()} aria-label="Send question" className="rounded-lg bg-emerald-500 px-3 text-slate-950 disabled:opacity-40">{loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}</button>
          </form>
        </div>
      )}
    </div>
  );
};
