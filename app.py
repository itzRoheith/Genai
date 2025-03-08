from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import google.generativeai as genai
from pymongo import MongoClient
import datetime

app = FastAPI()

# Configure Gemini API Key
genai.configure(api_key="AIzaSyCqM2i_9xqy2rTFdtigshIVp9PpZS2En0o")

# MongoDB Connection
MONGO_URI = "mongodb+srv://itzrth:Roheith1979@clus.ke3bg.mongodb.net/chat_database?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client["chat_database"]  # Main Database

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    try:
        # Get initial message
        initial_prompt = await websocket.receive_text()

        # Ask Gemini to generate a collection name
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"Generate a short, relevant MongoDB collection name for this conversation topic: {initial_prompt}. "
            f"Keep it concise, lowercase, and use underscores instead of spaces. Avoid special characters."
        )
        collection_name = response.text.strip().replace(" ", "_").lower()  # Ensure a valid collection name

        # Ensure the collection name is unique (if already exists, append a number)
        counter = 1
        original_name = collection_name
        while collection_name in db.list_collection_names():
            collection_name = f"{original_name}_{counter}"
            counter += 1

        chat_collection = db[collection_name]  # Create the collection

        # Store the initial message
        chat_collection.insert_one({"role": "User", "message": initial_prompt, "timestamp": datetime.datetime.utcnow()})

        # Send AI response to the user
        ai_response = model.generate_content(initial_prompt)
        chat_collection.insert_one({"role": "AI", "message": ai_response.text, "timestamp": datetime.datetime.utcnow()})

        await websocket.send_text(ai_response.text)

        # Continue conversation
        while True:
            data = await websocket.receive_text()
            chat_collection.insert_one({"role": "User", "message": data, "timestamp": datetime.datetime.utcnow()})

            response = model.generate_content(data)
            chat_collection.insert_one({"role": "AI", "message": response.text, "timestamp": datetime.datetime.utcnow()})

            await websocket.send_text(response.text)

    except WebSocketDisconnect:
        print(f"User {user_id} disconnected. Chat stored in collection: {collection_name}")
