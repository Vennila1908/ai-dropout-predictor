import { useQuery } from '@tanstack/react-query';
import { ChatPanel } from '@/components/chat/ChatPanel';
import { Card, CardBody, CardHeader } from '@/components/ui/Card';
import { api, unwrap } from '@/lib/api';

interface LlmHealth { ok: boolean; model: string; base_url: string; models?: string[]; error?: string }

export function ChatPage() {
  const { data: llm } = useQuery({
    queryKey: ['health', 'llm'],
    queryFn: () => unwrap(api.get<LlmHealth>('/health/llm')),
  });

  return (
    <div className="grid h-[calc(100vh-7rem)] grid-cols-1 gap-4 lg:grid-cols-[1fr,280px]">
      <ChatPanel />
      <div className="space-y-4">
        <Card>
          <CardHeader title="Local LLM" subtitle="Ollama status." />
          <CardBody className="space-y-2 text-sm">
            <p>
              Status:{' '}
              <span className={llm?.ok ? 'text-risk-low' : 'text-risk-medium'}>
                {llm?.ok ? 'connected' : 'offline (using fallback)'}
              </span>
            </p>
            {llm && (
              <>
                <p className="text-xs text-ink-muted">model: {llm.model}</p>
                <p className="text-xs text-ink-muted break-all">url: {llm.base_url}</p>
                {llm.models && llm.models.length > 0 && (
                  <p className="text-xs text-ink-muted">installed: {llm.models.join(', ')}</p>
                )}
              </>
            )}
            {!llm?.ok && (
              <p className="text-xs text-ink-muted">
                Install Ollama and run <code>ollama pull phi3</code> to enable AI answers.
              </p>
            )}
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Privacy" subtitle="Your data never leaves the server." />
          <CardBody className="text-sm text-ink-muted">
            All prompts are constructed from your own database and sent to a local Ollama daemon. No external API calls
            are made.
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
