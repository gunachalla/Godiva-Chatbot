import streamlit as st
import requests
import subprocess
import sys
import time
import threading
import uuid

# Set Streamlit page configuration
st.set_page_config(
    page_title="DialogXR Godiva Chatbot",
    page_icon="dialogXR_Icon.png",
    layout="wide"
)

# Server management functions
@st.cache_resource
def start_chat_api():
    try:
        proc = subprocess.Popen([sys.executable, "chat_server.py"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        
        start_time = time.time()
        server_ready = False
        
        with st.spinner("🚀 Starting chat server..."):
            while (time.time() - start_time) < 30:
                try:
                    response = requests.get("http://localhost:7898/health", timeout=2)
                    if response.status_code == 200:
                        server_ready = True
                        break
                except (requests.ConnectionError, requests.Timeout):
                    pass
                time.sleep(2)

        if not server_ready:
            st.error(f"""
                ⚠️ Server startup failed!
                Status: {'running' if proc.poll() is None else 'stopped'}
                Error: {proc.stderr.read()}
            """)
            st.stop()
        
        return proc

    except Exception as e:
        st.error(f"🚨 Critical error: {str(e)}")
        st.stop()

chat_api_proc = start_chat_api()

# API configuration
API_URL = "http://localhost:7898/predict"

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "template_used" not in st.session_state:
    st.session_state.template_used = False
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
if "session_map" not in st.session_state:
    st.session_state.session_map = {}  # {conversation_index: session_id}

# Template questions
template_questions = [
    "Can you explain Godiva's approach to creating tax-efficient retirement income strategies?",
    "What investment strategies does Godiva recommend for preserving wealth across generations?",
    "How does Godiva's wealth management service address inheritance tax planning?",
    # ... (other template questions)
]

# UI styling
st.markdown("""
    <style>
    .template-box {
        background-color: #018926;
        padding: 12px;
        border-radius: 8px;
        color: #FFFFFF;
        text-align: center;
        margin-bottom: 10px;
    }
    .stButton>button {
        width: 100%;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar components
with st.sidebar:
    st.title("🤖 Godiva Wealth Management Chatbot")
    st.image("dialogXR_Typography.png", width=300)
    st.image("Bikal_logo.svg", width=120)
    
    st.markdown("### Conversation History")
    if st.session_state.chat_history:
        for idx, (conv, session_id) in enumerate(st.session_state.chat_history, 1):
            with st.expander(f"Conversation {idx}", expanded=False):
                preview = conv[-2:] if len(conv) >= 2 else conv
                preview_html = "<div style='font-size:12px; max-width:200px;'>"
                for msg in preview:
                    preview_html += f"<p><strong>{msg['role'].capitalize()}:</strong> {msg['content']}</p>"
                preview_html += "</div>"
                st.markdown(preview_html, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Load", key=f"load_{idx}"):
                        st.session_state.messages = conv.copy()
                        st.session_state.current_session_id = session_id
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"delete_{idx}"):
                        del st.session_state.chat_history[idx-1]
                        del st.session_state.session_map[idx]
                        st.rerun()
    else:
        st.info("No previous conversations")
    
    if st.button("🆕 New Chat"):
        if st.session_state.messages:
            new_idx = len(st.session_state.chat_history) + 1
            st.session_state.chat_history.append(
                (st.session_state.messages.copy(), 
                 st.session_state.current_session_id)
            )
            st.session_state.session_map[new_idx] = st.session_state.current_session_id
        
        st.session_state.messages = []
        st.session_state.template_used = False
        st.session_state.current_session_id = str(uuid.uuid4())
        st.rerun()

# Main chat interface
st.markdown("### Welcome to Godiva Chatbot")

# Show template questions if no active conversation
if not st.session_state.messages and not st.session_state.template_used:
    st.markdown("<div class='template-box'><strong>Suggested Questions:</strong></div>", 
                unsafe_allow_html=True)
    
    cols = st.columns(5)
    for idx, question in enumerate(template_questions):
        if cols[idx % 5].button(question, key=f"template_{idx}"):
            st.session_state.pending_input = question
            st.session_state.template_used = True
            st.rerun()

# Display messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Process input
if st.session_state.get("pending_input"):
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None
else:
    user_input = st.chat_input("Ask me anything...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.write(user_input)

    assistant_message = st.chat_message("assistant")
    response_placeholder = assistant_message.empty()

    # API request handling
    response_container = {"response": None}
    
    def fetch_response():
        try:
            payload = {
                "query": user_input,
                "session_id": st.session_state.current_session_id
            }
            
            response = requests.post(
                API_URL, 
                json=payload, 
                timeout=90
            )
            
            if response.status_code == 200:
                response_container["response"] = response.json().get("response", 
                    "No response received")
            else:
                response_container["response"] = "Service temporary unavailable"

        except Exception as e:
            response_container["response"] = "Connection error. Please try again."

    # Response animation
    with response_placeholder:
        with st.spinner("🔍 Analyzing question..."):
            time.sleep(1.5)
        with st.spinner("💭 Processing..."):
            time.sleep(2)
        with st.spinner("📝 Generating response..."):
            time.sleep(1)

    # Start request thread
    response_thread = threading.Thread(target=fetch_response)
    response_thread.start()
    
    # Wait for completion
    response_thread.join()
    
    # Display final response
    bot_response = response_container["response"]
    st.session_state.messages.append({"role": "assistant", "content": bot_response})
    response_placeholder.write(bot_response)
    
    st.rerun()
