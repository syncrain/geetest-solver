# GeeTest ICON Solver

Python library for solving GeeTest v4 ICON CAPTCHA using YOLO object detection and template matching.

## Installation

```bash
pip install geetest-solver
```

## Usage

```python
from captcha_solver import solve_captcha

# Basic usage
seccode = solve_captcha(captcha_id="your_captcha_id")

# With proxy
proxies = {
    'http': 'http://proxy.example.com:8080',
    'https': 'http://proxy.example.com:8080'
}
seccode = solve_captcha(captcha_id="your_captcha_id", proxies=proxies)
```

## Features

- YOLO-based object detection for ICON captchas
- Template matching for icon recognition
- Automatic retry on failure
- Proxy support
- High success rate

## Requirements

- Python 3.8+
- CUDA (optional, for GPU acceleration)

## License

MIT
