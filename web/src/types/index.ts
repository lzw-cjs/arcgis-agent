export interface ToolCall {
  name: string;
  args: Record<string, unknown>;
  result?: string;
  success?: boolean;
  status: 'running' | 'success' | 'error';
}

export interface ToolCallEvent {
  event: 'tool_start' | 'tool_end';
  data: {
    name: string;
    args?: Record<string, unknown>;
    success?: boolean;
    result?: string;
  };
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  toolCalls?: ToolCall[];
  suggestions?: string[];
  timestamp: number;
}

export interface ChatRequest {
  session_id: string;
  message: string;
  stream: boolean;
}

export interface SSEEvent {
  event: 'token' | 'tool_start' | 'tool_end' | 'progress' | 'suggestions' | 'error' | 'done';
  data: Record<string, unknown>;
}

export interface ChatState {
  messages: Message[];
  sessionId: string;
  loading: boolean;
  mapPanelOpen: boolean;
  error: string | null;
  addMessage: (msg: Message) => void;
  appendContent: (content: string) => void;
  setLoading: (v: boolean) => void;
  toggleMapPanel: () => void;
  setError: (err: string | null) => void;
  clearMessages: () => void;
  updateLastToolCall: (call: Partial<ToolCall>) => void;
  addToolCallToLastMessage: (call: ToolCall) => void;
  setSuggestions: (suggestions: string[]) => void;
}
