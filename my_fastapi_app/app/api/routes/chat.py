from fastapi import APIRouter
from pydantic import BaseModel
import json
from pathlib import Path
import time
import httpx  # 🔥 for making internal HTTP requests

router = APIRouter()
chat_log_path = Path("docs/chat_log.json")
chat_log_path.parent.mkdir(parents=True, exist_ok=True)

class ChatMessage(BaseModel):
    query: str

def load_chat_log():
    if chat_log_path.exists():
        return json.loads(chat_log_path.read_text(encoding="utf-8"))
    return []

def save_chat_log(chat_data):
    chat_log_path.write_text(json.dumps(chat_data, indent=2), encoding="utf-8")

@router.post("/chat-with-agent")
async def chat_with_agent(msg: ChatMessage):
    chat_data = load_chat_log()

    new_user_msg = {
        "role": "user",
        "content": msg.query,
        "timestamp": time.time(),
        "processed": False
    }
    chat_data.append(new_user_msg)

    unprocessed = [m for m in chat_data if m["role"] == "user" and not m.get("processed")]
    if not unprocessed:
        save_chat_log(chat_data)
        return {"response": "No new message found."}

    last_msg = unprocessed[-1]
    last_msg["processed"] = True

    try:
        async with httpx.AsyncClient() as client:
            print("Sending query:", msg.query)
            response = await client.post("http://127.0.0.1:8000/process", json={"query": msg.query}, timeout=60)
            print("Raw response:", response.text)
            response.raise_for_status()
            agent_reply = response.json().get("result", "Agent returned no result.")
    except httpx.HTTPStatusError as http_err:
        print("HTTP Error:", http_err.response.status_code, http_err.response.text)
        agent_reply = f"[Agent HTTP error: {http_err.response.status_code} - {http_err.response.text}]"
    except Exception as e:
        print("General Error:", repr(e))
        agent_reply = f"[Agent error: {repr(e)}]"


    chat_data.append({
        "role": "assistant",
        "content": agent_reply,
        "timestamp": time.time(),
        "processed": True
    })

    save_chat_log(chat_data)
    print(agent_reply)

    return {"response": agent_reply}





@router.get("/get-agent-response")
def get_agent_response():
    if chat_log_path.exists():
        chat_data = json.loads(chat_log_path.read_text(encoding="utf-8"))
        return {"chat_history": chat_data}
    return {"chat_history": []}


@router.get("/check-status")
def check_status():
    return {"status": "Agent is active"}


@router.delete("/clear-chat")
def clear_chat():
    if chat_log_path.exists():
        chat_log_path.unlink()
    return {"status": "Chat log cleared"}
