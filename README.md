# GeeTest Solver

Python library for solving GeeTest v4 captchas (ICON and MATCH/IconCrush types).

## Installation

```bash
pip install geetest-solver

```

## Usage

### Synchronous

```python
from geetest_solver import solve_captcha

# Icon captcha (default)
seccode = solve_captcha(captcha_id="<CAPTCHA_ID>", captcha_type="icon")

# Match/IconCrush captcha
seccode = solve_captcha(captcha_id="<CAPTCHA_ID>", captcha_type="match")

# With proxy
proxies = {
    'http': 'http://user:pass@proxy.example.com:8080',
    'https': 'http://user:pass@proxy.example.com:8080'
}
seccode = solve_captcha(
    captcha_id="<CAPTCHA_ID>", 
    captcha_type="icon",
    proxies=proxies
)
```

### Async (FastAPI, aiohttp, etc.)

```python
from geetest_solver.async_wrapper import solve_captcha_async

# Icon captcha
seccode = await solve_captcha_async(captcha_id="<CAPTCHA_ID>", captcha_type="icon")

# Match captcha
seccode = await solve_captcha_async(captcha_id="<CAPTCHA_ID>", captcha_type="match")

# With proxy
proxies = {
    'http': 'http://user:pass@proxy.example.com:8080',
    'https': 'http://user:pass@proxy.example.com:8080'
}
seccode = await solve_captcha_async(
    captcha_id="<CAPTCHA_ID>",
    captcha_type="icon",
    proxies=proxies
)
```

### FastAPI Example

```python
from fastapi import FastAPI
from geetest_solver.async_wrapper import solve_captcha_async

app = FastAPI()

@app.post("/solve")
async def solve_captcha_endpoint(captcha_id: str):
    result = await solve_captcha_async(captcha_id=captcha_id)
    return {"seccode": result}
```

### Model Reuse (for multiple solves)

```python
from geetest_solver.solver import get_model, solve_captcha

# Load model once
model = get_model()

# Solve 100 captchas with same model (saves CPU/memory)
for i in range(100):
    result = solve_captcha(
        captcha_id="<CAPTCHA_ID>",
        model=model  # Reuse model
    )
```

### Async with Model Reuse

```python
from geetest_solver.solver import get_model
from geetest_solver.async_wrapper import solve_captcha_async

# Load model once
model = get_model()

# Solve multiple captchas
for i in range(100):
    result = await solve_captcha_async(
        captcha_id="<CAPTCHA_ID>",
        model=model
    )
```

## Features

- **Icon captcha**: YOLO-based object detection + template matching
- **Match captcha**: Grid-based puzzle solver (swap to match 3)
- **Async support**: Non-blocking execution for FastAPI/async frameworks
- **Thread-safe**: No matplotlib global lock issues
- Automatic retry on failure
- Proxy support
- High success rate

## Captcha Types

- `icon`: Click icons in sequence (uses YOLO model)
- `match`: Swap grid items to match 3 in a row (IconCrush)

## Configuration

### Model Management

The YOLO model is cached in memory after first load. To manually free memory:

```python
from geetest_solver.solver import get_model, unload_model

# Load model
model = get_model()

# Use model for solving...

# Free memory when done
unload_model()
```

**Note**: In FastAPI/long-running servers, the model stays loaded for the entire process lifetime (recommended for performance).

### Disable Matplotlib (default)

Matplotlib is disabled by default to avoid global lock issues in multi-threaded environments. To enable for debugging:

```bash
export ENABLE_MATPLOTLIB=1
```

### Disable YOLO Verbose Output

```python
import os
os.environ['YOLO_VERBOSE'] = 'False'
```

## Requirements

- Python 3.8+
- CUDA (optional, for GPU acceleration)

## License

MIT
