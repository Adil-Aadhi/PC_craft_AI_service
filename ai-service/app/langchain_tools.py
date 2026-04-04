from langchain.tools import tool
import re
import json
from .tools import (
    get_best_gpu_under_budget,
    get_best_cpu_under_budget,
    build_pc,
    build_pc_with_requirements
)
from .ai_extractor import extract_requirements


def extract_number(text):
    numbers = re.findall(r'\d+', str(text))
    return int(numbers[0]) if numbers else 0


@tool
def gpu_recommendation(budget: str):
    """Get best GPU under a given budget."""
    budget = extract_number(budget)
    result = get_best_gpu_under_budget(budget)
    return json.dumps(result)


@tool
def cpu_recommendation(budget: str):
    """Get best CPU under a given budget."""
    budget = extract_number(budget)
    result = get_best_cpu_under_budget(budget)
    return json.dumps(result)


@tool
def pc_builder(budget: str):
    """Build a complete PC under a given budget."""
    budget = extract_number(budget)
    result = build_pc(budget)
    return json.dumps(result)


@tool
def smart_pc_builder(requirements: str):
    """Build PC based on requirements like gaming, AI, editing, Ryzen, ASUS GPU, RAM size, etc."""
    data = extract_requirements(requirements)
    result = build_pc_with_requirements(data)
    return json.dumps(result)