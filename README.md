# Credit_scoring
# Project Overview

This project is structured into three main components:

---

## 📦 `my_fast_api/`

This folder contains the backend logic and the AI processing server.

- `server.py`:  
  - Contains the core AI logic and query processing.  
  - Runs a FastAPI server on **port 8000**.  
  - Accepts POST requests at `/process` with a user query.  
  - Returns the AI-generated response.

- Backend (e.g. `backend.py`):  
  - Runs on **port 5000**.  
  - Acts as a bridge between the frontend and the AI server.  
  - Sends user queries to the FastAPI AI server and returns the model's response.

- `docs/`:  
  - Stores all documents uploaded by users through the frontend interface.  
  - These files are used for context-aware query processing by the AI.

---

## 💻 `agent-ui-main/`

This folder contains the **frontend** of the application.

- Users can upload files and submit queries.  
- Queries are sent to the backend which forwards them to the AI server.  
- The response is displayed in the UI.

---

## 🔁 Workflow Summary

1. **Frontend (`agent-ui-main`)**:  
   User uploads documents and submits a query.

2. **Backend (`my_fast_api` on port 5000)**:  
   Receives the query and any file references, and forwards them to the AI server.

3. **AI Server (`server.py` on port 8000)**:  
   Processes the query using the shared documents and returns the AI response.

4. **Backend** sends the result back to the frontend for display.

---

## 🚀 How to Run

Make sure both the backend and the server are running:

1. Start the AI server:
   ```bash
   uvicorn server:app --host 0.0.0.0 --port 8000 --reload
   ```

2. Start the backend (e.g. Flask or FastAPI on port 5000):
   ```bash
   python backend.py
   ```

3. Start the frontend (from `agent-ui-main`):
   ```bash
   npm install
   npm run dev
   ```

---

## 📂 Folder Summary

```plaintext
my_fast_api/
├── server.py          # FastAPI app with AI logic
├── backend.py         # Query relay server
├── docs/              # Uploaded files from users

agent-ui-main/
├── ...                # Frontend React/Next.js project
```
