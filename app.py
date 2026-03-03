import os
from functools import lru_cache
from typing import List, Dict

import requests
import streamlit as st

DEFAULT_CATALOG_URL = "https://share.note.sx/2bfsuvcx#69oXW5Jp6sHy9PL05gRKQFyEVyjku5+VMjkVk96vQwo"
DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_OPENAI_MODEL = "gpt-4o-mini"


def clean_catalog_url(url: str) -> str:
    return url.split("#", 1)[0]


@lru_cache(maxsize=4)
def load_catalog_from_url(url: str) -> str:
    response = requests.get(clean_catalog_url(url), timeout=30)
    response.raise_for_status()
    return response.text


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


def llm_chat(
    api_key: str,
    model: str,
    base_url: str,
    system_prompt: str,
    history: List[Dict[str, str]],
) -> str:
    endpoint = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "temperature": 0.2,
        "messages": [{"role": "system", "content": system_prompt}, *history],
    }

    response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
    response.raise_for_status()

    data = response.json()
    choices = data.get("choices", [])
    if not choices:
        return "Ich konnte keine Antwort vom Modell erhalten. Bitte versuche es erneut."

    message = choices[0].get("message", {})
    return message.get("content", "") or "Ich konnte keine Antwort vom Modell erhalten."


def main() -> None:
    st.set_page_config(page_title="Seminarfinder-Chatbot", page_icon="🎓", layout="wide")
    st.title("🎓 Seminarfinder-Chatbot")
    st.write("LLM-basierter Studienberater auf Grundlage des Seminar-Katalogs.")

    catalog_url = os.getenv("CATALOG_URL", DEFAULT_CATALOG_URL)
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", DEFAULT_OPENAI_BASE_URL)
    model = os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)

    with st.sidebar:
        st.header("Konfiguration")
        st.caption("Der Katalog wird immer automatisch aus der URL geladen.")
        st.text_input("Katalog-URL", value=catalog_url, disabled=True)
        st.text_input("LLM Base URL", value=base_url, disabled=True)
        st.text_input("LLM Modell", value=model, disabled=True)
        st.text_input("OPENAI_API_KEY gesetzt", value="Ja" if api_key else "Nein", disabled=True)

    if "catalog_text" not in st.session_state:
        try:
            st.session_state["catalog_text"] = load_catalog_from_url(catalog_url)
        except Exception as exc:
            st.error(
                "Katalog konnte nicht geladen werden. "
                "Bitte prüfe CATALOG_URL oder die Erreichbarkeit der Quelle.\n\n"
                f"Fehler: {exc}"
            )
            st.stop()

    if not api_key:
        st.error("OPENAI_API_KEY ist nicht gesetzt. Bitte als Umgebungsvariable konfigurieren.")
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
                answer = llm_chat(
                    api_key=api_key,
                    model=model,
                    base_url=base_url,
                    system_prompt=build_system_prompt(st.session_state["catalog_text"]),
                    history=history,
                )
            except Exception as exc:
                answer = (
                    "Beim Aufruf des LLM ist ein Fehler aufgetreten. "
                    "Bitte prüfe API-Key, Base-URL und Modell.\n\n"
                    f"Fehler: {exc}"
                )

            st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
