#!/usr/bin/env python3
"""
Example usage of geetest_solver package
"""
from geetest_solver import solve_captcha

# Example 1: Icon captcha (default)
print("Solving icon captcha...")
seccode = solve_captcha(
    captcha_id="<YOUR_CAPTCHA_ID>",
    captcha_type="icon",
    verbose=True
)
print(f"Success! Seccode: {seccode}")

# Example 2: Match/IconCrush captcha
print("\nSolving match captcha...")
seccode = solve_captcha(
    captcha_id="<YOUR_CAPTCHA_ID>",
    captcha_type="match",
    verbose=True
)
print(f"Success! Seccode: {seccode}")

# Example 3: With proxy
print("\nSolving with proxy...")
proxies = {
    'http': 'http://user:pass@proxy.example.com:8080',
    'https': 'http://user:pass@proxy.example.com:8080'
}
seccode = solve_captcha(
    captcha_id="<YOUR_CAPTCHA_ID>",
    captcha_type="icon",
    proxies=proxies,
    verbose=True
)
print(f"Success! Seccode: {seccode}")
