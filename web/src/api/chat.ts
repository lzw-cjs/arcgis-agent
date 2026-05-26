import type { SSEEvent } from '../types';

const API_BASE = '/api/v1';

/**
 * Send a chat message and yield SSE events from the response stream.
 *
 * Uses the sse-starlette wire format:
 *   event: <type>
 *   data: <json>
 *   (empty line)
 *
 * Returns an async generator of SSEEvent objects.
 */
export async function* sendMessage(
  sessionId: string,
  message: string
): AsyncGenerator<SSEEvent> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      stream: true,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    yield {
      event: 'error',
      data: { code: 'HTTP_ERROR', message: errorText },
    };
    return;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    yield { event: 'error', data: { code: 'NO_BODY', message: 'No response body' } };
    return;
  }

  const decoder = new TextDecoder();
  let buffer = '';

  // SSE parser state: accumulate lines until an empty line (event boundary)
  let currentEvent = '';
  let currentData = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    // Keep the last (potentially incomplete) line in buffer
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line === '') {
        // Empty line = end of SSE event
        if (currentData) {
          try {
            const data = JSON.parse(currentData);
            yield { event: currentEvent || 'message', data } as SSEEvent;
          } catch {
            // Skip unparseable data payloads
          }
        }
        currentEvent = '';
        currentData = '';
      } else if (line.startsWith('event:')) {
        currentEvent = line.slice(6).trim();
      } else if (line.startsWith('data:')) {
        currentData = line.slice(5).trim();
      }
    }
  }

  // Flush any remaining buffered event at stream end
  if (currentData) {
    try {
      const data = JSON.parse(currentData);
      yield { event: currentEvent || 'message', data } as SSEEvent;
    } catch {
      // Skip
    }
  }
}

export async function fetchTools() {
  const res = await fetch(`${API_BASE}/tools`);
  return res.json();
}

export async function fetchTasks(sessionId: string) {
  const res = await fetch(`${API_BASE}/tasks?session_id=${sessionId}`);
  return res.json();
}

export async function clearSession(sessionId: string) {
  const res = await fetch(`${API_BASE}/chat/${sessionId}`, { method: 'DELETE' });
  return res.json();
}
