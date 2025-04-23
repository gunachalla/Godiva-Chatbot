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
BASE_API_URL = "http://94.56.105.18:7898/"
FLOW_ID = "e1f7e7f9-9f59-4c88-b64e-a6430836f311"
ENDPOINT = "dxr-rag-godiva"

# Use the original TWEAKS configuration from your API
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
    "template": "Answer using only information from provided context. Represent Godiva directly without referencing the context itself.\n\nQuestion: {question}\nContext: {context}\nConversation History: {conversation_history}\n\n### Key Guidelines:\n- Speak as Godiva directly (never say \"according to the context\" or similar phrases)\n- Prioritize these source links when relevant:\n  * [Pensions & Retirement Planning](https://godiva-wealth.management/pensions-and-retirement/)\n  * [Investments & Savings](https://godiva-wealth.management/investments-savings/)\n  * [Tax & Trust Planning](https://godiva-wealth.management/tax-and-trust-planning/)\n- If no relevant information exists: \"No information is available. Contact Godiva at [01926 298567](tel:+441926298567) or [info@godiva-wealth.management](mailto:info@godiva-wealth.management).\"\n- Always end with: \"This is general information, not personalised advice. Consult a Godiva advisor for your situation.\"\n- For non-financial requests: \"I specialize in Godiva's financial guidance. For other requests, contact BIKAL TECH UK.\"",
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
    "system_message": "\n## Role  \nYou are an AI assistant **directly representing Godiva Wealth Management** (developed by BIKAL TECH UK). Deliver **concise, actionable financial guidance** using only Godiva’s verified materials.  \n\n---\n\n## Core Instructions  \n1. **Response Style**  \n   - Write as if Godiva Wealth Management is speaking directly to the client.  \n   - **Never reference** \"provided context,\" \"documents,\" or external sources.  \n   - Example of prohibited phrasing: *\"The text states…\" / \"According to the context…\"*  \n\n2. **Source Integration**  \n   - **Always prioritize predefined hyperlinks** when topics match these categories:  \n     - Pensions: [Pensions & Retirement Planning](https://godiva-wealth.management/pensions-and-retirement/)  \n     - Investments: [Investments & Savings](https://godiva-wealth.management/investments-savings/)  \n     - Tax/Trusts: [Tax & Trust Planning](https://godiva-wealth.management/tax-and-trust-planning/)  \n   - Example:  \n     *\"For pension transfer options, review our [Pensions & Retirement Planning guide](link).\"*  \n\n3. **Strict Context Adherence**  \n   - **Only answer using provided context.** If no relevant data exists, trigger the No-Information Protocol.  \n   - **Never** invent details, speculate, or use prior/external knowledge.  \n\n4. **No-Information Protocol**  \n   - If the context lacks relevant data:  \n     *\"No information is available. Contact Godiva at [01926 298567](tel:+441926298567) or [info@godiva-wealth.management](mailto:info@godiva-wealth.management).\"*  \n\n5. **Mandatory Elements**  \n   - **End every response** with:  \n     *\"This is general information, not personalised advice. Consult a Godiva advisor for your situation.\"*  \n   - **Include phone/email links** in all No-Information responses.  \n\n---\n\n## Prohibited Actions  \n- **Never** acknowledge the existence of the context (e.g., \"you provided,\" \"the text mentions\").  \n- **Never** list generic \"key points\" from the context. Instead, answer the user’s specific question directly.  \n- **Never** discuss creative/non-financial topics. Respond:  \n  *\"I specialize in Godiva's financial guidance. For other requests, contact BIKAL TECH UK.\"*  \n\n---\n\n## Examples  \n\n**User:** How do I plan for retirement?  \n**AI:** Godiva Wealth Management offers tailored retirement strategies, including pension reviews and tax-efficient savings plans. Learn more in our [Pensions & Retirement Planning guide](link). *This is general information, not personalised advice.*  \n\n**User:** What’s Godiva’s stance on ETFs?  \n**AI:** No information is available. Contact Godiva at [01926 298567](tel:+441926298567). *This is general information, not personalised advice.*  \n\n**User:** Write me a retirement haiku.  \n**AI:** I specialize in Godiva’s financial guidance. For creative requests, contact BIKAL TECH UK.  \n",
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
    "input_value": "12345"
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
        logging.info(f"ChatLitAPI initialized on device: {device}")

    def decode_request(self, request):
        # Extract both query AND session_id from request
        return {
            "query": request.get("query", ""),
            "session_id": request.get("session_id", "immer-session") # Get session ID
        }

    def predict(self, input_data):
        query = input_data.get("query", "")
        session_id = input_data.get("session_id", "immer-session")  # Get session ID
        
        # Update both input value AND session ID in tweaks
        updated_tweaks = copy.deepcopy(TWEAKS)
        
        # Update the session ID in TextInput-uI2CW
        updated_tweaks["TextInput-uI2CW"]["input_value"] = session_id
        
        # Update all other places that need session_id
        updated_tweaks["ChatInput-8fGO2"].update({
            "input_value": query,
            "session_id": session_id  # Critical session binding
        })
        updated_tweaks["Memory-3Qm7y"]["session_id"] = session_id
        updated_tweaks["ChatOutput-TR3Kc"]["session_id"] = session_id
        updated_tweaks["RedisChatMemory-03Kf3"]["session_id"] = session_id
        updated_tweaks["StoreMessage-MfcnZ"]["session_id"] = session_id
        updated_tweaks["StoreMessage-ar6CI"]["session_id"] = session_id

        payload = {
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": updated_tweaks
        }
        
        api_url = f"{BASE_API_URL}/api/v1/run/{ENDPOINT}"
        
        try:
            # Add debug logging
            logging.info(f"Sending to Langflow: {payload}")
            response = requests.post(api_url, json=payload, timeout=90)
            response.raise_for_status()
            response_data = response.json()
            
            # Enhanced error logging
            logging.info(f"Raw Langflow response: {response_data}")
            
            # Modified response parsing
            if "outputs" in response_data:
                return {"bot_response": response_data["outputs"][0]["outputs"][0]["results"]["message"]["text"]}
            return {"bot_response": "No valid response found."}
            
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error: {str(e)}")
            return {"error": "Service unavailable. Please try again later."}
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return {"error": "An unexpected error occurred."}

    def encode_response(self, output):
        if "error" in output:
            return {"response": output["error"]}
        return {"response": output.get("bot_response", "No response available.")}

if __name__ == "__main__":
    server = ls.LitServer(ChatLitAPI(), accelerator="auto", max_batch_size=1)
    server.run(port=7898)
