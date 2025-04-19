
from uuid import uuid4
import logging
import requests
import litserve as ls
import copy
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ready", "service": "chat_api"}

# Configuration
BASE_API_URL = "http://94.56.105.18:7898"
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
    "template": "Answer the user's question using only information from the provided context.\n- Focus solely on providing relevant information from the context.\n- Do not start with phrases like \"Based on the provided information\" or \"You've provided a text\".\n- If the context doesn't contain relevant information, follow the No-Information Protocol.\n- Present the information as if it's coming directly from Godiva Wealth Management.\n- Include the mandatory disclaimer at the end of every response.\n\nQuestion: {question}  \nContext: {context}  \nConversation History: {conversation_history}",
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
        logging.info(f"ChatLitAPI initialized on {device}")

    def decode_request(self, request):
        return {
            "query": request.get("query", ""),
            "session_id": request.get("session_id", str(uuid4()))
        }

    def predict(self, input_data):
        session_id = input_data["session_id"]
        query = input_data["query"]
        
        updated_tweaks = copy.deepcopy(TWEAKS)
        
        # Session-aware configuration
        updated_tweaks.update({
            "ChatInput-8fGO2": {
                **TWEAKS["ChatInput-8fGO2"],
                "input_value": query,
                "session_id": session_id
            },
            "RedisChatMemory-03Kf3": {
                **TWEAKS["RedisChatMemory-03Kf3"],
                "session_id": session_id,
                "key_prefix": f"godiva:{session_id}",
                "ttl": 172800  # 48-hour expiration
            },
            "Memory-3Qm7y": {
                **TWEAKS["Memory-3Qm7y"],
                "session_id": session_id
            }
        })

        payload = {
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": updated_tweaks
        }

        try:
            response = requests.post(
                f"{BASE_API_URL}/api/v1/run/{ENDPOINT}",
                json=payload,
                timeout=90
            )
            response.raise_for_status()
            
            
            return {"bot_response": processed_response}
            
        except Exception as e:
            logging.error(f"Session {session_id} error: {str(e)}")
            return {"error": "Service unavailable"}

    def encode_response(self, output):
        return {"response": output.get("bot_response", "Error")}

if __name__ == "__main__":
    server = ls.LitServer(
        ChatLitAPI(),
        accelerator="auto",
        timeout=300
    )
    server.run(port=7898)
