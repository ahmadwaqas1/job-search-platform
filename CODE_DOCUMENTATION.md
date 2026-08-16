# Code Documentation

A file-by-file map of the codebase: what each thing is, why it exists, and
what depends on it. Read [APP_FLOW_AND_FEATURES.md](APP_FLOW_AND_FEATURES.md)
first if you haven't — it explains the *behavior*; this document explains
the *code that produces it*.

## How to use this document

- §1 explains the handful of patterns that repeat across many files, once,
  so the per-file tables below don't have to re-explain them every time.
- §2 and §3 are per-file reference tables for backend and frontend.
- §4 is a "if you want to do X, start at Y" cookbook for common changes.

---

## 1. Patterns used throughout the codebase

### 1.1 Backend: routers are thin, services hold the logic

Every backend feature is split into three layers:

```
routers/*.py     HTTP only: parse the request, call a service, shape the response.
services/*.py    The actual logic. No FastAPI imports here.
models/*.py      SQLAlchemy tables.
```

**Why**: `services/` functions are called from two different places -
routers (handling a live HTTP request, async) and workers (background
jobs, sync, no HTTP request in sight). Keeping logic out of routers means
it's usable from both without duplication. You'll notice several service
files (`matching_service.py`, `salary_service.py`, `job_ingestion_service.py`)
contain both an `async def` version and a `sync` version of similar
queries - that split exists for the same reason (see 1.2).

### 1.2 Backend: two SQLAlchemy engines, on purpose

`database.py` sets up **two** engines against the same Postgres database:

- an **async** one (`asyncpg` driver), used by every FastAPI router
- a **sync** one (`psycopg` driver), used by every RQ worker task and the
  scheduler

**Why**: FastAPI's request handlers are `async def` and expect an async
DB driver. RQ workers and APScheduler are plain synchronous Python
processes with no event loop running - forcing async code in there means
manually managing `asyncio.run()` everywhere, which gets messy fast. It's
simpler to give each side the driver style it naturally wants. Both point
at the same tables via the same SQLAlchemy models
(`get_async_session()` vs `get_sync_session()`).

### 1.3 Backend: how background jobs get scheduled and run

Three-piece system, all in `app/workers/`:

1. **`queue.py`** defines two Redis-backed queues, `default` (quick work:
   ingesting/upserting) and `llm` (slow work: anything that calls Ollama).
   Splitting them means one slow LLM call can't make quick housekeeping
   work wait behind it.
2. Routers enqueue work by calling e.g.
   `default_queue().enqueue("app.workers.cv_tasks.parse_cv_document", doc_id)`
   — note that's a **string** naming the function, not the function
   itself. That's a normal RQ pattern: it lets the API process enqueue
   work without importing the (heavier, sync-only) worker modules; the
   worker resolves and imports that path only when it actually runs the
   job.
3. **`worker.py`** is the process that drains both queues (`python -m
   app.workers.worker`). **`scheduler.py`** is a separate process (`python
   -m app.workers.scheduler`) whose only job is deciding *when* to enqueue
   recurring work — it doesn't do any of the work itself. It must only
   ever run as a single instance (see the file's docstring for why).

Every other file in `workers/` (`cv_tasks.py`, `embedding_tasks.py`,
`matching_tasks.py`, `ingestion_tasks.py`, `generation_tasks.py`,
`salary_tasks.py`) is just a set of plain functions that the worker
process calls by name. They tend to follow the same shape: open a sync DB
session, load a row by ID, do the (often Ollama-calling) work, save the
result.

### 1.4 Backend: the matching pipeline's "cheap filter, then expensive step" shape

`services/matching_service.py` is the one file worth reading closely if
you want to understand the app's core AI feature. The shape - cheap bulk
filtering via a database query, then an LLM call only on the few results
that survive - is deliberate and explained in the module docstring and in
[APP_FLOW_AND_FEATURES.md §4.4](APP_FLOW_AND_FEATURES.md#44-smart-match).
The same shape shows up in `salary_service.py` (compute cheaply from data
you already have; only call an external API when that's not enough).

### 1.5 Backend: job-source and salary-source "adapters"

`integrations/job_sources/*.py` all implement one interface
(`JobSourceAdapter.fetch(config) -> list[NormalizedJobPosting]`, defined in
`base.py`). `integrations/salary_apis/*.py` follow the same idea without a
shared base class (just two similarly-shaped functions). **Why**: adding a
tenth job source should mean adding a tenth file, not touching the nine
that already work. `services/job_ingestion_service.py` is the only place
that knows how to go from "a `JobSource` row" to "the right adapter" -
everything else just deals in the adapter interface.

### 1.6 Frontend: one folder per feature, not one folder per file type

`frontend/src/features/<name>/` holds everything about one product area:
its React Query hooks (`api.ts`) and, for the bigger ones, its own
components (`profile/sections/`, `profile/CVUpload.tsx`). `pages/` holds
only the route-level component that composes a feature's pieces onto a
page. **Why**: when you're working on, say, applications, everything
relevant is in one folder instead of scattered across parallel
`hooks/`, `components/`, `types/` directories.

### 1.7 Frontend: React Query owns all server state

Nothing in `features/*/api.ts` uses `useState`+`useEffect` to fetch data.
Every read is a `useQuery`, every write a `useMutation`, and mutations
that change something another query depends on call
`queryClient.invalidateQueries(...)` in their `onSuccess`. **Why**:
caching, automatic refetching, and polling (see `useCVDocument`'s
`refetchInterval` and `useApplication`'s same pattern for draft
generation) all come for free instead of being hand-rolled per component.

### 1.8 Frontend: no component library dependency

`components/ui/*.tsx` are small, hand-written primitives in the
shadcn/ui *style* (Tailwind classes, `class-variance-authority` for
variants) but without pulling in Radix UI - `Dialog`, `Tabs`, and `Select`
are plain implementations over native HTML elements. **Why**: this app's
UI needs are simple enough that a full component library would be more
dependency than value; these files are short enough to read end to end.

---

## 2. Backend reference (`backend/app/`)

### Core / app-wide

| File | Purpose |
|---|---|
| `main.py` | Builds the FastAPI app: registers CORS, mounts all routers under `/api`, and on startup seeds the default job sources if none exist yet (`_seed_default_job_sources`). |
| `config.py` | One `Settings` class (pydantic-settings) holding every environment variable, with sane defaults. Everything else reads config through `get_settings()` rather than `os.environ` directly. |
| `database.py` | The dual async/sync engine setup - see §1.2. |
| `security.py` | Password hashing (argon2) and JWT issue/verify. Pure functions, no FastAPI/DB imports - easy to unit test (see `tests/test_security.py`). |
| `deps.py` | FastAPI dependency-injection functions: `get_db` (DB session), `get_current_user` (decodes the bearer token, loads the user, 401s if invalid). |

### `models/` — SQLAlchemy tables

One file per entity group. `models/__init__.py` imports all of them so
SQLAlchemy's mapper registry sees every class (needed for the string-based
`relationship("OtherClass")` references to resolve, and for Alembic to see
the full schema).

| File | Tables | Notes |
|---|---|---|
| `mixins.py` | — | `UUIDPk` (UUID primary key) and `TimestampMixin` (`created_at`/`updated_at`), mixed into almost every model below. |
| `user.py` | `users` | One row per login. |
| `profile.py` | `profiles`, `work_experience`, `education`, `certifications`, `projects`, `languages`, `skills` | The canonical, user-confirmed CV data. `profiles.embedding` is the vector used for matching (see `searchable_text()`, which flattens all of this into text for embedding). |
| `cv.py` | `cv_documents` | Both uploaded resumes (`kind="uploaded"`, holds `parsed_json` from AI extraction) and generated tailored-resume metadata (`kind="generated"`, used by the applications flow). |
| `job.py` | `job_sources`, `job_postings` | A source describes *where* to pull jobs from; postings are the actual listings, deduplicated on `(source_id, external_id)`. `job_postings.embedding` is the other half of the matching pipeline. |
| `match.py` | `matches` | One row per (profile, job) pair that's been scored. This is the table the frontend reads - see §1.4. |
| `application.py` | `applications`, `application_events` | One application per job you're tracking; events are an audit trail of status changes for the kanban history view. |
| `salary.py` | `salary_snapshots` | Cached salary data per (role, location, source). |
| `chat.py` | `chat_sessions`, `chat_messages` | Copilot conversations. |
| `app_settings.py` | `app_settings` | Key/value table for future runtime-editable settings (see `routers/settings.py`'s docstring - not fully wired up yet). |

### `schemas/` — request/response shapes (Pydantic)

Mirrors `models/` roughly 1:1, but these are the *API contract*, not the
database shape - e.g. `ProfileOut` flattens nested lists the frontend
needs, and `*In` schemas (like `ProfileIn`) are what the frontend is
allowed to send, which is deliberately narrower than what the DB can
store. If you're changing what an endpoint accepts or returns, this is the
file to edit alongside the matching router.

### `routers/` — HTTP endpoints

Each file is `prefix="/api/<name>"`, all mounted in `main.py`. Per §1.1,
these should stay thin - if you find yourself writing more than a few
lines of logic directly in a route function, it probably belongs in the
matching `services/` file instead.

| File | Prefix | Covers |
|---|---|---|
| `health.py` | `/api` | `/health` - container healthchecks. |
| `auth.py` | `/api/auth` | Register (once), login, `/me`. |
| `profile.py` | `/api/profile` | Get/replace the profile. |
| `cv.py` | `/api/cv` | Upload, list/get documents, PDF export. |
| `jobs.py` | `/api/jobs` | Browse postings, manage job sources. |
| `matching.py` | `/api/matches` | Read precomputed matches, trigger a refresh. |
| `applications.py` | `/api/applications` | The application tracker + draft generation + tailored resume download. |
| `salary.py` | `/api/salary` | Salary insights + the curated role/location suggestions. |
| `chat.py` | `/api/chat` | Sessions + the streaming message endpoint. |
| `settings.py` | `/api/settings` | Read-only effective server config. |

### `services/` — business logic

| File | Owns | Called from |
|---|---|---|
| `auth_service.py` | Registration lock, login, token issuing | `routers/auth.py` |
| `profile_service.py` | Full-form profile replace/read | `routers/profile.py`, `routers/cv.py` |
| `cv_parser_service.py` | The JSON schema + prompt for AI CV extraction | `workers/cv_tasks.py` |
| `cv_export_service.py` | Rendering the profile (or a tailored variant) to PDF via WeasyPrint/Jinja2 | `routers/cv.py`, `routers/applications.py` |
| `job_ingestion_service.py` | Source→adapter dispatch, upsert-with-change-detection, source CRUD | `workers/ingestion_tasks.py`, `routers/jobs.py` |
| `matching_service.py` | The full matching pipeline - see §1.4 | `workers/embedding_tasks.py`, `workers/matching_tasks.py`, `routers/matching.py` |
| `application_service.py` | Draft generation prompt/logic, application CRUD + status transitions | `workers/generation_tasks.py`, `routers/applications.py` |
| `salary_service.py` | Percentile math over postings, snapshot caching | `workers/salary_tasks.py`, `routers/salary.py` |
| `chat_service.py` | System-prompt grounding, streaming a reply while persisting messages | `routers/chat.py` |

### `integrations/` — everything that talks to the outside world

| File | Talks to |
|---|---|
| `ollama_client.py` | Ollama. The **only** file that does - every AI feature (extraction, matching, drafting, chat) goes through `chat()`, `chat_stream()`, `embed()`, or `generate_json()` here. If you're swapping models or debugging a prompt, start here. |
| `job_sources/base.py` | — (defines the adapter interface + `NormalizedJobPosting`) |
| `job_sources/{adzuna,remotive,remoteok,arbeitnow,usajobs,themuse,greenhouse,lever}.py` | One external job API each. |
| `job_sources/custom_rss.py` | Whatever RSS/Atom feed URL a user adds. |
| `job_sources/__init__.py` | The `ADAPTERS` registry mapping a `JobSource.type` string to its adapter instance. |
| `salary_apis/adzuna_salary.py` | Adzuna (reuses its job-search endpoint, aggregated into percentiles). |
| `salary_apis/bls.py` | US Bureau of Labor Statistics - ships opt-in/empty, see its docstring. |
| `auto_submit/` | Empty on purpose - reserved, isolated location for a possible future "true API auto-submit" for boards with an official application API (Greenhouse/Lever). Physically separate from the review-then-submit flow so it can never be accidentally wired into it. |

### `workers/` — background job definitions + the two long-running processes

Covered in detail in §1.3. Quick index:

| File | Role |
|---|---|
| `queue.py` | Redis connection + the two `Queue` objects. |
| `worker.py` | The RQ worker process entrypoint. |
| `scheduler.py` | The APScheduler process entrypoint - decides *when*, enqueues, does no work itself. |
| `cv_tasks.py` | Parse an uploaded CV. |
| `embedding_tasks.py` | Embed a profile or job posting, then kick off matching for it. |
| `matching_tasks.py` | The candidate-search + LLM-explain sweep for one profile or job. |
| `ingestion_tasks.py` | Poll one job source. |
| `generation_tasks.py` | Generate an application draft. |
| `salary_tasks.py` | The nightly salary-snapshot refresh. |

### `templates/cv/` and `utils/`

- `templates/cv/modern.html`, `classic.html` — Jinja2 + inline CSS resume
  layouts, rendered to PDF by `cv_export_service.py`. To add a third
  template: drop a new HTML file here, add it to `AVAILABLE_TEMPLATES` in
  `cv_export_service.py`.
- `utils/text_extract.py` — PDF/DOCX/TXT → plain text, used only by the CV
  upload flow.
- `utils/html_clean.py` — strips HTML tags from job descriptions that
  several source APIs (Remotive, Greenhouse, Lever, The Muse) return as
  HTML rather than plain text.

### `alembic/`

- `alembic/env.py` — wires Alembic to `app.config`'s database URL and
  `app.models`' metadata.
- `alembic/versions/0001_initial.py` — the entire schema in one migration:
  every table, the `CREATE EXTENSION vector` statement, and the two HNSW
  indexes. This is the authoritative source of exact column types/defaults
  if a model docstring and the migration ever seem to disagree.

### `tests/`

Pure-logic unit tests only (no DB/Redis/Ollama required to run them) -
`test_security.py`, `test_salary_service.py`, `test_job_ingestion_service.py`,
`test_html_clean.py`. Run with `pytest` from `backend/`.

---

## 3. Frontend reference (`frontend/src/`)

### Entry points & app shell

| File | Purpose |
|---|---|
| `main.tsx` | Mounts `<App />`. |
| `App.tsx` | Sets up the React Query client and the router provider; renders the global `<Toaster />`. |
| `router.tsx` | Every route in the app, plus `ProtectedRoute` (redirects to `/login` if there's no valid session). |
| `layouts/AppLayout.tsx` | The sidebar + page frame every authenticated page renders inside. |
| `vite-env.d.ts` | Types for `import.meta.env.VITE_API_BASE_URL`. |

### `api/` — talking to the backend

| File | Purpose |
|---|---|
| `client.ts` | The shared axios instance (attaches the auth token, redirects to `/login` on 401), plus two helpers that plain axios doesn't do well in a browser: `downloadAuthedFile` (blob download with an auth header, since a plain `<a href>` can't send one) and `streamChatMessage` (reads the copilot's streaming response chunk by chunk via `fetch`). |
| `types.ts` | Hand-written TypeScript mirrors of the backend's Pydantic schemas. Run `npm run generate:types` (needs the backend running) to generate real types from the live OpenAPI schema instead - see that script's note in `package.json`. |

### `store/` — small global state (Zustand)

| File | Purpose |
|---|---|
| `authStore.ts` | Just the JWT, persisted to localStorage. |
| `toastStore.ts` | Notification queue for the toast popups; call `toast({ title, ... })` from anywhere. |

### `features/` — one folder per product area

Each `features/<name>/api.ts` is a set of React Query hooks wrapping the
matching backend router - e.g. `features/jobs/api.ts` ↔ `routers/jobs.py`.
That mapping is 1:1 for every feature, so it's not repeated in the table
below. Notable non-`api.ts` files:

| File | Purpose |
|---|---|
| `profile/formTypes.ts` | The CV builder's form shape (`ProfileFormValues`), its Zod validation schema, and the blank-profile default. Kept separate from `ProfileForm.tsx` so the section components (below) can import the type without an import cycle. |
| `profile/ProfileForm.tsx` | Orchestrator only: creates the `react-hook-form` instance and one `useFieldArray` per repeatable section, then hands each down to a section component. |
| `profile/sections/shared.tsx` | `<Section>`, `<Field>`, `<RemoveButton>` - the wrapper markup every section reuses. |
| `profile/sections/*Section.tsx` | One file per CV section (Basics, Experience, Education, Skills, Projects, Certifications, Languages) - each is just the fields for that section, nothing else. |
| `profile/CVUpload.tsx` | The upload dropzone + parse-status polling + "Use this data" handoff back to the form. |
| `profile/extractedToForm.ts` | Defensively maps the AI's raw extraction JSON onto `ProfileFormValues` - handles missing/malformed fields since it's LLM output the user will review anyway. |

### `pages/` — one component per route

Each composes hooks from `features/*/api.ts` with `components/ui/*` -
there's normally not much logic here beyond "fetch, render, handle a
mutation." A few worth calling out:

| File | Notable because |
|---|---|
| `Login.tsx` | Handles both login and the one-time owner registration in the same form, toggled by a mode switch. |
| `Applications.tsx` | The kanban board - `@dnd-kit`'s `DndContext`/`useDraggable`/`useDroppable`, where dropping a card in a new column calls the same status-update mutation as the detail page's dropdown. |
| `ApplicationDetail.tsx` | The draft review screen - shows different content depending on `draft_status` (generating/ready/failed), and is the one place a tailored resume gets downloaded from. |
| `Copilot.tsx` | Owns the streaming chat UI - accumulates chunks from `streamChatMessage` into local state while streaming, then invalidates the React Query cache once done so the persisted message list takes over. |
| `Market.tsx` | Renders `SalarySnapshot[]` as a Recharts bar chart, one bar group per source, so you can see where a number came from. |

### `components/ui/` — shared primitives

Small, dependency-light building blocks (§1.8): `button`, `input`,
`textarea`, `label`, `card`, `badge`, `select`, `tabs`, `dialog`, `spinner`,
`toaster`. None of these know anything about the job-search domain - safe
to reuse as-is for any new page.

### `lib/utils.ts`

Just `cn()` - merges Tailwind classes safely (handles conflicting utility
classes), used by every `components/ui/*` file.

---

## 4. Cookbook: common changes

| I want to... | Start here |
|---|---|
| Add a new job source (a company's Greenhouse/Lever board, or an RSS feed) | No code change needed - add it from the Settings page. |
| Add a new *type* of job source (a new API) | Add a file to `backend/app/integrations/job_sources/`, implement `fetch()`, register it in that folder's `__init__.py`'s `ADAPTERS` dict, add the type string to `JOB_SOURCE_TYPES` in `models/job.py`. |
| Change which LLM model is used | Edit `OLLAMA_CHAT_MODEL` / `OLLAMA_EMBED_MODEL` in `.env` (see the note there about `OLLAMA_EMBED_DIM` if you change the embedding model). No code change. |
| Change a prompt (extraction, matching, drafting, chat) | `services/cv_parser_service.py`, `services/matching_service.py`, `services/application_service.py`, or `services/chat_service.py` respectively - each has its system prompt as a module-level constant near the top. |
| Add a field to the CV builder (e.g. "portfolio URL") | Add it to the model (`models/profile.py`), a migration, the schema (`schemas/profile.py`), and the relevant section component (`features/profile/sections/`) + its Zod schema entry in `formTypes.ts`. |
| Add a new resume PDF template | Add an HTML file to `backend/app/templates/cv/`, register it in `AVAILABLE_TEMPLATES` in `services/cv_export_service.py`, add the option to the `<Select>` in `pages/Profile.tsx`. |
| Change what counts as a "strong" match | `SIMILARITY_FLOOR` in `services/matching_service.py` (the pgvector cutoff before an LLM call happens at all). |
| Add a new page | Add the route + component under `pages/`, wire it into `router.tsx`'s children array and `layouts/AppLayout.tsx`'s `NAV_ITEMS`. |
| See why something failed in the background | `docker compose logs worker` (most AI/ingestion work) or `docker compose logs scheduler` (missed polls); job-source-specific errors also show in the Settings page next to each source. |
