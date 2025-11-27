# Testing

## Run All Tests

```bash
cd backend
pytest tests/ -v
```

## Test Structure

```
backend/tests/
├── conftest.py          # Fixtures
├── test_auth.py         # Auth unit tests
├── test_validation.py   # Input validation tests
├── test_api.py          # API integration tests
├── test_authorization.py # Access control tests
└── test_security.py     # Security tests
```

## Test Categories

### Unit Tests
- Password hashing/verification
- JWT token creation/validation
- Input validation (email, length limits)

### Integration Tests
- All API endpoints
- Authentication flows
- Error handling

### Security Tests
- SQL injection
- XSS payloads
- Buffer overflow (long strings)
- Unicode edge cases

## Running Specific Tests

```bash
# Unit tests only
pytest tests/test_auth.py tests/test_validation.py -v

# Security tests only
pytest tests/test_security.py -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

## Expected Behaviour

- Valid requests: 200/201
- Validation errors: 400/422
- Unauthorized: 401
- Forbidden: 403
- Not found: 404
- Conflict: 409

Server never crashes regardless of input.
