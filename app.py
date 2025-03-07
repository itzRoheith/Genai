from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import google.generativeai as genai
from PIL import Image
import io
import base64

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
            data = await websocket.receive()  # Receives both text and binary data

            # Check if received data is binary (assumed to be an image)
            if isinstance(data, bytes):
                print("Received an image file.")

                # Convert binary data to PIL Image
                image = Image.open(io.BytesIO(data))

                # Process with Gemini (Only `gemini-1.5-pro` supports images)
                model = genai.GenerativeModel("gemini-1.5-pro")
                response = model.generate_content([{"type": "image", "data": image}])

                # Send AI response
                await websocket.send_text(response.text)

            else:
                print(f"Received text: {data}")
                user_conversations[user_id].append(f"User: {data}")

                # Send conversation history to Gemini
                chat_history = "\n".join(user_conversations[user_id])
                model = genai.GenerativeModel("gemini-1.5-flash")  # Flash for faster response
                response = model.generate_content(chat_history)

                user_conversations[user_id].append(f"AI: {response.text}")
                await websocket.send_text(response.text)

    except WebSocketDisconnect:
        print(f"User {user_id} disconnected. Clearing chat history.")
        del user_conversations[user_id]  # Delete conversation when user disconnects
