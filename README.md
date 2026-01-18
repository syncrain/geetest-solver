# GeeTest Solver

Python library for solving GeeTest v4 captchas (ICON and MATCH/IconCrush types).

## Installation

```bash
pip install geetest-solver
```

## Usage

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

## Features

- **Icon captcha**: YOLO-based object detection + template matching
- **Match captcha**: Grid-based puzzle solver (swap to match 3)
- Automatic retry on failure
- Proxy support
- High success rate

## Captcha Types

- `icon`: Click icons in sequence (uses YOLO model)
- `match`: Swap grid items to match 3 in a row (IconCrush)

## Requirements

- Python 3.8+
- CUDA (optional, for GPU acceleration)

## License

MIT
