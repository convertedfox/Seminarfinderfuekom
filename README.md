# Seminarfinder-Chatbot (Streamlit + Abacus AI API)

Diese App berät Studierende bei der Seminarwahl mit einem LLM über **Abacus AI** und nutzt den Seminar-Katalog als Wissensbasis.

## Verhalten

- Der Katalog wird **immer automatisch** aus einer Datei im Repo geladen.
- Standardpfad: `data/catalog.md`
- Der Chat nutzt die Abacus-AI-kompatible Chat-Completions-API.
- Antworten stützen sich auf den Katalog und bleiben im Chat kurz.
- Passende Seminare werden als strukturierte Ergebnisse direkt unter dem Chat angezeigt.
- Ergebnisse enthalten Filter-Chips und kompakte Badges (Kategorie, Dualis, Thema).

## Umgebungsvariablen

- `ABACUS_API_KEY` (Pflicht)
  - Fallback: `OPENAI_API_KEY`
- `ABACUS_API_URL` (optional, Default: `https://routellm.abacus.ai/v1/chat/completions`)
- `ABACUS_MODEL` (optional, Default: `gpt-5-nano`)
- `ABACUS_STREAM` (optional, `true`/`false`, Default: `false`)
- `CATALOG_FILE` (optional, Default: `data/catalog.md`)

## Lokal starten

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export ABACUS_API_KEY="..."
streamlit run app.py
```

## Streamlit Cloud (streamlit.io)

In den App-Secrets setzen:

```toml
ABACUS_API_KEY = "..."
ABACUS_API_URL = "https://routellm.abacus.ai/v1/chat/completions"
ABACUS_MODEL = "gpt-5-nano"
ABACUS_STREAM = "false"
CATALOG_FILE = "data/catalog.md"
```

## Hinweis zur Abacus-Beispielintegration

Die Implementierung folgt dem von dir gezeigten Muster:

- `Authorization: Bearer <api_key>`
- `POST` auf `https://routellm.abacus.ai/v1/chat/completions`
- optionales Streaming via `data: ...` Zeilen und `[DONE]`
