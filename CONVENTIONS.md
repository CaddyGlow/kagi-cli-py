# Coding Conventions

## 1. Guiding Principles

Our primary goal is to build a robust, maintainable, code base.

Key principles:

* **Clarity over Cleverness:** Code should be easy to read and understand
* **Explicit over Implicit:** Be clear about intentions and dependencies
* **Consistency:** Follow established patterns within the project
* **Single Responsibility Principle:** Each module, class, or function should have one clear purpose
* **Loose Coupling, High Cohesion:** Modules should be independent but related components within a module should be grouped
* **Testability:** Write code that is inherently easy to unit and integration test
* **Pythonic:** Embrace PEP 8 and the Zen of Python (`import this`)

## 2. General Python Conventions

* **PEP 8 Compliance:** Adhere strictly to PEP 8
  * Use `ruff format` for auto-formatting to ensure consistent style
  * Line length limit is **88 characters** (ruff's default)
* **Python Version:** Target **Python 3.11+**. Utilize modern features like union types (`X | Y`)
* **No Mutable Default Arguments:** Avoid using mutable objects as default arguments
  * **Bad:** `def foo(items=[])`
  * **Good:** `def foo(items: list | None = None): if items is None: items = []`

## 3. Naming Conventions

* **Packages/Directories:** `snake_case` (e.g., `api`, `claude_sdk`, `auth`)
* **Modules:** `snake_case` (e.g., `manager.py`, `client.py`)
* **Classes:** `CamelCase` (e.g., `OpenAIAdapter`, `ServiceContainer`)
  * **Abstract Base Classes:** Suffix with `ABC` or `Protocol`
  * **Pydantic Models:** `CamelCase` (e.g., `MessageCreateParams`)
* **Functions/Methods/Variables:** `snake_case` (e.g., `handle_request`, `get_access_token`)
* **Constants:** `UPPER_SNAKE_CASE` (e.g., `DEFAULT_PORT`, `API_VERSION`)
* **Private Members:** `_single_leading_underscore` for internal use

## 4. Imports

* **Ordering:** Standard library → Third-party → First-party → Relative
* **Absolute Imports Preferred:** Use absolute imports for modules within the project
* **`__all__` in `__init__.py`:** Define to explicitly expose public API

## 5. Typing

Type hints are mandatory for clarity and maintainability:

* **All Function Signatures:** Type-hint all parameters and return values, avoid `Any`
* **Class Attributes:** Use type hints, especially for Pydantic models
* **Union Types:** Use `Type | None` for optional values (Python 3.11+)
* **Type Aliases:** Define in `core/types.py` for complex types
* **Generics:** Use `Generic[T]` for classes/functions that operate on multiple types

## 7. Error Handling

* **Custom Exceptions:** Inherit from `kagicli.errors.BaseError`
* **Catch Specific Exceptions:** Never use bare `except:`
* **Chain Exceptions:** Use `raise NewError(...) from original`

## 8. Asynchronous Programming

* **`async`/`await`:** Use consistently for all I/O operations
* **Libraries:** Prefer `httpx` for HTTP, `asyncio` for concurrency
* **No Blocking Code:** Never use blocking I/O in async functions

## 9. Testing

* **Framework:** `pytest` with `pytest-asyncio`
* **Architecture:** Streamlined after aggressive refactoring (606 tests, was 786)
* **Structure:** Clean separation with proper boundaries:
  * `tests/unit/` - Fast, isolated unit tests (mock at service boundaries only)
  * `tests/integration/` - Cross-component interaction tests (core)
* **Markers:** Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.network`,  `@pytest.mark.slow`
* **Fixtures:** Essential fixtures only in `conftest.py` (515 lines, was 1117)
* **Mocking:** External services only - no internal component mocking
* **Type Safety:** All test functions must have `-> None` return type
* **Coverage:** High coverage on critical paths with real component testing

## 10. Configuration

* **Pydantic Settings:** All config in `config/settings.py`
* **Environment Variables:** Use `__` for nesting 
* **Priority:** CLI args → Environment → TOML files → Defaults

## 11. Security

* **Input Validation:** All API inputs validated with Pydantic
* **No Secrets in Code:** Use environment variables

## 12. Tooling

Core tools enforced via pre-commit and CI:

* **Package Manager:** `uv` (via Makefile only)
* **Formatter:** `ruff format`
* **Linter:** `ruff check`
* **Type Checker:** `mypy`
* **Test Runner:** `pytest`
* **Dev Scripts:** helper scripts under `scripts/` for local testing and debugging

## 13. Development Workflow

### Required Before Commits
```bash
make pre-commit  # Comprehensive checks + auto-fixes
make test        # Run tests with coverage
```

## 14. Documentation

* **Docstrings:** Required for all public APIs (Google style)
* **Comments:** Explain *why*, not *what*
* **TODO/FIXME:** Use consistently with explanations

## 15. Git Workflow

* **Commits:** Follow Conventional Commits (feat:, fix:, docs:, etc.)
* **Branches:** Use feature branches (`feature/`, `fix/`, `docs/`)
* **No `git add .`:** Only stage specific files

