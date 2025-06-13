from fastapi import APIRouter, UploadFile, File, Form
import os
from typing import List

router = APIRouter()


@router.get("/create-knowledgebase")
def createKnowledgebase():
    return {"message": "Knowledgebase created"}


@router.get("/rename-knowledgebase")
def renameKnowledgebase():
    return {"message": "Knowledgebase renamed"}


@router.get("/get-knowledgebase-list")
def getKnowledgebaseList():
    return {"knowledgebases": ["kb1", "kb2"]}


@router.get("/delete-knowledgebase")
def deleteKnowledgebase():
    return {"message": "Knowledgebase deleted"}


@router.post("/add-files")
async def upload_files(
    files: List[UploadFile] = File(...),
    kb_name: str = Form(default="default_kb")
):
    upload_dir = f"docs"
    os.makedirs(upload_dir, exist_ok=True)

    saved_files = []
    for file in files:
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        saved_files.append(file.filename)

    return {"message": "Files uploaded successfully", "files": saved_files}



@router.get("/list-files")
def listKnowledgebaseFiles():
    return {"files": ["doc1.pdf", "doc2.pdf"]}


@router.post("/delete-files")
def deleteKnowledgebaseFiles():
    return {"message": "Files deleted"}
