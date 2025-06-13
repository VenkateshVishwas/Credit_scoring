from fastapi import APIRouter

router = APIRouter()


@router.get("/test")
def test():
    return {"message": "Test successful"}


@router.get("/create-agent")
def createAgent():
    return {"message": "Agent created"}


@router.post("/set-agent-domain")
def setAgentDomain():
    return {"message": "Agent domain set"}


@router.get("/rename-agent")
def renameAgent():
    return {"message": "Agent renamed"}


@router.get("/delete-agent")
def deleteAgent():
    return {"message": "Agent deleted"}


@router.get("/attach-tool-to-agent")
def attachToolToAgent():
    return {"message": "Tool attached to agent"}


@router.post("/attach-kb-to-agent")
def attachKbToAgent():
    return {"message": "Knowledgebase attached to agent"}


@router.get("/list-agent-kb")
def listAgentKnowledgebases():
    return {"knowledgebases": ["kb1", "kb2"]}
