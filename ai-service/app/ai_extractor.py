import ollama
import json
import re

def extract_requirements(text: str):

    prompt = f"""
Extract PC build requirements from this text and return JSON only.

Text: {text}

Return this exact JSON format with no extra text, no markdown, no backticks:
{{
 "budget": number or null,
 "cpu_brand": string or null,
 "cpu_model": string or null,
 "gpu_brand": string or null,
 "gpu_model": string or null,
 "ram": number or null,
 "storage": number or null,
 "purpose": string or null
}}

Examples:

Input: Build gaming PC under 2 lakh with Ryzen CPU and ASUS GPU
Output:
{{"budget": 200000, "cpu_brand": "AMD", "cpu_model": "Ryzen", "gpu_brand": "ASUS", "gpu_model": null, "ram": null, "storage": null, "purpose": "gaming"}}

Input: PC build under 80000 for video editing with 32GB RAM
Output:
{{"budget": 80000, "cpu_brand": null, "cpu_model": null, "gpu_brand": null, "gpu_model": null, "ram": 32, "storage": null, "purpose": "editing"}}

Return ONLY the JSON object. Nothing else.
"""

    client = ollama.Client(host="http://host.docker.internal:11434")
    response = client.chat(
        model="mistral:7b-instruct-q4_0",
        messages=[{"role": "user", "content": prompt}]
    )

    raw = response["message"]["content"].strip()

    # Strip markdown code fences if Mistral wraps in ```json ... ```
    raw = re.sub(r"^```(?:json)?", "", raw).strip()
    raw = re.sub(r"```$", "", raw).strip()

    # Extract first JSON object found (handles extra text)
    match = re.search(r'\{.*\}', raw, re.DOTALL)
    if match:
        raw = match.group(0)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"budget": None}