# Seminarfinder-Chatbot (Streamlit)

Diese Streamlit-App hilft Studierenden, im Seminar-Katalog passende Veranstaltungen zu finden.

## Features

- Chat-Interface mit `st.chat_input` / `st.chat_message`
- Wissensbasis aus Markdown (URL oder Datei-Upload)
- Semantische Suche via TF-IDF + Cosine Similarity
- Antwort mit relevanten Katalogausschnitten und Empfehlung

## Lokal starten

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud (streamlit.io)

1. Repository nach GitHub pushen.
2. Auf Streamlit Cloud neues App-Deployment erstellen.
3. Main file: `app.py`
4. Optionales Secret setzen:
   - `CATALOG_URL`: Standard-URL des Katalogs.

## Hinweise zur Katalog-URL

Die App lädt bei URL-Nutzung den Inhalt per HTTP-Request. Falls die Quelle eine besondere Authentifizierung oder clientseitige Entschlüsselung benötigt, nutze stattdessen den Datei-Upload in der Sidebar.
