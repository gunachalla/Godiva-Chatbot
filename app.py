
import streamlit as st
import requests
import subprocess
import sys
import time
import threading
import uuid
import logging
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("godiva_app.log")
    ]
)
logger = logging.getLogger("godiva_app")

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
        logger.info("Starting chat server process...")
        proc = subprocess.Popen(
            [sys.executable, "chat_server.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        start_time = time.time()
        server_ready = False
        
        with st.spinner("🚀 Starting chat server..."):
            while (time.time() - start_time) < 60:  # Increased timeout to 60 seconds
                try:
                    logger.info("Checking if server is ready...")
                    response = requests.get("http://94.56.105.18:7898/health", timeout=5)
                    if response.status_code == 200:
                        server_ready = True
                        logger.info("Server is ready!")
                        break
                except (requests.ConnectionError, requests.Timeout) as e:
                    logger.warning(f"Server not ready yet: {str(e)}")
                    pass
                time.sleep(2)

        if not server_ready:
            stderr_content = proc.stderr.read() if proc.stderr else "No error output"
            logger.error(f"Server startup failed: {stderr_content}")
            st.error(f"""
                ⚠️ Server startup failed!
                Status: {'running' if proc.poll() is None else 'stopped'}
                Error: {stderr_content[:500]}
            """)
            st.stop()
        
        return proc

    except Exception as e:
        logger.critical(f"Critical error starting server: {str(e)}")
        st.error(f"🚨 Critical error: {str(e)}")
        st.stop()

# Start the chat server
chat_api_proc = start_chat_api()

# API configuration
API_URL = "http://94.56.105.18:7898/predict"
API_TIMEOUT = 120  # Increased timeout

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "template_used" not in st.session_state:
    st.session_state.template_used = False
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    logger.info(f"Created new session ID: {st.session_state.current_session_id}")
if "session_map" not in st.session_state:
    st.session_state.session_map = {}  # {conversation_index: session_id}
if "error_count" not in st.session_state:
    st.session_state.error_count = 0

# Template questions
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
    .error-message {
        color: #FF4B4B;
        background-color: #FFE5E5;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .success-message {
        color: #0BAB64;
        background-color: #E7F9ED;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar components
with st.sidebar:
    st.title("🤖 Godiva Wealth Management Chatbot")
    st.image("dialogXR_Typography.png", width=300)
    st.image("Bikal_logo.svg", width=120)
    
    # Debug tools (collapsible)
    with st.expander("Debug Info", expanded=False):
        st.text(f"Session ID: {st.session_state.current_session_id}")
        st.text(f"Messages: {len(st.session_state.messages)}")
        st.text(f"API URL: {API_URL}")
        if st.button("Test API Connection"):
            try:
                health_response = requests.get("http://localhost:7898/health", timeout=5)
                st.success(f"API Status: {health_response.status_code} - {health_response.text}")
            except Exception as e:
                st.error(f"API Error: {str(e)}")
    
    st.markdown("### Conversation History")
    if st.session_state.chat_history:
        for idx, (conv, session_id) in enumerate(st.session_state.chat_history, 1):
            with st.expander(f"Conversation {idx}", expanded=False):
                preview = conv[-2:] if len(conv) >= 2 else conv
                preview_html = "<div style='font-size:12px; max-width:200px;'>"
                for msg in preview:
                    preview_html += f"<p><strong>{msg['role'].capitalize()}:</strong> {msg['content'][:50]}...</p>"
                preview_html += "</div>"
                st.markdown(preview_html, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Load", key=f"load_{idx}"):
                        st.session_state.messages = conv.copy()
                        st.session_state.current_session_id = session_id
                        logger.info(f"Loaded conversation {idx} with session ID: {session_id}")
                        st.rerun()
                with col2:
                    if st.button("Delete", key=f"delete_{idx}"):
                        del st.session_state.chat_history[idx-1]
                        if idx in st.session_state.session_map:
                            del st.session_state.session_map[idx]
                        logger.info(f"Deleted conversation {idx}")
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
            logger.info(f"Saved current conversation to history with index {new_idx}")
        
        st.session_state.messages = []
        st.session_state.template_used = False
        st.session_state.current_session_id = str(uuid.uuid4())
        logger.info(f"Created new chat with session ID: {st.session_state.current_session_id}")
        st.session_state.error_count = 0
        st.rerun()

# Main chat interface
st.markdown("### Welcome to Godiva Chatbot")

# Show template questions if no active conversation
if not st.session_state.messages and not st.session_state.template_used:
    st.markdown("<div class='template-box'><strong>Suggested Questions:</strong></div>", 
                unsafe_allow_html=True)
    
    cols = st.columns(len(template_questions))
    for idx, question in enumerate(template_questions):
        if cols[idx].button(question, key=f"template_{idx}"):
            st.session_state.pending_input = question
            st.session_state.template_used = True
            logger.info(f"Selected template question: {question[:50]}...")
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
    logger.info(f"Received user input: {user_input[:50]}...")
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.write(user_input)

    assistant_message = st.chat_message("assistant")
    response_placeholder = assistant_message.empty()

    # API request handling
    response_container = {"response": None, "error": None}
    
    def fetch_response():
        try:
            payload = {
                "query": user_input,
                "session_id": st.session_state.current_session_id
            }
            
            logger.info(f"Sending request to API with session ID: {st.session_state.current_session_id}")
            response = requests.post(
                API_URL, 
                json=payload, 
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                try:
                    response_json = response.json()
                    response_container["response"] = response_json.get("response", 
                        "No response received")
                    logger.info(f"Received API response: {response_container['response'][:50]}...")
                    st.session_state.error_count = 0  # Reset error count on success
                except json.JSONDecodeError as e:
                    error_msg = f"Invalid JSON response: {str(e)}"
                    logger.error(error_msg)
                    response_container["error"] = error_msg
                    st.session_state.error_count += 1
            else:
                error_msg = f"Service error: {response.status_code} - {response.text[:100]}"
                logger.error(error_msg)
                response_container["error"] = error_msg
                st.session_state.error_count += 1

        except requests.ConnectionError as e:
            error_msg = f"Connection error: {str(e)}"
            logger.error(error_msg)
            response_container["error"] = error_msg
            st.session_state.error_count += 1
        except requests.Timeout as e:
            error_msg = f"Request timeout: {str(e)}"
            logger.error(error_msg)
            response_container["error"] = error_msg
            st.session_state.error_count += 1
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            response_container["error"] = error_msg
            st.session_state.error_count += 1

    # Response animation
    with response_placeholder:
        with st.spinner("🔍 Analyzing question..."):
            time.sleep(1)
        with st.spinner("💭 Processing..."):
            time.sleep(1)
        with st.spinner("📝 Generating response..."):
            time.sleep(0.5)

    # Start request thread
    response_thread = threading.Thread(target=fetch_response)
    response_thread.start()
    
    # Wait for completion
    response_thread.join()
    
    # Check for errors and display response
    if response_container["error"]:
        error_message = response_container["error"]
        
        # Suggest restart if multiple consecutive errors
        if st.session_state.error_count >= 3:
            error_message += "\n\nTry starting a new conversation to reset the connection."
        
        with response_placeholder:
            st.error(error_message)
        
        # Only add error to message history if it's a user-facing issue
        if "Connection error" in error_message or "Service unavailable" in error_message:
            st.session_state.messages.append({
                "role": "assistant", 
                "content": f"Sorry, I'm having trouble connecting to the service. Please try again later."
            })
    else:
        # Display final response
        bot_response = response_container["response"]
        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        response_placeholder.write(bot_response)
    
    # Rerun only if there's no error (to avoid endless error loops)
    if not response_container["error"]:
        st.rerun()
