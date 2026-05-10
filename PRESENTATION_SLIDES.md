# SecurCoach AI — Presentation Slides (Outline)

Slide 1 — Title
- Title: SecurCoach AI — RAG + Agent Upgrade
- Subtitle: Production-ready chatbot demo
- Presenter: Your Name, Course, Date

Slide 2 — Goals
- Objective: Move from basic LLM wrapper to production-ready AI app
- Requirements: RAG or Agentic AI + prompt defenses

Slide 3 — Design Decisions
- Chosen architectures: Implemented both RAG and a limited Agentic loop
- Why: RAG provides grounded answers; agent enables controlled tool use
- Models & frameworks: Groq client (existing), `sentence-transformers` for embeddings, Streamlit UI

Slide 4 — System Architecture
- Diagram (speak): Browser -> Streamlit -> LLM client + RAG store
- Components: `streamlit/app.py`, `streamlit/llm_engine.py`, `streamlit/rag.py`, `db/auth`

Slide 5 — RAG Implementation
- Local vector store: `streamlit/rag.py` (SentenceTransformers, persisted to `vectorstore.pkl`)
- UI: sidebar uploader + index/clear buttons
- Retrieval flow: top-k passages inserted as `system` context

Slide 6 — Agentic Loop
- Model can emit tool call tags: `<CALL_TOOL name="search_docs">query</CALL_TOOL>`
- App runs the safe `search_docs` tool against the RAG store and re-queries model
- No arbitrary code execution; tool is read-only

Slide 7 — Prompt Defenses
- Input sanitization: `sanitize_input()` filters injection patterns
- Output cleaning: `_clean_response()` removes metadata & hides TITLE lines
- UI-level protections: HTML escaping for user content

Slide 8 — Demo Plan
- Show indexing: upload a policy or sample doc and index it
- Ask a question referencing the doc — show retrieval context
- Trigger agentic search via model instruction and show final grounded answer

Slide 9 — Limitations & Future Work
- Local vector store suitable for demo; recommend Pinecone/Weaviate/Chroma for production
- Add Langfuse or observability for prompt/version tracing
- Expand agent tools: safe web search, sandboxed Python execution (carefully constrained)

Slide 10 — Repo & App Links
- Repo: (paste your GitHub URL)
- Live demo: (paste Streamlit Cloud URL)

Slide 11 — Appendix / Prompt Engineering
- System prompts used: high-level examples stored in `streamlit/llm_engine.py`
- Sanitization rules and examples of adversarial inputs and mitigations

Speaker Notes: Use these bullets as prompts when presenting; keep demo steps short and rehearsed. Convert to PPTX or PDF with `pandoc` or copy into PowerPoint.

Conversion tip (optional):
```bash
pandoc PRESENTATION_SLIDES.md -o SecurCoach_Slides.pdf
```
