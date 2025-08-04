# llm_vision.py
import os
from typing import List, Optional

def describe_images(image_paths: List[str], hint: Optional[str] = None,
                    max_new_tokens: int = 64, temperature: float = 0.1) -> List[Optional[str]]:
    """
    Return short captions for images via a local vision model in Ollama.
    Requires env: LLM_VISION_MODEL (e.g., 'llava:7b' or 'qwen2-vl:2b').
    If not set, returns [None]*N (skips vision to conserve resources).
    """
    model = os.getenv("LLM_VISION_MODEL")
    if not model:
        return [None] * len(image_paths)

    import ollama
    captions = []
    for p in image_paths:
        msg = "Caption this image in ≤ 15 words. Be factual and concise."
        if hint: msg += f" Context: {hint}"
        resp = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": msg, "images": [p]}],
            options={"num_predict": max_new_tokens, "temperature": temperature, "seed": 42},
        )
        captions.append((resp.get("message", {}) or {}).get("content", "").strip() or None)
    return captions
