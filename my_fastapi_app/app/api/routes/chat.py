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
    text: str

def load_chat_log():
    if chat_log_path.exists():
        return json.loads(chat_log_path.read_text(encoding="utf-8"))
    return []

def save_chat_log(chat_data):
    chat_log_path.write_text(json.dumps(chat_data, indent=2), encoding="utf-8")

@router.post("/chat-with-agent")
def chat_with_agent(msg: ChatMessage):
    chat_data = load_chat_log()

    new_user_msg = {
        "role": "user",
        "content": msg.text,
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
        with httpx.Client() as client:
            response = client.post("http://127.0.0.1:8000/process", json={"query": last_msg["content"]})
            response.raise_for_status()
            agent_reply = response.json().get("response", "Agent failed to respond.")
    except Exception as e:
        agent_reply = f"[Agent error: {str(e)}]"

    # 4. Append assistant reply
    chat_data.append({
        "role": "assistant",
        "content": agent_reply,
        "timestamp": time.time(),
        "processed": True
    })

    # 5. Save updated chat log
    save_chat_log(chat_data)
    print(agent_reply)

    return {"response":agent_reply}



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
