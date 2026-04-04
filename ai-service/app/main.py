from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .auth import verify_token
from .game import search_game 
from .langchain_agent import run_langchain_agent

class Question(BaseModel):
    question: str
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/ai/chat")
def chat_ai(data: Question, user=Depends(verify_token)):

    result = run_langchain_agent(data.question)

    return {
        "user": user,
        "question": data.question,
        "result": result
    }