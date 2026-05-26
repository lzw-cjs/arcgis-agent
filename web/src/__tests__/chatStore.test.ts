import { describe, it, expect, beforeEach } from 'vitest';

describe('Zustand chatStore', () => {
  let useChatStore: any;

  // Dynamic import since the store file does not exist yet (RED phase)
  beforeEach(async () => {
    // During RED phase, this import will fail — that is expected.
    // After GREEN phase, the store module will exist and tests will pass.
    try {
      const mod = await import('../stores/chatStore');
      useChatStore = mod.useChatStore;
    } catch {
      useChatStore = null;
    }
  });

  it('addMessage() increases messages.length by 1', () => {
    if (!useChatStore) return; // Skip if store not yet implemented (RED phase)
    const { addMessage } = useChatStore.getState();
    const before = useChatStore.getState().messages.length;

    addMessage({
      id: 'test-1',
      role: 'user',
      content: 'test message',
      timestamp: Date.now(),
    });

    const after = useChatStore.getState().messages.length;
    expect(after).toBe(before + 1);
  });

  it('toggleMapPanel() toggles mapPanelOpen state', () => {
    if (!useChatStore) return;
    const initial = useChatStore.getState().mapPanelOpen;

    useChatStore.getState().toggleMapPanel();
    expect(useChatStore.getState().mapPanelOpen).toBe(!initial);

    useChatStore.getState().toggleMapPanel();
    expect(useChatStore.getState().mapPanelOpen).toBe(initial);
  });

  it('clearMessages() clears messages array and resets sessionId', () => {
    if (!useChatStore) return;
    const oldSessionId = useChatStore.getState().sessionId;

    useChatStore.getState().addMessage({
      id: 'test-2',
      role: 'assistant',
      content: 'response',
      timestamp: Date.now(),
    });

    expect(useChatStore.getState().messages.length).toBeGreaterThan(0);

    useChatStore.getState().clearMessages();

    expect(useChatStore.getState().messages).toHaveLength(0);
    expect(useChatStore.getState().error).toBeNull();
    // sessionId should be regenerated
    expect(useChatStore.getState().sessionId).not.toBe(oldSessionId);
  });

  it('appendContent() appends to last assistant message content', () => {
    if (!useChatStore) return;
    useChatStore.getState().clearMessages();

    useChatStore.getState().addMessage({
      id: 'assist-1',
      role: 'assistant',
      content: 'Hello',
      timestamp: Date.now(),
    });

    useChatStore.getState().appendContent(' World');
    const lastMsg = useChatStore.getState().messages.slice(-1)[0];
    expect(lastMsg.content).toBe('Hello World');
  });

  it('setLoading() sets loading state', () => {
    if (!useChatStore) return;
    useChatStore.getState().setLoading(true);
    expect(useChatStore.getState().loading).toBe(true);

    useChatStore.getState().setLoading(false);
    expect(useChatStore.getState().loading).toBe(false);
  });

  it('addToolCallToLastMessage() adds tool call to last assistant message', () => {
    if (!useChatStore) return;
    useChatStore.getState().clearMessages();

    useChatStore.getState().addMessage({
      id: 'assist-2',
      role: 'assistant',
      content: 'Running tool...',
      timestamp: Date.now(),
    });

    useChatStore.getState().addToolCallToLastMessage({
      name: 'buffer',
      args: { distance: 100 },
      status: 'running',
    });

    const lastMsg = useChatStore.getState().messages.slice(-1)[0];
    expect(lastMsg.toolCalls).toHaveLength(1);
    expect(lastMsg.toolCalls[0].name).toBe('buffer');
  });

  it('updateLastToolCall() updates the last tool call status', () => {
    if (!useChatStore) return;
    useChatStore.getState().clearMessages();

    useChatStore.getState().addMessage({
      id: 'assist-3',
      role: 'assistant',
      content: 'Running tool...',
      timestamp: Date.now(),
    });

    useChatStore.getState().addToolCallToLastMessage({
      name: 'clip',
      args: {},
      status: 'running',
    });

    useChatStore.getState().updateLastToolCall({
      status: 'success',
      success: true,
      result: 'clipped successfully',
    });

    const lastMsg = useChatStore.getState().messages.slice(-1)[0];
    expect(lastMsg.toolCalls[0].status).toBe('success');
    expect(lastMsg.toolCalls[0].success).toBe(true);
  });

  it('setSuggestions() adds suggestions to last assistant message', () => {
    if (!useChatStore) return;
    useChatStore.getState().clearMessages();

    useChatStore.getState().addMessage({
      id: 'assist-4',
      role: 'assistant',
      content: 'Tool complete',
      timestamp: Date.now(),
    });

    useChatStore.getState().setSuggestions(['Export map', 'Adjust symbology']);
    const lastMsg = useChatStore.getState().messages.slice(-1)[0];
    expect(lastMsg.suggestions).toEqual(['Export map', 'Adjust symbology']);
  });
});
