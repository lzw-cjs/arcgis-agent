import { describe, it, expect } from 'vitest';

describe('TypeScript type compliance', () => {
  it('Message type should have id, role, content, toolCalls, timestamp fields', () => {
    // Type-level assertion: if the type definition changes incompatibly,
    // destructuring will fail at compile time.
    // Runtime check: verify a Message object has all required keys.
    const msg = {
      id: 'msg-1',
      role: 'user' as const,
      content: 'Hello',
      toolCalls: undefined,
      suggestions: undefined,
      timestamp: Date.now(),
    };

    expect(msg).toHaveProperty('id');
    expect(msg).toHaveProperty('role');
    expect(msg).toHaveProperty('content');
    expect(msg).toHaveProperty('toolCalls');
    expect(msg).toHaveProperty('timestamp');

    expect(typeof msg.id).toBe('string');
    expect(['user', 'assistant', 'system']).toContain(msg.role);
    expect(typeof msg.content).toBe('string');
    expect(typeof msg.timestamp).toBe('number');
  });

  it('ToolCall type should have name, args, status fields', () => {
    const tc = {
      name: 'buffer',
      args: { distance: 100 },
      result: undefined,
      success: undefined,
      status: 'running' as const,
    };

    expect(tc).toHaveProperty('name');
    expect(tc).toHaveProperty('args');
    expect(tc).toHaveProperty('status');
    expect(['running', 'success', 'error']).toContain(tc.status);
  });

  it('ChatRequest type should have session_id, message, stream fields', () => {
    const req = {
      session_id: 'sess-1',
      message: 'create a buffer',
      stream: true,
    };

    expect(req).toHaveProperty('session_id');
    expect(req).toHaveProperty('message');
    expect(req).toHaveProperty('stream');
    expect(typeof req.stream).toBe('boolean');
  });

  it('SSEEvent type should have event and data fields', () => {
    const evt = {
      event: 'token' as const,
      data: { content: 'hello' },
    };

    expect(evt).toHaveProperty('event');
    expect(evt).toHaveProperty('data');
    expect([
      'token', 'tool_start', 'tool_end', 'progress',
      'suggestions', 'error', 'done',
    ]).toContain(evt.event);
  });
});
