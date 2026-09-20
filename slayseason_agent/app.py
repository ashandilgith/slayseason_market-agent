import streamlit as st
import os
from dotenv import load_dotenv

# 1. Force dotenv to find the .env file in the current script's directory
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))

# 2. NOW it is safe to import LangChain and our internal modules
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver

from core.config import DB_URI
from agent.graph import get_graph_builder

st.set_page_config(page_title="Jarvis | SlaySeason", layout="centered")
st.title("SlaySeason Jarvis: Founder Beta")

TEST_TENANT_ID = "synthetic_shop_123"

#TEST_TENANT_ID = os.getenv("SHOPIFY_SHOP_DOMAIN")
THREAD_ID = "founder_session_01"

if "messages" not in st.session_state:
    st.session_state.messages = []

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat Input
if prompt := st.chat_input("E.g., What is our MER for January 2026?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Reconciling canonical data..."):
            
            # Use PostgresSaver as a context manager to ensure clean connections in Streamlit
            with PostgresSaver.from_conn_string(DB_URI) as checkpointer:
                # setup() safely creates checkpoint tables if they don't exist
                checkpointer.setup()
                
                # Compile the graph with persistent memory
                builder = get_graph_builder()
                jarvis_agent = builder.compile(checkpointer=checkpointer)
                
                config = {"configurable": {"thread_id": THREAD_ID}}
                
                # Execute graph
                response = jarvis_agent.invoke(
                    {
                        "messages": [HumanMessage(content=prompt)],
                        "tenant_id": TEST_TENANT_ID
                    },
                    config=config
                )
                
                # Extract and display the final AI message
                final_answer = response["messages"][-1].content
                st.markdown(final_answer)
                
    st.session_state.messages.append({"role": "assistant", "content": final_answer})