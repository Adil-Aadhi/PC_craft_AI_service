import re
from google import genai
import os
import time

from .tools import (
    get_best_gpu_under_budget,
    get_best_cpu_under_budget,
    build_pc_with_requirements
)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def chat_with_gemini(question: str) -> str:
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=question
            )
            return response.text
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(30)
                continue
            return f"AI service temporarily unavailable. Please try again later."

def extract_requirements_regex(question: str) -> dict:
    q = question.lower().replace(",", "")

    budget = None
    lakh = re.search(r'(\d+(?:\.\d+)?)\s*lakh', q)
    if lakh:
        budget = int(float(lakh.group(1)) * 100000)
    else:
        k = re.search(r'(\d+)\s*k\b', q)
        if k:
            budget = int(k.group(1)) * 1000
        else:
            nums = re.findall(r'\d{4,}', q)
            if nums:
                budget = int(nums[0])

    cpu_brand = None
    cpu_model = None
    if "ryzen" in q or "amd" in q:
        cpu_brand = "AMD"
        ryzen = re.search(r'ryzen\s*\d+', q)
        if ryzen:
            cpu_model = ryzen.group(0)
    elif "intel" in q or "core i" in q:
        cpu_brand = "Intel"
        intel = re.search(r'i[3579]\s*-?\s*\d+', q)
        if intel:
            cpu_model = intel.group(0)

    gpu_brand = None
    gpu_model = None
    if "nvidia" in q or "rtx" in q or "gtx" in q:
        gpu_brand = "Nvidia"
        rtx = re.search(r'rtx\s*\d+\w*', q)
        if rtx:
            gpu_model = rtx.group(0)
    elif "asus" in q:
        gpu_brand = "ASUS"
    elif "msi" in q:
        gpu_brand = "MSI"
    elif "gigabyte" in q:
        gpu_brand = "Gigabyte"
    elif "amd" in q and ("rx" in q or "radeon" in q):
        gpu_brand = "AMD"
        rx = re.search(r'rx\s*\d+\w*', q)
        if rx:
            gpu_model = rx.group(0)

    ram = None
    ram_match = re.search(r'(\d+)\s*gb\s*ram', q)
    if ram_match:
        ram = int(ram_match.group(1))

    storage = None
    storage_match = re.search(r'(\d+)\s*(tb|gb)\s*(ssd|hdd|storage)', q)
    if storage_match:
        val = int(storage_match.group(1))
        unit = storage_match.group(2)
        storage = val * 1000 if unit == "tb" else val

    purpose = None
    if "gaming" in q:
        purpose = "gaming"
    elif "editing" in q or "video" in q:
        purpose = "editing"
    elif "workstation" in q or "3d" in q:
        purpose = "workstation"
    elif "ai" in q or "ml" in q:
        purpose = "ai"

    return {
        "budget": budget,
        "cpu_brand": cpu_brand,
        "cpu_model": cpu_model,
        "gpu_brand": gpu_brand,
        "gpu_model": gpu_model,
        "ram": ram,
        "storage": storage,
        "purpose": purpose
    }

# def run_langchain_agent(question: str):
#     q = question.lower()

#     try:
#         if "best gpu" in q:
#             data = extract_requirements_regex(question)
#             gpus = get_best_gpu_under_budget(data.get("budget") or 0)
#             return {"type": "gpu", "results": gpus}

#         if "best cpu" in q:
#             data = extract_requirements_regex(question)
#             cpu = get_best_cpu_under_budget(data.get("budget") or 0)
#             return {"type": "cpu", "results": cpu}

#         if any(word in q for word in [
#             "pc", "build", "gaming", "editing", "ai", "workstation", "computer"
#         ]):
#             data = extract_requirements_regex(question)
#             if not data.get("budget"):
#                 return {
#                     "type": "error",
#                     "answer": "Please mention a budget, e.g. 'under 1.5 lakh' or '80000'."
#                 }
#             result = build_pc_with_requirements(data)
#             return {"type": "smart_build", "result": result}

#         response = chat_with_gemini(question)
#         return {"type": "chat", "answer": response}

#     except Exception as e:
#         return {"error": str(e)}

def run_langchain_agent(question: str):
    q = question.lower()

    try:
        # 1. Extract requirements first to see what we actually have
        data = extract_requirements_regex(question)
        has_budget = data.get("budget") is not None

        # 2. ONLY trigger DB tools if a budget is present
        if has_budget:
            if "best gpu" in q:
                gpus = get_best_gpu_under_budget(data.get("budget"))
                return {"type": "gpu", "results": gpus}

            if "best cpu" in q:
                cpu = get_best_cpu_under_budget(data.get("budget"))
                return {"type": "cpu", "results": cpu}

            if any(word in q for word in ["pc", "build", "gaming", "editing", "ai", "workstation", "computer"]):
                result = build_pc_with_requirements(data)
                return {"type": "smart_build", "result": result}

        # 3. If it's a general question or NO budget was found, use Gemini Chat
        # This will catch "Is Ryzen or Intel best?"
        response = chat_with_gemini(question)
        return {"type": "chat", "answer": response}

    except Exception as e:
        return {"error": str(e)}