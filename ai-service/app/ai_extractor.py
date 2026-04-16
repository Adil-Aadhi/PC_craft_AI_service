from google import genai
import json
import re
import os
import time

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

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

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.1-flash-lite-preview",
                contents=prompt
            )
            raw = response.text.strip()
            raw = re.sub(r"^```(?:json)?", "", raw).strip()
            raw = re.sub(r"```$", "", raw).strip()
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                raw = match.group(0)
            return json.loads(raw)
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(30)
                continue
            return {"budget": None}