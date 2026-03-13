from fastapi import FastAPI
from .tools import get_best_gpu_under_budget,get_best_cpu_under_budget,build_pc
from pydantic import BaseModel
import ollama
from .ai_agent import run_agent
from fastapi.middleware.cors import CORSMiddleware
from .auth import verify_token
from fastapi import Depends
from .game import search_game 



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "AI service running"}

@app.get("/gpu-recommendation/{budget}")
def gpu_recommendation(budget: int):

    gpus = get_best_gpu_under_budget(budget)

    return {
        "budget": budget,
        "results": gpus
    }

@app.get("/cpu-recommendation/{budget}")
def cpu_recommendation(budget: int):

    cpus = get_best_cpu_under_budget(budget)

    return {
        "budget": budget,
        "results": cpus
    }

@app.get("/build-pc/{budget}")
def pc_builder(budget: int):

    build = build_pc(budget)

    return build

class Question(BaseModel):
    question: str


@app.post("/ai/chat")
def chat_ai(data: Question, user=Depends(verify_token)):

    result = run_agent(data.question)

    return {
        "user": user,
        "question": data.question,
        "result": result
    }

@app.get("/games/search")
def game_search(name: str):

    return search_game(name)