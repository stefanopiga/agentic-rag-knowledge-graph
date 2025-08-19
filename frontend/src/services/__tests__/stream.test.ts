import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { startChatStream } from '../stream';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock TextDecoder
class MockTextDecoder {
  decode(chunk: Uint8Array, options?: { stream?: boolean }): string {
    // Simple mock: convert Uint8Array to string
    return new TextDecoder().decode(chunk, options);
  }
}

// Mock ReadableStream and Reader
class MockReader {
  private chunks: string[];
  private index: number = 0;

  constructor(chunks: string[]) {
    this.chunks = chunks;
  }

  async read(): Promise<{ done: boolean; value?: Uint8Array }> {
    if (this.index >= this.chunks.length) {
      return { done: true };
    }
    
    const chunk = this.chunks[this.index++];
    return {
      done: false,
      value: new TextEncoder().encode(chunk)
    };
  }
}

describe('SSE Stream Service', () => {
  let mockHandlers: any;

  beforeEach(() => {
    vi.clearAllMocks();
    mockHandlers = {
      onSession: vi.fn(),
      onText: vi.fn(),
      onTools: vi.fn(),
      onEnd: vi.fn(),
      onError: vi.fn(),
    };
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should handle successful SSE stream with text chunks', async () => {
    // Mock SSE response chunks
    const chunks = [
      'data: {"type":"session","session_id":"test-session-123"}\n\n',
      'data: {"type":"text","content":"Hello "}\n\n',
      'data: {"type":"text","content":"World!"}\n\n',
      'data: {"type":"end"}\n\n'
    ];

    const mockReader = new MockReader(chunks);
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse);

    await startChatStream(
      {
        message: 'Test message',
        tenant_id: 'test-tenant',
      },
      mockHandlers
    );

    // Verify handlers were called correctly
    expect(mockHandlers.onSession).toHaveBeenCalledWith('test-session-123');
    expect(mockHandlers.onText).toHaveBeenCalledWith('Hello ');
    expect(mockHandlers.onText).toHaveBeenCalledWith('World!');
    expect(mockHandlers.onEnd).toHaveBeenCalled();
    expect(mockHandlers.onError).not.toHaveBeenCalled();
  });

  it('should handle SSE stream with tools', async () => {
    const chunks = [
      'data: {"type":"session","session_id":"test-session"}\n\n',
      'data: {"type":"tools","tools":[{"name":"search","args":{"query":"test"}}]}\n\n',
      'data: {"type":"end"}\n\n'
    ];

    const mockReader = new MockReader(chunks);
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse);

    await startChatStream(
      {
        message: 'Test with tools',
        tenant_id: 'test-tenant',
      },
      mockHandlers
    );

    expect(mockHandlers.onTools).toHaveBeenCalledWith([
      { name: 'search', args: { query: 'test' } }
    ]);
  });

  it('should handle stream errors gracefully', async () => {
    const chunks = [
      'data: {"type":"session","session_id":"test-session"}\n\n',
      'data: {"type":"error","content":"Something went wrong"}\n\n'
    ];

    const mockReader = new MockReader(chunks);
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse);

    await startChatStream(
      {
        message: 'Test error',
        tenant_id: 'test-tenant',
      },
      mockHandlers
    );

    expect(mockHandlers.onError).toHaveBeenCalledWith('Something went wrong');
  });

  it('should handle HTTP errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      body: null
    });

    await startChatStream(
      {
        message: 'Test HTTP error',
        tenant_id: 'test-tenant',
      },
      mockHandlers
    );

    expect(mockHandlers.onError).toHaveBeenCalledWith('HTTP 500');
  });

  it('should handle invalid JSON in stream', async () => {
    const chunks = [
      'data: {"type":"session","session_id":"test-session"}\n\n',
      'data: invalid-json\n\n'
    ];

    const mockReader = new MockReader(chunks);
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse);

    await startChatStream(
      {
        message: 'Test invalid JSON',
        tenant_id: 'test-tenant',
      },
      mockHandlers
    );

    expect(mockHandlers.onError).toHaveBeenCalledWith('invalid JSON event');
  });

  it('should respect abort controller', async () => {
    const abortController = new AbortController();
    
    // Mock a slow stream
    const mockReader = {
      read: vi.fn().mockImplementation(() => {
        return new Promise((resolve) => {
          setTimeout(() => {
            resolve({ done: true });
          }, 1000);
        });
      })
    };

    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse);

    // Start streaming and abort immediately
    const streamPromise = startChatStream(
      {
        message: 'Test abort',
        tenant_id: 'test-tenant',
      },
      mockHandlers,
      abortController
    );

    abortController.abort();

    // The fetch should have been called with the abort signal
    expect(mockFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        signal: abortController.signal
      })
    );
  });

  it('should handle partial SSE messages across chunks', async () => {
    // Test chunked data that spans multiple reads
    const chunks = [
      'data: {"type":"session","sess',
      'ion_id":"test-session"}\n\ndata: {"type":"text",',
      '"content":"Split message"}\n\n'
    ];

    const mockReader = new MockReader(chunks);
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse);

    await startChatStream(
      {
        message: 'Test split message',
        tenant_id: 'test-tenant',
      },
      mockHandlers
    );

    expect(mockHandlers.onSession).toHaveBeenCalledWith('test-session');
    expect(mockHandlers.onText).toHaveBeenCalledWith('Split message');
  });

  it('should send correct request payload', async () => {
    const mockReader = new MockReader(['data: {"type":"end"}\n\n']);
    const mockResponse = {
      ok: true,
      body: {
        getReader: () => mockReader
      }
    };

    mockFetch.mockResolvedValueOnce(mockResponse);

    const payload = {
      message: 'Hello World',
      session_id: 'existing-session',
      tenant_id: 'test-tenant-123',
      user_id: 'user-456'
    };

    await startChatStream(payload, mockHandlers);

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining('/chat/stream'),
      expect.objectContaining({
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
        signal: expect.any(AbortSignal)
      })
    );
  });
});
