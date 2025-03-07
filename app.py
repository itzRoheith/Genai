from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import google.generativeai as genai

app = FastAPI()

# Configure Gemini API Key
genai.configure(api_key="AIzaSyCqM2i_9xqy2rTFdtigshIVp9PpZS2En0o")
print("Gemini API Key configured successfully.")
# Store user conversations
user_conversations = {}

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await websocket.accept()

    # Initialize conversation history for the user
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    try:
        while True:
            data = await websocket.receive_text()
            user_conversations[user_id].append(f"User: {data}")

            # Send entire conversation history to Gemini
            chat_history = "\n".join(user_conversations[user_id])
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(chat_history)

            user_conversations[user_id].append(f"AI: {response.text}")
            await websocket.send_text(response.text)
    
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected. Clearing chat history.")
        del user_conversations[user_id]  # Delete conversation when user disconnects
