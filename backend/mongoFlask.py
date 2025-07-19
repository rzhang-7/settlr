from flask import Flask
from pymongo import MongoClient
from urllib.parse import quote_plus
import certifi  # For Solution 2

app = Flask(__name__)

def get_db():
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
            tlsCAFile=certifi.where(),  # For Solution 2
            # tlsAllowInvalidCertificates=True,  # For Solution 1
            connectTimeoutMS=30000,
            socketTimeoutMS=30000
        )
        return client["MegaData"]
    except Exception as e:
        print(f"Connection error: {e}")
        raise

@app.route('/')
def show_top_3():
    try:
        db = get_db()
        collection = db["csvdata"]
        top_3 = list(collection.find({}, {'_id': 0}).limit(3))
        
        if not top_3:
            return "No data found"
            
        fields = list(top_3[0].keys())
        result = ["Top 3 Records:", " | ".join(fields), "-"*50]
        for record in top_3:
            result.append(" | ".join(str(record.get(f, "")) for f in fields))
        
        return "<pre>" + "\n".join(result) + "</pre>"
    
    except Exception as e:
        return f"Database error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)