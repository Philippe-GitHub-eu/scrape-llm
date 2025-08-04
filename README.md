# scrape-llm

Small Python scraping + LLM pipeline with strict resource/output caps.
Works with Ollama (local) or Hugging Face Inference.

## Quick start (Windows / PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements.txt

# Copy .env.example to .env and adjust values
copy .env.example .env
notepad .env
```

## Next Steps

It is an interesting project that I wanted to do, as it helps understanding basic LLM use cases.
Therefore, I will go forward with different iteretions and models:
- Vision: llava:7b or qwen2-vl:2b
- Audio output: whisper-tiny
- Audio: Input: Qwen2-Audio 7B



