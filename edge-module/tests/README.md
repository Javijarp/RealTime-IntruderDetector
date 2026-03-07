# Exception Handling Test Suite

Comprehensive testing suite for the edge module exception handling implementation.

## Test Files

### 1. Unit Tests (`tests/test_exceptions.py`)

Automated unit tests using pytest framework.

**Test Coverage:**

- ✅ Camera exceptions (not found, initialization, disconnection)
- ✅ Queue exceptions (frame queue full, event queue full)
- ✅ Network exceptions (connection, timeout, HTTP errors)
- ✅ Circuit breaker pattern (state transitions)
- ✅ Memory pressure monitoring

**Run:**

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all unit tests
python tests/test_exceptions.py

# Or using pytest
pytest tests/test_exceptions.py -v

# With coverage report
pytest tests/test_exceptions.py --cov=src --cov-report=html
```

### 2. Integration Tests (`tests/test_integration.py`)

End-to-end integration tests simulating real-world scenarios.

**Test Scenarios:**

1. Camera not found with invalid index
2. Camera disconnection and reconnection
3. Network failure with event buffering
4. Queue overflow handling
5. Circuit breaker integration
6. Memory pressure detection
7. End-to-end resilience

**Run:**

```bash
python tests/test_integration.py
```

### 3. Manual Test Script (`test_exception_handlers.py`)

Interactive test script with colored output for manual verification.

**Features:**

- 🎨 Colored terminal output
- ⏱️ Test timing and performance metrics
- 📊 Detailed summary and statistics
- 🔍 Step-by-step test execution

**Run:**

```bash
# Make executable (first time only)
chmod +x test_exception_handlers.py

# Run tests
python test_exception_handlers.py
```

## Test Results

### Expected Output

When all tests pass, you should see:

```
======================================================================
  EDGE MODULE - EXCEPTION HANDLING TEST SUITE
  Manual Testing Script
======================================================================

...

======================================================================
  TEST SUMMARY
======================================================================

Results:
  Total Tests:    9
  Passed:         9
  Failed:         0
  Success Rate:   100.0%
  Total Time:     X.XXs

🎉 ALL TESTS PASSED! 🎉
Exception handling is fully functional.
```

## Individual Test Details

### Test 1: Camera Not Found

- **Exception:** `CameraNotFoundException`
- **Scenario:** No camera available at any index
- **Expected Behavior:**
  - Retries with exponential backoff
  - Tries alternative camera indices
  - Raises `CameraNotFoundException` after all attempts

### Test 2: Camera Disconnection

- **Exception:** `CameraDisconnectionError`
- **Scenario:** Camera disconnects during operation
- **Expected Behavior:**
  - Detects 10 consecutive failures
  - Triggers reconnection logic
  - Falls back to simulation mode if reconnection fails

### Test 3: Frame Queue Full

- **Exception:** `FrameQueueFullError`
- **Scenario:** Frame buffer at capacity (5/5)
- **Expected Behavior:**
  - Drops frames when queue full
  - Implements backpressure mechanism
  - Logs dropped frame statistics

### Test 4: Event Queue Full

- **Exception:** `EventQueueFullError`
- **Scenario:** Event queue at capacity (10/10)
- **Expected Behavior:**
  - Buffers events to LocalBuffer
  - Prevents event loss
  - Alerts on frequent buffering

### Test 5: Backend Connection Error

- **Exception:** `BackendConnectionError`
- **Scenario:** Cannot connect to backend
- **Expected Behavior:**
  - Catches connection error
  - Returns False
  - Events buffered for retry

### Test 6: Backend Timeout

- **Exception:** `BackendTimeoutError`
- **Scenario:** Request exceeds timeout (5s)
- **Expected Behavior:**
  - Catches timeout error
  - Returns False
  - Respects configured timeout value

### Test 7: Backend HTTP Errors

- **Exceptions:** `BackendClientError`, `BackendServerError`
- **Scenarios:** 400, 404, 429, 500, 503 errors
- **Expected Behavior:**
  - Handles each error code appropriately
  - 429: Backs off and retries
  - 4xx: Logs and doesn't retry
  - 5xx: Retries with backoff

### Test 8: Circuit Breaker

- **Pattern:** Circuit Breaker with 3 states
- **Scenarios:** CLOSED → OPEN → HALF_OPEN → CLOSED
- **Expected Behavior:**
  - Opens after 5 failures
  - Transitions to HALF_OPEN after 30s
  - Closes after 2 successes in HALF_OPEN
  - Prevents request flooding

### Test 9: Memory Pressure

- **Exception:** `OutOfMemoryError`
- **Scenarios:** OK (50%), WARNING (75%), CRITICAL (90%)
- **Expected Behavior:**
  - Detects memory levels correctly
  - Triggers appropriate responses
  - Drops frames when CRITICAL

## Troubleshooting

### Tests Fail to Import Modules

```bash
# Ensure you're in the edge-module directory
cd edge-module

# Install dependencies
pip install -r requirements.txt
```

### Mock Issues

If you see import errors for `unittest.mock`:

```bash
# Python 3.3+ should have it built-in
python --version  # Ensure Python 3.3+
```

### pytest Not Found

```bash
pip install pytest pytest-mock
```

## Continuous Integration

To integrate with CI/CD:

```yaml
# .github/workflows/test.yml
name: Test Exception Handling

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: "3.9"
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run unit tests
        run: pytest tests/test_exceptions.py -v
      - name: Run integration tests
        run: python tests/test_integration.py
      - name: Run manual test script
        run: python test_exception_handlers.py
```

## Coverage Report

Generate coverage report:

```bash
# Install coverage tools
pip install pytest-cov

# Run with coverage
pytest tests/ --cov=src --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

## Performance Benchmarks

Expected test execution times:

- Unit Tests: ~2-5 seconds
- Integration Tests: ~5-10 seconds
- Manual Test Script: ~5-10 seconds

## Adding New Tests

To add new exception tests:

1. Add exception class to `src/exceptions.py`
2. Add unit test to `tests/test_exceptions.py`
3. Add integration test to `tests/test_integration.py`
4. Add manual test to `test_exception_handlers.py`
5. Update this README

## Test Configuration

Test behavior can be configured in `src/config.py`:

```python
# Exception Handling Configuration
CAMERA_RETRY_ATTEMPTS: int = 5
CAMERA_FAILURE_THRESHOLD: int = 10
CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT_S: int = 30
MEMORY_WARNING_THRESHOLD_PERCENT: float = 75.0
MEMORY_CRITICAL_THRESHOLD_PERCENT: float = 90.0
```

## License

Same as parent project.
