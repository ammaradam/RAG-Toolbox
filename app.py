import gc
import qdrant_client
import streamlit as st
from streamlit_pdf_viewer import pdf_viewer
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    Settings)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from utils.util import save_uploaded_file


Settings.embed_model = FastEmbedEmbedding(model_name="BAAI/bge-base-en-v1.5")

client = qdrant_client.QdrantClient(location=":memory:")
vector_store = QdrantVectorStore(client=client, collection_name="user_documents")
storage_context = StorageContext.from_defaults(vector_store=vector_store)


st.title("Chat with your Docs! :page_with_curl:")

def reset_chat():
    st.session_state.messages = []
    st.session_state.context = None
    gc.collect()

@st.cache_resource(show_spinner=False)
def load_data(file_path):
    with st.spinner(text="Loading and indexing your document! Ready in few minutes..."):
        reader = SimpleDirectoryReader(
            input_files=[file_path],
            required_exts=[".pdf"],
            recursive=True
        )
        docs = reader.load_data()
        index = VectorStoreIndex.from_documents(
            docs,
            storage_context=storage_context,
        )
    st.success("Ready to Chat!")
    return index

if "pdf_ref" not in st.session_state:
    st.session_state.pdf_ref = None

if "openai_model" not in st.session_state:
    st.session_state.openai_model = "gpt-3.5-turbo"

if "messages" not in st.session_state:
    reset_chat()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# main component
if prompt := st.chat_input("What's up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        streaming_response = st.session_state.chat_engine.stream_chat(prompt)

        for chunk in streaming_response.response_gen:
            full_response += chunk
            message_placeholder.markdown(full_response + " ")
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})

# sidebar component
with st.sidebar:
    st.button(
        label="New chat :repeat:",
        on_click=reset_chat,
        use_container_width=True
    )

    st.markdown("# Add your documents!")
    uploaded_file = st.file_uploader(
        label="Choose your `.pdf` file",
        type="pdf",
        key="pdf"
    )

    if st.session_state.pdf:
        st.session_state.pdf_ref = st.session_state.pdf
    
    if st.session_state.pdf_ref:
        if uploaded_file is not None:
            file_path = save_uploaded_file(uploaded_file)
            index = load_data(file_path)
            if "chat_engine" not in st.session_state.keys():
                st.session_state.chat_engine = index.as_chat_engine(
                    streaming=True,
                    similarity_top_k=5
                )

        st.markdown("# PDF Preview")

        binary_data = st.session_state.pdf_ref.getvalue()
        pdf_viewer(input=binary_data, width=500)