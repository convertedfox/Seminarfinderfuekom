import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import requests
import streamlit as st

DEFAULT_CATALOG_FILE = "data/catalog.md"
DEFAULT_ABACUS_ENDPOINT = "https://routellm.abacus.ai/v1/chat/completions"
DEFAULT_ABACUS_MODEL = "gpt-5"


@lru_cache(maxsize=4)
def load_catalog_from_file(file_path: str) -> str:
    catalog_text = Path(file_path).read_text(encoding="utf-8")
    if not catalog_text.strip():
        raise ValueError("Katalogdatei ist leer.")
    return catalog_text


def build_system_prompt(catalog_text: str) -> str:
    return (
        "Du bist ein Studienberater für Seminare. "
        "Deine Aufgabe ist, Studierende bei der Auswahl passender Seminare zu unterstützen.\n\n"
        "Regeln:\n"
        "1) Antworte auf Deutsch, klar und freundlich.\n"
        "2) Verwende ausschließlich Informationen aus dem bereitgestellten Katalog.\n"
        "3) Wenn Informationen fehlen, sage das transparent.\n"
        "4) Stelle bei Bedarf gezielte Rückfragen (Interessen, Vorkenntnisse, Zeit, Sprache, Prüfungsform).\n"
        "5) Gib konkrete Empfehlungen mit kurzer Begründung.\n\n"
        "KATALOG (Wissensbasis):\n"
        f"{catalog_text[:120000]}"
    )


def _extract_non_stream_response(payload: Dict) -> str:
    choices = payload.get("choices", [])
    if not choices:
        return "Ich konnte keine Antwort vom Modell erhalten. Bitte versuche es erneut."
    message = choices[0].get("message", {})
    return message.get("content", "") or "Ich konnte keine Antwort vom Modell erhalten."


def _extract_stream_response(response: requests.Response) -> str:
    chunks: List[str] = []
    for line in response.iter_lines():
        if not line:
            continue

        decoded = line.decode("utf-8")
        if not decoded.startswith("data: "):
            continue

        data_part = decoded[6:]
        if data_part == "[DONE]":
            break

        try:
            chunk_json = json.loads(data_part)
        except json.JSONDecodeError:
            continue

        delta = chunk_json.get("choices", [{}])[0].get("delta", {})
        token = delta.get("content")
        if token:
            chunks.append(token)

    return "".join(chunks).strip() or "Ich konnte keine Antwort vom Modell erhalten."


def llm_chat_abacus(
    api_key: str,
    model: str,
    endpoint: str,
    system_prompt: str,
    history: List[Dict[str, str]],
    stream: bool,
) -> str:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system_prompt}, *history],
        "temperature": 0.2,
        "stream": stream,
    }

    if stream:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=120, stream=True)
        response.raise_for_status()
        return _extract_stream_response(response)

    response = requests.post(endpoint, headers=headers, data=json.dumps(payload), timeout=120)
    response.raise_for_status()
    return _extract_non_stream_response(response.json())


def main() -> None:
    st.set_page_config(page_title="Seminarfinder-Chatbot", page_icon="🎓", layout="wide")
    st.title("🎓 Seminarfinder-Chatbot")
    st.write("Seminarfinder für die Fükom-Seminare.")

    catalog_file = os.getenv("CATALOG_FILE", DEFAULT_CATALOG_FILE)
    abacus_api_key = os.getenv("ABACUS_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    abacus_endpoint = os.getenv("ABACUS_API_URL", DEFAULT_ABACUS_ENDPOINT)
    abacus_model = os.getenv("ABACUS_MODEL", DEFAULT_ABACUS_MODEL)
    abacus_stream = os.getenv("ABACUS_STREAM", "false").lower() in {"1", "true", "yes"}

    with st.sidebar:
        st.header("Konfiguration")
        st.caption("Der Katalog wird immer automatisch aus der Datei im Repo geladen.")
        st.text_input("Katalog-Datei", value=catalog_file, disabled=True)
        st.text_input("Abacus API URL", value=abacus_endpoint, disabled=True)
        st.text_input("Abacus Modell", value=abacus_model, disabled=True)
        st.text_input("Streaming", value="Aktiv" if abacus_stream else "Inaktiv", disabled=True)
        st.text_input("ABACUS_API_KEY gesetzt", value="Ja" if abacus_api_key else "Nein", disabled=True)

    if "catalog_text" not in st.session_state:
        try:
            st.session_state["catalog_text"] = load_catalog_from_file(catalog_file)
        except Exception as exc:
            st.error(
                "Katalog konnte nicht geladen werden. "
                "Bitte prüfe CATALOG_FILE und den Dateipfad.\n\n"
                f"Fehler: {exc}"
            )
            st.stop()

    if not abacus_api_key:
        st.error("ABACUS_API_KEY ist nicht gesetzt. Bitte als Umgebungsvariable konfigurieren.")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! Ich berate dich bei der Seminarwahl anhand des Katalogs. Was suchst du?",
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("z. B. Ich möchte meine Selbstsicherheit steigern.")
    if not user_prompt:
        return

    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    with st.chat_message("assistant"):
        with st.spinner("Ich suche passende Seminare im Katalog …"):
            try:
                history = [
                    {"role": m["role"], "content": m["content"]}
                    for m in st.session_state.messages
                    if m["role"] in {"user", "assistant"}
                ]
                answer = llm_chat_abacus(
                    api_key=abacus_api_key,
                    model=abacus_model,
                    endpoint=abacus_endpoint,
                    system_prompt=build_system_prompt(st.session_state["catalog_text"]),
                    history=history,
                    stream=abacus_stream,
                )
            except Exception as exc:
                answer = (
                    "Beim Aufruf der Abacus API ist ein Fehler aufgetreten. "
                    "Bitte prüfe API-Key, URL und Modell.\n\n"
                    f"Fehler: {exc}"
                )

            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
