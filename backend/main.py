import os
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse
from typing import List, Literal, Dict, Any
import json
from fastapi.responses import JSONResponse

# --- Imports for Geocoding and Distance ---
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# --- Imports for MongoDB ---
from pymongo import MongoClient
from urllib.parse import quote_plus
import certifi

# --- Initial Setup ---
load_dotenv()
app = FastAPI(
    title="Settlr Agent API",
    description="API with an AI Router and Tools for intelligent neighborhood search and conversational chat.",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Add your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================================================================
# ** MongoDB Connection and Data Loading **
# ==================================================================
def get_db_connection():
    """Establishes a connection to the MongoDB database."""
    username = "maksimichess"
    password = "dYgL1UN5yBHLeOko"
    cluster = "settlrcluster.bmklrom.mongodb.net"
    
    escaped_username = quote_plus(username)
    escaped_password = quote_plus(password)
    
    connection_string = f"mongodb+srv://{escaped_username}:{escaped_password}@{cluster}/?retryWrites=true&w=majority"
    
    try:
        client = MongoClient(
            connection_string,
            tls=True,
            tlsCAFile=certifi.where(),
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        return client["MegaData"]
    except Exception as e:
        print(f"MongoDB Connection error: {e}")
        raise

print("Connecting to MongoDB and loading MasterDataset...")
try:
    db = get_db_connection()
    collection = db["csvdata"]
    cursor = collection.find({}, {'_id': 0})
    data_list = list(cursor)
    if not data_list:
        raise Exception("No data found in the 'csvdata' MongoDB collection.")
    neighborhood_df = pd.DataFrame(data_list)
    ALL_NEIGHBORHOOD_NAMES = neighborhood_df['AREA_NAME'].unique().tolist()
    print(f"Successfully loaded {len(neighborhood_df)} records.")
except Exception as e:
    print(f"FATAL ERROR: Could not load data from MongoDB. Error: {e}")
    exit()

# ==================================================================
# ** AI Agent and Tools Section **
# ==================================================================
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-1.5-flash')
    geolocator = Nominatim(user_agent="settlr_agent_v5")
except Exception as e:
    print(f"FATAL ERROR: Could not configure API clients. Error: {e}")
    exit()

# --- Pydantic Models ---
class ChatMessage(BaseModel):
    sender: Literal['bot', 'user']
    text: str

class ChatRequest(BaseModel):
    history: List[ChatMessage]

# --- TOOL 1: Find by Metric (Top/Bottom) ---
def find_top_bottom_by_metric_tool(metric: str, order: str, top_n: int = 5) -> List[str]:
    print(f"Executing TOOL: find_top_bottom_by_metric_tool (metric={metric}, order={order})")
    sort_ascending = True if order == 'bottom' else False
    sorted_df = neighborhood_df.sort_values(by=metric, ascending=sort_ascending)
    return sorted_df.head(top_n)['AREA_NAME'].tolist()

# --- TOOL 2: Find Nearby ---
def find_nearby_neighborhoods_tool(location_name: str, top_n: int = 5) -> List[str]:
    print(f"Executing TOOL: find_nearby_neighborhoods_tool (location={location_name})")
    try:
        target_location = geolocator.geocode(f"{location_name}, Toronto, ON")
        if not target_location: return []
        target_coords = (target_location.latitude, target_location.longitude)
        distances = neighborhood_df.apply(lambda row: geodesic(target_coords, (row['latitude'], row['longitude'])).km, axis=1)
        return neighborhood_df.loc[distances.nsmallest(top_n).index]['AREA_NAME'].tolist()
    except Exception as e:
        print(f"Geocoding/distance calculation error: {e}")
        return []

# --- TOOL 3: Semantic Search ---
async def semantic_search_tool(query: str, all_names: List[str], top_n: int = 5) -> List[str]:
    print(f"Executing TOOL: semantic_search_tool for query: '{query}'")
    names_list_str = ", ".join(f'"{name}"' for name in all_names)
    prompt = f'You are a search expert. From the list [{names_list_str}], pick the top {top_n} that best match the query: "{query}". Respond with only a comma-separated list of names.'
    response = await model.generate_content_async(prompt)
    return [name.strip().strip('"') for name in response.text.split(',')]

# --- TOOL 4: General Chat / Persona ---
async def general_chat_tool(history: List[Dict[str, Any]]) -> str:
    print("Executing TOOL: general_chat_tool")
    persona_prompt = """
    You are "Settlr Agent," a friendly, professional, and expert AI assistant.
    
    **Your Identity and Purpose:**
    - Your Name: Settlr Agent.
    - Your Job: To help users find the perfect neighborhood in Toronto by providing data-driven insights.
    - Your Data Source: You have access to a comprehensive dataset of all 158 official Toronto neighborhoods, including scores for safety, schools, amenities, and growth potential.

    **Your Capabilities:**
    - You can find the "top 5 safest" or "bottom 5 for schools."
    - You can find neighborhoods "near" or "close to" specific locations like the CN Tower or a university.
    - You can perform general searches for lifestyle needs like "good for families" or "vibrant nightlife."
    - You can answer questions about yourself (your name, your purpose).

    **How to Behave:**
    - Always be helpful and conversational.
    - If you don't know an answer or if the user asks something outside your scope (e.g., stock market advice), politely state your purpose and guide the conversation back to Toronto neighborhoods.
    - Keep your answers concise and use Markdown for formatting.

    Based on this persona and our chat history, provide a natural response to the user's last message.
    """
    chat_session = model.start_chat(history=history)
    response = await chat_session.send_message_async(persona_prompt)
    return response.text

# --- The AI Router (Now with a 4th tool) ---
async def classify_intent_and_get_params(query: str) -> Dict[str, Any]:
    print(f"--- AI Router: Classifying intent for query: '{query}' ---")
    prompt = f"""
    You are an intelligent router. Your job is to analyze the user's query and decide which tool to use.
    The available tools are:
    1. `find_top_bottom`: For queries asking for "top", "bottom", "best", "worst", "safest", etc., based on a metric.
       - Required parameters: `metric` (one of 'safety_score', 'school_score', 'business_job_score', 'growth_potential_score'), `order` ('top' or 'bottom').
    2. `find_nearby`: For queries asking for neighborhoods "near", "close to", or "around" a specific location.
       - Required parameters: `location_name`.
    3. `semantic_search`: For general, subjective, or lifestyle-based queries about neighborhoods (e.g., "good for families", "quiet areas").
       - Required parameters: None.
    4. `general_chat`: Use for greetings (hello, hi), questions about the AI's identity (who are you, what's your name), its capabilities (what can you do), or any other off-topic chat.
       - Required parameters: None.

    User Query: "{query}"

    Your response MUST be a single, valid JSON object with two keys: "tool" and "parameters".
    
    Examples:
    - Query: "What are the top 5 safest areas?" -> {{"tool": "find_top_bottom", "parameters": {{"metric": "safety_score", "order": "top"}}}}
    - Query: "Show me places near the CN Tower" -> {{"tool": "find_nearby", "parameters": {{"location_name": "CN Tower"}}}}
    - Query: "I want somewhere good for a young professional" -> {{"tool": "semantic_search", "parameters": {{}}}}
    - Query: "hi what is your name?" -> {{"tool": "general_chat", "parameters": {{}}}}
    """
    try:
        response = await model.generate_content_async(prompt)
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "")
        result = json.loads(cleaned_text)
        print(f"--- AI Router determined tool: {result.get('tool')} with params: {result.get('parameters')} ---")
        return result
    except Exception as e:
        print(f"Router failed: {e}. Defaulting to semantic_search.")
        return {"tool": "semantic_search", "parameters": {}}

@app.post("/api/chat", summary="Get AI-powered neighborhood recommendations with an intelligent tool router")
async def chat_handler(request: ChatRequest):
    try:
        latest_user_message = request.history[-1].text
        gemini_history = [{'role': 'model' if msg.sender == 'bot' else 'user', 'parts': [msg.text]} for msg in request.history]
        
        router_result = await classify_intent_and_get_params(latest_user_message)
        tool_name = router_result.get("tool")
        params = router_result.get("parameters", {})
        
        if tool_name == "general_chat":
            reply = await general_chat_tool(gemini_history)
            return {"reply": reply}

        relevant_names = []
        if tool_name == "find_top_bottom":
            relevant_names = find_top_bottom_by_metric_tool(params.get("metric"), params.get("order"))
        elif tool_name == "find_nearby":
            relevant_names = find_nearby_neighborhoods_tool(params.get("location_name"))
        else:
            relevant_names = await semantic_search_tool(latest_user_message, ALL_NEIGHBORHOOD_NAMES)

        if not relevant_names:
            return {"reply": "I'm sorry, I couldn't find any specific neighborhoods based on your request. Could you try rephrasing it?"}

        relevant_hoods_df = neighborhood_df[neighborhood_df['AREA_NAME'].isin(relevant_names)]
        context = "\n".join([f"- Neighborhood: \"{row.get('AREA_NAME', 'N/A')}\"\n  - Growth: {row.get('growth_potential_score', 0):.0f}/100, Safety: {row.get('safety_score', 0):.0f}/100, Schools: {row.get('school_score', 0):.0f}/100, Amenities: {row.get('business_job_score', 0):.0f}/100" for _, row in relevant_hoods_df.iterrows()])

        chat_session = model.start_chat(history=gemini_history)
        final_message_to_send = f"""(You are Settlr Agent. Continue the conversation naturally.) Based on my request, you performed a search and found these relevant neighborhoods: --- {context} --- Please provide a helpful, conversational response. Analyze the data and explain *why* these neighborhoods are a good match. Use Markdown for formatting."""
        
        response = await chat_session.send_message_async(final_message_to_send)
        return {"reply": response.text}
        
    except Exception as e:
        print(f"An error occurred during chat processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to get a response from the AI agent.")


# ==================================================================
# ** MongoDB Viewer Route (Unchanged) **
# ==================================================================
@app.get("/", response_class=HTMLResponse, summary="Show top 3 records from MongoDB")
async def show_top_3_mongo():
    """
    Connects to MongoDB and displays the top 3 records from the 'csvdata' collection.
    """
    try:
        db = get_db_connection()
        collection = db["csvdata"]
        top_3 = list(collection.find({}, {'_id': 0}).limit(3))
        
        if not top_3:
            return "<h1>No data found in MongoDB collection.</h1>"
            
        fields = list(top_3[0].keys())
        header_html = " | ".join(fields)
        rows_html = [ " | ".join(str(record.get(f, ""))) for f in fields for record in top_3 ]
        
        result_string = "\n".join([
            "Top 3 Records from MongoDB:",
            header_html,
            "-" * (len(header_html) + 10),
            *rows_html
        ])
        
        return f"<pre>{result_string}</pre>"
    
    except Exception as e:
        return f"<h1>Database Error</h1><p>{str(e)}</p>", 500

@app.get("/api/neighbourhoods", response_class=JSONResponse, summary="Get all neighbourhood socioeconomic stats as JSON")
async def get_all_neighbourhoods():
    """
    Returns all neighbourhood socioeconomic stats from MongoDB as JSON.
    """
    try:
        db = get_db_connection()
        collection = db["csvdata"]
        data = list(collection.find({}, {'_id': 0}))
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)