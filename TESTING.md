# Streamlined Testing Guide

## Philosophy

After aggressive refactoring and architecture realignment, our testing philosophy is:
- **Clean boundaries**: Unit tests for isolated components, integration tests for cross-component behavior
- **Fast execution**: Unit tests run in milliseconds, mypy completes in seconds  
- **Modern patterns**: Type-safe fixtures, clear separation of concerns
- **Minimal mocking**: Only mock external services, test real internal behavior

## Quick Start

```bash
# Run all tests
make test

# Run specific test categories
pytest tests/unit/auth/          # Authentication tests
pytest tests/unit/config/      # Config tests
pytest tests/integration/        # Cross-component integration tests (core)

# Run with coverage
make test-coverage

# Type checking and quality (now sub-second)
make typecheck
make pre-commit
```


## Writing Tests

### Clean Architecture Principles

**Unit Tests** (tests/unit/):
- Mock at **service boundaries only** - never mock internal components
- Test **pure functions and single components** in isolation
- **No timing dependencies** - all asyncio.sleep() removed
- **No database operations** - moved to integration tests

**Integration Tests** (tests/integration/):
- Test **cross-component interactions** with minimal mocking
- Include **HTTP client testing **
- Test **async coordination when needed**
- Validate configuration end-to-end

### Mocking Strategy (Simplified)

- **External APIs only** 
- **Internal services**: Use real implementations with dependency injection
- **Configuration**: Use test settings objects, not mocks
- **No mock explosion**

## Type Safety and Code Quality

**REQUIREMENT**: All test files MUST pass type checking and linting. This is not optional.

### Type Safety Requirements

1. **All test files MUST pass mypy type checking** - No `Any` types unless absolutely necessary
2. **All test files MUST pass ruff formatting and linting** - Code must be properly formatted
3. **Add proper type hints to all test functions and fixtures** - Include return types and parameter types
4. **Import necessary types** - Use `from typing import` for type annotations

### Required Type Annotations

- **Test functions**: Must have `-> None` return type annotation
- **Fixtures**: Must have proper return type hints
- **Parameters**: Must have type hints where not inferred from fixtures
- **Variables**: Add type hints for complex objects when not obvious

## Architecture Overview 

### Essential Fixtures 


## Test Markers

- `@pytest.mark.unit` - Fast unit tests (default)
- `@pytest.mark.integration` - Cross-component integration tests
- `@pytest.mark.network` - Tests requiring network access (external APIs) 
- `@pytest.mark.slow` - Tests that take longer than 1 second (avoid if possible) 

## Best Practices

1. **Clean boundaries** - Unit tests mock at service boundaries only
2. **Fast execution** - Unit tests run in milliseconds, no timing dependencies
3. **Type safety** - All fixtures properly typed, mypy compliant
4. **Real components** - Test actual internal behavior, not mocked responses
5. **Performance-optimized patterns** - Use session-scoped fixtures for expensive operations
6. **Modern async patterns** - `@pytest.mark.asyncio(loop_scope="session")` for integration tests
7. **No overengineering** - Removed 180+ tests, 3000+ lines of complexity

### Performance Guidelines

#### When to Use Session-Scoped Fixtures
- **Plugin integration tests** - Plugin initialization is expensive
- **Database/external service tests** - Connection setup overhead
- **Complex app configuration** - Multiple services, middleware stacks
- **Consistent test state needed** - Tests require same app configuration

#### When to Use Factory Patterns  
- **Dynamic configurations** - Each test needs different plugin settings
- **Isolation required** - Tests might interfere with shared state
- **Simple setup** - Minimal overhead for app creation

#### Logging Performance Tips
- **Use `ERROR` level** - Minimal logging for faster test execution
- **Disable JSON logs** - `json_logs=False` for better performance
- **Manual setup required** - Call `setup_logging()` explicitly in test environment


## Running Tests

### Make Commands

```bash
make test                 # Run all tests with coverage except network, slow
make test-coverage        # With coverage report
```

### Direct pytest

```bash
pytest -v                          # Verbose output
pytest -k "test_auth"              # Run matching tests
pytest --lf                        # Run last failed
pytest -x                          # Stop on first failure
pytest -s -v                       # No capture, verbose 
pytest --pdb                       # Debug on failure
pytest -m unit                     # Unit tests only
pytest -m integration              # Integration tests only
pytest -m slow                     # Slow tests only 
```

## Migration from Old Architecture

**All existing test patterns still work** - but new tests should use the performance-optimized patterns:

