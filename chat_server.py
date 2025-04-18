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
    "ChatInput-8fGO2": {},
    "Milvus-tbjwD": {},
    "Prompt-Ciphp": {},
    "Memory-3Qm7y": {},
    "ParseData-FAWPR": {},
    "ChatOutput-TR3Kc": {},
    "OllamaEmbeddings-EarNo": {},
    "OllamaModel-RdzdC": {},
    "TextInput-uI2CW": {},
    "RedisChatMemory-03Kf3": {},
    "StoreMessage-MfcnZ": {},
    "StoreMessage-ar6CI": {}
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
        updated_tweaks["ChatInput-8fGO2"]["input_value"] = query
        updated_tweaks["TextInput-uI2CW"]["input_value"] = session_id

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
