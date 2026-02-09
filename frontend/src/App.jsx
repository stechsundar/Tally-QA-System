import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Loader2, Link as LinkIcon, Sparkles, RefreshCw, ChevronDown } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import subdomainsData from './subdomains.json';
import './index.css';

const API_BASE = "http://localhost:8000";

function App() {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: "Hello! I'm your Tally Expert AI. Ask me anything about TallyPrime, and I'll consult the latest documentation for you." }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [subdomain, setSubdomain] = useState('');
    const [config, setConfig] = useState(null);
    const messagesEndRef = useRef(null);

    useEffect(() => {
        // 1. Detect Label (Subdomain or URL Path)
        const host = window.location.hostname;
        const pathParts = window.location.pathname.split('/').filter(Boolean);
        const path = pathParts[0];
        const parts = host.split('.');

        let currentLabel = '';

        if (path && path.length > 1) {
            currentLabel = path.toLowerCase();
        } else if (parts.length > 2) {
            currentLabel = parts[0].toLowerCase();
        }

        if (currentLabel) {
            setSubdomain(currentLabel);
            // 2. Set Branding Config directly from imported JSON
            if (subdomainsData[currentLabel]) {
                setConfig(subdomainsData[currentLabel]);
            }
        }
    }, []);

    useEffect(() => {
        if (config?.name) {
            document.title = `Tally Expert (${config.name})`;
        } else if (subdomain) {
            // Capitalize fallback if not in config
            const displaySub = subdomain.charAt(0).toUpperCase() + subdomain.slice(1);
            document.title = `Tally Expert (${displaySub})`;
        } else {
            document.title = "Tally Expert AI";
        }
    }, [subdomain, config]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setLoading(true);

        try {
            const response = await axios.post(`${API_BASE}/ask`, { question: userMsg });
            const { answer, sources } = response.data;

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: answer,
                sources: sources
            }]);
        } catch (error) {
            setMessages(prev => [...prev, {
                role: 'assistant',
                content: "I'm having trouble connecting to my brain. Please make sure the backend server (server.py) is running on port 8000."
            }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex flex-col items-center bg-bg-dark text-text-main font-sans selection:bg-blue-500/30">
            {/* Background Gradient */}
            <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_top_right,_rgba(37,99,235,0.15),_transparent_px)] pointer-events-none" />
            <div className="fixed inset-0 -z-10 bg-[radial-gradient(circle_at_bottom_left,_rgba(56,189,248,0.1),_transparent_px)] pointer-events-none" />

            {/* Header */}
            <header className="w-full max-w-5xl p-6 flex justify-between items-center sticky top-0 z-20 bg-bg-dark/80 backdrop-blur-md">
                <div className="flex items-center gap-3 group cursor-default">
                    <div className="bg-gradient-to-br from-blue-600 to-accent rounded-xl shadow-lg shadow-blue-500/20 group-hover:scale-105 transition-transform overflow-hidden">
                        {config?.logo ? (
                            <img src={config.logo} alt="brand logo" className="w-10 h-10 object-cover" />
                        ) : (
                            <div className="p-2">
                                <Sparkles className="text-white" size={24} />
                            </div>
                        )}
                    </div>
                    <h1 className="text-2xl tracking-tighter font-outfit">
                        Tally Expert {config?.name ? (
                            <span className="text-blue-200">({config.name})</span>
                        ) : subdomain ? (
                            <>({subdomain}) <span className="text-blue-400">AI</span></>
                        ) : (
                            <span className="text-blue-400">AI</span>
                        )}
                    </h1>
                </div>
                <button
                    onClick={() => window.location.reload()}
                    className="flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-full bg-white/5 hover:bg-white/10 border border-white/10 transition-all text-text-muted hover:text-white"
                >
                    <RefreshCw size={14} /> RELOAD APP
                </button>
            </header>

            {/* Main Chat Area */}
            <main className="flex-1 w-full max-w-4xl px-4 pb-32">
                <div className="space-y-8 pt-8">
                    {messages.map((msg, i) => (
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.4, ease: "easeOut" }}
                            key={i}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div className={`max-w-[90%] md:max-w-[80%] rounded-3xl p-6 glass-panel relative group ${msg.role === 'user' ? 'bg-blue-600/10 border-blue-500/20' : ''
                                }`}>
                                {/* Avatar/Label */}
                                <div className="flex items-center gap-2 mb-4">
                                    <div className={`p-1.5 rounded-lg ${msg.role === 'user' ? 'bg-blue-500' : 'bg-accent/20'}`}>
                                        {msg.role === 'user' ? <User size={14} className="text-white" /> : <Bot size={14} className="text-accent" />}
                                    </div>
                                    <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-text-muted">
                                        {msg.role === 'user' ? 'YOU' : 'AI ASSISTANT'}
                                    </span>
                                </div>

                                {/* Content */}
                                <div className="markdown-content text-base md:text-lg leading-relaxed text-white/90">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>

                                {/* Sources Section */}
                                {msg.sources && msg.sources.length > 0 && (
                                    <div className="mt-8 pt-6 border-t border-white/10">
                                        <div className="flex items-center gap-2 mb-4">
                                            <LinkIcon size={14} className="text-accent" />
                                            <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-blue-400">Documentation Sources</span>
                                        </div>
                                        <div className="grid grid-cols-1 gap-3">
                                            {msg.sources.filter(s => !s.source.toLowerCase().endsWith('.pdf')).map((s, idx) => {
                                                const citationId = idx + 1;

                                                return (
                                                    <div
                                                        key={idx}
                                                        className={`flex flex-col gap-1 p-3 rounded-2xl border border-white/5 bg-white/5 hover:bg-white/10 transition-colors ${msg.content.includes(`[Source ${citationId}]`) ? 'ring-1 ring-blue-500/50 bg-blue-500/5' : 'opacity-70'
                                                            }`}
                                                    >
                                                        <div className="flex items-center justify-between">
                                                            <span className="text-[9px] font-bold px-2 py-0.5 rounded bg-blue-600/30 text-blue-300 uppercase">
                                                                Source {citationId}
                                                            </span>
                                                        </div>

                                                        <div className="text-xs font-semibold text-white/80 mt-1">
                                                            📄 {s.title}
                                                        </div>
                                                        <a
                                                            href={s.source}
                                                            target="_blank"
                                                            rel="noreferrer"
                                                            className="text-[10px] font-medium text-blue-400 hover:text-blue-300 mt-1 break-all flex items-center gap-1 group/link"
                                                        >
                                                            🌐 {s.source}
                                                            <ChevronDown size={12} className="-rotate-90 opacity-0 group-hover/link:opacity-100 transition-opacity" />
                                                        </a>
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </motion.div>
                    ))}

                    <AnimatePresence>
                        {loading && (
                            <motion.div
                                initial={{ opacity: 0, scale: 0.95 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0 }}
                                className="flex justify-start"
                            >
                                <div className="glass-panel p-6 flex items-center gap-4 border-blue-500/20">
                                    <div className="relative">
                                        <Loader2 className="animate-spin text-accent" size={20} />
                                        <div className="absolute inset-0 blur-sm animate-pulse bg-accent/20 rounded-full" />
                                    </div>
                                    <span className="text-xs font-semibold text-text-muted italic tracking-wide">
                                        Deep searching Tally documentation...
                                    </span>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                    <div ref={messagesEndRef} className="h-4" />
                </div>
            </main>

            {/* Floating Input Area */}
            <div className="fixed bottom-0 w-full max-w-4xl px-4 pb-8 pt-4 bg-gradient-to-t from-bg-dark via-bg-dark/95 to-transparent z-10">
                <form onSubmit={handleSend} className="relative group">
                    {/* Subtle Glow Effect */}
                    <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600/20 to-accent/20 rounded-2xl blur opacity-0 group-focus-within:opacity-100 transition duration-500" />

                    <div className="relative flex items-center bg-[#1a2235]/80 backdrop-blur-xl rounded-2xl p-2 border border-white/10 group-focus-within:border-blue-500/50 transition-all shadow-2xl">
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder="How do I record RCM sales in TallyPrime?"
                            className="flex-1 bg-transparent border-none px-6 py-4 text-white outline-none placeholder:text-text-muted text-base md:text-lg"
                        />
                        <button
                            type="submit"
                            disabled={loading || !input.trim()}
                            className="bg-blue-600 hover:bg-blue-500 disabled:opacity-30 disabled:hover:bg-blue-600 p-4 rounded-xl transition-all shadow-lg active:scale-95 group/btn"
                        >
                            <Send size={20} className="text-white group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
                        </button>
                    </div>
                </form>

                <div className="flex justify-between items-center mt-4 px-2">
                    <p className="text-[10px] uppercase tracking-[0.2em] text-white/20 font-bold">
                        Apps Technologies AI
                    </p>
                    <div className="flex gap-4">
                        <span className="text-[10px] text-white/20 hover:text-white/40 cursor-default transition-colors">Privacy</span>
                        <span className="text-[10px] text-white/20 hover:text-white/40 cursor-default transition-colors">Documentation</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
