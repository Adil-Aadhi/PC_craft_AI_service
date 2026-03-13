import re

def extract_budget(text: str):

    text = text.lower()

    # match numbers like 50000
    match = re.search(r"\d{4,6}", text)
    if match:
        return int(match.group())

    # match 50k
    match = re.search(r"(\d+)\s*k", text)
    if match:
        return int(match.group(1)) * 1000

    # match lakh
    match = re.search(r"(\d+)\s*lakh", text)
    if match:
        return int(match.group(1)) * 100000

    return None