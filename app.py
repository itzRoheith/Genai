from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import google.generativeai as genai
from pymongo import MongoClient
import datetime

app = FastAPI()

# Configure Gemini API Key
genai.configure(api_key="AIzaSyCqM2i_9xqy2rTFdtigshIVp9PpZS2En0o")
print("Gemini API Key configured successfully.")

# Connect to MongoDB (Replace with your MongoDB URI)
MONGO_URI = "mongodb+srv://itzrth:Roheith1979@clus.ke3bg.mongodb.net/chat_database?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI)
db = client["MS"]
conversations_collection = db["msg"]

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()

            # Store user message in MongoDB
            conversations_collection.insert_one({
                "user_id": user_id,
                "role": "user",
                "message": data,
                "timestamp": datetime.datetime.utcnow()
            })

            # Send query to Gemini API
            model = genai.GenerativeModel("gemini-2.0-flash")
            response = model.generate_content(data)

            # Store AI response in MongoDB
            conversations_collection.insert_one({
                "user_id": user_id,
                "role": "ai",
                "message": response.text,
                "timestamp": datetime.datetime.utcnow()
            })

            # Send response back to user
            await websocket.send_text(response.text)

    except WebSocketDisconnect:
        print(f"User {user_id} disconnected.")
