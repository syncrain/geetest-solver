#!/usr/bin/env python3
import sys
import os
import time
import json
import requests

os.environ['YOLO_VERBOSE'] = 'False'

try:
    from ultralytics import YOLO
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-q', 'ultralytics'])
    from ultralytics import YOLO

sys.path.insert(0, os.path.dirname(__file__))
from hybrid_solver import load_geetest_captcha, hybrid_solve, submit_verify_request, generate_w_parameter
from iconcrush_solver import iconcrush_solve_all, generate_w_parameter_iconcrush

# Global model cache
_model_cache = None

def get_model():
    """Get or load YOLO model (cached)"""
    global _model_cache
    if _model_cache is None:
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'best.pt')
            _model_cache = YOLO(model_path, verbose=False)
        except:
            _model_cache = YOLO('yolov8n.pt', verbose=False)
    return _model_cache

def unload_model():
    """Manually unload the cached model to free memory"""
    global _model_cache
    if _model_cache is not None:
        del _model_cache
        _model_cache = None
        import gc
        gc.collect()

def solve_captcha(captcha_id=None, captcha_type="icon", max_attempts=999, interactive=False, proxies=None, verbose=False, model=None):
    """Solve captcha with retry until success
    
    Args:
        captcha_id: GeeTest captcha ID
        captcha_type: "icon" or "match" (iconcrush)
        max_attempts: Maximum retry attempts
        interactive: Show visualization popups
        proxies: Proxy dict {'http': 'url', 'https': 'url'}
        verbose: Print debug info
        model: Pre-loaded YOLO model (optional, for reuse)
    
    Returns:
        seccode dict on success, None on failure
    """
    if not captcha_id:
        captcha_id = os.environ.get('CAPTCHA_ID')
        if not captcha_id:
            raise ValueError("captcha_id is required")
    
    if captcha_type == "icon":
        # Use provided model or get cached model
        if model is None:
            model = get_model()
        
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
    
    elif captcha_type == "match":
        for attempt in range(max_attempts):
            callback = f"geetest_{int(time.time() * 1000)}"
            url = f"https://gcaptcha4.geetest.com/load?callback={callback}&captcha_id={captcha_id}&client_type=web&risk_type=match&pt=1&lang=eng"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': '*/*'
            }
            
            try:
                response = requests.get(url, headers=headers, proxies=proxies, timeout=30)
                if response.status_code != 200:
                    time.sleep(3)
                    continue
                
                json_str = response.text[response.text.find('(')+1:response.text.rfind(')')]
                data = json.loads(json_str)
                
                if data['status'] != 'success':
                    time.sleep(3)
                    continue
                
                captcha_data = data['data']
                captcha_data['captcha_id'] = captcha_id
                
                solutions = iconcrush_solve_all(captcha_data, verbose=verbose)
                if not solutions:
                    time.sleep(2)
                    continue
                
                solution = solutions[0]
                time.sleep(1.5)
                
                w = generate_w_parameter_iconcrush(captcha_data, solution)
                
                verify_callback = f"geetest_{int(time.time() * 1000)}"
                verify_url = (
                    f"https://gcaptcha4.geetest.com/verify"
                    f"?callback={verify_callback}"
                    f"&captcha_id={captcha_id}"
                    f"&client_type=web"
                    f"&lot_number={captcha_data['lot_number']}"
                    f"&risk_type=match"
                    f"&payload={captcha_data['payload']}"
                    f"&process_token={captcha_data['process_token']}"
                    f"&payload_protocol=1"
                    f"&pt={captcha_data.get('pt', '1')}"
                    f"&w={w}"
                )
                
                verify_response = requests.get(verify_url, headers=headers, proxies=proxies, timeout=30)
                json_str = verify_response.text[verify_response.text.find('(')+1:verify_response.text.rfind(')')]
                result_data = json.loads(json_str)
                
                if result_data.get('status') == 'success' and result_data.get('data', {}).get('result') == 'success':
                    return result_data['data']['seccode']
                
                if result_data.get('code') == '-50305':
                    time.sleep(1)
                    continue
                    
            except Exception as e:
                if verbose:
                    print(f"Error: {e}")
                time.sleep(2)
    
    return None
