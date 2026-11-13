# ReportPulse: Power BI validation assistant (proof of concept)

Upload a Power BI validation file (Refresh or Row-Level Security). The portal finds the problems, then an AI
assistant troubleshoots each one **as a conversation**: it suggests one fix, you report back, and it adapts. You can
also ask it to prepare a ready-to-apply code or configuration snippet in chat. It uses
RAG (Retrieval-Augmented Generation), so answers come from a knowledge base, not from hard-coded rules.
It can prepare implementation artifacts, but it never applies changes to a report.

```
backend/    FastAPI service: RAG engine + Groq or OpenAI. Holds the API key.
  knowledge/   the knowledge base: one Markdown file per topic (edit these to teach it)
  app/         API, RAG (chunking, embeddings, search), prompts, the troubleshooting loop
  tests/       offline tests (no key needed)
frontend/   React + Vite web page. Reads the Excel/CSV in the browser.
samples/    Refresh_Validation.xlsx and RLS_Validation.xlsx for testing
scripts/    make_zip.ps1 (safe zip for another computer)
docs/       workflow plan (PDF)
```

## The screen

A chat-style portal: a sidebar (New chat, Search chats, chats from this session) and a centred welcome with one message
box. Attach a validation file (or type a question) and send. The assistant replies inside the conversation with the
checks, the counts and the findings, and each finding opens its own troubleshooting conversation. Chats last until the
page is refreshed. Names and wording are in `frontend/src/config.js` (assistant name, subtitle, file limits).

## How it works

1. **Browser:** reads the file, detects the type, finds the problems with plain rules (counts are never AI-generated).
2. **You approve** each finding. Nothing is sent until you do. For Row-Level Security (RLS) the portal first asks how access should work.
3. **Backend `/api/troubleshoot`** (one round of the conversation):
   - cleans the error text and **searches the knowledge base** by meaning (embeddings) and by keyword together
   - gives the AI the best excerpts, the company guidance, the conversation so far and the file details
   - the AI replies with one next action, or questions to ask, or an escalation summary
   - guardrails: no repeated action, escalate after `MAX_ROUNDS`, never claim "from the knowledge base" when nothing matched
4. **You answer** with a button (It worked, Still failing, I can't do this step, Different error now) or free text. The page sends the full history next round.
5. **It worked** saves the case as *pending*. After a person approves it, the case is searchable, so the assistant learns from your own fixes.

New or unfamiliar errors are handled in three levels, shown on the card: *From the knowledge base*,
*General guidance, please verify*, or *Not enough information yet* (it asks, then escalates with a summary to send).

There is no runbook code. The former runbook is now plain knowledge documents in `backend/knowledge/`. The company
standards (timeout: reduce the data size first; processing error: gateway and credentials first; RLS: ask how access
should work) are in `knowledge/company-guidance.md`, which is given to the AI on every request.

## Run it (Windows, Python 3.9.13, Node 18+)

Backend, from the project root:

```bash
python -m venv backend\.venv
backend\.venv\Scripts\python -m pip install -r backend/requirements.txt
copy backend\.env.example backend\.env
```

Open `backend\.env`, keep `AI_PROVIDER=gemini`, and paste a newly created Gemini key after `GEMINI_API_KEY=`. The default model is `gemini-3.1-flash-lite`. Then check the key, and start the backend:

```bash
backend\.venv\Scripts\python backend\check_key.py
backend\.venv\Scripts\python -m uvicorn app.main:app --app-dir backend --port 8000
```

Frontend, in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The header shows the selected model and knowledge search mode. Gemini and Groq use keyword search; OpenAI can use embeddings and keyword search together.
Without a key the page still loads, but troubleshooting says the key is missing (there is no offline answer set).

## Provider keys

- The Gemini key goes only in `backend/.env` as `GEMINI_API_KEY` (or use `GROQ_API_KEY` with `AI_PROVIDER=groq`, or `OPENAI_API_KEY` with `AI_PROVIDER=openai`). It is read by the backend and never reaches the browser or the logs.
- `.env` is git-ignored and **left out of the zip** made by `scripts\make_zip.ps1`.
- Do not keep `.env` in a OneDrive folder. The backend logs a warning if it is.
- Gemini and Groq use keyword search in this app. OpenAI can additionally use embeddings; if those are unavailable, it falls back to keyword search.
- `check_key.py` tests the selected chat model and, when supported, the embedding model.

## Move it to another computer

```bash
powershell -ExecutionPolicy Bypass -File scripts\make_zip.ps1
```

This creates `release\ReportPulse-<date>.zip` without `.env`, `.venv`, `node_modules` or cached data. On the other
computer, unzip it and follow "Run it" above (create the venv, install, add the key).

## Check the quality

```bash
backend\.venv\Scripts\python backend\eval.py     # needs the key: runs scripted scenarios against the real AI
backend\.venv\Scripts\python -m pytest backend   # offline tests with a stand-in AI
cd frontend && npm test
```

`eval.py` checks that the timeout and processing-error fixes come first, that the assistant does not repeat a failed
fix, that a new error is not claimed as certain, and that RLS gives roles, DAX filters and a View as test.

## Teach it

- **Add knowledge:** drop a Markdown file in `backend/knowledge/` (copy an existing one for the header), then
  `POST /api/reindex` or restart. Embeddings are cached, so only new text is embedded.
- **Approve learned cases:** open http://localhost:8000/api/docs, use `GET /api/cases?status=pending`, then
  `POST /api/cases/{id}/approve` (or `/reject`).

## API

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | AI on or off, models, knowledge base size and search type |
| `POST /api/troubleshoot` | One round: `{ issue, file_type, error?, reports[], rows[], turns[], context? }` returns `{ status, basis, confidence, diagnosis, causes[], action?, questions[], escalation?, sources[], round }` |
| `POST /api/chat` | Free question for the side panel: returns `{ answer, sources[], basis }` |
| `POST /api/cases` | Save a resolved case (pending until approved) |
| `GET /api/cases`, `POST /api/cases/{id}/approve`, `.../reject` | Review learned cases |
| `POST /api/reindex` | Reload the knowledge documents |

Errors from the selected provider come back as `503` with `{ detail: { code, message } }` in plain language (`no_key`, `auth`, `model`,
`rate_limit`, `network`, `timeout`, `bad_answer`). Interactive docs: http://localhost:8000/api/docs
