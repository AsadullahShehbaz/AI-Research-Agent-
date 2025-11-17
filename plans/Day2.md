# Day 2 — 5 Subtasks (Coding Day) — Step-by-Step Implementation (No code)

Great — below are **five concrete subtasks** to implement Day 2 (the Research Agent coding day). Each subtask contains explicit, step-by-step instructions, deliverables, acceptance criteria, testing steps, and common pitfalls. Follow them in order.

---

# 1) Repo & dev environment setup — skeleton + basic CI

**Goal:** Create project repository, Python environment, CI skeleton, and run a minimal FastAPI app scaffold.

**Steps**

1. Create repo & branches: `main` (protected) + `dev`.
2. Create `.gitignore`, `README.md`, `LICENSE`.
3. Initialize Python project: create `pyproject.toml` or `requirements.txt`.
4. Create virtual environment and install dev tools (linters, pytest, pre-commit). (List packages in requirements but don’t write code.)
5. Add basic folder structure shown earlier (`app/api`, `app/agents`, `app/tools`, `app/memory`, `app/tasks`, `app/models`, `app/core`).
6. Add a minimal FastAPI app file placeholder and a `/health` endpoint (describe file path and intended behavior).
7. Add CI pipeline skeleton (GitHub Actions or similar) that runs linting and tests (empty test run OK). Include pipeline steps: checkout, set up Python, install deps, run `pytest` and linter.

**Deliverables**

* Repo with branch structure, README, skeleton folders, placeholder FastAPI app exposing `/health`.
* CI workflow file that runs lint & tests.

**Acceptance criteria**

* `git clone` + venv + install results in project ready.
* CI passes on empty tests.

**Tests**

* Run `pytest` (should pass with placeholder test).
* Curl `GET /health` returns `{"status":"ok"}` (or similar).

**Pitfalls**

* Missing `.env` handling — create `.env.example`.
* CI secrets not stored — don't hardcode keys.

---

# 2) Pydantic schemas, config & core utils

**Goal:** Implement all data models, configuration loader, and core utilities used across agents and API.

**Steps**

1. Create `app/models/schemas.py` (or `app/models/*.py`) and add Pydantic models: `AgentInput`, `AgentOutput`, `ResearchTaskRequest`, `TaskStatus`, `HealthResponse`, and any tool call result schemas. Document fields and validation rules.
2. Implement config loader `app/core/config.py` to read environment variables (API keys, model settings, Redis/Vector DB endpoints) and expose typed config objects. Include defaults and fail-fast checks for required values.
3. Add `app/core/utils.py` for common utilities: normalized query hashing, safe-truncate text, safe URL sanitizer, and simple logging helpers.
4. Add JSON schema examples or examples in docstrings for each model to help devs and tests.
5. Add unit tests validating schema validation: required fields, invalid inputs produce validation errors.

**Deliverables**

* Pydantic schema files and config + utility modules.
* Tests validating schema behavior.

**Acceptance criteria**

* Creating model instances with valid data succeeds; invalid data raises `ValidationError`.
* Config raises clear error if required env vars missing.

**Tests**

* `pytest` tests for models and config edge cases.

**Pitfalls**

* Overly permissive models — add length / type validation to avoid huge payloads later.
* Secrets in config — ensure no secrets logged.

---

# 3) Research Agent core & tool interfaces (no LLM integrations yet)

**Goal:** Implement Research Agent class, BaseTool interface, and concrete tool wrappers (stubs/mocks) so the agent can be exercised locally without a paid LLM.

**Steps**

1. Design `BaseAgent` abstract interface (methods, input/output contract) and create `ResearchAgent` skeleton implementing it.
2. Create `BaseTool` abstract interface with `execute(input: dict) -> dict` and common metadata (name, description, timeout).
3. Implement tool stubs:

   * `WebSearchTool` stub that returns pre-defined search results (read from fixtures).
   * `RAGTool` stub that returns chunked text from sample documents in `tests/fixtures/`.
   * `DocumentLoaderTool` stub that simulates file chunking and metadata extraction.
     These stubs let you develop the agent logic without external APIs.
4. Implement agent logic for:

   * simple intent parsing (is user asking for summary, deep research, or citation?)
   * planning step: produce a list of sub-queries or actions (plain Python structures)
   * tool orchestration: call tools sequentially or in simple branching logic and collect observations
   * synthesis: combine observations into an `AgentOutput` object with `response`, `citations`, and `reasoning_steps`
5. Add unit tests for the ResearchAgent using the tool stubs to verify planning → tool calls → synthesis paths.

**Deliverables**

* `app/agents/research_agent.py` with concrete logic connecting to BaseTool interfaces.
* Tool stubs in `app/tools/` and fixtures for predictable responses.
* Unit tests covering typical flows: short chat, document-only query, hybrid query.

**Acceptance criteria**

* ResearchAgent returns structured `AgentOutput` given stubbed tools.
* Tests cover at least planning, one web search flow, and one RAG flow.

**Tests**

* Unit tests assert `response` contains expected summary text from fixtures and `citations` reference fixture URLs/titles.

**Pitfalls**

* Mixing LLM behavior into logic — keep agent logic deterministic (planning, orchestration) and stub LLM calls so tests are repeatable.

---

# 4) Tool integrations & local LLM mocking (pluggable adapters)

**Goal:** Implement real tool adapters as pluggable components and a mock LLM adapter to emulate LLM responses during development.

**Steps**

1. Define adapter pattern: `ToolAdapter` wraps an external API and conforms to `BaseTool`. Each adapter must support timeouts, retries, and error wrapping.
2. Implement a `WebSearchAdapter` that can be configured to use a real provider later (parameterize provider via config). For now, wiring should accept provider choice but default to stub.
3. Implement `DocumentLoaderAdapter` that plugs into actual extraction libraries later (pdfminer / pypdf). For now, ensure interface supports `load(url_or_file) -> List[Chunk]`.
4. Add a `MockLLMAdapter` that accepts prompts and returns deterministic outputs from templates or mapping files—used inside the ResearchAgent’s synthesis step.
5. Wire the ResearchAgent to use adapters via dependency injection (config-driven).
6. Add integration tests that exercise the ResearchAgent using `MockLLMAdapter` + real tool adapters switched off.

**Deliverables**

* `app/tools/adapters/*.py` adapters with clear docstrings.
* `app/agents` wired to accept adapter instances in the constructor.
* Integration tests demonstrating the agent works end-to-end with the mock LLM.

**Acceptance criteria**

* Swapping adapters requires no code changes — only config.
* Agent works end-to-end with `MockLLMAdapter`.

**Tests**

* Integration test simulating a hybrid query: the agent plans, calls WebSearchAdapter (stubbed), calls DocumentLoaderAdapter (stubbed), and synthesizes a final output using MockLLMAdapter.

**Pitfalls**

* Tight coupling between agent and adapters — prefer DI and configuration.

---

# 5) API endpoints, async task plumbing & basic memory store

**Goal:** Expose the ResearchAgent through FastAPI endpoints (`/v1/agent/chat`, `/v1/agent/task`, `/v1/agent/status`) and implement a simple per-thread memory backed by Redis or an in-memory fallback.

**Steps**

1. Implement `/v1/agent/chat`:

   * Validate request with Pydantic models.
   * Resolve thread memory, call ResearchAgent synchronously (using `await` if async), record agent response to memory, return `AgentOutput`.
2. Implement `/v1/agent/task`:

   * Accept long job request, create task record, enqueue background job (use FastAPI `BackgroundTasks` initially), return `task_id`.
3. Implement task worker (`app/tasks/worker.py`) to run research tasks using the ResearchAgent and store progress & final result.
4. Implement `/v1/agent/status/{task_id}` to read task progress and final result.
5. Implement memory layer:

   * Abstraction: `MemoryStore` with `get(thread_id)`, `append(thread_id, memory_item)`, `search(thread_id, query)` (for later vector search).
   * Provide two implementations:

     * In-memory dict (fast for local dev)
     * Redis-backed store (if Redis URI present in config)
   * For now, store simple JSON objects (timestamped) and ensure retention policy is configurable.
6. Add tests:

   * API-level tests using TestClient: chat synchronous flow, create task + poll status, memory is persisted and returned.
   * Worker tests: simulate background execution and verify task status transitions.

**Deliverables**

* API routes implemented and wired to ResearchAgent.
* Background worker and task status handling.
* Memory store with both in-memory and Redis options.
* API tests validating the main flows.

**Acceptance criteria**

* `POST /v1/agent/chat` returns structured response and memory is updated.
* `POST /v1/agent/task` returns `task_id` and worker updates status to `completed`.
* `/v1/agent/status/{task_id}` shows progress and final result.

**Tests**

* End-to-end test: submit task that triggers RAG + web search stubs, await background worker completion, verify final `report` and `citations`.

**Pitfalls**

* BackgroundTasks are tied to process lifetime — for production use Celery/Redis workers later.
* Race conditions in memory store — implement simple locking or atomic ops for Redis.

---

# Final Checklist before moving to Day 3 (Coding complete)

* [ ] Repo & CI ready.
* [ ] All Pydantic models and config validated by tests.
* [ ] ResearchAgent implemented with deterministic planning + tool orchestration using stubs.
* [ ] Adapter pattern in place and agents wired via DI.
* [ ] FastAPI endpoints present: chat, task, status, health.
* [ ] Memory layer implemented (in-memory + optional Redis).
* [ ] Unit + integration tests covering main flows.
* [ ] README updated with dev instructions and how to run tests.

---

If you want, I can convert any of the five subtasks above into a **detailed ticket list** with acceptance tests and checklist items (suitable for GitHub Issues or Jira). Which subtask would you like turned into tickets first?
