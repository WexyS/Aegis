"use client";

import React, { useRef, useEffect, useCallback } from 'react';
import { useChatStore } from '@/store/useChatStore';
import { useRuntimeStore } from '@/store/useRuntimeStore';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, User, Zap, Terminal } from 'lucide-react';
import { sendCommand } from '@/lib/socket';

export const ChatPanel = () => {
  const messages = useChatStore((state) => state.messages);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="flex-1 flex flex-col min-w-0 bg-transparent relative h-full">
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-5 lg:p-6 space-y-5 custom-scrollbar">
        <AnimatePresence initial={false}>
          {messages.map((msg) => (
            <ChatMessage key={msg.id} msg={msg} />
          ))}
          {isStreaming && <StreamingIndicator />}
        </AnimatePresence>
      </div>

      <ChatInput />
    </div>
  );
};

const ChatMessage = React.memo(({ msg }: { msg: any }) => (
  <motion.div
    initial={{ opacity: 0, y: 15 }}
    animate={{ opacity: 1, y: 0 }}
    className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
  >
    <div className={`w-8 h-8 rounded-md flex items-center justify-center shrink-0 relative ${msg.role === 'user' ? 'bg-secondary/10 border border-secondary/25' : 'bg-accent/10 border border-accent/25'}`}>
      {msg.role === 'user' ? <User size={16} className="text-secondary-light" /> : <Zap size={16} className="text-accent fill-current" />}
    </div>
    
    <div className={`flex-1 max-w-[85%] space-y-2 flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
      <div className={`p-4 rounded-lg ${msg.role === 'user' ? 'bg-secondary/10 border border-secondary/20 rounded-tr-sm' : 'bg-white/[0.03] border border-white/10 rounded-tl-sm'}`}>
        <p className="text-[13px] leading-relaxed text-foreground/90 whitespace-pre-wrap selection:bg-accent/30 font-medium">
          {msg.content}
        </p>
      </div>
      <span className="text-[10px] font-mono text-foreground/30 px-2 uppercase tracking-widest">{msg.timestamp}</span>
    </div>
  </motion.div>
));

const ChatInput = () => {
  const [input, setInput] = React.useState("");
  const [mode, setMode] = React.useState<'auto' | 'raw'>('auto');
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const addMessage = useChatStore((state) => state.addMessage);
  const connectionState = useRuntimeStore((state) => state.connectionState ?? 'disconnected');
  const canSend = connectionState === 'connected';

  const handleInput = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 180)}px`;
    }
  }, []);

  const submit = useCallback(() => {
    if (!input.trim() || !canSend) return;
    const text = input.trim();
    addMessage({ role: 'user', content: text });
    sendCommand(text, mode); // Wire to real backend with mode
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }, [input, addMessage, mode, canSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="p-5 lg:p-6 pt-0 mt-auto">
      <div className="relative group glass-panel rounded-lg p-2 transition-colors focus-within:border-accent/50 bg-surface-secondary/80">
        <textarea 
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={canSend ? (mode === 'auto' ? "Command Aegis Runtime..." : "Execute raw command...") : "Backend socket unavailable..."}
          disabled={!canSend}
          className="w-full bg-transparent border-none rounded-md p-4 pr-16 text-[13px] font-medium placeholder:text-foreground/30 focus:outline-none transition-all resize-none min-h-[58px] max-h-[180px] custom-scrollbar disabled:cursor-not-allowed disabled:opacity-60"
          rows={1}
        />
        <div className="absolute right-4 bottom-4 flex items-center gap-3">
          <button 
            type="button"
            aria-label="Send command"
            onClick={submit}
            disabled={!input.trim() || !canSend}
            className="p-2.5 rounded-md bg-accent text-background hover:bg-accent-light active:translate-y-px transition-all flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed">
            <Send size={16} className="translate-x-[1px] translate-y-[-1px]" />
          </button>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between gap-4 px-1">
        <div className="flex gap-5">
          <QuickAction 
            icon={<Terminal size={14}/>} 
            label="Raw Execute" 
            active={mode === 'raw'} 
            onClick={() => setMode('raw')}
          />
          <QuickAction 
            icon={<Zap size={14}/>} 
            label="Auto Mode" 
            active={mode === 'auto'} 
            onClick={() => setMode('auto')}
          />
        </div>
        <span className="text-[10px] font-mono uppercase tracking-widest text-foreground/35">socket {connectionState}</span>
      </div>
    </div>
  );
};

const QuickAction = ({ icon, label, active, onClick }: any) => (
  <button 
    onClick={onClick}
    className={`flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest transition-colors ${active ? 'text-accent' : 'text-foreground/40 hover:text-accent-light'}`}>
    {icon} {label}
  </button>
);

const StreamingIndicator = () => (
  <motion.div 
    initial={{ opacity: 0 }} 
    animate={{ opacity: 1 }} 
    className="flex gap-6 items-center"
  >
    <div className="w-8 h-8 rounded-md bg-accent/10 border border-accent/30 flex items-center justify-center relative">
      <div className="w-2 h-2 rounded-full bg-accent" />
    </div>
    <span className="text-[11px] font-bold uppercase tracking-[0.18em] text-accent">Aegis Thinking...</span>
  </motion.div>
);
