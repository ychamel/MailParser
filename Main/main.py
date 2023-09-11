import json

import streamlit as st
from PIL import Image

from Main.components.sidebar import sidebar
from Main.core import queries

from Main.ui import (
    is_file_valid,
    is_open_ai_key_valid,
    display_file_read_error,
)

from Main.core.caching import bootstrap_caching

from Main.core.parsing import read_file
from Main.core.chunking import chunk_file

EMBEDDING = "openai"
VECTOR_STORE = "faiss"
MODEL = "openai"

# For testing
# EMBEDDING, VECTOR_STORE, MODEL = ["debug"] * 3

# init
st.set_page_config(page_title="Synapse Email Parser", page_icon="📖", layout="wide")

# image
image = Image.open('Main/assets/logo.png')
st.image(image)
# Title
st.header("Synapse Email Parser")

# Enable caching for expensive functions
bootstrap_caching()

# sidebar
sidebar()

openai_api_key = st.session_state.get("OPENAI_API_KEY")

if not openai_api_key:
    st.warning(
        "please enter a password to access the app!"
    )

# uploader
message_file = st.file_uploader(
    "Upload the message File here.",
    type=["msg"],
    help="Scanned documents are not supported yet!",
)
attachment_files = st.file_uploader(
    "Upload attachments here,pdf, docx, or txt file are supported...",
    type=["pdf", "docx", "txt"],
    help="Scanned documents are not supported yet!",
    accept_multiple_files=True
)

if not message_file or not openai_api_key:
    st.stop()

update_btn = st.button('Update Files')

# get records
message_doc = st.session_state.get("MESSAGE")
attachment_docs = st.session_state.get("ATTACHMENTS")

# read files
if update_btn:
    try:
        # read message file
        message_doc = read_file(message_file)
        # read attatchment files
        attachment_docs = []
        for attachment_file in attachment_files:
            attachment_doc = read_file(attachment_file)
            attachment_docs.append(attachment_doc)
        # save to memory
        st.session_state["MESSAGE"] = message_doc
        st.session_state["ATTACHMENTS"] = attachment_docs

        # extract from chatgpt
        # chunk files into chunks readable by chatgpt
        chunked_files = []

        # chunk mail file
        chunked_file = chunk_file(message_doc, chunk_size=400, chunk_overlap=0)
        chunked_files.append(chunked_file)
        # chunk attachments
        for attachment in attachment_docs:
            chunked_file = chunk_file(attachment, chunk_size=400, chunk_overlap=0)
            chunked_files.append(chunked_file)

        data = queries.get_output_format()

        all_data = []
        updated_data = data

        # get text info from chunks and order into list
        contexts = []
        for chunked_file in chunked_files:
            for doc in chunked_file.docs:
                content = doc.page_content
                contexts.append(content)

        parsing_bar = st.progress(0.0, text="Analyzing Chunks")
        start = 0
        end = 0
        while end < len(contexts):
            prompt = None
            if len("\n\n---\n\n".join(contexts[start:end])) >= 3500:
                prompt = (
                    "\n\n---\n\n".join(contexts[start:end - 1])
                )
                start = end
            elif end == len(contexts) - 1:
                prompt = (
                    "\n\n---\n\n".join(contexts[start:end])
                )
            if prompt:
                updated_data = queries.parse_document(data, updated_data, prompt)
                parsing_bar.progress(min(end / len(contexts), 1.0), "Analyzing Chunks")
            end += 1
        parsing_bar.progress(1.0, "Analyzing Chunks")

        st.session_state["OUTPUT_DATA"] = updated_data
    except Exception as e:
        display_file_read_error(e)
elif not message_doc:
    st.stop()

if not is_file_valid(message_doc):
    st.stop()

if not is_open_ai_key_valid(openai_api_key):
    st.stop()

updated_data = st.session_state["OUTPUT_DATA"]

# return download button to return output
output = json.dumps(updated_data, indent=4)
# for key, val in updated_data.items():
#     output += f"{key} : {val} \n"
st.download_button('Download file', output, 'summary.txt')
