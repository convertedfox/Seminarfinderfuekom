import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple

import requests
import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DEFAULT_CATALOG_URL = "https://share.note.sx/2bfsuvcx#69oXW5Jp6sHy9PL05gRKQFyEVyjku5+VMjkVk96vQwo"


@dataclass
class CatalogChunk:
    title: str
    text: str


@lru_cache(maxsize=8)
def load_catalog_from_url(url: str) -> str:
    """Lädt den Katalog-Text von einer URL. URL-Fragmente werden ignoriert."""
    clean_url = url.split("#", 1)[0]
    response = requests.get(clean_url, timeout=20)
    response.raise_for_status()
    return response.text


@lru_cache(maxsize=8)
def load_catalog_from_file(path: str) -> str:
    with open(path, "r", encoding="utf-8") as file:
        return file.read()


def split_markdown_into_chunks(markdown_text: str) -> List[CatalogChunk]:
    """Teilt Markdown anhand von Überschriften in durchsuchbare Blöcke."""
    sections = re.split(r"\n(?=#{1,3}\s)", markdown_text)
    chunks: List[CatalogChunk] = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        lines = section.splitlines()
        first_line = lines[0].strip()
        if first_line.startswith("#"):
            title = re.sub(r"^#{1,3}\s*", "", first_line).strip()
            body = "\n".join(lines[1:]).strip()
        else:
            title = "Allgemein"
            body = section

        cleaned_body = re.sub(r"\n{3,}", "\n\n", body).strip()
        combined_text = f"{title}\n{cleaned_body}".strip()

        if len(combined_text) > 20:
            chunks.append(CatalogChunk(title=title or "Ohne Titel", text=combined_text))

    return chunks


def retrieve_relevant_chunks(question: str, chunks: List[CatalogChunk], top_k: int = 4) -> List[Tuple[CatalogChunk, float]]:
    corpus = [chunk.text for chunk in chunks]
    vectorizer = TfidfVectorizer(stop_words="german", ngram_range=(1, 2), min_df=1)
    matrix = vectorizer.fit_transform(corpus)
    question_vec = vectorizer.transform([question])
    scores = cosine_similarity(question_vec, matrix).flatten()

    top_indices = scores.argsort()[::-1][:top_k]
    results = [(chunks[idx], float(scores[idx])) for idx in top_indices if scores[idx] > 0]
    return results


def format_answer(question: str, matches: List[Tuple[CatalogChunk, float]]) -> str:
    if not matches:
        return (
            "Ich habe im Katalog nichts Passendes gefunden. "
            "Formuliere deine Frage bitte konkreter (z. B. Thema, ECTS, Sprache, Terminlage oder Vorkenntnisse)."
        )

    response_lines = [
        f"Für deine Frage **\"{question}\"** passen diese Seminar-Optionen aus dem Katalog:",
        "",
    ]

    for i, (chunk, score) in enumerate(matches, start=1):
        snippet = chunk.text[:500].strip().replace("\n", " ")
        response_lines.append(
            f"**{i}. {chunk.title}**  \n"
            f"Relevanz: {score:.0%}  \n"
            f"Hinweis aus dem Katalog: {snippet}..."
        )
        response_lines.append("")

    response_lines.extend(
        [
            "### Empfehlung",
            "Vergleiche vor allem Themenfokus, Anforderungen und organisatorische Rahmenbedingungen. "
            "Wenn du willst, kann ich dir als Nächstes eine Priorisierung nach deinen Präferenzen erstellen "
            "(z. B. **praxisnah**, **methodisch**, **wenig Vorkenntnisse**, **bestimmte Tage**).",
        ]
    )

    return "\n".join(response_lines)


def main() -> None:
    st.set_page_config(page_title="Seminarfinder-Chatbot", page_icon="🎓", layout="wide")

    st.title("🎓 Seminarfinder-Chatbot")
    st.write(
        "Dieser Chatbot hilft Studierenden, aus einem Markdown-Katalog passende Seminare zu finden. "
        "Die Antworten basieren auf einer semantischen Suche im Katalogtext."
    )

    with st.sidebar:
        st.header("Datenquelle")
        source = st.radio("Katalog laden aus", ["URL", "Lokale Datei"], horizontal=False)

        markdown_text = ""
        if source == "URL":
            catalog_url = st.text_input("Katalog-URL", value=os.getenv("CATALOG_URL", DEFAULT_CATALOG_URL))
            if st.button("Katalog von URL laden", use_container_width=True):
                try:
                    markdown_text = load_catalog_from_url(catalog_url)
                    st.session_state["catalog_text"] = markdown_text
                    st.success("Katalog erfolgreich geladen.")
                except Exception as exc:
                    st.error(f"Katalog konnte nicht geladen werden: {exc}")
        else:
            upload = st.file_uploader("Markdown-Datei hochladen", type=["md", "markdown", "txt"])
            if upload is not None:
                markdown_text = upload.getvalue().decode("utf-8")
                st.session_state["catalog_text"] = markdown_text
                st.success("Katalog-Datei geladen.")

        if "catalog_text" not in st.session_state:
            st.info("Lade den Katalog, um den Chatbot zu nutzen.")

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    "Hi! Ich unterstütze dich bei der Seminarwahl. "
                    "Lade links den Katalog und stelle dann deine Frage."
                ),
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_prompt = st.chat_input("Welche Art von Seminar suchst du?")

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        catalog_text = st.session_state.get("catalog_text", "")
        if not catalog_text.strip():
            answer = "Bitte lade zuerst den Katalog in der Sidebar."
        else:
            chunks = split_markdown_into_chunks(catalog_text)
            matches = retrieve_relevant_chunks(user_prompt, chunks)
            answer = format_answer(user_prompt, matches)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        with st.chat_message("assistant"):
            st.markdown(answer)


if __name__ == "__main__":
    main()
