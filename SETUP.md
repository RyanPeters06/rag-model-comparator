# Plant Maintenance AI Model Comparison Tool — Setup Guide

## What This Tool Does

A desktop application that sends the same question to 16 AI models simultaneously and displays all responses side-by-side. It includes a local RAG (Retrieval-Augmented Generation) pipeline so you can load your own plant manuals and maintenance PDFs — the tool will automatically find the most relevant sections and include them in every query.

---

## Step 1: Install Python

You need Python 3.11 or newer.

- Download from https://www.python.org/downloads/
- During installation, check **"Add Python to PATH"**
- Verify: open a terminal and run `python --version`

---

## Step 2: Install Dependencies

Open a terminal in the project folder (the folder containing `main.py`) and run:

```
pip install -r requirements.txt
```

This installs:
- **PyQt5** — desktop GUI framework
- **anthropic** — Claude SDK
- **openai** — OpenAI SDK (also used for DeepSeek, xAI, OpenRouter)
- **google-generativeai** — Google Gemini SDK
- **mistralai** — Mistral SDK
- **sentence-transformers** — Local embedding model (downloads ~90 MB on first run)
- **faiss-cpu** — Local vector database for RAG
- **pymupdf** — PDF text extraction
- **numpy, pandas** — Data processing
- **python-dotenv** — API key loading

**First-time note:** When you first run the app, `sentence-transformers` will download the `all-MiniLM-L6-v2` model (~90 MB) to your local cache (`~/.cache/huggingface/`). Subsequent runs use the cached model.

---

## Step 3: Configure API Keys

### Create your .env file

Copy the template and fill it in:

```
copy .env.example .env
```

Then open `.env` in any text editor and add your keys:

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...
MISTRAL_API_KEY=...
XAI_API_KEY=xai-...
OPENROUTER_API_KEY=sk-or-...
```

You don't need all keys — models without a key will show a clear error message in their panel. You can still use the tool with just one or two providers.

---

## Step 4: Get API Keys

### Anthropic (Claude Haiku 4.5, Claude Sonnet 4.6)
- Sign up: https://console.anthropic.com/
- Navigate to: Settings → API Keys → Create Key
- **Free tier:** None. Requires a paid account with credits.
- **Variable:** `ANTHROPIC_API_KEY`

### OpenAI (GPT-4o Mini, GPT-4o, o4-mini)
- Sign up: https://platform.openai.com/
- Navigate to: API Keys → Create new secret key
- **Free tier:** New accounts may receive $5 free credit.
- **Variable:** `OPENAI_API_KEY`

### Google AI (Gemini 2.0 Flash, Gemini 2.5 Pro)
- Sign up: https://aistudio.google.com/
- Navigate to: Get API Key → Create API key
- **Free tier:** Gemini 2.0 Flash has a generous free tier (15 requests/minute, 1,500 requests/day).
- **Variable:** `GOOGLE_API_KEY`

### DeepSeek (DeepSeek V3, DeepSeek R1)
- Sign up: https://platform.deepseek.com/
- Navigate to: API Keys → Create API Key
- **Free tier:** New accounts get a small free quota.
- **Variable:** `DEEPSEEK_API_KEY`

### Mistral (Mistral Large, Mistral Small)
- Sign up: https://console.mistral.ai/
- Navigate to: API Keys → Create new key
- **Free tier:** Mistral offers limited free access for experimentation.
- **Variable:** `MISTRAL_API_KEY`

### xAI (Grok 3, Grok 3 Mini)
- Sign up: https://x.ai/api
- Navigate to: API Keys → Create Key
- **Free tier:** Check current offer at x.ai/api (limited free credits available).
- **Variable:** `XAI_API_KEY`

### OpenRouter (Llama 4 Maverick, Llama 4 Scout, Qwen3 235B)
- Sign up: https://openrouter.ai/
- Navigate to: Keys → Create Key
- **Free tier:** OpenRouter offers free credits on sign-up. Some models have free tiers.
- **Variable:** `OPENROUTER_API_KEY`

---

## Step 5: Run the Application

```
python main.py
```

The application window opens. Models without API keys show a clear error — all other models work immediately.

---

## Estimated Cost Per 1,000 Questions

Assumes an average of 500 input tokens (question + RAG context) and 400 output tokens per query.

| Model | Provider | Per Query | Per 1,000 Questions |
|---|---|---|---|
| Claude Haiku 4.5 | Anthropic | ~$0.0006 | ~$0.56 |
| Claude Sonnet 4.6 | Anthropic | ~$0.0075 | ~$7.50 |
| GPT-4o Mini | OpenAI | ~$0.0001 | ~$0.10 |
| GPT-4o | OpenAI | ~$0.0053 | ~$5.25 |
| o4-mini | OpenAI | ~$0.0023 | ~$2.31 |
| Gemini 2.0 Flash | Google | ~$0.00007 | ~$0.07 |
| Gemini 2.5 Pro | Google | ~$0.0027 | ~$2.63 |
| DeepSeek V3 | DeepSeek | ~$0.0002 | ~$0.18 |
| DeepSeek R1 | DeepSeek | ~$0.0004 | ~$0.39 |
| Mistral Large | Mistral | ~$0.0026 | ~$2.60 |
| Mistral Small | Mistral | ~$0.00008 | ~$0.08 |
| Grok 3 | xAI | ~$0.0075 | ~$7.50 |
| Grok 3 Mini | xAI | ~$0.00035 | ~$0.35 |
| Llama 4 Maverick | OpenRouter | ~$0.00018 | ~$0.18 |
| Llama 4 Scout | OpenRouter | ~$0.00006 | ~$0.06 |
| Qwen3 235B | OpenRouter | ~$0.00021 | ~$0.21 |

*Prices are approximate and subject to change. Check provider dashboards for current pricing.*

---

## Using the Knowledge Base (RAG Pipeline)

### Loading PDFs

1. In the left **Knowledge Base** panel, click **"+ Add PDFs"**
2. Select one or more PDF files (plant manuals, maintenance guides, etc.)
3. Click **"Build Index"** — this extracts text, creates embeddings, and builds a searchable database
4. The status shows how many text chunks were indexed

**How long does indexing take?**
- ~100 pages of PDF: 30–90 seconds (depending on your CPU)
- ~500 pages: 3–8 minutes
- ~2,000 pages: 15–30 minutes
- The index is saved to disk (`./knowledge_base_index/`) and reloaded instantly on next launch

### Adding New Manuals After Initial Setup

1. Click **"+ Add PDFs"** and select the new files
2. Click **"Build Index"** again — this rebuilds the full index including the new documents
3. The old index is replaced; rebuilding takes the same time as the initial build

### How RAG Works

When you send a question:
1. Your question is embedded using a local AI model (no API call, runs offline)
2. The 5 most relevant document chunks are retrieved from the index
3. Those chunks are automatically prepended to every model's system prompt
4. Each model's response panel shows which sources were retrieved

This means the AI models answer based on your actual plant documentation rather than general knowledge.

### If the Index Gets Corrupted

Delete the index folder and rebuild:

```
rmdir /s /q knowledge_base_index
```

Then reopen the app and click "Build Index" again.

---

## Using Ground Truth Verification

In the **Ground Truth** field, paste the correct answer to your question. After querying:
- Panels with a **green border** matched the ground truth (≥25% keyword overlap)
- Panels with a **red border** did not match

This is a keyword-overlap heuristic, not an exact match — it's most useful for factual questions with specific terminology.

---

## Exporting Results

Click **"Export Results"** to save all current responses to a CSV file in the `./exports/` folder. The file includes:
- Question text
- Each model's full response
- Response time
- Estimated cost
- Token counts
- Source documents cited

---

## Troubleshooting

### "API key 'X' is not set" error in a panel
- Open your `.env` file and verify the key is present and has no leading/trailing spaces
- The `.env` file must be in the same folder as `main.py`
- Restart the application after editing `.env`

### App opens but all panels show errors
- Check that your `.env` file exists (not just `.env.example`)
- Run `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.environ.get('ANTHROPIC_API_KEY', 'NOT SET'))"` to verify keys are loading

### "No module named X" error on startup
- Re-run: `pip install -r requirements.txt`
- If using multiple Python installs, ensure you're using the same Python that has the packages: `python -m pip install -r requirements.txt`

### DeepSeek R1 shows "[Thinking...]" blocks
- This is correct behavior. DeepSeek R1 is a reasoning model that shows its chain-of-thought before the final answer.

### Gemini models return empty responses
- Check your Google API key is for **Google AI Studio** (not Google Cloud)
- Verify the key has the Generative Language API enabled

### Index build fails with "out of memory"
- Reduce the number of PDFs in a single batch
- Index PDFs in groups of 5–10 at a time

### faiss-cpu installation fails on Windows
- Try: `pip install faiss-cpu --no-cache-dir`
- If that fails: `conda install -c conda-forge faiss-cpu` (requires Anaconda)

### PyQt5 installation fails
- Try: `pip install PyQt5 --config-settings --confirm-license=`
- Alternative: `pip install PySide6` (you would need to change imports in the code)

### Models respond slowly
- This is normal for larger models (GPT-4o, Gemini 2.5 Pro, Grok 3, Claude Sonnet)
- All models run in parallel — you don't wait for one to finish before others start

---

## File Structure Reference

```
AI comparison program/
├── main.py                 ← Run this to start the application
├── requirements.txt        ← Python package dependencies
├── .env                    ← Your API keys (create this from .env.example)
├── .env.example            ← Template for .env
├── SETUP.md                ← This file
├── settings.json           ← Auto-created: model enable/disable states
├── knowledge_base_index/   ← Auto-created: FAISS index files
├── exports/                ← Auto-created: CSV exports land here
└── app/                    ← Application source code
```
