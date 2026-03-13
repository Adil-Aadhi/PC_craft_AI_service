from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from .tools import get_best_gpu_under_budget, build_pc

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

tools = [
    Tool(
        name="gpu_recommendation",
        func=get_best_gpu_under_budget,
        description="Get best GPUs under a given budget"
    ),
    Tool(
        name="pc_builder",
        func=build_pc,
        description="Build a gaming PC under a given budget"
    )
]

agent = initialize_agent(
    tools,
    llm,
    agent="zero-shot-react-description",
    verbose=True
)

def ask_agent(question: str):
    response = agent.run(question)
    return response