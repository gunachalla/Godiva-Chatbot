from uuid import uuid4
import logging
import requests
import litserve as ls
import copy

# Use the same configuration as your original API
BASE_API_URL = "http://94.56.105.18:7898"
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
    "template": "Answer the user’s question using the most recent and relevant information from the provided context.\n\n- Prioritise the current context over previous conversation history.\n- Use conversation history only if it directly supports the current topic or entity (e.g., named child or case).\n- If the conversation has shifted to a new case, do not carry over assumptions from earlier discussions.\n- If unclear, ask the user for clarification instead of guessing.\n\nQuestion: {question}  \nContext: {context}  \nConversation History: {conversation_history}",
    "tool_placeholder": "",
    "question": "",
    "conversation_history": "",
    "context": ""
  },
  "Memory-3Qm7y": {
    "n_messages": 1000,
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
    "system_message": "<Role>  \nYou are a highly intelligent AI assistant representing *Godiva Wealth Management, developed by **BIKAL TECH UK* using advanced AI technology. Your core responsibility is to support individuals and businesses by providing *independent, evidence-based financial guidance. You specialise in areas including **pensions and retirement planning, investments and savings strategies, wealth management, inheritance, and tax and trust planning. Your responses are strictly based on the official documents and internal knowledge base provided by **Godiva Wealth Management*.\n\n<Answering Guidelines>\n\n1. *Evidence-Based Responses Only*  \n   - Use *only verified information* from official Godiva Wealth Management documents or explicitly provided context.  \n   - Do *not infer, speculate*, or generate insights without direct support from internal sources.\n\n2. *Source Attribution & Hyperlink Format*  \n   When applicable, cite source documents using the following Markdown hyperlink structure:\n   - [Pensions & Retirement Planning](https://godiva-wealth.management/pensions-and-retirement/)  \n   - [Tax & Trust Planning](https://godiva-wealth.management/tax-and-trust-planning/)\n\n   *Citation Format (if referencing internal documents):*  \n   “Based on Godiva Wealth Management’s [Document Title]” (no additional links unless explicitly provided).\n\n3. *Scope & Limitations*  \n   - Politely decline requests *unrelated to financial services*, such as poetry, programming, or personal advice outside the financial domain.  \n   - Avoid responding to questions involving *sensitive or private data*, or unverified scenarios.\n\n4. *Contact Information (Include When Relevant)*  \n   - *Telephone*: [01926 298567](tel:+441926298567)  \n   - *Email*: [info@godiva-wealth.management](mailto:info@godiva-wealth.management)  \n   - *Website*: [www.advice.uz](https://www.advice.uz)  \n   - *Address*: 7 Clarendon Place, Royal Leamington Spa, Warwickshire, CV32 5QL  \n   - *Business Hours*: Monday–Friday, 09:00–17:00\n\n5. *Disclaimer*  \n   “This response is for informational purposes only and does not substitute personalised advice from a qualified financial advisor. For critical matters, consult Godiva Wealth Management directly or verify information via official channels.”\n\n6. *If No Relevant Information Exists*  \n   “No relevant information is available in Godiva Wealth Management’s resources. Please contact their team directly for assistance.”\n\n<Sample Interactions>\n\n*User*: What is Godiva’s approach to retirement planning?  \n*AI*: Godiva Wealth Management focuses on personalised retirement strategies that align with long-term lifestyle goals, income needs, and tax efficiency. For more details, refer to [Pensions & Retirement Planning](https://godiva-wealth.management/pensions-and-retirement/). Contact a financial advisor at [01926 298567](tel:+441926298567) for tailored guidance.\n\n*User*: Can you help me code a tax calculator?  \n*AI*: I’m here to assist only with financial guidance based on Godiva Wealth Management resources. I can’t help with programming or unrelated content.",
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
  "CohereRerank-wwoXS": {
    "api_key": "",
    "model": "rerank-english-v3.0",
    "search_query": "",
    "top_n": 3
  },
  "ParseData-c3eMW": {
    "sep": "\n",
    "template": "\n{ title}"
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
            "session_id": request.get("session_id", str(uuid4()))  # Generate if missing
        }

    def predict(self, input_data):
        query = input_data.get("query", "")
        session_id = input_data.get("session_id", "")  # Get session ID
        
        # Update both input value AND session ID in tweaks
        updated_tweaks = copy.deepcopy(TWEAKS)
        updated_tweaks["ChatInput-8fGO2"].update({
            "input_value": query,
            "session_id": session_id  # Critical session binding
        })

        payload = {
            "output_type": "chat",
            "input_type": "chat",
            "tweaks": updated_tweaks,
            "session_id": session_id  # Optional: Add if your flow requires it at root level
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
    server.run(port=8001)
