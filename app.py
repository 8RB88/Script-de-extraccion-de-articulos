"""Interfaz web para extraer metadatos de Scopus."""

from __future__ import annotations

import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from scopus_extractor.client import ScopusAPIError, ScopusClient, ScopusQuery
from scopus_extractor.exporters import articles_to_csv, articles_to_json
from scopus_extractor.open_access import OpenAccessClient, build_pdf_archive


load_dotenv()
st.set_page_config(page_title="Extractor de Scopus", page_icon="📚", layout="wide")
st.title("📚 Extractor de metadatos de Scopus")
st.caption("Consulta Scopus y descarga metadatos o copias PDF legalmente disponibles en acceso abierto.")

with st.sidebar:
    st.header("Configuración")
    api_key = st.text_input(
        "Clave API de Scopus",
        value=os.getenv("SCOPUS_API_KEY", ""),
        type="password",
        help="Obtén una clave en https://dev.elsevier.com/",
    )
    unpaywall_email = st.text_input(
        "Correo para localizar PDFs OA",
        value=os.getenv("UNPAYWALL_EMAIL", ""),
        help="Unpaywall requiere un correo para identificar sus solicitudes.",
    )
    search_mode = st.radio("Modo de búsqueda", ["Guiada", "Avanzada"], horizontal=True)
    if search_mode == "Guiada":
        topic = st.text_area(
            "Tema o expresión de búsqueda",
            placeholder='Ejemplo: ("machine learning" OR "deep learning") AND agriculture',
        )
        advanced_query = None
    else:
        topic = ""
        advanced_query = st.text_area(
            "Consulta avanzada de Scopus",
            placeholder="TITLE-ABS-KEY(\"machine learning\") AND PUBYEAR > 2020 AND SUBJAREA(COMP)",
            help="Escribe directamente la sintaxis de Scopus. Los filtros de años, idioma, tipo y área de abajo no se aplican en este modo.",
        )
        st.caption("Ejemplo: `AUTHLASTNAME(Smith) AND SRCTITLE(Nature) AND OPENACCESS(1)`")
    max_results = st.number_input("Número de artículos", min_value=1, max_value=200, value=25)
    open_access_only = st.checkbox("Solo acceso abierto", value=True)
    year_from, year_to = st.slider("Rango de años", min_value=1900, max_value=2030, value=(2015, 2026))
    language = st.selectbox("Idioma", ["Todos", "English", "Spanish", "Portuguese", "French"])
    document_type = st.selectbox("Tipo de documento", ["Todos", "ar", "re", "cp", "ch"])
    subject_area = st.text_input("Área temática (código Scopus, opcional)", placeholder="COMP, MED, ENVI...")
    sort = st.selectbox("Ordenar por", ["-coverDate", "-citedby-count", "relevancy"])
    run = st.button("Extraer artículos", type="primary", width="stretch")

if run:
    if not api_key.strip():
        st.error("Introduce una clave API de Scopus.")
    elif search_mode == "Guiada" and not topic.strip():
        st.error("Introduce un tema o expresión de búsqueda.")
    elif search_mode == "Avanzada" and not advanced_query.strip():
        st.error("Introduce una consulta avanzada de Scopus.")
    else:
        query = ScopusQuery(
            topic=topic,
            max_results=int(max_results),
            open_access_only=open_access_only,
            year_from=year_from,
            year_to=year_to,
            language=None if language == "Todos" else language,
            document_type=None if document_type == "Todos" else document_type,
            subject_area=subject_area or None,
            sort=sort,
            advanced_query=advanced_query,
        )
        try:
            with st.spinner("Consultando Scopus..."):
                articles = ScopusClient(api_key).search(query)
            st.session_state["articles"] = articles
            st.session_state.pop("pdf_archive", None)
            st.session_state.pop("pdf_downloaded", None)
            st.session_state.pop("pdf_unavailable", None)
            st.session_state.pop("pdf_errors", None)
            st.success(f"Se obtuvieron {len(articles)} artículos.")
        except (ScopusAPIError, ValueError) as exc:
            st.error(str(exc))

articles = st.session_state.get("articles", [])
if articles:
    frame = pd.DataFrame([article.as_dict() for article in articles])
    st.download_button(
        "Descargar metadatos JSON",
        data=articles_to_json(articles),
        file_name="scopus_metadata.json",
        mime="application/json",
    )
    st.download_button(
        "Descargar CSV",
        data=articles_to_csv(articles),
        file_name="scopus_articles.csv",
        mime="text/csv",
    )
    st.subheader("PDFs de acceso abierto")
    st.caption(
        "Los PDFs se buscan por DOI en Unpaywall. Solo se descargan copias que el "
        "repositorio identifica como de acceso abierto; Scopus no entrega PDFs directamente."
    )
    if not unpaywall_email.strip():
        st.info("Añade un correo en la barra lateral para habilitar la búsqueda de PDFs.")
    elif st.button("Buscar y preparar PDFs OA"):
        try:
            with st.spinner("Localizando y descargando copias OA..."):
                archive, downloaded, unavailable, errors = build_pdf_archive(
                    OpenAccessClient(unpaywall_email),
                    articles,
                )
            st.session_state["pdf_archive"] = archive
            st.session_state["pdf_downloaded"] = downloaded
            st.session_state["pdf_unavailable"] = unavailable
            st.session_state["pdf_errors"] = errors
        except ValueError as exc:
            st.error(str(exc))
    if st.session_state.get("pdf_downloaded"):
        st.success(f"PDFs preparados: {len(st.session_state['pdf_downloaded'])}.")
        st.download_button(
            "Descargar PDFs en ZIP",
            data=st.session_state["pdf_archive"],
            file_name="scopus_open_access_pdfs.zip",
            mime="application/zip",
        )
    if st.session_state.get("pdf_unavailable"):
        st.warning(
            f"No se encontró una copia PDF OA para {len(st.session_state['pdf_unavailable'])} artículo(s). "
            "Esto puede ocurrir aunque Scopus marque el registro como acceso abierto."
        )
    if st.session_state.get("pdf_errors"):
        st.error(f"No se pudieron descargar {len(st.session_state['pdf_errors'])} PDF(s).")
        with st.expander("Ver detalles de los errores"):
            for error in st.session_state["pdf_errors"]:
                st.write(error)
    st.dataframe(
        frame[["title", "authors", "publication_name", "cover_date", "doi", "cited_by_count", "open_access"]],
        width="stretch",
        hide_index=True,
    )
else:
    st.info("Configura la búsqueda en la barra lateral para comenzar.")
