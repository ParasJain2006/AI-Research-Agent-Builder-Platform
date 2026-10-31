# CSE Research & Agent Builder Platform

Team Development, Data Contract & Integration Specification

## 1. Document Purpose and Authority

This document is the shared engineering contract for the project. All three team members must follow it unless the team explicitly approves and documents a change. It defines module boundaries, folder structure, naming, request/response schemas, LangGraph state, API behavior, persistence boundaries, error handling, guardrails, testing, Git workflow, integration procedure, and deployment conventions.

> **RULE 0 — CONTRACT FIRST.** No member may silently rename a shared field, change an enum value, alter an API payload, or change a shared schema. Contract changes require a pull request and approval from at least one other member.

The product supports three user journeys: (1) Research Only, (2) Direct Agent Building, and (3) Research-to-Agent. The Research module can operate independently; the Agent Builder can operate independently; completed research can optionally be converted into agent-building context.

## 2. System Scope and Team Ownership

| Member | Primary ownership | Must not own |
| --- | --- | --- |
| Member 1 — Platform | React frontend; FastAPI HTTP layer; auth; database integration; persistence; API client; deployment; integration wiring | Research reasoning internals or Agent Builder reasoning internals |
| Member 2 — Research Agent | Research LangGraph; planning; GitHub/paper/web-doc tools; evidence normalization/filtering; synthesis; citations; research output | Frontend routes, auth implementation, Agent Builder internals |
| Member 3 — Agent Builder | Builder LangGraph; requirement analysis; tool selection; architecture generation; agent definition; validation; refinement; controlled execution | Frontend routes, research search internals, auth implementation |

Shared code is jointly governed. The shared package is a contract package, not a dumping ground for arbitrary helpers.

### 2.1 Allowed dependency direction

```
frontend -> backend API
backend -> research_agent service
backend -> agent_builder service
research_agent -> shared
agent_builder -> shared
backend -> shared

research_agent -X-> agent_builder internals
agent_builder -X-> research_agent internals
frontend -X-> LangGraph internals
```

Research-to-Agent integration happens through a shared typed contract. The Agent Builder must not import Research Agent state or nodes.

## 3. Canonical Monorepo Structure

```
cse-ai-platform/
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── client.js
│   │   │   ├── researchApi.js
│   │   │   ├── agentBuilderApi.js
│   │   │   └── authApi.js
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── Research/
│   │   │   ├── AgentBuilder/
│   │   │   └── ResearchToAgent/
│   │   ├── hooks/
│   │   ├── context/
│   │   ├── types/
│   │   ├── utils/
│   │   └── App.jsx
│   ├── package.json
│   └── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/
│   │   │   ├── auth.py
│   │   │   ├── research.py
│   │   │   └── agents.py
│   │   ├── services/
│   │   │   ├── research_service.py
│   │   │   └── agent_service.py
│   │   ├── database/
│   │   │   ├── connection.py
│   │   │   ├── models/
│   │   │   └── repositories/
│   │   ├── middleware/
│   │   ├── config/
│   │   └── dependencies/
│   └── tests/
├── research_agent/
│   ├── service.py
│   ├── graph/
│   │   ├── graph.py
│   │   ├── state.py
│   │   └── nodes/
│   │       ├── requirement_analyzer.py
│   │       ├── planner.py
│   │       ├── github_search.py
│   │       ├── paper_search.py
│   │       ├── web_search.py
│   │       ├── evidence_filter.py
│   │       └── synthesizer.py
│   ├── tools/
│   ├── prompts/
│   ├── services/
│   └── tests/
├── agent_builder/
│   ├── service.py
│   ├── graph/
│   │   ├── graph.py
│   │   ├── state.py
│   │   └── nodes/
│   │       ├── requirement_analyzer.py
│   │       ├── architecture_designer.py
│   │       ├── tool_selector.py
│   │       ├── agent_generator.py
│   │       ├── validator.py
│   │       └── refiner.py
│   ├── templates/
│   ├── tools/
│   ├── prompts/
│   ├── services/
│   └── tests/
├── shared/
│   ├── schemas/
│   │   ├── common.py
│   │   ├── research.py
│   │   ├── agent.py
│   │   └── errors.py
│   ├── enums/
│   ├── constants/
│   ├── exceptions/
│   └── utils/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── API_CONTRACT.md
│   ├── DATA_CONTRACT.md
│   ├── NAMING_CONVENTIONS.md
│   └── INTEGRATION_CHECKLIST.md
├── tests/integration/
├── scripts/
├── .github/workflows/ci.yml
├── .env.example
├── .gitignore
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

### 3.1 Folder rules

- Each module exposes one public service entry point (`service.py`). Backend calls the service, not graph nodes directly.
- `shared/` contains only cross-module contracts, enums, exceptions, constants, and truly shared utilities.
- Prompts stay inside the module that owns them. Do not place prompts in backend routes.
- External tool adapters stay under the owning module `tools/` or a deliberately shared integration package if later required.
- Database ORM models and repositories are owned by backend. Agent modules should return domain objects and should not directly write arbitrary database tables.
- Tests live beside each module; end-to-end integration tests live under `tests/integration/`.
## 4. Naming and Formatting Standard

| Artifact | Convention | Example |
| --- | --- | --- |
| Python file/module | snake_case | research_service.py |
| Python variable/function | snake_case | research_result / run_research() |
| Python class/schema | PascalCase | ResearchResult |
| React component | PascalCase | ResearchWorkspace.jsx |
| JavaScript variable/function | camelCase | researchResult / startResearch() |
| API JSON field | snake_case | research_id |
| REST path | lowercase plural nouns; hyphens only when needed | /api/v1/research-sessions |
| Database table | plural snake_case | research_sessions |
| Database column | snake_case | created_at |
| Environment variable | UPPER_SNAKE_CASE | GITHUB_TOKEN |
| Enum value | lowercase snake_case | synthesizing |
| ID field | <entity>_id | agent_id |

> **DO NOT MIX** `researchID`, `researchId`, `res_id`, and `research_id`. The API/domain contract uses `research_id`. Frontend may map internally, but network payloads remain snake_case.

## 5. Identifier, Timestamp, Nullability and Version Rules

- IDs are strings. Prefer UUIDs generated server-side. Human-readable prefixes such as `res_` or `agt_` are optional only if implemented consistently.
- All timestamps use ISO 8601 UTC, e.g. `2026-10-31T03:45:10Z`. Never transmit locale-formatted dates between modules.
- Use `null` only when a field is genuinely optional. Do not use empty string to mean missing.
- Empty collections use `[]`, not `null`, unless absence has different semantics from an empty list.
- API version is `/api/v1`. Breaking contract changes require `/v2` or coordinated migration.
- Every persisted entity should include `created_at` and `updated_at`; mutable entities may include a numeric `version` for optimistic updates.
## 6. Shared Enumerations

```
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ResearchStatus(str, Enum):
    CREATED = "created"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    SEARCHING = "searching"
    FILTERING = "filtering"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentStatus(str, Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    DESIGNING = "designing"
    GENERATING = "generating"
    VALIDATING = "validating"
    READY = "ready"
    FAILED = "failed"

class SourceType(str, Enum):
    GITHUB = "github"
    PAPER = "paper"
    WEB = "web"
    DOCUMENTATION = "documentation"
```

Enums are serialized using the exact string values above. No module invents synonyms such as `done`, `finished`, or `complete`.

## 7. Canonical Shared Data Schemas

The following Pydantic models are the cross-module source of truth. Internal module state may contain extra fields, but public inputs and outputs must conform to these contracts.

### 7.1 Common source and evidence schemas

```
from pydantic import BaseModel, Field, HttpUrl
from typing import Any

class SourceReference(BaseModel):
    source_id: str
    source_type: SourceType
    title: str
    url: str
    authors: list[str] = []
    published_at: str | None = None
    retrieved_at: str
    snippet: str | None = None

class EvidenceItem(BaseModel):
    evidence_id: str
    source_id: str
    claim: str
    supporting_text: str | None = None
    relevance_score: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
```

### 7.2 Research request

```
class ResearchRequest(BaseModel):
    session_id: str
    query: str = Field(min_length=3, max_length=4000)
    source_types: list[SourceType] = [
        SourceType.GITHUB, SourceType.PAPER,
        SourceType.WEB, SourceType.DOCUMENTATION
    ]
    max_sources: int = Field(default=20, ge=1, le=50)
    user_constraints: list[str] = []
```

`user_id` should normally come from authenticated backend context, not from an untrusted request body. If an internal service contract includes user_id, backend injects it after authentication.

### 7.3 Research result

```
class ResearchResult(BaseModel):
    research_id: str
    session_id: str
    original_query: str
    normalized_query: str
    summary: str
    key_findings: list[str]
    recommended_approach: str | None = None
    sources: list[SourceReference]
    evidence: list[EvidenceItem] = []
    limitations: list[str] = []
    status: ResearchStatus
    created_at: str
    completed_at: str | None = None
```

### 7.4 Research-to-Agent handoff

```
class ResearchToAgentRequest(BaseModel):
    session_id: str
    research_id: str
    original_query: str
    research_summary: str
    key_findings: list[str]
    recommended_approach: str | None = None
    sources: list[SourceReference]
    agent_instruction: str | None = None
```

> **CRITICAL HANDOFF** Member 2 guarantees this output can be created from completed research. Member 3 accepts this object as research context. Member 3 must never depend on Member 2’s private LangGraph state.

### 7.5 Direct Agent Build request

```
class AgentBuildRequest(BaseModel):
    session_id: str
    agent_name: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=3, max_length=2000)
    objective: str = Field(min_length=3, max_length=2000)
    required_tools: list[str] = []
    constraints: list[str] = []
    research_context: ResearchToAgentRequest | None = None
```

Direct build sets `research_context = None`. Research-to-Agent populates it. This keeps one Agent Builder pipeline instead of maintaining two divergent implementations.

### 7.6 Generated agent definition

```
class AgentNodeDefinition(BaseModel):
    node_id: str
    node_type: str
    description: str
    allowed_tools: list[str] = []

class AgentEdgeDefinition(BaseModel):
    source_node: str
    target_node: str
    condition: str | None = None

class AgentDefinition(BaseModel):
    agent_id: str
    agent_name: str
    description: str
    objective: str
    system_prompt: str
    tools: list[str]
    workflow_nodes: list[AgentNodeDefinition]
    workflow_edges: list[AgentEdgeDefinition]
    entry_node: str
    constraints: list[str] = []
    status: AgentStatus
    schema_version: str = "1.0"
    created_at: str
    updated_at: str
```

Persist the declarative AgentDefinition rather than treating arbitrary generated Python code as the primary product. Runtime code should be constructed from approved templates and registered tools.

### 7.7 Agent test and refinement contracts

```
class AgentTestRequest(BaseModel):
    input_text: str = Field(min_length=1, max_length=8000)
    test_context: dict = {}

class AgentTestResult(BaseModel):
    test_id: str
    agent_id: str
    success: bool
    output: str | None = None
    errors: list[str] = []
    execution_trace: list[str] = []
    started_at: str
    completed_at: str

class AgentRefineRequest(BaseModel):
    instruction: str = Field(min_length=3, max_length=4000)
    expected_behavior: str | None = None
```

## 8. Standard HTTP API Envelope

```
class ErrorDetail(BaseModel):
    code: str
    message: str
    field: str | None = None
    details: dict | None = None

class ApiResponse(BaseModel):
    success: bool
    data: dict | list | None = None
    error: ErrorDetail | None = None
    request_id: str
    timestamp: str
```

Successful response: `success=true`, `error=null`. Failed response: `success=false`, `data=null`. Never return HTTP 200 for a real application error simply because the server returned JSON.

### 8.1 HTTP status mapping

| HTTP | Use | Example error code |
| --- | --- | --- |
| 200 | Successful read/action | — |
| 201 | Resource created | — |
| 202 | Long-running job accepted | — |
| 400 | Malformed/invalid request | INVALID_REQUEST |
| 401 | Missing/invalid authentication | UNAUTHORIZED |
| 403 | Authenticated but forbidden | FORBIDDEN |
| 404 | Entity not found | RESEARCH_NOT_FOUND |
| 409 | State/version conflict | INVALID_STATE_TRANSITION |
| 422 | Schema/semantic validation failure | VALIDATION_ERROR |
| 429 | Rate limit | RATE_LIMITED |
| 500 | Unexpected server failure | INTERNAL_ERROR |
| 502/503 | Required external provider unavailable | SOURCE_UNAVAILABLE |

## 9. API Contract — Version 1

| Method | Endpoint | Purpose | Input | Output |
| --- | --- | --- | --- | --- |
| POST | /api/v1/research | Start research | ResearchRequest | ResearchResult or accepted job |
| GET | /api/v1/research/{research_id} | Get research/status | Path ID | ResearchResult |
| GET | /api/v1/research | List user research | Query params | Paginated results |
| POST | /api/v1/agents | Build direct agent | AgentBuildRequest | AgentDefinition |
| POST | /api/v1/agents/from-research | Build using research | ResearchToAgentRequest + builder fields | AgentDefinition |
| GET | /api/v1/agents/{agent_id} | Get saved agent | Path ID | AgentDefinition |
| GET | /api/v1/agents | List saved agents | Query params | Paginated agents |
| POST | /api/v1/agents/{agent_id}/test | Controlled test | AgentTestRequest | AgentTestResult |
| POST | /api/v1/agents/{agent_id}/refine | Refine definition | AgentRefineRequest | AgentDefinition |

### 9.1 Example Research request/response

```
POST /api/v1/research
{
  "session_id": "...",
  "query": "Compare approaches for a GitHub code review agent",
  "source_types": ["github", "paper", "documentation"],
  "max_sources": 20,
  "user_constraints": ["Python implementation"]
}
```

```
{
  "success": true,
  "data": {
    "research_id": "...",
    "session_id": "...",
    "original_query": "...",
    "normalized_query": "...",
    "summary": "...",
    "key_findings": ["..."],
    "recommended_approach": "...",
    "sources": [],
    "evidence": [],
    "limitations": [],
    "status": "completed",
    "created_at": "2026-10-31T03:45:10Z",
    "completed_at": "2026-10-31T03:46:40Z"
  },
  "error": null,
  "request_id": "...",
  "timestamp": "2026-10-31T03:46:40Z"
}
```

## 10. Service Interfaces Between Backend and Agent Modules

The backend owns HTTP concerns. Agent modules expose Python service functions. This prevents FastAPI details from leaking into LangGraph code.

```
# research_agent/service.py
async def run_research(request: ResearchRequest, context: ServiceContext) -> ResearchResult:
    ...

# agent_builder/service.py
async def build_agent(request: AgentBuildRequest, context: ServiceContext) -> AgentDefinition:
    ...

async def test_agent(agent: AgentDefinition, request: AgentTestRequest, context: ServiceContext) -> AgentTestResult:
    ...
```

```
class ServiceContext(BaseModel):
    user_id: str
    request_id: str
    correlation_id: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
```

No service function should accept a FastAPI `Request` object. This keeps domain modules independently testable.

## 11. Research Agent Internal Contract

### 11.1 Typed LangGraph state

```
class ResearchState(TypedDict):
    user_id: str
    request_id: str
    session_id: str
    research_id: str
    query: str
    normalized_query: str
    research_plan: list[str]
    github_results: list[dict]
    paper_results: list[dict]
    web_results: list[dict]
    normalized_sources: list[SourceReference]
    evidence: list[EvidenceItem]
    key_findings: list[str]
    research_summary: str
    recommended_approach: str | None
    limitations: list[str]
    status: ResearchStatus
    errors: list[str]
```

### 11.2 Recommended node responsibilities

| Node | Input responsibility | Output responsibility |
| --- | --- | --- |
| requirement_analyzer | Raw query | Normalized query + constraints |
| planner | Normalized query | Search plan/subqueries |
| github_search | Plan | Raw GitHub candidates |
| paper_search | Plan | Paper candidates |
| web_search | Plan | Web/docs candidates |
| evidence_filter | All candidates | Deduplicated sources + scored evidence |
| synthesizer | Evidence | Summary, findings, recommendation, limitations |

Nodes should return only the state updates they own. They should not mutate unrelated fields. External-source failures should be recorded and, where possible, allow partial research rather than destroying all successful evidence.

## 12. Agent Builder Internal Contract

### 12.1 Typed LangGraph state

```
class AgentBuilderState(TypedDict):
    user_id: str
    request_id: str
    session_id: str
    build_request: AgentBuildRequest
    analyzed_requirements: dict
    selected_tools: list[str]
    proposed_nodes: list[AgentNodeDefinition]
    proposed_edges: list[AgentEdgeDefinition]
    generated_definition: AgentDefinition | None
    validation_errors: list[str]
    refinement_count: int
    status: AgentStatus
    errors: list[str]
```

### 12.2 Recommended node responsibilities

| Node | Responsibility |
| --- | --- |
| requirement_analyzer | Convert direct request/research context into explicit objective, constraints and capabilities. |
| tool_selector | Choose only tools available in the approved registry. |
| architecture_designer | Create node/edge plan and entry point. |
| agent_generator | Generate declarative AgentDefinition and prompts. |
| validator | Check schema, graph connectivity, tools, prompt constraints and runtime policy. |
| refiner | Apply validation/user feedback with bounded refinement attempts. |

## 13. Tool Registry Contract

Tools are capabilities, not arbitrary functions selected by an LLM. Every executable tool must be registered with metadata and an implementation controlled by the application.

```
class ToolDefinition(BaseModel):
    tool_name: str
    description: str
    input_schema: dict
    risk_level: str
    requires_auth: bool
    enabled: bool = True

ALLOWED_TOOL_NAMES = {
    "github_search",
    "paper_search",
    "web_search",
    "documentation_search",
    "document_reader",
}

```

An LLM may recommend a tool name; runtime resolves that name against the registry. Unknown or disabled tools are rejected. Never execute a function name, shell command, URL action, or generated code merely because the model emitted it.

## 14. Database and Persistence Boundary

The project specification calls for users, projects/sessions, agent definitions, metadata, and audit records in the application database. Backend owns persistence. The following is a recommended V1 logical model; exact migrations may evolve while preserving API contracts.

| Table | Key fields | Purpose |
| --- | --- | --- |
| users | user_id, email, password_hash/auth_provider, created_at | Identity/account record |
| sessions | session_id, user_id, title, created_at, updated_at | Groups a user workflow |
| research_sessions | research_id, session_id, user_id, query, status, result_json, created_at, completed_at | Research lifecycle and result |
| agents | agent_id, user_id, session_id, research_id?, name, status, definition_json, version, created_at, updated_at | Saved generated agent definition |
| agent_tests | test_id, agent_id, user_id, success, input_json, output_json, created_at | Controlled execution history |
| audit_logs | audit_id, user_id, request_id, action, entity_type, entity_id, metadata_json, created_at | Traceability and debugging |

- Never store plaintext passwords or API secrets in application tables.
- Every query for user-owned data must scope by authenticated `user_id`.
- JSON columns are acceptable for evolving agent/research definitions in V1, but stable searchable metadata should remain first-class columns.
- Database writes should happen through backend repositories/services, not directly from LangGraph nodes.
## 15. Authentication and Authorization Contract

- Frontend sends authentication credential/token to backend only; it does not send a trusted `user_id` as proof of identity.
- Backend validates authentication and derives `user_id`.
- Backend injects user identity into ServiceContext before calling agent services.
- Every read/update/delete verifies resource ownership.
- Agent tools that access user-connected resources require explicit authorization context; credentials are never placed into prompts or persisted in generated AgentDefinition.
- Logs must redact tokens, passwords, API keys, authorization headers, and sensitive provider credentials.
## 16. Guardrails and Security Requirements

### 16.1 Input guardrails

- Validate every external request using Pydantic/FastAPI schemas.
- Enforce min/max lengths and collection limits.
- Normalize and validate URLs before fetching.
- Whitelist source types, tool names, and model/provider identifiers.
- Reject unexpected fields when appropriate for security-sensitive requests.
- Apply rate limits to expensive research/build/test endpoints.
### 16.2 LLM guardrails

- Prefer structured output validated against Pydantic schemas.
- Treat model output as untrusted data until validation succeeds.
- Use bounded retries for malformed structured output; do not loop indefinitely.
- Separate system/developer instructions from retrieved source content to reduce prompt-injection risk.
- Retrieved web/GitHub/paper content must never be treated as instructions that can override system/tool policy.
- Do not place secrets, auth tokens, raw environment variables, or private credentials in prompts.
### 16.3 Execution guardrails

- Generated agents may invoke only registered tools.
- No arbitrary shell execution, `eval`, `exec`, dynamic import, or unsandboxed generated code in V1.
- Network access should be performed through controlled adapters with timeouts and allow/deny policies as appropriate.
- Set maximum graph steps, maximum refinement attempts, request timeout, and token/cost limits.
- Testing an agent must be isolated from production-destructive actions unless a future explicitly approved tool supports them.
### 16.4 Research integrity guardrails

- Keep source URL/title/type with evidence through the pipeline.
- Do not fabricate citations when a source is missing.
- Deduplicate equivalent sources before synthesis.
- Expose limitations when sources fail, evidence conflicts, or confidence is low.
- Research synthesis should distinguish evidence-backed findings from recommendations/inference.
## 17. Error Taxonomy

| Code | Owner/meaning | Retry? |
| --- | --- | --- |
| INVALID_REQUEST | Request violates contract | No, fix input |
| VALIDATION_ERROR | Schema/semantic validation failed | No, fix input/output |
| UNAUTHORIZED | Authentication missing/invalid | After auth |
| FORBIDDEN | User lacks access | No |
| RESEARCH_NOT_FOUND | Research ID unavailable to user | No |
| AGENT_NOT_FOUND | Agent ID unavailable to user | No |
| SOURCE_UNAVAILABLE | External research provider failed | Maybe |
| RATE_LIMITED | Provider/application rate limit | Yes, with backoff |
| RESEARCH_FAILED | Research workflow terminal failure | Maybe after diagnosis |
| AGENT_GENERATION_FAILED | Builder failed to produce valid definition | Maybe |
| AGENT_VALIDATION_FAILED | Generated definition violates rules | Refine/rebuild |
| TOOL_NOT_ALLOWED | Unknown/disabled tool requested | No |
| INVALID_STATE_TRANSITION | Operation not valid for current status/version | Refresh state |
| INTERNAL_ERROR | Unexpected application error | Maybe; inspect request_id |

All unexpected exceptions are logged with `request_id`. Client-facing messages should be useful but must not expose stack traces, filesystem paths, secrets, SQL, or provider credentials.

## 18. Logging, Observability and Correlation

- Generate a `request_id` at the HTTP boundary if one is not supplied by trusted infrastructure.
- Propagate `request_id` through backend -> Research/Builder -> tools.
- Log structured fields: timestamp, level, request_id, user_id (safe internal ID), module, operation, status, duration_ms, error_code.
- For research, log provider/tool latency and source counts, not entire copyrighted/private documents by default.
- For agent execution, log node transitions and tool names; redact tool inputs/outputs when they may contain secrets.
- Never use `print()` as the production logging strategy.
## 19. Configuration and Environment Variables

```
# .env.example — names only, NEVER real secrets
APP_ENV=development
API_V1_PREFIX=/api/v1
DATABASE_URL=
JWT_SECRET=
GITHUB_TOKEN=
SEMANTIC_SCHOLAR_API_KEY=
SEARCH_API_KEY=
LLM_PROVIDER=
LLM_MODEL=
LLM_API_KEY=
REDIS_URL=
CORS_ALLOWED_ORIGINS=http://localhost:5173
LOG_LEVEL=INFO
```

- Commit `.env.example`; never commit `.env`.
- Access configuration through one backend/module settings object rather than scattered `os.getenv()` calls.
- Development, test, and production use different secrets/configuration.
- Do not hardcode localhost URLs in application logic; use configuration.
## 20. Frontend Integration Rules

- All HTTP calls go through `frontend/src/api/client.js`; pages/components do not duplicate fetch/axios configuration.
- Create feature API wrappers (`researchApi.js`, `agentBuilderApi.js`) matching the documented endpoints.
- UI must render backend status enum values through a mapping layer; do not invent backend status strings.
- Handle loading, empty, partial, completed, and failed states explicitly.
- Never assume `data` exists when `success=false`.
- Use `request_id` in user-visible support/debug details when an operation fails.
- Do not expose provider API keys in browser environment variables. Provider calls requiring secrets go through backend.
## 21. Research-to-Agent Integration Sequence

1. User completes research through `/api/v1/research`.
1. Backend persists the completed ResearchResult.
1. Frontend shows “Build Agent from Research” only for an eligible completed research item.
1. Backend loads the research result after verifying ownership.
1. Backend converts it into `ResearchToAgentRequest`; frontend should not be trusted to resubmit or alter authoritative research evidence.
1. Backend constructs `AgentBuildRequest` with populated `research_context`.
1. Agent Builder analyzes objective/constraints, selects registered tools, designs graph, generates AgentDefinition, and validates it.
1. Backend persists AgentDefinition and returns the standard API envelope.
> **INTEGRATION PRINCIPLE** Pass IDs from the client; reconstruct trusted cross-module context on the server whenever possible. This avoids stale/tampered handoff payloads.

## 22. State Transition Rules

```
Research:
created -> analyzing -> planning -> searching -> filtering -> synthesizing -> completed
                                                            \-> failed

Agent:
draft -> analyzing -> designing -> generating -> validating -> ready
                                                   \-> failed
```

A module may skip an internal status only if the external contract remains coherent. Completed/ready resources should not silently return to an earlier status. Refinement should create an updated agent version or an explicit refinement operation rather than mutating history invisibly.

## 23. Testing Standard

### 23.1 Required test layers

| Layer | Owner | Minimum coverage goal |
| --- | --- | --- |
| Schema/unit | All | Validation, enums, pure helpers, state transformations |
| Research nodes | Member 2 | Mock external providers; test success, empty, timeout, malformed result |
| Builder nodes | Member 3 | Tool whitelist, graph validation, malformed LLM output, refinement bounds |
| Backend API | Member 1 | Auth, status codes, envelopes, ownership, repository behavior |
| Contract tests | All | Service input/output validates against shared schemas |
| Integration | All | Research Only, Direct Build, Research-to-Agent |
| Smoke/E2E | All before release | Frontend -> backend -> module -> persistence happy path |

### 23.2 Mandatory integration test cases

- Valid ResearchRequest returns a schema-valid ResearchResult.
- One research source provider fails while others succeed; output reports limitation rather than fabricating data.
- Direct AgentBuildRequest with no research_context produces a valid AgentDefinition.
- Completed ResearchResult can be transformed into ResearchToAgentRequest and consumed by Agent Builder.
- Unknown tool emitted by LLM is rejected by validator.
- Invalid/malformed LLM structured output is retried within bound and then fails safely.
- User A cannot access User B research or agents.
- Agent test cannot execute unregistered arbitrary code/tool.
- Frontend correctly handles standard error envelope and displays request_id.
## 24. Git and Collaboration Workflow

### 24.1 Branches

```
main                 # deployable/stable
develop              # integration branch (optional but recommended for student team)
feature/frontend-*
feature/backend-*
feature/research-*
feature/agent-builder-*
fix/*
docs/*
```

### 24.2 Pull request rules

- No direct feature work on `main`.
- Pull latest integration branch before opening PR and resolve conflicts locally.
- PR description states what changed, contract impact, tests run, and screenshots/API examples where relevant.
- Any change under `shared/schemas`, `shared/enums`, API paths, or DB contract must be explicitly marked “CONTRACT CHANGE”.
- At least one teammate reviews contract changes before merge.
- CI must pass before merge.
- Do not combine unrelated refactors with a contract change unless necessary.
### 24.3 Commit convention

```
feat(research): add paper search node
feat(builder): validate tool registry
feat(api): add research-to-agent endpoint
fix(shared): correct research status enum
test(integration): add research-to-agent flow
docs(contract): document AgentDefinition v1
```

## 25. Definition of Done Per Module

### 25.1 Platform

- Routes match API contract.
- Auth identity is injected server-side.
- Persistence/repositories implemented and tested.
- Standard response/error envelope used everywhere.
- Frontend API client handles all documented states.
- Docker/config/deployment does not require source-code edits.
### 25.2 Research Agent

- Public `run_research()` accepts canonical ResearchRequest.
- All provider results are normalized before synthesis.
- ResearchResult validates against shared schema.
- Citations/sources are traceable; failures/limitations are represented.
- No direct DB or frontend dependency.
- Unit tests mock external services.
### 25.3 Agent Builder

- Public `build_agent()` accepts canonical AgentBuildRequest.
- Direct and research-based builds use same core pipeline.
- Only registered tools can enter AgentDefinition.
- AgentDefinition passes structural/guardrail validation.
- Testing is controlled and does not execute arbitrary generated code.
- No direct Research Agent internal dependency.
## 26. CI/CD Quality Gates

A minimal GitHub Actions pipeline should run on pull requests and pushes to integration/main branches.

```
1. Install Python and frontend dependencies
2. Python formatting/lint checks
3. Frontend lint/build
4. Unit tests
5. Shared schema/contract tests
6. Integration tests with mocked external providers
7. Build Docker images
8. On approved main release: deploy using environment-specific secrets
```

Never run costly live LLM/web-provider integration tests on every PR unless intentionally configured. Use mocks/fixtures for deterministic CI and a separate optional live smoke workflow.

## 27. Deployment Contract

- Frontend and backend are independently buildable containers/services.
- Backend is the public gateway to Research and Agent Builder services in V1; do not expose internal module endpoints directly unless architecture later changes intentionally.
- Production secrets come from deployment secret management/environment configuration.
- Database migrations run as a controlled deployment step.
- Health endpoint should verify application process health; deeper dependency health may be exposed separately.
- CORS allows only approved frontend origins in production.
- External provider timeouts and retry policies must be configured; avoid hanging requests.
- If research/build operations become long-running, migrate endpoint behavior to 202 + job polling/streaming without breaking the domain schemas.
## 28. Contract Change Procedure

1. Developer proposes the change in a PR and updates this document / DATA_CONTRACT / API_CONTRACT.
1. Mark whether the change is additive, compatible, deprecated, or breaking.
1. Identify affected modules: frontend, backend, research, builder, DB.
1. At least one other member approves.
1. Update shared schema first.
1. Update producer and consumer tests.
1. Merge dependent changes in coordinated order.
1. For breaking public API changes, create a version/migration plan rather than silently changing V1 behavior.
## 29. Pre-Integration Checklist

- All members use the same shared schema revision.
- No duplicate local versions of ResearchRequest/ResearchResult/AgentDefinition exist.
- Research service runs independently with mocked/real configured providers.
- Builder service runs independently with direct input.
- ResearchResult -> ResearchToAgentRequest transformation passes contract tests.
- Backend can call both public service entry points.
- Auth identity and ownership checks work.
- Frontend uses only documented endpoints.
- Error envelopes/status codes are consistent.
- Environment variable names match `.env.example`.
- No secrets exist in Git history/current files.
- Integration tests pass before deployment.
## 30. Anti-Patterns — Explicitly Forbidden

- Passing arbitrary dictionaries between modules without validation.
- Duplicating shared schemas inside each member’s folder.
- Importing another member’s graph nodes to “quickly integrate”.
- Hardcoding provider keys, URLs, user IDs, or environment-specific values.
- Using `done`, `finished`, and `completed` interchangeably.
- Letting an LLM invent executable tool/function names at runtime.
- Executing generated Python/shell code without an approved sandbox/policy.
- Allowing frontend-supplied user_id to decide data ownership.
- Returning raw stack traces to the browser.
- Changing an API payload without updating contract docs and tests.
- Putting business logic directly in FastAPI route functions or React components.
- Calling external providers directly from the browser when credentials are required.
## 31. Initial Implementation Order

1. Create repository skeleton and shared package.
1. Freeze enums and Pydantic schemas in this document.
1. Member 1 creates stub FastAPI endpoints using fake ResearchResult/AgentDefinition responses.
1. Frontend integrates against stubs immediately.
1. Member 2 implements Research Agent behind `run_research()` and passes contract tests.
1. Member 3 implements Agent Builder behind `build_agent()` and passes contract tests.
1. Replace backend stubs with real service calls without changing frontend payloads.
1. Integrate Research-to-Agent handoff.
1. Add persistence/auth/ownership tests and E2E tests.
1. Containerize, configure CI, deploy, and run production smoke tests.
> **WHY THIS ORDER** The frontend/backend member can work before AI modules are finished, while the two AI members can work independently. Integration becomes implementation replacement behind stable contracts instead of a late redesign.

## 32. V1 Architectural Decisions to Keep Stable

- The product has three user journeys but two primary AI modules: Research and Agent Builder.
- Research is optional for agent creation.
- Research-to-Agent uses shared structured context, not direct graph coupling.
- LangGraph owns stateful AI workflow orchestration; LangChain may be used for model/tool abstractions and structured output.
- Backend owns HTTP, authentication, persistence, and cross-module orchestration.
- Generated agents are represented by validated declarative definitions and approved tool references.
- MySQL/application DB stores users, sessions, research metadata/results, agent definitions, tests, and audit metadata; vector retrieval may be added/used for semantic retrieval according to implementation needs.
- Every boundary is typed, versioned, testable, and observable.
## Appendix A — Shared Schema File Map

```
shared/schemas/common.py
  SourceReference
  EvidenceItem
  ServiceContext
  ApiResponse

shared/schemas/research.py
  ResearchRequest
  ResearchResult
  ResearchToAgentRequest

shared/schemas/agent.py
  AgentBuildRequest
  AgentNodeDefinition
  AgentEdgeDefinition
  AgentDefinition
  AgentTestRequest
  AgentTestResult
  AgentRefineRequest

shared/schemas/errors.py
  ErrorDetail

shared/enums/status.py
  JobStatus
  ResearchStatus
  AgentStatus
  SourceType
```

## Appendix B — Team Integration Sign-off

| Agreement | Member 1 | Member 2 | Member 3 |
| --- | --- | --- | --- |
| I will follow shared field names and schemas. |  |  |  |
| I will not depend on another module’s internals. |  |  |  |
| I will raise contract changes through PR/documentation. |  |  |  |
| My module will expose/test its public service interface. |  |  |  |
| I will not commit secrets. |  |  |  |

This specification is intended to be committed to the repository and treated as a living engineering contract. Update it whenever an approved architectural or contract decision changes.
