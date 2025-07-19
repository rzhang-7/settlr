import os
import pandas as pd
from dotenv import load_dotenv
import google.generativeai as genai

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- Initial Setup ---
load_dotenv()
app = FastAPI(
    title="Urban Bloom AI Agent API",
    description="API for the Settlr AI Agent to provide neighborhood recommendations.",
    version="1.0.0"
)

# Allow requests from your React frontend (adjust port if necessary)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"], # Add your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Load Data ONCE at Startup ---
CSV_PATH = 'SocioeconomicStats.csv'
try:
    neighborhood_df = pd.read_csv(CSV_PATH)
    print(f"Successfully loaded and parsed {len(neighborhood_df)} neighborhood records.")
except FileNotFoundError:
    print(f"FATAL ERROR: Could not find the master CSV file at {CSV_PATH}")
    exit()

# --- Configure Gemini API ---
try:
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel('gemini-2.0-flash')
except Exception as e:
    print(f"FATAL ERROR: Could not configure Gemini API. Check your GEMINI_API_KEY. Error: {e}")
    exit()


# --- Pydantic Model for Request Body Validation ---
class ChatRequest(BaseModel):
    message: str

# --- Core RAG Logic: The "Smart Librarian" ---
def find_relevant_neighborhoods(query: str, top_n: int = 5):
    """
    Scans the entire dataset to find the most relevant neighborhoods based on the query.
    """
    lower_query = query.lower()
    
    # Create a relevance score for each neighborhood
    def calculate_score(row):
        score = 0
        # Add points based on keywords matching high-scoring attributes
        if 'safe' in lower_query or 'crime' in lower_query:
            score += row['safety_score']
        if 'school' in lower_query or 'education' in lower_query:
            score += row['school_score']
        if 'job' in lower_query or 'business' in lower_query or 'amenit' in lower_query:
            score += row['business_job_score']
        if 'growth' in lower_query or 'potential' in lower_query or 'invest' in lower_query:
            score += row['growth_potential_score']
        
        # If no specific keywords match, default to a blend of growth and safety
        return score if score > 0 else (row['growth_potential_score'] * 0.6 + row['safety_score'] * 0.4)

    neighborhood_df['relevance_score'] = neighborhood_df.apply(calculate_score, axis=1)
    
    # Sort and return the top N most relevant neighborhoods
    return neighborhood_df.sort_values('relevance_score', ascending=False).head(top_n)

# --- API Endpoint ---
@app.post("/api/chat", summary="Get AI-powered neighborhood recommendations")
async def chat_handler(request: ChatRequest):
    """
    Receives a user's query, finds relevant neighborhood data,
    and uses Gemini to generate a helpful, data-driven response.
    """
    try:
        # 1. RETRIEVE relevant data from the entire dataset
        relevant_hoods = find_relevant_neighborhoods(request.message)

        # 2. AUGMENT the prompt with the retrieved context
        context = "\n".join([
            f"- Neighborhood: \"{row['AREA_NAME']}\"\n"
            f"  - Growth Potential Score: {row['growth_potential_score']:.0f}/100\n"
            f"  - Safety Score: {row['safety_score']:.0f}/100\n"
            f"  - School Score: {row['school_score']:.0f}/100\n"
            f"  - Business/Amenity Score: {row['business_job_score']:.0f}/100"
            for index, row in relevant_hoods.iterrows()
        ])

        prompt = f"""You are "Settlr Agent", an expert AI assistant for finding neighborhoods in Toronto. Your goal is to help users find the perfect neighborhood based on their needs. You must use the provided data context to answer the user's question. Be friendly, helpful, and base your answer ONLY on the data provided. Do not make up information or scores.

        Here is the data context of the top 5 most relevant neighborhoods based on the user's query:
        ---
        {context}
        ---

        User's request: "{request.message}"

        Your task: Analyze the user's request and the provided data. Recommend one or two of the best-matching neighborhoods from the data and explain WHY they are a good fit, referencing their specific scores. If the user asks a general question (e.g., "what is the safest neighborhood?"), use the data to provide a direct, data-driven answer. Keep your response concise and easy to read."""

        # 3. GENERATE a response from Gemini
        response = await model.generate_content_async(prompt)
        
        return {"reply": response.text}

    except Exception as e:
        print(f"An error occurred during chat processing: {e}")
        raise HTTPException(status_code=500, detail="Failed to get a response from the AI agent.")