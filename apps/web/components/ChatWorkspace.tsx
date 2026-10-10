'use client';

import React, { useState } from 'react';
import { sendQuery } from '../lib/api';
import { QueryResponse } from '../lib/types';

interface Message {
  role: 'user' | 'assistant';
  content?: string;
  thoughts?: string;
  retrieved_docs?: QueryResponse['retrieved_docs'];
}

export default function ChatWorkspace() {
  const [query, setQuery] = useState<string>('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim() || loading) return;

    const userText = query;
    setQuery('');
    setMessages((prev) => [...prev, { role: 'user', content: userText }]);
    setLoading(true);

    try {
      const res = await sendQuery(userText);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.answer,
          thoughts: res.thoughts,
          retrieved_docs: res.retrieved_docs,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error connecting to backend API.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ flex: 1, padding: '15px', display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <h2>RAG Workspace</h2>

      {/* Message History */}
      <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '15px' }}>
        {messages.length === 0 && <p style={{ color: '#888' }}>No queries sent yet.</p>}

        {messages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: '15px' }}>
            <b>{msg.role === 'user' ? 'User:' : 'Assistant:'}</b>

            {/* DeepSeek Reasoning Log (<think>) */}
            {msg.role === 'assistant' && msg.thoughts && (
              <details style={{ margin: '5px 0', padding: '5px', background: '#f9f9f9', border: '1px solid #ddd' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 'bold' }}>Reasoning Process (&lt;think&gt;)</summary>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px', margin: '5px 0' }}>{msg.thoughts}</pre>
              </details>
            )}

            <p style={{ margin: '5px 0', whiteSpace: 'pre-wrap' }}>{msg.content}</p>

            {/* Retrieved Source Context & Distance Scores */}
            {msg.role === 'assistant' && msg.retrieved_docs && msg.retrieved_docs.length > 0 && (
              <details style={{ margin: '5px 0', padding: '5px', background: '#f0f4f8', border: '1px solid #cbd5e1' }}>
                <summary style={{ cursor: 'pointer', fontSize: '13px' }}>
                  Retrieved Context ({msg.retrieved_docs.length} chunks)
                </summary>
                <div style={{ marginTop: '5px' }}>
                  {msg.retrieved_docs.map((doc, dIdx) => (
                    <div key={dIdx} style={{ padding: '5px', borderBottom: '1px solid #ddd', fontSize: '12px' }}>
                      <div><b>Source:</b> {doc.metadata.source || 'N/A'} | <b>Distance:</b> {doc.distance}</div>
                      <div>{doc.content}</div>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        ))}

        {loading && <p><i>Searching context & generating response...</i></p>}
      </div>

      {/* Simple Query Input Form */}
      <form onSubmit={handleSend} style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          style={{ flex: 1, padding: '8px' }}
        />
        <button type="submit" disabled={loading || !query.trim()} style={{ padding: '8px 16px' }}>
          Send
        </button>
      </form>
    </div>
  );
}