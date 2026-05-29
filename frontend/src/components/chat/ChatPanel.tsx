import { useEffect, useRef, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { Send } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { Button } from '@/components/ui/Button';
import { chatApi, type ChatArtifacts } from '@/features/chat/chatApi';
import { QUICK_PROMPTS } from '@/lib/constants';

interface Msg {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  source?: 'llm' | 'fallback';
  artifacts?: ChatArtifacts;
}

export function ChatPanel() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        'Hi! I can answer questions about your students, attendance, risk distribution, and more — using only your local data. Try one of the quick prompts below or ask anything.',
    },
  ]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages]);

  const send = useMutation({
    mutationFn: (message: string) => chatApi.query({ message }),
    onSuccess: (res, message) => {
      setMessages((prev) => [
        ...prev,
        { id: `u-${Date.now()}`, role: 'user', content: message },
        { id: `a-${Date.now()}`, role: 'assistant', content: res.answer, source: res.source, artifacts: res.artifacts },
      ]);
      setInput('');
    },
    onError: (_err, message) => {
      setMessages((prev) => [
        ...prev,
        { id: `u-${Date.now()}`, role: 'user', content: message },
        { id: `a-${Date.now()}`, role: 'assistant', content: 'Sorry, I could not reach the assistant. Please try again.' },
      ]);
    },
  });

  function submit(e?: React.FormEvent) {
    e?.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || send.isPending) return;
    send.mutate(trimmed);
  }

  return (
    <div className="flex h-full flex-col rounded-xl border bg-surface">
      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4 scrollbar-thin">
        {messages.map((m) => (
          <ChatMessage key={m.id} role={m.role} content={m.content} source={m.source} artifacts={m.artifacts} />
        ))}
        {send.isPending && (
          <ChatMessage role="assistant" content="…" />
        )}
      </div>
      <div className="border-t p-3 space-y-2">
        <div className="flex flex-wrap gap-2">
          {QUICK_PROMPTS.map((p) => (
            <button
              key={p}
              onClick={() => setInput(p)}
              className="rounded-full border bg-surface-subtle px-3 py-1 text-xs text-ink-muted hover:bg-surface-inset hover:text-ink"
            >
              {p}
            </button>
          ))}
        </div>
        <form onSubmit={submit} className="flex items-center gap-2">
          <input
            className="input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your students…"
            disabled={send.isPending}
          />
          <Button type="submit" loading={send.isPending} icon={<Send className="h-4 w-4" />}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
}
