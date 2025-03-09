from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import google.generativeai as genai
from pymongo import MongoClient
import datetime
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS to allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini API Key
genai.configure(api_key="AIzaSyCqM2i_9xqy2rTFdtigshIVp9PpZS2En0o")

# MongoDB Connection
MONGO_URI = "mongodb+srv://itzrth:Roheith1979@clus.ke3bg.mongodb.net/chat_database?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client["Genai"]  # Main Database

@app.get("/collections")
async def get_collections():
    """Returns the list of collection names from MongoDB."""
    collections = db.list_collection_names()
    return JSONResponse(content={"collections": collections})

@app.get("/chats/{collection_name}")
async def get_chats(collection_name: str):
    """Fetches chat messages from the selected collection."""
    chat_collection = db[collection_name]
    messages = list(chat_collection.find({}, {"_id": 0, "role": 1, "message": 1, "timestamp": 1}))
    return JSONResponse(content={"messages": messages})

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    """WebSocket for real-time chat communication."""
    await websocket.accept()

    try:
        # Get initial message
        initial_prompt = await websocket.receive_text()

        # Ask Gemini to generate a collection name
        model = genai.GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(
            f"Generate a short MongoDB collection name for this topic: {initial_prompt}. Use underscores instead of spaces."
        )
        collection_name = response.text.strip().replace(" ", "_").lower()

        # Ensure unique collection name
        counter = 1
        original_name = collection_name
        while collection_name in db.list_collection_names():
            collection_name = f"{original_name}_{counter}"
            counter += 1

        chat_collection = db[collection_name]  # Create the collection

        # Store the initial message
        chat_collection.insert_one({
            "role": "User", 
            "message": initial_prompt, 
            "timestamp": datetime.datetime.utcnow()
        })

        # Send AI response
        ai_response = model.generate_content(initial_prompt)
        chat_collection.insert_one({
            "role": "AI", 
            "message": ai_response.text, 
            "timestamp": datetime.datetime.utcnow()
        })

        await websocket.send_text(ai_response.text)

        # Continue conversation
        while True:
            data = await websocket.receive_text()
            chat_collection.insert_one({
                "role": "User", 
                "message": data, 
                "timestamp": datetime.datetime.utcnow()
            })

            response = model.generate_content(data)
            chat_collection.insert_one({
                "role": "AI", 
                "message": response.text, 
                "timestamp": datetime.datetime.utcnow()
            })

            await websocket.send_text(response.text)

    except WebSocketDisconnect:
        print(f"User {user_id} disconnected. Chat stored in collection: {collection_name}")
