"""Interfaz web para extraer metadatos de Scopus y PubMed."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from scopus_extractor.client import ScopusAPIError, ScopusClient, ScopusQuery
from scopus_extractor.exporters import articles_to_csv, articles_to_json
from scopus_extractor.open_access import OpenAccessClient, build_pdf_archive
from scopus_extractor.pubmed import PubMedAPIError, PubMedClient, PubMedQuery


load_dotenv()
st.set_page_config(page_title="Extractor bibliográfico", page_icon="📚", layout="wide")
st.title("📚 Extractor de metadatos")
st.caption("Selecciona una base bibliográfica; la barra lateral se adapta a la fuente elegida.")

source = st.radio(
    "Base bibliográfica",
    ["Scopus", "PubMed"],
    horizontal=True,
    key="bibliographic_source",
)

if source == "Scopus":
    st.header("Búsqueda en Scopus")
    with st.sidebar:
        st.header("Configuración de Scopus")
        api_key = st.text_input("Clave API de Scopus", value=os.getenv("SCOPUS_API_KEY", ""), type="password")
        unpaywall_email = st.text_input("Correo para localizar PDFs OA", value=os.getenv("UNPAYWALL_EMAIL", ""))
        search_mode = st.radio("Modo de búsqueda", ["Guiada", "Avanzada"], horizontal=True)
        if search_mode == "Guiada":
            topic = st.text_area("Tema o expresión de búsqueda", placeholder="machine learning AND agriculture")
            advanced_query = None
        else:
            topic = ""
            advanced_query = st.text_area("Consulta avanzada de Scopus", placeholder='TITLE-ABS-KEY("machine learning")')
        max_results = st.number_input("Número de artículos", min_value=1, value=25, step=1)
        open_access_only = st.checkbox("Solo acceso abierto", value=True)
        year_from, year_to = st.slider("Rango de años", 1900, 2030, (2015, 2026))
        language = st.selectbox("Idioma", ["Todos", "English", "Spanish", "Portuguese", "French"])
        document_type = st.selectbox("Tipo de documento", ["Todos", "ar", "re", "cp", "ch"])
        subject_area = st.text_input("Área temática (código Scopus, opcional)", placeholder="COMP, MED, ENVI...")
        sort = st.selectbox("Ordenar por", ["-coverDate", "-citedby-count", "relevancy"])
        run = st.button("Extraer artículos de Scopus", type="primary", width="stretch")

    if run:
        if not api_key.strip():
            st.error("Introduce una clave API de Scopus.")
        elif search_mode == "Guiada" and not topic.strip():
            st.error("Introduce un tema o expresión de búsqueda.")
        elif search_mode == "Avanzada" and not advanced_query.strip():
            st.error("Introduce una consulta avanzada de Scopus.")
        else:
            query = ScopusQuery(
                topic=topic, max_results=int(max_results), open_access_only=open_access_only,
                year_from=year_from, year_to=year_to,
                language=None if language == "Todos" else language,
                document_type=None if document_type == "Todos" else document_type,
                subject_area=subject_area or None, sort=sort, advanced_query=advanced_query,
            )
            try:
                progress = st.progress(0, text="Consultando Scopus...")
                progress.progress(50, text="Consultando Scopus...")
                st.session_state["articles"] = ScopusClient(api_key).search(query)
                progress.progress(100, text="Búsqueda de Scopus completada.")
                for key in ("pdf_archive", "pdf_downloaded", "pdf_unavailable", "pdf_errors"):
                    st.session_state.pop(key, None)
                st.success(f"Se obtuvieron {len(st.session_state['articles'])} artículos.")
            except (ScopusAPIError, ValueError) as exc:
                st.error(str(exc))

    articles = st.session_state.get("articles", [])
    if articles:
        frame = pd.DataFrame([article.as_dict() for article in articles])
        st.download_button("Descargar metadatos JSON", articles_to_json(articles), "scopus_metadata.json", "application/json")
        st.download_button("Descargar CSV", articles_to_csv(articles), "scopus_articles.csv", "text/csv")
        st.subheader("PDFs de acceso abierto")
        if not unpaywall_email.strip():
            st.info("Añade un correo en la barra lateral para habilitar la búsqueda de PDFs.")
        elif st.button("Buscar y preparar PDFs OA"):
            try:
                progress = st.progress(0, text="Localizando y descargando copias OA...")
                result = build_pdf_archive(
                    OpenAccessClient(unpaywall_email),
                    articles,
                    progress_callback=lambda value: progress.progress(
                        value, text=f"Procesando artículos OA: {value}%"
                    ),
                )
                progress.progress(100, text="Preparación de PDFs completada.")
                st.session_state["pdf_archive"], st.session_state["pdf_downloaded"] = result[0], result[1]
                st.session_state["pdf_unavailable"], st.session_state["pdf_errors"] = result[2], result[3]
            except ValueError as exc:
                st.error(str(exc))
        if st.session_state.get("pdf_downloaded"):
            st.download_button("Descargar PDFs en ZIP", st.session_state["pdf_archive"], "scopus_open_access_pdfs.zip", "application/zip")
        st.dataframe(frame[["title", "authors", "publication_name", "cover_date", "doi", "cited_by_count", "open_access"]], width="stretch", hide_index=True)
    else:
        st.info("Configura la búsqueda de Scopus en la barra lateral para comenzar.")

else:
    st.header("Búsqueda en PubMed")
    with st.sidebar:
        st.header("Configuración de PubMed")
        st.caption("Estos son los controles específicos de búsqueda de PubMed.")
        pubmed_email = st.text_input("Correo para PubMed (opcional)", value=os.getenv("PUBMED_EMAIL", ""), key="pubmed_email")
        pubmed_api_key = st.text_input("Clave API de NCBI (opcional)", value=os.getenv("PUBMED_API_KEY", ""), type="password", key="pubmed_api_key")
        pubmed_search_mode = st.radio("Modo de búsqueda", ["Guiada", "Avanzada"], horizontal=True, key="pubmed_mode")
        if pubmed_search_mode == "Guiada":
            pubmed_topic = st.text_area("Términos de búsqueda", placeholder="machine learning AND agriculture", key="pubmed_topic")
            pubmed_advanced = None
        else:
            pubmed_topic = ""
            pubmed_advanced = st.text_area("Consulta avanzada de PubMed", placeholder='"lung cancer"[Title/Abstract] AND 2020:2026[Date - Publication]', key="pubmed_advanced")
        pubmed_max = st.number_input("Número de artículos", min_value=1, value=25, step=1, key="pubmed_max")
        pubmed_years = st.slider("Fecha de publicación", 1900, 2030, (2015, 2026), key="pubmed_years")
        pubmed_language = st.selectbox("Idioma", ["Todos", "English", "Spanish", "Portuguese", "French"], key="pubmed_language")
        pubmed_type = st.selectbox("Tipo de publicación", ["Todos", "Journal Article", "Review", "Clinical Trial", "Meta-Analysis"], key="pubmed_type")
        pubmed_sort = st.selectbox("Ordenar por", ["relevance", "pub date", "Author"], key="pubmed_sort")
        pubmed_run = st.button("Buscar en PubMed", type="primary", width="stretch", key="pubmed_run")

    if pubmed_run:
        if pubmed_search_mode == "Guiada" and not pubmed_topic.strip():
            st.error("Introduce términos de búsqueda para PubMed.")
        elif pubmed_search_mode == "Avanzada" and not pubmed_advanced.strip():
            st.error("Introduce una consulta avanzada de PubMed.")
        else:
            query = PubMedQuery(
                topic=pubmed_topic, max_results=int(pubmed_max),
                year_from=None if pubmed_advanced else pubmed_years[0],
                year_to=None if pubmed_advanced else pubmed_years[1],
                language=None if pubmed_language == "Todos" else pubmed_language,
                publication_type=None if pubmed_type == "Todos" else pubmed_type,
                sort=pubmed_sort, advanced_query=pubmed_advanced,
            )
            try:
                progress = st.progress(0, text="Consultando PubMed...")
                progress.progress(50, text="Consultando PubMed...")
                st.session_state["pubmed_articles"] = PubMedClient(email=pubmed_email, api_key=pubmed_api_key).search(query)
                progress.progress(100, text="Búsqueda de PubMed completada.")
                st.success(f"Se obtuvieron {len(st.session_state['pubmed_articles'])} artículos de PubMed.")
            except (PubMedAPIError, ValueError) as exc:
                st.error(str(exc))

    pubmed_articles = st.session_state.get("pubmed_articles", [])
    if pubmed_articles:
        frame = pd.DataFrame([article.as_dict() for article in pubmed_articles])
        st.download_button("Descargar metadatos JSON", articles_to_json(pubmed_articles), "pubmed_metadata.json", "application/json")
        st.download_button("Descargar CSV", articles_to_csv(pubmed_articles), "pubmed_articles.csv", "text/csv")
        st.subheader("PDFs de acceso abierto")
        if not pubmed_email.strip():
            st.info("Añade un correo en la barra lateral para habilitar la búsqueda de PDFs.")
        elif st.button("Buscar y preparar PDFs OA de PubMed"):
            try:
                progress = st.progress(0, text="Localizando y descargando copias OA...")
                result = build_pdf_archive(
                    OpenAccessClient(pubmed_email),
                    pubmed_articles,
                    progress_callback=lambda value: progress.progress(
                        value, text=f"Procesando artículos OA: {value}%"
                    ),
                )
                progress.progress(100, text="Preparación de PDFs completada.")
                st.session_state["pubmed_pdf_archive"], st.session_state["pubmed_pdf_downloaded"] = result[0], result[1]
                st.session_state["pubmed_pdf_unavailable"], st.session_state["pubmed_pdf_errors"] = result[2], result[3]
            except ValueError as exc:
                st.error(str(exc))
        if st.session_state.get("pubmed_pdf_downloaded"):
            st.download_button("Descargar PDFs de PubMed en ZIP", st.session_state["pubmed_pdf_archive"], "pubmed_open_access_pdfs.zip", "application/zip")
        st.dataframe(frame[["title", "authors", "publication_name", "cover_date", "doi", "pmid", "pmc_id", "open_access"]], width="stretch", hide_index=True)
    else:
        st.info("Configura la búsqueda de PubMed en la barra lateral para comenzar.")
