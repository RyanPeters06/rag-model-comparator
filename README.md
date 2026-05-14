# AI RAG Comparator — Plant Operations Edition

A desktop tool for production plant operators and engineers to evaluate how different AI models reason over your own operational documentation. Load your manuals, procedures, and maintenance records once — then interrogate 16 AI models simultaneously and compare their answers side by side.

Built for environments where generic AI knowledge is not enough: the models answer from *your* plant data, not from the internet.

---

## The Problem This Solves

Modern AI models are impressive at general knowledge but unreliable for plant-specific questions:

- *"What is the correct torque spec for the HP compressor stage 3 bolts?"* — a general model will guess.
- *"What does Alarm 47 mean on the Siemens S7 controller?"* — it might hallucinate a plausible-sounding answer.
- *"What is the lockout/tagout procedure for the cooling water pump on Train B?"* — getting this wrong is a safety incident.

This tool solves that by loading your actual plant documentation into a local vector database. Every query automatically retrieves the most relevant sections from your manuals before asking any model — so the AI is reasoning off your procedures, not its training data.

It also lets you compare 16 models at once to find which one reasons most accurately over your specific documentation.

---

## How It Works

```
Your Question
     │
     ▼
┌─────────────────────────────────┐
│  Local RAG Pipeline (offline)   │
│  ┌─────────────────────────┐   │
│  │  FAISS Vector Index     │   │
│  │  (your PDFs, chunked)   │   │
│  └────────────┬────────────┘   │
│               │ top 5 relevant  │
│               │ chunks          │
└───────────────┼─────────────────┘
                │
                ▼
    System Prompt = [retrieved context] + question
                │
    ┌───────────┴──────────────────────────────────┐
    │         16 models queried in parallel         │
    └──────┬──────┬──────┬──────┬──────┬──────┬────┘
           │      │      │      │      │      │
        Claude  GPT-4o Gemini DeepSeek Grok Llama ...
           │      │      │      │      │      │
    ┌──────▼──────▼──────▼──────▼──────▼──────▼────┐
    │      Streaming responses shown side by side   │
    │      with response time, cost, and sources    │
    └───────────────────────────────────────────────┘
```

The vector index is built and stored locally — no plant data ever leaves your machine during indexing. Queries do send the retrieved text chunks to whichever AI APIs you have enabled.

---

## Models Supported

| Provider | Models |
|---|---|
| Anthropic | Claude Haiku 4.5, Claude Sonnet 4.6 |
| OpenAI | GPT-4o Mini, GPT-4o, o4-mini |
| Google | Gemini 2.0 Flash, Gemini 2.5 Pro |
| DeepSeek | DeepSeek V3, DeepSeek R1 |
| Mistral | Mistral Large, Mistral Small |
| xAI | Grok 3, Grok 3 Mini |
| Meta (via OpenRouter) | Llama 4 Maverick, Llama 4 Scout |
| Alibaba (via OpenRouter) | Qwen3 235B |

You don't need all 16. Enable only the models you have API keys for — the rest show a clear error and stay out of the way.

---

## Features

- **Side-by-side streaming responses** — all models answer in parallel, text appears as it generates
- **Local RAG pipeline** — FAISS + ONNX embeddings, runs fully offline, no cloud indexing
- **Source citations** — each response shows exactly which manual pages were retrieved
- **Ground truth scoring** — paste the correct answer and the tool highlights which models got it right
- **Cost tracking** — estimated API cost per query shown per model
- **Export to CSV** — save a full comparison session for review
- **Persistent index** — build the index once, reuse it every session
- **Per-model enable/disable** — run only the models you want on a given session
- **Dark theme** — colour-coded by provider

---

## Typical Use Cases

**Maintenance procedure validation** — ask the same question about a procedure across all models and check which ones cite the correct page from your SOP manual.

**Training material generation** — draft operator training content, compare which model produces the most accurate and readable output against your actual procedures.

**Alarm and fault diagnosis** — query your fault-finding guides and compare how different models walk through the diagnostic steps.

**Regulatory compliance queries** — load your compliance documentation and evaluate which models correctly interpret permit requirements or safety standards.

**Cost benchmarking** — compare quality vs cost across models to decide which to integrate into a production workflow. Gemini Flash at $0.07/1,000 queries vs Grok 3 at $7.50/1,000 queries — is the difference worth it for your application?

---

## Quick Start

**1. Clone and install**
```bash
git clone https://github.com/your-username/ai-rag-comparator.git
cd ai-rag-comparator
pip install -r requirements.txt
```

**2. Configure API keys**
```bash
copy .env.example .env
# Open .env and paste in your keys — you only need one to get started
```

**3. Run**
```bash
python main.py
```

**4. Load your documentation**
- Click **"+ Add PDFs"** in the Knowledge Base panel
- Select your plant manuals, P&IDs, SOPs, maintenance records
- Click **"Build Index"** — takes ~1 minute per 100 pages, saved permanently after

**5. Start comparing**
- Type a question in the query box
- Click **"Send to All"**
- Watch 16 models answer simultaneously, with citations showing which pages they drew from

Full setup details, API key sources, pricing tables, and troubleshooting are in [SETUP.md](SETUP.md).

---

## Privacy and Data Handling

- **Indexing is fully local** — your PDFs are processed on your machine using a local ONNX model. No document content is sent anywhere during index building.
- **Query context is sent to AI APIs** — when you submit a question, the retrieved text chunks (excerpts from your manuals) are sent to whichever AI providers you query. Review each provider's data handling policy if your documentation is sensitive.
- **API keys stay local** — keys are loaded from your `.env` file and never logged or transmitted beyond the provider's own API endpoint.
- **No telemetry** — this tool has no analytics, no call-home, no usage tracking.

---

## Requirements

- Python 3.11+
- Windows / macOS / Linux
- At least one AI provider API key
- ~500 MB disk space (ONNX embedding model cache)

---

## License

MIT
