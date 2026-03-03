# Seminarfinder-Chatbot (Streamlit + LLM API)

Diese App berät Studierende bei der Seminarwahl mit einem LLM und nutzt den Seminar-Katalog als Wissensbasis.

## Verhalten

- Der Katalog wird **immer automatisch** aus `CATALOG_URL` geladen.
- Der Chat läuft über eine OpenAI-kompatible Chat-Completions-API.
- Antworten sollen sich auf den Katalog stützen.

## Umgebungsvariablen

- `OPENAI_API_KEY` (Pflicht)
- `OPENAI_MODEL` (optional, Default: `gpt-4o-mini`)
- `OPENAI_BASE_URL` (optional, Default: `https://api.openai.com/v1`)
- `CATALOG_URL` (optional, Default ist die vorgegebene Katalog-URL)

## Lokal starten

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export OPENAI_API_KEY="..."
streamlit run app.py
```

## Streamlit Cloud (streamlit.io)

In den App-Secrets setzen:

```toml
OPENAI_API_KEY = "..."
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_BASE_URL = "https://api.openai.com/v1"
CATALOG_URL = "https://share.note.sx/2bfsuvcx#69oXW5Jp6sHy9PL05gRKQFyEVyjku5+VMjkVk96vQwo"
```
