import os
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.responses import HTMLResponse

# --- Imports for MongoDB ---
from pymongo import MongoClient
from urllib.parse import quote_plus
import certifi

# --- Initial Setup ---
load_dotenv()
app = FastAPI(
    title="Urban Bloom API",
    description="API using MongoDB as the single source of truth for the AI Agent.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
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

# --- Load Data from MongoDB ONCE at Startup ---
print("Connecting to MongoDB and loading MasterDataset...")
try:
    db = get_db_connection()
    collection = db["csvdata"]
    # Fetch all documents from the collection and convert to a list
    cursor = collection.find({}, {'_id': 0}) # Exclude the Mongo _id
    data_list = list(cursor)
    
    if not data_list:
        print("FATAL ERROR: No data found in the 'csvdata' MongoDB collection.")
        exit()
        
    # Convert the list of dictionaries into a Pandas DataFrame
    neighborhood_df = pd.DataFrame(data_list)
    print(f"Successfully loaded {len(neighborhood_df)} neighborhood records from MongoDB.")

except Exception as e:
    print(f"FATAL ERROR: Could not load data from MongoDB. Error: {e}")
    exit()

# ==================================================================
# ** AI Agent Section (Now using the DataFrame from MongoDB) **
# ==================================================================
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"FATAL ERROR: Could not configure Gemini API. Check your GEMINI_API_KEY. Error: {e}")
    exit()

class ChatRequest(BaseModel):
    message: str

def find_relevant_neighborhoods(query: str, top_n: int = 5):
    """
    Scans the in-memory DataFrame (sourced from MongoDB) to find relevant neighborhoods.
    """
    lower_query = query.lower()
    def calculate_score(row):
        score = 0
        if 'safe' in lower_query or 'crime' in lower_query: score += row.get('safety_score', 0)
        if 'school' in lower_query or 'education' in lower_query: score += row.get('school_score', 0)
        if 'job' in lower_query or 'business' in lower_query or 'amenit' in lower_query: score += row.get('business_job_score', 0)
        if 'growth' in lower_query or 'potential' in lower_query or 'invest' in lower_query: score += row.get('growth_potential_score', 0)
        return score if score > 0 else (row.get('growth_potential_score', 0) * 0.6 + row.get('safety_score', 0) * 0.4)
    
    # Use .get() for safety in case a column is missing from a document
    neighborhood_df['relevance_score'] = neighborhood_df.apply(calculate_score, axis=1)
    return neighborhood_df.sort_values('relevance_score', ascending=False).head(top_n)

@app.post("/api/chat", summary="Get AI-powered neighborhood recommendations from MongoDB data")
async def chat_handler(request: ChatRequest):
    try:
        relevant_hoods = find_relevant_neighborhoods(request.message)
        context = "\n".join([
            f"- Neighborhood: \"{row.get('AREA_NAME', 'N/A')}\"\n"
            f"  - Growth Potential Score: {row.get('growth_potential_score', 0):.0f}/100\n"
            f"  - Safety Score: {row.get('safety_score', 0):.0f}/100\n"
            f"  - School Score: {row.get('school_score', 0):.0f}/100\n"
            f"  - Business/Amenity Score: {row.get('business_job_score', 0):.0f}/100"
            for index, row in relevant_hoods.iterrows()
        ])
        prompt = f"""You are "Settlr Agent", an expert AI assistant for finding neighborhoods in Toronto... (rest of your prompt)""" # Keep your detailed prompt
        response = await model.generate_content_async(prompt)
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
        rows_html = [ " | ".join(str(record.get(f, "")) for f in fields) for record in top_3 ]
        
        result_string = "\n".join([
            "Top 3 Records from MongoDB:",
            header_html,
            "-" * (len(header_html) + 10),
            *rows_html
        ])
        
        return f"<pre>{result_string}</pre>"
    
    except Exception as e:
        return f"<h1>Database Error</h1><p>{str(e)}</p>", 500