'use client';

import React, { useEffect, useState } from 'react';
import { fetchSystemConfig, updateSystemConfig, fetchAvailableModels, triggerIngestion } from '@/lib/api';
import { SystemConfig, ModelListResponse } from '@/lib/types';

export default function Sidebar() {
  const [config, setConfig] = useState<SystemConfig | null>(null);
  const [models, setModels] = useState<ModelListResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [ingesting, setIngesting] = useState<boolean>(false);
  const [ingestStatus, setIngestStatus] = useState<string>('');

  useEffect(() => {
    async function loadData() {
      try {
        const [configData, modelsData] = await Promise.all([
          fetchSystemConfig(),
          fetchAvailableModels(),
        ]);
        setConfig(configData);
        setModels(modelsData);
      } catch (err) {
        console.error('Failed to load system config/models:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const handleProviderChange = async (provider: 'local' | 'ollama') => {
    if (!config || !models) return;
    const defaultEmbed = provider === 'ollama'
      ? (models.ollama.embedders[0] || '')
      : (models.local.embedders[0] || '');
    const defaultLLM = provider === 'ollama'
      ? (models.ollama.generators[0] || '')
      : (models.local.generators[0] || '');

    const updated = await updateSystemConfig({
      provider,
      selected_embed_model: defaultEmbed,
      selected_llm_model: defaultLLM,
    });
    setConfig(updated.config);
  };

  const handleModelChange = async (field: 'selected_embed_model' | 'selected_llm_model', value: string) => {
    if (!config) return;
    const updated = await updateSystemConfig({ [field]: value });
    setConfig(updated.config);
  };

  const handleIngest = async () => {
    setIngesting(true);
    setIngestStatus('Ingesting documents into ChromaDB...');
    try {
      const res = await triggerIngestion('./docs');
      setIngestStatus(`Success: ${res.chunks_ingested} chunk(s) ingested from ${res.documents_loaded} doc(s).`);
    } catch (err) {
      setIngestStatus('Ingestion failed. Ensure ./docs directory exists and contains files.');
    } finally {
      setIngesting(false);
    }
  };

  if (loading || !config || !models) {
    return (
      <div style={{ width: '280px', padding: '15px', borderRight: '1px solid #ccc', backgroundColor: '#f9f9f9', color: '#111827' }}>
        Loading configuration...
      </div>
    );
  }

  const currentEmbedOptions = config.provider === 'ollama' ? models.ollama.embedders : models.local.embedders;
  const currentLLMOptions = config.provider === 'ollama' ? models.ollama.generators : models.local.generators;

  return (
    <div style={{ width: '280px', padding: '15px', borderRight: '1px solid #ccc', backgroundColor: '#f9f9f9', color: '#111827', height: '100vh', boxSizing: 'border-box' }}>
      <h3 style={{ marginBottom: '15px' }}>System Configuration</h3>

      {/* Provider Selection */}
      <div style={{ marginBottom: '15px' }}>
        <label><b>Provider:</b></label><br />
        <label style={{ marginRight: '10px' }}>
          <input
            type="radio"
            name="provider"
            value="ollama"
            checked={config.provider === 'ollama'}
            onChange={() => handleProviderChange('ollama')}
          />
          Ollama
        </label>
        <label>
          <input
            type="radio"
            name="provider"
            value="local"
            checked={config.provider === 'local'}
            onChange={() => handleProviderChange('local')}
          />
          Local (PyTorch)
        </label>
      </div>

      {/* Embedding Model Dropdown */}
      <div style={{ marginBottom: '15px' }}>
        <label><b>Embedding Model:</b></label><br />
        <select
          value={config.selected_embed_model}
          onChange={(e) => handleModelChange('selected_embed_model', e.target.value)}
          style={{ width: '100%', marginTop: '5px', padding: '5px', backgroundColor: '#ffffff', color: '#111827', border: '1px solid #ccc' }}
        >
          {currentEmbedOptions.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>

      {/* LLM Generator Dropdown */}
      <div style={{ marginBottom: '15px' }}>
        <label><b>LLM Generator:</b></label><br />
        <select
          value={config.selected_llm_model}
          onChange={(e) => handleModelChange('selected_llm_model', e.target.value)}
          style={{ width: '100%', marginTop: '5px', padding: '5px', backgroundColor: '#ffffff', color: '#111827', border: '1px solid #ccc' }}
        >
          {currentLLMOptions.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>

      <hr style={{ margin: '15px 0' }} />

      {/* Ingestion Section */}
      <div>
        <h4 style={{ marginBottom: '10px' }}>Document Ingestion</h4>
        <button
          onClick={handleIngest}
          disabled={ingesting}
          style={{ width: '100%', padding: '8px', backgroundColor: '#2563eb', color: '#ffffff', border: 'none', borderRadius: '4px', fontWeight: 'bold' }}
        >
          {ingesting ? 'Ingesting...' : 'Ingest Docs Folder'}
        </button>
        {ingestStatus && (
          <p style={{ fontSize: '12px', marginTop: '10px', background: '#e5e7eb', color: '#111827', padding: '8px', borderRadius: '4px' }}>
            {ingestStatus}
          </p>
        )}
      </div>
    </div>
  );
}