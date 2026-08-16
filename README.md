# Job Search Copilot

A self-hosted, AI-powered job search assistant: upload or build your CV, get
AI-ranked job matches from multiple job boards, draft tailored
applications for review, track everything on a kanban board, check live
salary data, and chat with a local-LLM copilot about your search. Runs
entirely on your own server via Docker Compose, using [Ollama](https://ollama.com)
for all AI features - no data leaves your infrastructure.

## Stack

- **Backend**: FastAPI (Python 3.11), PostgreSQL + [pgvector](https://github.com/pgvector/pgvector)
  for embeddings, Redis + [RQ](https://python-rq.org) for background jobs,
  APScheduler for polling/cron, Alembic for migrations.
- **Frontend**: React + TypeScript + Vite, TanStack Query, Tailwind CSS,
  Zustand, React Hook Form + Zod.
- **AI**: [Ollama](https://ollama.com), self-hosted - a chat/reasoning model
  (default `llama3.1:8b`) for extraction/matching/drafting/chat, and an
  embedding model (default `nomic-embed-text`) for Smart Match.

**Documentation**: this README covers setup and running the app. For how
it actually works and why it's built this way, see
**[APP_FLOW_AND_FEATURES.md](APP_FLOW_AND_FEATURES.md)** (every feature's
flow, end to end). For a file-by-file map of the codebase - what each file
is for and why - see **[CODE_DOCUMENTATION.md](CODE_DOCUMENTATION.md)**.

Short version of the two decisions that shape everything else:

- **Auto-apply is review-then-submit, always.** The AI drafts a tailored
  resume, cover letter, and answers to common questions - you always click
  submit yourself, on the real site. There is no code anywhere in this repo
  that logs into LinkedIn/Indeed/etc. and submits on your behalf; that
  requires automating around platform bot-detection with stored
  credentials, which risks a permanent account ban and violates those
  platforms' Terms of Service.
- **Job sources are public/official APIs plus links you add**, not scraping
  of authenticated platforms. Built-in: Adzuna, Remotive, RemoteOK,
  Arbeitnow, USAJobs, The Muse, and any company's public Greenhouse/Lever
  board. You can add your own regional job board as an RSS/Atom feed from
  Settings.

## Quick start

1. Install [Docker](https://docs.docker.com/get-docker/) on your server.
2. Copy `.env.example` to `.env` and fill in at least `SECRET_KEY` (any long
   random string) and Postgres credentials. Everything else has a sane
   default; job-source API keys (Adzuna, USAJobs) are optional - sources
   that need a key you haven't set are just skipped, not fatal.
3. `docker compose up -d --build`
4. First boot: the `ollama-init` service automatically pulls the chat and
   embedding models (a few GB - this takes a while on first run). Watch
   progress with `docker compose logs -f ollama-init`.
5. Once `ollama-init` finishes, open `http://your-server:8080`. The first
   thing you'll be asked to do is create the owner account - this only
   works once (see "Auth model" below), then registration locks itself.

That's it - Postgres, Redis, Ollama, the API, a background worker, the
scheduler, and the frontend are all running as one stack.

## Using it

1. **Profile → CV**: upload an existing resume (PDF/DOCX/TXT) to have it
   parsed automatically, or fill in the form directly (LinkedIn-style
   sections: experience, education, skills, projects, certifications,
   languages). Either way, you review and confirm before it's saved -
   nothing from an upload is written to your profile without you seeing it
   first. Download a formatted PDF any time from the same page.
2. **Settings**: the built-in job sources (Remotive, RemoteOK, Arbeitnow,
   The Muse) are seeded automatically and start polling right away. Add
   Adzuna/USAJobs API keys in `.env` for more coverage, or add any
   company's Greenhouse/Lever board or a regional board's RSS feed here.
3. **Smart Match**: once your profile has skills/experience and job
   sources have run at least one poll cycle, matches appear automatically
   (background workers do the embedding + LLM scoring - no action needed).
4. **Applications**: from a job's detail page, "Start application draft"
   generates a tailored resume + cover letter + draft answers. Review,
   edit, download the tailored PDF, then apply on the real site and mark
   it "Applied" - the kanban board tracks it from there.
5. **Market Insights**: salary ranges by role/location, sourced from your
   ingested job postings (always available) plus Adzuna if configured.
6. **Copilot**: a chat assistant grounded in your profile (and, if opened
   from a job page, that job) for resume feedback, interview prep, etc.

## Repo layout

```
backend/app/
  models/          SQLAlchemy ORM models
  schemas/         Pydantic request/response DTOs
  routers/         FastAPI HTTP endpoints (thin)
  services/        business logic, shared by routers (async) and workers (sync)
  integrations/    Ollama client, job-source adapters, salary-data adapters
  workers/         RQ tasks + the APScheduler process
  templates/cv/    Jinja2/CSS resume templates rendered to PDF via WeasyPrint
frontend/src/
  api/             axios client + hand-written API types
  features/        one folder per domain (auth, profile, jobs, matching, applications, salary, chat)
  pages/           route-level components
  components/ui/   small shadcn/ui-style primitives
```

## Development (without Docker)

Backend:
```
cd backend
uv venv && uv pip install -e ".[dev]"
# point DATABASE_URL/SYNC_DATABASE_URL/REDIS_URL/OLLAMA_BASE_URL at local services
alembic upgrade head
uvicorn app.main:app --reload
# in separate terminals:
python -m app.workers.worker
python -m app.workers.scheduler
```

Frontend:
```
cd frontend
npm install
npm run dev   # proxies /api to http://localhost:8000 - see vite.config.ts
```

Run `npm run generate:types` (with the backend running) to regenerate
`src/api/schema.d.ts` from the live OpenAPI schema via openapi-typescript;
`src/api/types.ts` is a hand-written stand-in used by the app today and is
worth reconciling against real codegen as the schema evolves.

Backend tests: `cd backend && pytest`. These cover pure business logic
(password/token handling, salary percentile math, content-hash change
detection, HTML cleaning) and don't need Postgres/Redis/Ollama running.
Frontend: `npm run build` runs a full type-check via `tsc -b`.

## Notes on scope and honesty about what's verified

- The full SQLAlchemy model graph, the Alembic migration (rendered and
  verified as valid SQL end-to-end in offline mode), the complete FastAPI
  app (all 30 endpoints resolve correctly), and the frontend (`tsc -b` and
  `vite build` both succeed) were all validated while building this. What
  was **not** possible to validate in this environment: an actual live run
  against real Postgres/Redis/Ollama containers (this sandbox couldn't pull
  Docker images), so treat first boot on your server as the real
  integration test, and check `docker compose logs` if any service doesn't
  come up clean.
- The `bls` salary source (`backend/app/integrations/salary_apis/bls.py`)
  ships with an **empty** role→series-ID mapping on purpose - correctly
  mapping a role title to BLS's exact OES series ID isn't something to
  guess at, so it's an opt-in extension point with instructions in the
  module docstring rather than a pre-filled (and possibly wrong) table.
  Salary insights work fully without it, via aggregated job-posting data
  and Adzuna.
- The Settings page currently shows server configuration (models, which
  API keys are set) as **read-only** - editable via `.env` and a restart.
  The `app_settings` table exists in the schema for making this
  live-editable without a redeploy, but that plumbing isn't wired up yet;
  said honestly rather than implied as finished.
- Job-source adapters (Adzuna, USAJobs, The Muse, etc.) are built against
  each provider's documented response shape from general knowledge, not
  tested against live traffic here - they're written defensively (a
  failing source is logged and skipped, never crashes the polling sweep),
  but it's worth checking `docker compose logs worker` after first setup
  in case any one API's shape has drifted since.
- The frontend bundle is a single ~950KB JS chunk (Vite warns about this).
  It works fine as-is for a personal/internal tool; splitting it further
  (route-based `React.lazy`) would be a reasonable follow-up, not required
  for correctness.
