# AGENTS

## Project Positioning

This project is a self-service invoice information extraction and form-filling program. The core process is as follows:

1. The user uploads invoice files.
2. The program uses the PaddleOCR API to perform OCR on the invoices and outputs Markdown files.
3. The Markdown files must preserve table structures so that invoice fields correspond to the original invoice content as closely as possible.
4. The program sends the Markdown together with prompts to the LLM API.
5. The LLM analyzes the Markdown fields and returns structured JSON.
6. The program automatically fills the Excel form based on the mapping between JSON fields and Excel template fields.

## Current Technical Constraints

- Target Python version: `3.9.25`
- Dependency management: `uv`
- Backend framework: `FastAPI`
- OCR technology: `PaddleOCR-VL-1.5`, called via API
- LLM technology: `DeepSeek API`, called via API
- Project directory layout: use `src layout`

## Functional Scope

### Confirmed Main Workflow

- Invoice file upload
- OCR recognition and generation of Markdown intermediate results
- LLM parsing of Markdown and output of JSON
- Filling Excel based on field mappings

### Template and Field Selection Capability

- The system must provide two default Excel templates for users to choose from.
- Users can select additional optional fields on top of the default template fields.
- Optional fields must be included in LLM prompt construction.
- LLM invocation must distinguish between:
  - System prompt: defines role, output format, field constraints, and missing-value handling rules
  - User prompt: contains OCR Markdown content, template information, required fields, and optional fields

## Design Principles

- OCR output must prioritize preserving the original invoice semantics and table structure to avoid introducing ambiguity for downstream LLM parsing.
- LLM output must be stable, validatable JSON and must not rely on natural-language explanations.
- Excel form-filling logic must be based on explicit field mappings and must avoid implicit matching.
- Templates, field definitions, and prompts should be configurable as much as possible and should not be hardcoded into the business workflow.
- OCR, LLM, template mapping, and form-filling workflows should be implemented in layers to make model or template replacement easier.

## Recommended Module Partitioning

- `src/api/`
  - FastAPI routes and request/response models
- `src/api/routes/`
  - Route definitions
- `src/api/schemas/`
  - Request and response models
- `src/api/services/`
  - Asynchronous request flow orchestration
- `src/api/app.py`
  - FastAPI main application and main route entry point
- `src/core/`
  - Configuration, environment variable loading, and shared foundational capabilities
- `src/core/config.py`
  - Mainly stores configuration definitions
  - Reads `.env` through `python-dotenv`
  - Sensitive configuration such as `api_key`, external service addresses, `host`, `port`, and similar values must be loaded from environment variables in a unified way
- `.env`
  - Stores sensitive data and environment-specific configuration and must not contain business logic
- `src/integrations/`
  - Wrappers for external interface calls, such as PaddleOCR and DeepSeek LLM
- `src/services/ocr/`
  - Invoice file preprocessing
  - PaddleOCR API calls
  - Markdown intermediate result generation
- `src/services/llm/`
  - Prompt assembly
  - DeepSeek API calls
  - JSON result cleaning and validation
- `src/services/template/`
  - Default template definitions
  - Optional field definitions
  - Field mapping management
- `src/services/excel/`
  - Excel reading and writing
  - Field placement and form filling
- `src/services/workflow`
  - Orchestrates the entire task workflow
  - Responsible for business orchestration of "read invoice -> OCR -> LLM analysis -> JSON validation -> fill Excel"

## API Layer Conventions

- `src/api/routes` is responsible for route definitions and interface decomposition.
- `src/api/schemas` is responsible for request and response model definitions.
- `src/api/services` is responsible for asynchronous processing at the API layer.
- `src/api/app.py` serves as the main route entry point and centrally registers routes, middleware, and cross-origin configuration.
- Asynchronous flows at the API layer should default to `async`, and `asyncio` should be used when task scheduling is involved.
- Cross-origin requests are a default requirement, and the main application should configure CORS middleware.
- The `host` and `port` required for service listening must be centrally managed in `src/core/config.py`.

## Configuration Management Conventions

- `src/core/config.py` is the main entry point for project configuration.
- Non-sensitive configuration can be defined centrally in `config.py`.
- Sensitive configuration must be placed in `.env`, such as API keys, tokens, authentication addresses, and similar data.
- `config.py` must read `.env` through `python-dotenv`; other layers must not repeatedly load environment variables.
- External interface clients must obtain configuration from `config.py` and should not directly scatter `os.getenv` references throughout the codebase.

## Data Conventions

It is recommended to maintain at least the following intermediate data objects:

- OCR Markdown
- Template metadata
- User-selected field list
- Raw LLM response
- Structured JSON
- Excel field mapping results

## Development Requirements

- New features should prioritize the main chain of "upload -> OCR -> Markdown -> LLM JSON -> Excel form filling".
- Any change involving the LLM must simultaneously consider the system prompt, user prompt, JSON schema, and exception fallback handling.
- Any change involving templates must simultaneously consider default templates, optional fields, field mappings, and front-end/back-end parameter passing.
- External capabilities must be uniformly wrapped through API clients and must not be assembled directly in the route layer.
- Key workflows should retain auditable intermediate results for troubleshooting recognition errors and field mapping errors.
- Code organization must follow the established directory responsibilities and must avoid mixing integration logic, workflow orchestration logic, and API route logic together.
- Asynchronous interfaces and task orchestration should prioritize `async/await` and avoid introducing blocking external calls in the API layer.
- Development must maintain modular thinking and should advance in small features and small phases rather than piling up a large number of changes at once.

## Git Commit Conventions

- Commits must follow the Conventional Commits specification.
- `commit message` must be written in Chinese.
- Commit descriptions must be as detailed as possible and must not be limited to vague titles.
- Commit content must clearly include the following information:
  - The core functionality implemented in this change
  - The implementation approach
  - The key workflow, algorithm formula, or processing pipeline
  - The scope of impact
- Recommended commit formats are as follows:
  - `feat: 新增发票 OCR 到 Markdown 的异步处理流程`
  - `fix: 修复 DeepSeek 返回非 JSON 时的解析兜底逻辑`
  - `refactor: 拆分模板字段映射与 Excel 填表服务`
- If more detail is needed, prefer using a multi-line commit message in Chinese.
- After completing each relatively independent small module, small feature, or small phase, proactively remind the user whether a `commit` is needed.

## Collaboration Conventions

- Maintain modular decomposition awareness throughout implementation.
- After completing each small part or independent feature, sync the current progress with the user.
- After completing each independently committable phase, proactively ask the user whether an immediate `commit` is needed.
- Do not create commits for the user without explicit user instruction.

## Notes

- The current Python version declaration in `pyproject.toml` may be inconsistent with the target version `3.9.25`; this should be unified in later implementation.
- The existing LLM integration code currently contains both `Qwen` and `DeepSeek` related implementations. If `DeepSeek API` is the formal solution, the interface and default configuration should be unified in later iterations.
