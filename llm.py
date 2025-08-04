
import os, json
from typing import Optional, Dict, Any

USE_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")  # "ollama" or "hf"
MODEL = os.getenv("LLM_MODEL", "deepseek-r1:8b")  # Ollama tag or HF repo id # "llama3.1:8b-instruct-q4_0"
#To be added: Vision Models, probably llama instruct [Multi-Modal]

def _clean_json(txt: str) -> str:
    txt = txt.strip()
    if txt.startswith("```"):
        txt = txt.strip("`")
        first_nl = txt.find("\n")
        if first_nl != -1:
            txt = txt[first_nl+1:]
    l, r = txt.find("{"), txt.rfind("}")
    return txt[l:r+1] if l != -1 and r != -1 and r > l else txt

def generate_json(prompt: str, schema_hint: Optional[str] = None,
                  max_new_tokens: int = 256, temperature: float = 0.2) -> Dict[str, Any]:
    system = (
        "Produce ONLY valid compact JSON. No explanations, no markdown, no extra text. "
        "If a field is unknown, output null. Respond in <= "
        f"{max_new_tokens} tokens. "
        + (f"Schema: {schema_hint}" if schema_hint else "")
    )

    if USE_PROVIDER == "ollama":
        import ollama
        resp = ollama.chat(
            model=MODEL,
            format="json",
            options={
                "temperature": temperature,
                "num_predict": max_new_tokens,
                "num_ctx": 2048,
                "seed": 42,
            },
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        raw = resp["message"]["content"]
    else:
        from huggingface_hub import InferenceClient
        client = InferenceClient(model=MODEL, token=os.getenv("HF_TOKEN"))
        raw = client.chat.completions.create(
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": prompt}],
            max_tokens=max_new_tokens,
            temperature=temperature,
        ).choices[0].message.content

    return json.loads(_clean_json(raw))
