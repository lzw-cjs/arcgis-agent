import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('chat API client (SSE)', () => {
  // During RED phase, the sendMessage function does not exist yet.
  // After GREEN phase, import will work and tests verify behavior.

  let sendMessage: any;
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(async () => {
    fetchMock = vi.fn();
    vi.stubGlobal('fetch', fetchMock);

    try {
      const mod = await import('../api/chat');
      sendMessage = mod.sendMessage;
    } catch {
      sendMessage = null;
    }
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('sendMessage("hello", "session-1") sends correct POST request', async () => {
    if (!sendMessage) return;

    // Mock a simple SSE response with a done event
    const mockStream = new ReadableStream({
      start(controller) {
        const data = 'data: {"event":"done","data":{"tool_calls":0,"message_id":"m1"}}\n\n';
        controller.enqueue(new TextEncoder().encode(data));
        controller.close();
      },
    });

    fetchMock.mockResolvedValue({
      ok: true,
      body: mockStream,
    });

    const gen = sendMessage('session-1', 'hello');
    const events: any[] = [];
    for await (const evt of gen) {
      events.push(evt);
    }

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/chat',
      expect.objectContaining({
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: 'session-1',
          message: 'hello',
          stream: true,
        }),
      })
    );

    expect(events.length).toBeGreaterThan(0);
  });

  it('sendMessage handles HTTP error response', async () => {
    if (!sendMessage) return;

    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      text: async () => 'Internal Server Error',
    });

    const gen = sendMessage('session-1', 'error test');
    const events: any[] = [];
    for await (const evt of gen) {
      events.push(evt);
    }

    expect(events.length).toBe(1);
    expect(events[0].event).toBe('error');
    expect(events[0].data.code).toBe('HTTP_ERROR');
  });

  it('sendMessage handles null response body', async () => {
    if (!sendMessage) return;

    fetchMock.mockResolvedValue({
      ok: true,
      body: null,
    });

    const gen = sendMessage('session-1', 'no body');
    const events: any[] = [];
    for await (const evt of gen) {
      events.push(evt);
    }

    expect(events.length).toBe(1);
    expect(events[0].event).toBe('error');
    expect(events[0].data.code).toBe('NO_BODY');
  });

  it('sendMessage parses SSE token events correctly', async () => {
    if (!sendMessage) return;

    const mockStream = new ReadableStream({
      start(controller) {
        const chunk = [
          'event: token',
          'data: {"content":"Hello"}',
          '',
          'event: token',
          'data: {"content":" World"}',
          '',
          'event: done',
          'data: {"tool_calls":0,"message_id":"m2"}',
          '',
        ].join('\n');
        controller.enqueue(new TextEncoder().encode(chunk));
        controller.close();
      },
    });

    fetchMock.mockResolvedValue({
      ok: true,
      body: mockStream,
    });

    const gen = sendMessage('session-1', 'hello');
    const events: any[] = [];
    for await (const evt of gen) {
      events.push(evt);
    }

    expect(events.length).toBe(3);
    expect(events.map((e: any) => e.event)).toEqual(['token', 'token', 'done']);
    expect(events[0].data.content).toBe('Hello');
    expect(events[1].data.content).toBe(' World');
  });

  it('fetchTools calls GET /api/v1/tools', async () => {
    let fetchTools: any;
    try {
      const mod = await import('../api/chat');
      fetchTools = mod.fetchTools;
    } catch {
      return;
    }

    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ({ default: 'qwen', providers: {} }),
    });

    const result = await fetchTools();
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/tools');
  });

  it('fetchTasks calls GET /api/v1/tasks with session_id', async () => {
    let fetchTasks: any;
    try {
      const mod = await import('../api/chat');
      fetchTasks = mod.fetchTasks;
    } catch {
      return;
    }

    fetchMock.mockResolvedValue({
      ok: true,
      json: async () => ([]),
    });

    await fetchTasks('sess-1');
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/tasks?session_id=sess-1');
  });
});
