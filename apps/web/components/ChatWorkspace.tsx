'use client';

import React, { useState } from 'react';
import { sendQuery } from '@/lib/api';
import { QueryResponse } from '@/lib/types';

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
    <div style={{ flex: 1, padding: '15px', display: 'flex', flexDirection: 'column', height: '100vh', backgroundColor: '#ffffff', color: '#111827', boxSizing: 'border-box' }}>
      <h2 style={{ marginBottom: '10px' }}>RAG Workspace</h2>

      {/* Message History */}
      <div style={{ flex: 1, overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '15px', backgroundColor: '#fafafa', borderRadius: '4px' }}>
        {messages.length === 0 && <p style={{ color: '#6b7280' }}>No queries sent yet.</p>}

        {messages.map((msg, idx) => (
          <div key={idx} style={{ marginBottom: '15px', backgroundColor: '#ffffff', padding: '10px', borderRadius: '4px', border: '1px solid #e5e7eb' }}>
            <b>{msg.role === 'user' ? 'User:' : 'Assistant:'}</b>

            {/* DeepSeek Reasoning Log (<think>) */}
            {msg.role === 'assistant' && msg.thoughts && (
              <details style={{ margin: '8px 0', padding: '8px', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: '4px' }}>
                <summary style={{ cursor: 'pointer', fontWeight: 'bold', color: '#b45309' }}>
                  Reasoning Process (&lt;think&gt;)
                </summary>
                <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px', margin: '8px 0', color: '#78350f', fontFamily: 'monospace' }}>
                  {msg.thoughts}
                </pre>
              </details>
            )}

            <p style={{ margin: '5px 0', whiteSpace: 'pre-wrap', color: '#111827' }}>{msg.content}</p>

            {/* Retrieved Source Context & Distance Scores */}
            {msg.role === 'assistant' && msg.retrieved_docs && msg.retrieved_docs.length > 0 && (
              <details style={{ margin: '8px 0', padding: '8px', background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '4px' }}>
                <summary style={{ cursor: 'pointer', fontSize: '13px', color: '#1d4ed8', fontWeight: 'bold' }}>
                  Retrieved Context ({msg.retrieved_docs.length} chunks)
                </summary>
                <div style={{ marginTop: '5px' }}>
                  {msg.retrieved_docs.map((doc, dIdx) => (
                    <div key={dIdx} style={{ padding: '6px', borderBottom: '1px solid #dbeafe', fontSize: '12px', color: '#1e293b' }}>
                      <div><b>Source:</b> {doc.metadata.source || 'N/A'} | <b>Distance:</b> {doc.distance}</div>
                      <div style={{ marginTop: '3px' }}>{doc.content}</div>
                    </div>
                  ))}
                </div>
              </details>
            )}
          </div>
        ))}

        {loading && <p style={{ color: '#2563eb' }}><i>Searching context & generating response...</i></p>}
      </div>

      {/* Simple Query Input Form */}
      <form onSubmit={handleSend} style={{ display: 'flex', gap: '10px' }}>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask a question..."
          style={{ flex: 1, padding: '10px', backgroundColor: '#ffffff', color: '#111827', border: '1px solid #ccc', borderRadius: '4px' }}
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          style={{ padding: '10px 20px', backgroundColor: '#2563eb', color: '#ffffff', border: 'none', borderRadius: '4px', fontWeight: 'bold' }}
        >
          Send
        </button>
      </form>
    </div>
  );
}