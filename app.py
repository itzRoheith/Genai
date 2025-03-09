from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pymongo import MongoClient
import datetime

app = FastAPI()

# MongoDB Connection
MONGO_URI = "mongodb+srv://itzrth:Roheith1979@clus.ke3bg.mongodb.net/chat_database?retryWrites=true&w=majority"
client = MongoClient(MONGO_URI, tls=True, tlsAllowInvalidCertificates=True)
db = client["Genai"]

@app.get("/collections")
async def get_collections():
    return db.list_collection_names()

@app.get("/chats/{collection_name}")
async def get_chats(collection_name: str):
    chat_collection = db[collection_name]
    messages = list(chat_collection.find({}, {"_id": 0}))
    return {"messages": messages}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()
    chat_collection = db[user_id]

    try:
        while True:
            data = await websocket.receive_text()
            chat_collection.insert_one({"role": "User", "message": data, "timestamp": datetime.datetime.utcnow()})

            response = f"AI Response to: {data}"
            chat_collection.insert_one({"role": "AI", "message": response, "timestamp": datetime.datetime.utcnow()})

            await websocket.send_text(response)

    except WebSocketDisconnect:
        print(f"User {user_id} disconnected.")
