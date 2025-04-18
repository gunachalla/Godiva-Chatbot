from uuid import uuid4
import logging
import requests
import litserve as ls
import copy
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ready", "service": "chat_api"}

# Use the same configuration as your original API
BASE_API_URL = "http://94.56.105.18:7898"  # Consider changing to internal IP when running locally
FLOW_ID = "e1f7e7f9-9f59-4c88-b64e-a6430836f311"
ENDPOINT = "dxr-rag-godiva"

# Use the original TWEAKS configuration from your API
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
        logging.info(f"ChatLitAPI initialized on device: {device}")

    def decode_request(self, request):
        # Extract query and session_id from request
        query = request.get("query", "")
        # Get session ID from request or generate a new one
        session_id = request.get("session_id", str(uuid4()))
        
        logging.info(f"Received request with session_id: {session_id}")
        
        return {
            "query": query,
            "session_id": session_id
        }

    def predict(self, input_data):
        query = input_data.get("query", "")
        session_id = input_data.get("session_id", "")
        
        logging.info(f"Processing query with session_id: {session_id}")
        
        # Update tweaks with query and session ID
        updated_tweaks = copy.deepcopy(TWEAKS)
        updated_tweaks["ChatInput-8fGO2"].update({
            "input_value": query,
            "session_id": session_id  # Pass session ID to Langflow
        })
        
        payload = {
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": updated_tweaks,
            "session_id": session_id  # Include session ID at top level too
        }
        
        api_url = f"{BASE_API_URL}/api/v1/run/{ENDPOINT}"
        
        try:
            logging.info(f"Sending to Langflow with session_id: {session_id}")
            response = requests.post(api_url, json=payload, timeout=90)
            response.raise_for_status()
            response_data = response.json()
            
            logging.info(f"Received response from Langflow for session_id: {session_id}")
            
            # Extract the response text
            if "outputs" in response_data:
                return {"bot_response": response_data["outputs"][0]["outputs"][0]["results"]["message"]["text"]}
            return {"bot_response": "No valid response found."}
            
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error with session_id {session_id}: {str(e)}")
            return {"error": "Service unavailable. Please try again later."}
        except Exception as e:
            logging.error(f"Unexpected error with session_id {session_id}: {str(e)}")
            return {"error": "An unexpected error occurred."}

    def encode_response(self, output):
        if "error" in output:
            return {"response": output["error"]}
        return {"response": output.get("bot_response", "No response available.")}

if __name__ == "__main__":
    server = ls.LitServer(ChatLitAPI(), accelerator="auto", max_batch_size=1)
    server.run(port=7898)
