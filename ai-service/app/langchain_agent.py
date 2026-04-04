from langchain_ollama import OllamaLLM
import re

from .tools import (
    get_best_gpu_under_budget,
    get_best_cpu_under_budget,
    build_pc_with_requirements
)

# -------------------------
# LLM (for plain chat only)
# -------------------------
llm = OllamaLLM(
    model="mistral:7b-instruct-q4_0",
    base_url="http://host.docker.internal:11434",
    temperature=0
)

# -------------------------
# Pure regex requirement extractor
# NO Ollama call — instant
# -------------------------
def extract_requirements_regex(question: str) -> dict:
    q = question.lower().replace(",", "")

    # --- Budget ---
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

    # --- CPU brand ---
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

    # --- GPU brand ---
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

    # --- RAM ---
    ram = None
    ram_match = re.search(r'(\d+)\s*gb\s*ram', q)
    if ram_match:
        ram = int(ram_match.group(1))

    # --- Storage ---
    storage = None
    storage_match = re.search(r'(\d+)\s*(tb|gb)\s*(ssd|hdd|storage)', q)
    if storage_match:
        val = int(storage_match.group(1))
        unit = storage_match.group(2)
        storage = val * 1000 if unit == "tb" else val

    # --- Purpose ---
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

# -------------------------
# Router
# -------------------------
def run_langchain_agent(question: str):
    q = question.lower()

    try:
        # ---------------- GPU only ----------------
        if "best gpu" in q:
            data = extract_requirements_regex(question)
            gpus = get_best_gpu_under_budget(data.get("budget") or 0)
            return {"type": "gpu", "results": gpus}

        # ---------------- CPU only ----------------
        if "best cpu" in q:
            data = extract_requirements_regex(question)
            cpu = get_best_cpu_under_budget(data.get("budget") or 0)
            return {"type": "cpu", "results": cpu}

        # ---------------- PC Build ----------------
        if any(word in q for word in [
            "pc", "build", "gaming", "editing", "ai", "workstation", "computer"
        ]):
            data = extract_requirements_regex(question)

            if not data.get("budget"):
                return {
                    "type": "error",
                    "answer": "Please mention a budget, e.g. 'under 1.5 lakh' or '80000'."
                }

            result = build_pc_with_requirements(data)
            return {"type": "smart_build", "result": result}

        # ---------------- Normal chat ----------------
        response = llm.invoke(question)
        return {"type": "chat", "answer": response}

    except Exception as e:
        return {"error": str(e)}