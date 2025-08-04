# scrape-llm

Small Python scraping + LLM pipeline with strict resource/output caps.
Works with Ollama (local) or Hugging Face Inference.

# scrape-llm

Lightweight web-scraper that combines **text extraction, image sampling, and local LLM reasoning**.  
Runs fully offline with **Ollama** (Gemma 3, DeepSeek R1 8B, Llama 3 8B, …) or via **Hugging Face Inference**.  
Includes a one-click Streamlit GUI.

---

## Key features
| Feature | Notes | Resource cap |
|---------|-------|--------------|
| **Text extraction** | Selectolax + Trafilatura first, LLM fills gaps | HTML trimmed to 6 kB |
| **Image sampling**  | Grabs ≤ 3 images ≥ 256 px, converts to JPEG | ≤ 2 MB each |
| **Optional captions** | Local vision LLM (Qwen2-VL 2B, LLaVA 7B, …) | 64 tokens / image |
| **GUI** | Streamlit at <http://localhost:8501> | none |
| **One-click launcher** | `start_scraper.cmd` | installs/updates deps automatically |

---

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

## Quick start (Windows 11) After latest merge

```powershell
git clone https://github.com/<YOUR-USER>/scrape-llm.git
cd scrape-llm

REM One-time: create .env from template and pick your model
copy .env.example .env
notepad .env            # set LLM_PROVIDER, LLM_MODEL, optional LLM_VISION_MODEL

REM One click from now on:
.\start_scraper.cmd
```


## Next Steps

It is an interesting project that I wanted to do, as it helps understanding basic LLM use cases.
Therefore, I will go forward with different iteretions and models:
- Vision: llava:7b or qwen2-vl:2b
- Audio output: whisper-tiny
- Audio: Input: Qwen2-Audio 7B

## And Try
.\.venv\Scripts\python.exe main.py https://www.bbc.com/news https://www.reuters.com






