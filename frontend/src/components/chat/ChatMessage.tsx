import { Bot, User } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  source?: 'llm' | 'fallback';
}

export function ChatMessage({ role, content, source }: ChatMessageProps) {
  const isUser = role === 'user';
  return (
    <div className={cn('flex gap-3', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser && (
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-primary-500/15 text-primary-600">
          <Bot className="h-4 w-4" />
        </div>
      )}
      <div
        className={cn(
          'max-w-[78%] rounded-2xl px-4 py-2.5 text-sm whitespace-pre-wrap break-words',
          isUser ? 'bg-primary-600 text-white' : 'bg-surface-subtle text-ink',
        )}
      >
        {content}
        {source && !isUser && (
          <div className="mt-1.5 text-[10px] uppercase tracking-wide text-ink-muted">
            {source === 'fallback' ? 'offline mode' : 'local LLM'}
          </div>
        )}
      </div>
      {isUser && (
        <div className="grid h-8 w-8 shrink-0 place-items-center rounded-full bg-surface-subtle text-ink">
          <User className="h-4 w-4" />
        </div>
      )}
    </div>
  );
}
