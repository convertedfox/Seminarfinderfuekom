# Seminarfinder-Chatbot (Streamlit + Abacus AI API)

Diese App berät Studierende bei der Seminarwahl mit einem LLM über **Abacus AI** und nutzt den Seminar-Katalog als Wissensbasis.

## Verhalten

- Der Katalog wird **immer automatisch** aus `CATALOG_URL` geladen.
- Der Chat nutzt die Abacus-AI-kompatible Chat-Completions-API.
- Antworten sollen sich auf den Katalog stützen.

## Umgebungsvariablen

- `ABACUS_API_KEY` (Pflicht)
  - Fallback: `OPENAI_API_KEY`
- `ABACUS_API_URL` (optional, Default: `https://routellm.abacus.ai/v1/chat/completions`)
- `ABACUS_MODEL` (optional, Default: `gpt-5`)
- `ABACUS_STREAM` (optional, `true`/`false`, Default: `false`)
- `CATALOG_URL` (optional, Default ist die vorgegebene Katalog-URL)

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
ABACUS_MODEL = "gpt-5"
ABACUS_STREAM = "false"
CATALOG_URL = "https://share.note.sx/2bfsuvcx#69oXW5Jp6sHy9PL05gRKQFyEVyjku5+VMjkVk96vQwo"
```

## Hinweis zur Abacus-Beispielintegration

Die Implementierung folgt dem von dir gezeigten Muster:

- `Authorization: Bearer <api_key>`
- `POST` auf `https://routellm.abacus.ai/v1/chat/completions`
- optionales Streaming via `data: ...` Zeilen und `[DONE]`

## Troubleshooting: 400 Bad Request

Wenn `400 Bad Request` von Abacus kommt, sind häufige Ursachen:

- Modellname nicht verfügbar/falsch geschrieben
- Payload zu groß
- Ungültige Parameterkombination

Die App reduziert deshalb den Katalogkontext automatisch auf relevante Abschnitte.
