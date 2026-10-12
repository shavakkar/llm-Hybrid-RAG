import { SystemConfig, ModelListResponse, IngestResponse, QueryResponse } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api';

export async function fetchHealth(): Promise<{ status: string; provider: string; database: string }> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) throw new Error('Failed to fetch health status');
  return res.json();
}

export async function fetchAvailableModels(): Promise<ModelListResponse> {
  const res = await fetch(`${API_BASE_URL}/models`);
  if (!res.ok) throw new Error('Failed to fetch models');
  return res.json();
}

export async function fetchSystemConfig(): Promise<SystemConfig> {
  const res = await fetch(`${API_BASE_URL}/config`);
  if (!res.ok) throw new Error('Failed to fetch configuration');
  return res.json();
}

export async function updateSystemConfig(config: Partial<SystemConfig>): Promise<{ message: string; config: SystemConfig }> {
  const res = await fetch(`${API_BASE_URL}/config`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config),
  });
  if (!res.ok) throw new Error('Failed to update configuration');
  return res.json();
}

export async function triggerIngestion(docsDir: string = './docs'): Promise<IngestResponse> {
  const res = await fetch(`${API_BASE_URL}/ingest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ docs_dir: docsDir }),
  });
  if (!res.ok) throw new Error('Failed to ingest documents');
  return res.json();
}

export async function sendQuery(query: string): Promise<QueryResponse> {
  const res = await fetch(`${API_BASE_URL}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error('Failed to execute query');
  return res.json();
}