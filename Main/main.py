import json

import streamlit as st
from PIL import Image

from Main.components.sidebar import sidebar
from Main.core import queries
from Main.core.queries import merge

from Main.ui import (
    wrap_doc_in_html,
    is_file_valid,
    is_open_ai_key_valid,
    display_file_read_error,
)

from Main.core.caching import bootstrap_caching

from Main.core.parsing import read_file
from Main.core.chunking import chunk_file
from Main.core.embedding import embed_files


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
        for attachment in attachment_docs:
            chunked_file = chunk_file(attachment, chunk_size=8000, chunk_overlap=0)
            chunked_files.append(chunked_file)

        data = queries.get_output_format()

        msg_file = ""
        all_data = []
        # parse email message
        for key, val in message_doc.metadata.items():
            msg_file += f"{key} : {val} \n"
        for doc in message_doc.docs:
            msg_file += doc.page_content + "\n"
        updated_data = queries.parse_document(data, msg_file)
        all_data.append(updated_data)
        # for chunk in chunks
        parsing_bar = st.progress(0.0, text="progress")
        i = 0
        for chunked_file in chunked_files:
            parsing_bar.progress(i + 1 / len(chunked_files) + 1, "Parsing chunks")
            i += 1
            for doc in chunked_file.docs:
                content = doc.page_content
                # insert data into dictionary
                updated_data = queries.parse_document(data, content)
                all_data.append(updated_data)
        st.session_state["OUTPUT_DATA"] = all_data
    except Exception as e:
        display_file_read_error(e)
elif not message_doc:
    st.stop()

if not is_file_valid(message_doc):
    st.stop()

if not is_open_ai_key_valid(openai_api_key):
    st.stop()

all_data = st.session_state["OUTPUT_DATA"]
# merge all results
out = {'Raw': all_data}
for data in all_data:
    merge(out, data)
# return download button to return output
output = json.dumps(out, indent=4)
# for key, val in updated_data.items():
#     output += f"{key} : {val} \n"
st.download_button('Download file', output, 'summary.txt')
