import ollama
import json
from .tools import get_best_gpu_under_budget, build_pc,get_best_cpu_under_budget
from .utils import extract_budget


# Tools available to the AI
TOOLS = {
    "gpu_recommendation": get_best_gpu_under_budget,
    "cpu_recommendation": get_best_cpu_under_budget,
    "pc_builder": build_pc
}


# ✅ System prompt (PUT IT HERE)
SYSTEM_PROMPT = """
You are an AI PC building assistant.

You MUST always return valid JSON.

Available tools:

1. gpu_recommendation(budget)
2. cpu_recommendation(budget)
3. pc_builder(budget)

Rules:

If the user asks about GPU recommendations → use gpu_recommendation.

If the user asks about CPU recommendations → use cpu_recommendation.

If the user asks to build a full PC → use pc_builder.

If the user asks a general PC question → answer normally.

Return ONLY JSON.

Example:

GPU recommendation:
{
 "tool": "gpu_recommendation",
 "input": 30000
}

CPU recommendation:
{
 "tool": "cpu_recommendation",
 "input": 20000
}

PC build:
{
 "tool": "pc_builder",
 "input": 100000
}

Normal chat:
{
 "tool": "chat",
 "input": "RTX 4060 is good for 1080p gaming."
}
"""


def decide_tool(question: str):

    client = ollama.Client(host="http://host.docker.internal:11434")
    response = client.chat(
        model="llama3",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]
    )

    return response["message"]["content"]


def run_agent(question: str):

    decision = decide_tool(question)

    try:
        data = json.loads(decision)
    except:
        return {
            "type": "chat",
            "answer": decision
        }

    tool = data.get("tool")
    input_value = data.get("input")

    # GPU recommendation
    if tool == "gpu_recommendation":
        gpus = get_best_gpu_under_budget(int(input_value))
        return {
            "type": "gpu",
            "results": gpus
        }

    # CPU recommendation
    if tool == "cpu_recommendation":
        cpus = get_best_cpu_under_budget(int(input_value))
        return {
            "type": "cpu",
            "results": cpus
        }

    # PC build
    if tool == "pc_builder":
        build = build_pc(int(input_value))
        return {
            "type": "build",
            **build
        }

    # Normal chat
    if tool == "chat":

        client = ollama.Client(host="http://host.docker.internal:11434")

        response = client.chat(
            model="llama3",
            messages=[
                {
                    "role": "system",
                    "content": "You are a PC hardware expert. Answer briefly and clearly."
                },
                {
                    "role": "user",
                    "content": question
                }
            ]
        )

        content = response["message"]["content"]

        try:
            parsed = json.loads(content)

            if isinstance(parsed, dict) and "input" in parsed:
                answer = parsed["input"]
            else:
                answer = content

        except:
            answer = content

        return {
            "type": "chat",
            "answer": answer
        }