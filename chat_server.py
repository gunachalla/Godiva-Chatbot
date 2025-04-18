from uuid import uuid4
import logging
import requests
import litserve as ls
import copy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import warnings

# Suppress Streamlit warnings
warnings.filterwarnings("ignore", message="missing ScriptRunContext! This warning can be ignored when running in bare mode.")
warnings.filterwarnings("ignore", category=UserWarning, module="streamlit.runtime.scriptrunner.script_runner")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "ready", "service": "chat_api"}

# Configuration
BASE_API_URL = "http://94.56.105.18:7898"
FLOW_ID = "e1f7e7f9-9f59-4c88-b64e-a6430836f311"
ENDPOINT = "dxr-rag-godiva"

TWEAKS = {
  "ChatInput-8fGO2": {
    "files": "",
    "background_color": "",
    "chat_icon": "",
    "input_value": "",
    "sender": "User",
    "sender_name": "User",
    "session_id": "",
    "should_store_message": True,
    "text_color": ""
  },
  "Milvus-tbjwD": {
    "collection_description": "web scraped data from godiva",
    "collection_name": "godiva_json",
    "connection_args": {},
    "consistency_level": "Strong",
    "drop_old": False,
    "index_params": {},
    "number_of_results": 3,
    "password": "Milvus Token",
    "primary_field": "pk",
    "search_params": {},
    "search_query": "",
    "text_field": "content",
    "timeout": None,
    "uri": "Milvus URL",
    "vector_field": "vector"
  },
  "Prompt-Ciphp": {
    "template": "Answer the user's question using only information from the provided context.\n- Focus solely on providing relevant information from the context.\n- Do not mention or reference the context itself in your answer.\n- Do not start with phrases like \"Based on the provided information\" or \"You've provided a text\".\n- If the context doesn't contain relevant information, follow the No-Information Protocol.\n- Present the information as if it's coming directly from Godiva Wealth Management.\n- Include the mandatory disclaimer at the end of every response.\n\nQuestion: {question}  \nContext: {context}  \nConversation History: {conversation_history}",
    "tool_placeholder": "",
    "question": "",
    "conversation_history": "",
    "context": ""
  },
  "Memory-3Qm7y": {
    "n_messages": 100,
    "order": "Ascending",
    "sender": "Machine and User",
    "sender_name": "",
    "session_id": "",
    "template": "{sender_name}: {text}"
  },
  "ParseData-FAWPR": {
    "sep": "\n",
    "template": "{text} , {title}"
  },
  "ChatOutput-TR3Kc": {
    "background_color": "",
    "chat_icon": "",
    "clean_data": False,
    "data_template": "{text}",
    "sender": "Machine",
    "sender_name": "AI Assistant",
    "session_id": "",
    "should_store_message": True,
    "text_color": ""
  },
  "OllamaEmbeddings-EarNo": {
    "base_url": "Ollama URL",
    "model_name": "nomic-embed-text:latest"
  },
  "OllamaModel-RdzdC": {
    "base_url": "Ollama URL",
    "format": "",
    "input_value": "",
    "metadata": {},
    "mirostat": "Disabled",
    "mirostat_eta": None,
    "mirostat_tau": None,
    "model_name": "llama3.3:latest",
    "num_ctx": None,
    "num_gpu": None,
    "num_thread": None,
    "repeat_last_n": None,
    "repeat_penalty": None,
    "stop_tokens": "",
    "stream": False,
    "system": "",
    "system_message": "# Godiva Wealth Management AI Assistant System Prompt  \n\n## Role  \nYou are an AI assistant representing **Godiva Wealth Management** (developed by BIKAL TECH UK), providing **evidence-based financial guidance** strictly from Godiva's official documents. Specializations:  \n- Pensions & Retirement Planning  \n- Investments & Savings Strategies  \n- Wealth Management, Inheritance, Tax & Trust Planning  \n\n---\n## Guidelines  \n### 1. Evidence-Based Responses  \n- **Only use verified information** from Godiva's documents or knowledge base.  \n- **Never speculate, infer, or use external knowledge.**  \n- **Never reference the existence of \"provided context\" or \"documents\" in your responses.**\n- Example: If asked about \"ETFs\" with no supporting documents, respond: *\"No relevant information found.\"*  \n\n### 2. Source Attribution  \n- **Predefined Hyperlinks** (use where applicable):  \n  - [Pensions & Retirement Planning](https://godiva-wealth.management/pensions-and-retirement/)  \n  - [Investments & Savings Strategies](https://godiva-wealth.management/investments-savings/)  \n  - [Tax & Trust Planning](https://godiva-wealth.management/tax-and-trust-planning/)  \n- For internal documents:  \n  *\"Based on Godiva Wealth Management's [Document Title].\"*  \n\n### 3. Scope Enforcement  \n- **Decline non-financial requests immediately**:  \n  > *\"I specialize in Godiva's financial guidance only. For other topics, contact BIKAL TECH UK.\"*  \n- **Never engage with sensitive/private data** (e.g., account details).  \n\n### 4. No-Information Protocol  \n- If no relevant documents exist:  \n  > *\"No information is available. Contact Godiva at [01926 298567](tel:+441926298567) or [info@godiva-wealth.management](mailto:info@godiva-wealth.management).\"*  \n\n### 5. Mandatory Disclaimer  \nInclude in **every response**:  \n> *\"This is general information, not personalised advice. Consult a Godiva advisor for your situation.\"*  \n\n---\n## Contact Information  \n- **Telephone**: [01926 298567](tel:+441926298567)  \n- **Email**: [info@godiva-wealth.management](mailto:info@godiva-wealth.management)  \n- **Business Hours**: Monday–Friday, 09:00–17:00  \n\n---\n## Examples  \n### User: How should I invest $5,000?  \n**AI**: Godiva Wealth Management tailors strategies to individual risk profiles. For lump-sum investments, see [Investments & Savings Strategies](https://godiva-wealth.management/investments-savings/) or contact an advisor at [01926 298567](tel:+441926298567). *This is general information, not personalised advice.*  \n\n### User: Write a retirement poem.  \n**AI**: I specialize in Godiva's financial guidance. For creative requests, contact BIKAL TECH UK.  \n\n### User: What's Godiva's ISA policy?  \n**AI**: No relevant information found. Contact Godiva at [01926 298567](tel:+441926298567).",
    "tags": "",
    "temperature": 0.18,
    "template": "",
    "tfs_z": None,
    "timeout": None,
    "tool_model_enabled": False,
    "top_k": None,
    "top_p": None,
    "verbose": False
  },
  "TextInput-uI2CW": {
    "input_value": ""
  },
  "RedisChatMemory-03Kf3": {
    "database": "9",
    "host": "Redis URL",
    "key_prefix": "",
    "password": "",
    "port": 6380,
    "session_id": "",
    "username": ""
  },
  "StoreMessage-MfcnZ": {
    "message": "",
    "sender": "",
    "sender_name": "",
    "session_id": ""
  },
  "StoreMessage-ar6CI": {
    "message": "",
    "sender": "",
    "sender_name": "",
    "session_id": ""
  }
}

logging.basicConfig(level=logging.INFO)

class ChatLitAPI(ls.LitAPI):
    def setup(self, device):
        self.device = device
        logging.info(f"Initialized chat API on {device}")

    def decode_request(self, request):
        session_id = request.get("session_id")
        query = request.get("query", "").strip()
        
        if not session_id:
            logging.error("Missing session ID in request")
            return {"error": "Session ID required"}
            
        if not query:
            logging.error("Empty query received")
            return {"error": "Query cannot be empty"}
            
        return {
            "query": query,
            "session_id": session_id
        }

    def predict(self, input_data):
        if "error" in input_data:
            return input_data
            
        query = input_data["query"]
        session_id = input_data["session_id"]
        
        updated_tweaks = copy.deepcopy(TWEAKS)
        
        # Set session ID across all relevant components
        updated_tweaks["TextInput-uI2CW"]["input_value"] = session_id
        updated_tweaks["RedisChatMemory-03Kf3"]["session_id"] = session_id
        updated_tweaks["Memory-3Qm7y"]["session_id"] = session_id
        updated_tweaks["ChatInput-8fGO2"]["session_id"] = session_id
        updated_tweaks["ChatOutput-TR3Kc"]["session_id"] = session_id
        updated_tweaks["StoreMessage-MfcnZ"]["session_id"] = session_id
        updated_tweaks["StoreMessage-ar6CI"]["session_id"] = session_id
        
        # Set query in appropriate components
        updated_tweaks["ChatInput-8fGO2"]["input_value"] = query
        updated_tweaks["Prompt-Ciphp"]["question"] = query

        payload = {
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": updated_tweaks,
            "session_id": session_id
        }

        api_url = f"{BASE_API_URL}/api/v1/run/{ENDPOINT}"
        
        try:
            response = requests.post(api_url, json=payload, timeout=90)
            response.raise_for_status()
            response_data = response.json()
            
            if "outputs" in response_data:
                return {"response": response_data["outputs"][0]["outputs"][0]["results"]["message"]["text"]}
            return {"response": "No valid response found."}

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error: {str(e)}")
            return {"error": "Service unavailable. Please try again later."}
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return {"error": "An unexpected error occurred."}

    def encode_response(self, output):
        return output

if __name__ == "__main__":
    server = ls.LitServer(
        ChatLitAPI(),
        accelerator="auto",
        max_batch_size=1,
        timeout=300
    )
    server.run(port=7898)
