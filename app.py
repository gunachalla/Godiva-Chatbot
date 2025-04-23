import streamlit as st
import requests
import subprocess
import sys
import time
import threading
from uuid import uuid4  # Added for session ID generation

# CRITICAL: Initialize session state at the very beginning
# This ensures it's done before any other code runs
if "messages" not in st.session_state:
    st.session_state["messages"] = []  # Active conversation
    st.session_state["session_id"] = str(uuid4())  # Generate initial session ID

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []  # Archived conversations
    
if "template_used" not in st.session_state:
    st.session_state["template_used"] = False
    
if "pending_input" not in st.session_state:
    st.session_state["pending_input"] = None

# Set Streamlit page configuration.
st.set_page_config(
    page_title="DialogXR Godiva Chatbot",
    page_icon="dialogXR_Icon.png",
    layout="wide"
)

# Start the chat server with health checks
@st.cache_resource
def start_chat_api():
    try:
        # Start server with output capture
        proc = subprocess.Popen([sys.executable, "chat_server.py"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True)
        
        # Wait for server to become ready
        start_time = time.time()
        server_ready = False
        
        with st.spinner("Starting chat server..."):
            while (time.time() - start_time) < 30:  # 30-second timeout
                try:
                    # Try hitting health endpoint
                    response = requests.get("http://94.56.105.18:7898/health", timeout=2)
                    if response.status_code == 200:
                        server_ready = True
                        break
                except (requests.ConnectionError, requests.Timeout):
                    pass  # Server not ready yet
                time.sleep(2)  # Check every 2 seconds

        if not server_ready:
            # Show error details
            st.error(f"""
                ⚠️ Chat server failed to start within 30 seconds!
                Server status: {'running' if proc.poll() is None else 'stopped'}
                Error logs: {proc.stderr.read()}
            """)
            st.stop()
        
        return proc

    except Exception as e:
        st.error(f"🚨 Critical server error: {str(e)}")
        st.stop()

chat_api_proc = start_chat_api()

# API configuration
API_URL = "http://94.56.105.18:7898/predict"

# Double check session_id exists (defensive programming)
if "session_id" not in st.session_state or not st.session_state["session_id"]:
    st.session_state["session_id"] = str(uuid4())

# Template questions (only show if no chat has started)
template_questions = [
    "Can you explain Godiva's approach to creating tax-efficient retirement income strategies?",
    "What investment strategies does Godiva recommend for preserving wealth across generations?",
    "How does Godiva's wealth management service address inheritance tax planning?",
    "What are the key considerations in Godiva's pension transfer advisory process?",
    "How does Godiva balance risk and return in long-term investment portfolios?",
    "What tax-efficient savings vehicles does Godiva recommend for high-net-worth individuals?",
    "How does Godiva's trust planning service protect family assets?",
    "What ethical investment options are available through Godiva's portfolios?",
    "How does Godiva help clients navigate complex cross-border wealth management scenarios?",
    "What strategies does Godiva employ to safeguard investments during market volatility?"
]

# Optional custom CSS for template question styling.
st.markdown("""
    <style>
    .template-box {
        background-color: #018926;  /* NSPCC Accessible Green */
        padding: 12px;
        border-radius: 8px;
        font-size: 16px;
        font-style: italic;
        color: #FFFFFF;  /* White Font */
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar: Branding, logos, conversation history, and control buttons.
with st.sidebar:
    st.title("🤖 Godiva Wealth Management Chatbot")
    
    # Primary Branding: DialogXR logo.
    st.markdown("### Powered by:")
    st.image("dialogXR_Typography.png", width=300)
    
    st.markdown(
        """<p style="margin-top:1rem; margin-bottom:0.5rem; font-size: 1.1rem; font-weight: bold;">Designed by</p>""",
        unsafe_allow_html=True
    )
    st.image("Bikal_logo.svg", width=120)
    
    st.markdown("### Conversation History")
    if st.session_state["chat_history"]:
        for idx, conv in enumerate(st.session_state["chat_history"], 1):
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
                        st.session_state["messages"] = conv.copy()
                        st.session_state["session_id"] = str(uuid4())  # New session when loading old chat
                with col2:
                    if st.button("Delete", key=f"delete_{idx}"):
                        st.session_state["chat_history"].pop(idx - 1)
                        st.rerun()
    else:
        st.info("No previous conversations stored.")
    
    if st.button("🆕 New Chat"):
        if st.session_state["messages"]:
            st.session_state["chat_history"].append(st.session_state["messages"].copy())
        # Reset conversation AND generate new session ID
        st.session_state["messages"] = []
        st.session_state["session_id"] = str(uuid4())
        st.session_state["template_used"] = False
        st.rerun()

# Main chat interface.
st.markdown("### Welcome to Godiva Chatbot!")

# Show template questions only if no chat has started.
if not st.session_state["messages"] and not st.session_state["template_used"]:
    st.markdown("<div class='template-box'><strong>Suggested Questions:</strong></div>", unsafe_allow_html=True)
    
    cols = st.columns(len(template_questions) if len(template_questions) < 5 else 5)
    for idx, question in enumerate(template_questions):
        if cols[idx % 5].button(question, key=f"template_{idx}", help="Click to ask this question", use_container_width=True):
            st.session_state["pending_input"] = question
            st.session_state["template_used"] = True
            st.rerun()

# Display existing chat messages.
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Check if a template question was selected and process it.
if st.session_state["pending_input"]:
    user_input = st.session_state["pending_input"]
    st.session_state["pending_input"] = None
else:
    user_input = st.chat_input("Ask me anything...")

# Process user input
if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Create a placeholder for the assistant's response.
    assistant_message = st.chat_message("assistant")
    response_placeholder = assistant_message.empty()

    # Get the session ID outside the thread
    current_session_id = st.session_state["session_id"]
    print(f"Using session ID (main thread): {current_session_id}")                # Debugging line 

    # Function to fetch API response.
    response_container = {"response": None}
    def fetch_response(session_id):
        try:
            print(f"Using session ID (in thread): {session_id}")                  # Debugging line
            
            response = requests.post(
                API_URL,
                json={
                    "query": user_input,
                    "session_id": session_id
                },
                timeout=90
            )
            response.raise_for_status()
            response_container["response"] = response.json().get("response", "Service is currently under maintenance. Please try again later.")
        except Exception as e:
            response_container["response"] = f"Error: {str(e)}"

    # Start API request in a separate thread.
    response_thread = threading.Thread(target=fetch_response, args=(current_session_id,))
    response_thread.start()

    # Show spinners
    with response_placeholder:
        with st.spinner("Analyzing the question..."):
            time.sleep(3)
        with st.spinner("Thinking..."):
            time.sleep(3)
        with st.spinner("Constructing response..."):
            time.sleep(2)

        # Wait for API response
        generating_spinner = response_placeholder.empty()
        while response_thread.is_alive():
            generating_spinner.write("⏳ Generating response...")
            time.sleep(0.5)
        generating_spinner.empty()

    # Display response
    response_thread.join()
    bot_response = response_container["response"]
    st.session_state["messages"].append({"role": "assistant", "content": bot_response})
    response_placeholder.write(bot_response)

    st.rerun()
