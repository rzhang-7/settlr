from flask import Flask, jsonify, render_template
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB connection setup
def get_db():
    # Replace with your MongoDB connection string
    client = MongoClient("mongodb://localhost:27017/")
    db = client["MegaData"]  # Your database name
    return db

@app.route('/')
def home():
    return """
    <h1>MegaData CSV Data Access</h1>
    <p>Available endpoints:</p>
    <ul>
        <li><a href="/csvdata">/csvdata</a> - Get all CSV data</li>
        <li>/csvdata/&lt;field&gt;/&lt;value&gt; - Filter data (e.g. <a href="/csvdata/name/John">/csvdata/name/John</a>)</li>
        <li><a href="/view-data">/view-data</a> - View data in HTML table</li>
    </ul>
    """

@app.route('/csvdata', methods=['GET'])
def get_csv_data():
    try:
        db = get_db()
        collection = db["csvdata"]  # Your collection name
        
        # Get all documents from the collection
        data = list(collection.find({}, {'_id': 0}))  # Exclude _id by default
        
        return jsonify({
            "status": "success",
            "data": data
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/csvdata/<field>/<value>', methods=['GET'])
def get_filtered_data(field, value):
    try:
        db = get_db()
        collection = db["csvdata"]
        
        # Create query - try to convert numeric values
        try:
            value = float(value) if '.' in value else int(value)
        except ValueError:
            pass
            
        query = {field: value}
        data = list(collection.find(query, {'_id': 0}))
        
        return jsonify({
            "status": "success",
            "data": data
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/view-data')
def view_data():
    try:
        db = get_db()
        collection = db["csvdata"]
        data = list(collection.find({}, {'_id': 0}))
        return render_template('data.html', data=data)
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True)