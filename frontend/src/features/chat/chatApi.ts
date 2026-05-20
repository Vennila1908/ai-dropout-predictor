import { api, unwrap } from '@/lib/api';

export interface ChatQuery {
  message: string;
  context_filters?: Record<string, unknown>;
  stream?: boolean;
}

export interface ChatResponse {
  answer: string;
  source: 'llm' | 'fallback';
}

export const chatApi = {
  query: (payload: ChatQuery) => unwrap(api.post<ChatResponse>('/chat/query', payload)),
};
