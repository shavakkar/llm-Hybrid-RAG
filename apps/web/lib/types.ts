export interface SystemConfig {
  id: number;
  provider: 'local' | 'ollama';
  selected_embed_model: string;
  selected_llm_model: string;
  chunk_size: number;
  chunk_overlap: number;
  updated_at: string;
}

export interface ModelListResponse {
  ollama: {
    embedders: string[];
    generators: string[];
  };
  local: {
    embedders: string[];
    generators: string[];
  };
}

export interface IngestResponse {
  message: string;
  documents_loaded: number;
  chunks_ingested: number;
}

export interface SearchResultDoc {
  content: string;
  metadata: {
    source?: string;
    chunk_id?: number;
    path?: string;
  };
  distance: number;
}

export interface QueryResponse {
  thoughts: string;
  answer: string;
  retrieved_docs: SearchResultDoc[];
}