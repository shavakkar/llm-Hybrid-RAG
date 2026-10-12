ai/config.py - Choose Ollama or Locally downloaded LLMs & embedding models
PROVIDER: ExecutionProvider = ExecutionProvider.LOCAL

ExecutionProvider.LOCAL -> Local LLMs
ExecutionProvider.OLLAMA -> Ollama

To update and utilise Local LLMs & Embed models;
Change the path of these variables:
LOCAL_EMBED_PATH
LOCAL_LLM_PATH

Create .env file and add;
RAG_PROVIDER=local

To run the code:
python test_rag.py

To start HTTP Server:
python -m uvicorn ai.main:app --reload --reload-dir ai --port 8000

// First Move to main & merge the working branch (for myself)
git merge <<'feature/adding-db'>>:<<branch needs to be merged to 'Main'>> -m "Merged feature-branch: Added SQLite DB" --no-ff