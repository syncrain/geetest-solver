#!/usr/bin/env python3
import sys
import os

# Check dependencies
try:
    import requests
    from ultralytics import YOLO
    import pyotp
except ImportError as e:
    print(f"Installing dependencies...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'requests', 'ultralytics', 'pyotp'])

sys.path.insert(0, os.path.dirname(__file__))
from hybrid_solver import load_geetest_captcha, hybrid_solve, submit_verify_request, generate_w_parameter
import time
import json

def solve_captcha(captcha_id=None, max_attempts=999, interactive=False, proxies=None, verbose=False):
    """Solve captcha with retry until success"""
    if not captcha_id:
        captcha_id = os.environ.get('CAPTCHA_ID')
        if not captcha_id:
            raise ValueError("captcha_id is required. Pass it as parameter or set CAPTCHA_ID environment variable.")
    
    # Suppress YOLO output
    os.environ['YOLO_VERBOSE'] = 'False'
    
    try:
        model_path = os.path.join(os.path.dirname(__file__), 'best.pt')
        model = YOLO(model_path, verbose=False)
    except:
        model = YOLO('yolov8n.pt', verbose=False)
    
    while True:
        captcha_data_raw = load_geetest_captcha(captcha_id, proxies=proxies, verbose=verbose)
        if not captcha_data_raw:
            time.sleep(10)
            continue
        
        if len(captcha_data_raw['ques']) == 1:
            time.sleep(3)
            continue
        
        coordinates_list = hybrid_solve(captcha_data_raw, model, attempt_num=1, interactive=interactive, verbose=verbose)
        if not coordinates_list:
            time.sleep(3)
            continue
        
        for coordinates in coordinates_list[:2]:
            w_param = generate_w_parameter(captcha_data_raw, coordinates)
            verify_response = submit_verify_request(captcha_data_raw, w_param, captcha_id, proxies=proxies, verbose=verbose)
            
            if verify_response.startswith('geetest_'):
                json_data = json.loads(verify_response[verify_response.find('(')+1:verify_response.rfind(')')])
                if 'data' in json_data and json_data['data'].get('result') == 'success':
                    return json_data['data']['seccode']
        
        time.sleep(3)

if __name__ == "__main__":
    result = solve_captcha()
    if result:
        print(f"\n🎉 SECCODE: {result}")
    else:
        print("\n❌ Failed")
