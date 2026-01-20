import requests
from PIL import Image
import numpy as np
from io import BytesIO
import json
import os
import cv2
import time
from ultralytics import YOLO
from scipy import ndimage

# Lazy load matplotlib only when interactive=True
_plt = None
_patches = None

def _load_matplotlib():
    global _plt, _patches
    if _plt is None and os.environ.get('ENABLE_MATPLOTLIB', '').lower() in ('1', 'true', 'yes'):
        try:
            import matplotlib.pyplot as plt
            import matplotlib.patches as patches
            _plt = plt
            _patches = patches
        except ImportError:
            pass
    return _plt is not None

def generate_w_parameter(captcha_data, coordinates):
    """Generate W parameter"""
    import random
    import urllib.parse
    import binascii
    from Crypto.Cipher import AES
    from Crypto.Util.Padding import pad
    from Crypto.PublicKey.RSA import construct
    from Crypto.Cipher import PKCS1_v1_5
    
    encryptor_pubkey = construct((
        int("00C1E3934D1614465B33053E7F48EE4EC87B14B95EF88947713D25EECBFF7E74C7977D02DC1D9451F79DD5D1C10C29ACB6A9B4D6FB7D0A0279B6719E1772565F09AF627715919221AEF91899CAE08C0D686D748B20A3603BE2318CA6BC2B59706592A9219D0BF05C9F65023A21D2330807252AE0066D59CEEFA5F2748EA80BAB81".lower(), 16),
        int("10001", 16))
    )
    
    def rand_uid():
        result = ''
        for _ in range(4):
            result += hex(int(65536 * (1 + random.random())))[2:].zfill(4)[-4:]
        return result
    
    def encrypt_symmetrical_1(o_text, random_str):
        key = random_str.encode('utf-8')
        iv = b'0000000000000000'
        cipher = AES.new(key, AES.MODE_CBC, iv)
        encrypted_bytes = cipher.encrypt(pad(o_text.encode('utf-8'), AES.block_size))
        return encrypted_bytes
    
    def encrypt_asymmetric_1(message: str) -> str:
        message_bytes = message.encode('utf-8')
        cipher = PKCS1_v1_5.new(encryptor_pubkey)
        encrypted_bytes = cipher.encrypt(message_bytes)
        encrypted_hex = binascii.hexlify(encrypted_bytes).decode('utf-8')
        return encrypted_hex
    
    def encrypt_w(raw_input, pt) -> str:
        if not pt or '0' == pt:
            return urllib.parse.quote_plus(raw_input)
        
        random_uid_val = rand_uid()
        if pt == "1":
            enc_key = encrypt_asymmetric_1(random_uid_val)
            enc_input = encrypt_symmetrical_1(raw_input, random_uid_val)
            return binascii.hexlify(enc_input).decode() + enc_key
        else:
            raise NotImplementedError("Only pt=1 supported")
    
    lot_number = captcha_data['lot_number']
    
    base = {
        "ypbF": "0P3G",
        "pow_msg": f"1|0|md5|2026-01-11T23:48:01|{captcha_data.get('captcha_id', '')}|{lot_number}||{rand_uid()}",
        "pow_sign": "e14b01c7ad40287f5b99fd567785a130",
        "biht": "1426265548",
        "device_id": "",
        "em": {"cp": 0, "ek": "11", "nt": 0, "ph": 0, "sc": 0, "si": 0, "wd": 1},
        "gee_guard": {"roe": {"auh": "3", "aup": "3", "cdc": "3", "egp": "3", "res": "3", "rew": "3", "sep": "3", "snh": "3"}},
        "ep": "123",
        "geetest": "captcha",
        "lang": "zh",
        "lot_number": lot_number,
        "passtime": random.randint(600, 1200),
        "userresponse": coordinates
    }
    
    return encrypt_w(json.dumps(base), captcha_data.get('pt', '1'))

def submit_verify_request(captcha_data, w_param, captcha_id, proxies=None, verbose=False):
    """Submit verify request"""
    import random
    
    verify_url = "https://gcaptcha4.geevisit.com/verify"
    callback = f"geetest_{int(random.random() * 10000) + int(time.time() * 1000)}"
    
    params = {
        "callback": callback,
        "captcha_id": captcha_id,
        "client_type": "web",
        "lot_number": captcha_data['lot_number'],
        "payload": captcha_data['payload'],
        "process_token": captcha_data['process_token'], 
        "payload_protocol": captcha_data['payload_protocol'],
        "pt": captcha_data['pt'],
        "w": w_param
    }
    
    time.sleep(3)
    
    try:
        response = requests.get(verify_url, params=params, timeout=15, proxies=proxies)
        if verbose:
            print(f"📤 Verify response: {response.text[:200]}")
        return response.text
    except Exception as e:
        if verbose:
            print(f"❌ Verify error: {e}")
        return f"Error: {e}"

def load_geetest_captcha(captcha_id, proxies=None, verbose=False):
    """Load captcha"""
    url = f"https://gcaptcha4.geevisit.com/load?captcha_id={captcha_id}&challenge=&client_type=web&risk_type=icon"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.aivora.com/',
        'Origin': 'https://www.aivora.com',
        'Sec-Fetch-Dest': 'script',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'cross-site'
    })
    
    for retry in range(10):
        try:
            time.sleep(3 + retry * 2)
            response = session.get(url, timeout=20, proxies=proxies)
            
            if response.status_code == 403:
                if retry < 9:
                    if verbose:
                        print(f"⚠️  Cloudflare block, waiting {10 + retry * 5}s...")
                    time.sleep(10 + retry * 5)
                    continue
                return None
                
            if response.status_code != 200:
                if retry < 9:
                    if verbose:
                        print(f"⚠️  HTTP {response.status_code}, retry {retry + 1}/10")
                    continue
                return None
            
            text = response.text
            if text.startswith('(') and text.endswith(')'):
                text = text[1:-1]
            
            return json.loads(text)['data']
        except Exception as e:
            if retry < 9:
                if verbose:
                    print(f"⚠️  Error: {str(e)[:50]}, retry {retry + 1}/10")
                continue
            return None

def visualize_detections(grid_image, detections, sequence, attempt_num, target_icons):
    """Show popup with detections, sequence, and target icons"""
    if not _load_matplotlib():
        return
    
    fig, axes = _plt.subplots(2, len(target_icons) + 1, figsize=(15, 10))
    
    # Top row: Target icons in sequence
    for i, target_icon in enumerate(target_icons):
        axes[0, i].imshow(target_icon)
        axes[0, i].set_title(f"Target {i+1}", fontsize=12, weight='bold', color='blue')
        axes[0, i].axis('off')
        # Add border
        for spine in axes[0, i].spines.values():
            spine.set_edgecolor('blue')
            spine.set_linewidth(3)
    
    # Hide extra subplot in top row
    if len(target_icons) < len(axes[0]):
        axes[0, -1].axis('off')
    
    # Bottom row: Grid with detections (span across all columns)
    grid_ax = _plt.subplot2grid((2, len(target_icons) + 1), (1, 0), colspan=len(target_icons) + 1)
    
    grid_ax.imshow(grid_image)
    grid_ax.set_title(f"Attempt {attempt_num}: Detection & Sequence", fontsize=16, weight='bold')
    
    colors = ['red', 'blue', 'green', 'orange', 'purple']
    
    # Show all detections as small circles
    for i, (x, y, method) in enumerate(detections):
        circle = _patches.Circle((x, y), 8, color=colors[i % len(colors)], 
                              fill=False, linewidth=2, alpha=0.7)
        grid_ax.add_patch(circle)
        grid_ax.text(x, y-15, f"{method}", color=colors[i % len(colors)], 
               fontsize=8, weight='bold', ha='center')
    
    # Show final sequence as big numbered circles
    for i, (x, y) in enumerate(sequence):
        img_x = int(x / 33)
        img_y = int(y / 49)
        
        # Big circle for final selection
        circle = _patches.Circle((img_x, img_y), 25, color='yellow', 
                              fill=False, linewidth=6)
        grid_ax.add_patch(circle)
        grid_ax.text(img_x, img_y, str(i+1), color='black', 
               fontsize=24, weight='bold', ha='center', va='center',
               bbox=dict(boxstyle="circle,pad=0.3", facecolor="yellow", alpha=0.8))
        
        if verbose:
            print(f"  Target {i+1}: Image({img_x},{img_y}) -> Scaled({x},{y})")
    
    grid_ax.axis('off')
    _plt.tight_layout()
    _plt.show(block=False)
    
    input(f"Press Enter to submit attempt {attempt_num}...")
    _plt.close()

def hybrid_solve(captcha_data, model, attempt_num=1, interactive=True, verbose=False):
    """Hybrid solver: YOLO + ddddocr + template matching with preprocessing"""
    grid_url = f"https://static.geetest.com/{captcha_data['imgs']}"
    grid_image = Image.open(BytesIO(requests.get(grid_url).content))
    grid_cv = cv2.cvtColor(np.array(grid_image), cv2.COLOR_RGB2BGR)
    
    target_count = len(captcha_data['ques'])
    
    # Skip single icon captchas
    if target_count == 1:
        if verbose:
            if verbose:
                print("⚠️  Single icon captcha detected - skipping")
        return None
    
    if target_count == 1:
        if verbose:
            if verbose:
                print("Single target - using template matching")
        # For single target, use template matching (previous method)
        icon_url = f"https://static.geetest.com/{captcha_data['ques'][0]}"
        target_icon = Image.open(BytesIO(requests.get(icon_url).content))
        target_cv = cv2.cvtColor(np.array(target_icon), cv2.COLOR_RGB2BGR)
        
        matches = []
        grid_h, grid_w = grid_cv.shape[:2]
        target_h, target_w = target_cv.shape[:2]
        
        for scale in [0.5, 0.7, 0.9, 1.1]:
            new_h, new_w = int(target_h * scale), int(target_w * scale)
            if new_h >= grid_h or new_w >= grid_w or new_h <= 5 or new_w <= 5:
                continue
                
            resized_target = cv2.resize(target_cv, (new_w, new_h))
            result = cv2.matchTemplate(grid_cv, resized_target, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= 0.4)
            
            for pt in zip(*locations[::-1]):
                center_x = int(pt[0] + new_w // 2)
                center_y = int(pt[1] + new_h // 2)
                confidence = float(result[pt[1], pt[0]])
                matches.append((center_x, center_y, confidence))
        
        # Remove duplicates
        unique_matches = []
        for match in sorted(matches, key=lambda x: x[2], reverse=True):
            x, y, conf = match
            is_duplicate = False
            for existing in unique_matches:
                if abs(x - existing[0]) < 50 and abs(y - existing[1]) < 50:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_matches.append(match)
        
        # Convert to coordinates
        coords = []
        for x, y, conf in unique_matches[:3]:
            coords.append([int(x * 33), int(y * 49)])
        
        # Pad with grid positions if needed
        grid_positions = [[1650, 1225], [4950, 1225], [8250, 1225]]
        while len(coords) < 3:
            coords.append(grid_positions[len(coords)])
        
        return [coords[:3]]
    
    else:
        if verbose:
            print("Multi-target - using YOLO + ddddocr + template matching")
        
        # Download target icons first
        target_icons_pil = []
        target_icons_cv = []  # Original small icons for template matching
        target_icons_cv_large = []  # Large white bg for YOLO
        
        for i, icon_path in enumerate(captcha_data['ques']):
            icon_url = f"https://static.geetest.com/{icon_path}"
            target_icon = Image.open(BytesIO(requests.get(icon_url).content))
            
            # Store original WITH white background for template matching
            if target_icon.mode == 'RGBA':
                # Create white background for original size
                white_bg_small = Image.new('RGB', target_icon.size, (255, 255, 255))
                white_bg_small.paste(target_icon, mask=target_icon.split()[3])
                target_cv_original = cv2.cvtColor(np.array(white_bg_small), cv2.COLOR_RGB2BGR)
            else:
                target_cv_original = cv2.cvtColor(np.array(target_icon.convert('RGB')), cv2.COLOR_RGB2BGR)
            
            target_icons_cv.append(target_cv_original)
            
            # Convert transparent background to white and enlarge for YOLO
            if target_icon.mode == 'RGBA':
                # Create larger white background (3x size)
                new_size = (target_icon.size[0] * 3, target_icon.size[1] * 3)
                white_bg = Image.new('RGB', new_size, (255, 255, 255))
                # Paste icon in center
                offset = ((new_size[0] - target_icon.size[0]) // 2, (new_size[1] - target_icon.size[1]) // 2)
                white_bg.paste(target_icon, offset, mask=target_icon.split()[3])  # Use alpha as mask
                target_icon_rgb = white_bg
            else:
                # Enlarge non-transparent images too
                new_size = (target_icon.size[0] * 3, target_icon.size[1] * 3)
                white_bg = Image.new('RGB', new_size, (255, 255, 255))
                offset = ((new_size[0] - target_icon.size[0]) // 2, (new_size[1] - target_icon.size[1]) // 2)
                white_bg.paste(target_icon.convert('RGB'), offset)
                target_icon_rgb = white_bg
            
            target_icons_pil.append(target_icon_rgb)
            target_cv_large = cv2.cvtColor(np.array(target_icon_rgb), cv2.COLOR_RGB2BGR)
            target_icons_cv_large.append(target_cv_large)
        
        # Step 1: Run YOLO on grid image to find 'icon' class
        if verbose:
            print("Step 1: YOLO detection on grid image (class: icon)")
        grid_results = model(grid_image)
        grid_yolo_detections = []
        
        if grid_results[0].boxes is not None:
            for box in grid_results[0].boxes:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                center = [int((x1 + x2) / 2), int((y1 + y2) / 2)]
                conf = float(box.conf[0].cpu().numpy())
                cls = int(box.cls[0].cpu().numpy())
                cls_name = grid_results[0].names[cls]
                
                # Only accept 'icon' class with high confidence
                if cls_name == 'icon' and conf >= 0.7:
                    grid_yolo_detections.append((center[0], center[1], conf))
                    if verbose:
                        print(f"  Found icon at ({center[0]}, {center[1]}) conf={conf:.2f}")
        
        if verbose:
            print(f"YOLO found {len(grid_yolo_detections)} 'icon' objects in grid")
        
        # Step 2: Check which target icons YOLO recognizes (tip class)
        if verbose:
            print("\nStep 2: Checking which target icons YOLO recognizes (class: tip)")
        yolo_recognized_targets = []  # List of target indices YOLO recognizes
        
        for target_idx, target_icon in enumerate(target_icons_pil):
            icon_results = model(target_icon)
            
            if icon_results[0].boxes is not None and len(icon_results[0].boxes) > 0:
                icon_conf = float(icon_results[0].boxes[0].conf[0].cpu().numpy())
                cls = int(icon_results[0].boxes[0].cls[0].cpu().numpy())
                cls_name = icon_results[0].names[cls]
                
                # Only accept 'tip' class
                if cls_name == 'tip' and icon_conf >= 0.5:
                    yolo_recognized_targets.append(target_idx)
                    if verbose:
                        print(f"  Target {target_idx+1}: YOLO detected 'tip' (conf={icon_conf:.2f})")
                else:
                    if verbose:
                        print(f"  Target {target_idx+1}: class={cls_name}, conf={icon_conf:.2f}")
            else:
                if verbose:
                    print(f"  Target {target_idx+1}: Not detected")
        
        if verbose:
            print(f"\nYOLO recognized {len(yolo_recognized_targets)} targets: {[i+1 for i in yolo_recognized_targets]}")
        
        # Step 3: Use template matching to match targets to grid detections
        if verbose:
            print("\nStep 3: Template matching to determine sequence")
        
        from scipy import ndimage
        
        def preprocess_image(img_gray, invert=False):
            """Enhance image features for better matching"""
            # Invert if needed (for targets with black icons)
            if invert:
                img_gray = 255 - img_gray
            
            # 1. Histogram equalization to normalize brightness
            img_eq = cv2.equalizeHist(img_gray)
            
            # 2. Denoise with bilateral filter (preserves edges)
            img_denoised = cv2.bilateralFilter(img_eq, 9, 75, 75)
            
            # 3. Sharpen to enhance edges
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]])
            img_sharp = cv2.filter2D(img_denoised, -1, kernel)
            
            return img_sharp
        
        def feature_match_score(target_cv, grid_cv, grid_x, grid_y, box_size=60, visualize=False):
            """SSIM-based matching with preprocessing"""
            from skimage.metrics import structural_similarity as ssim
            
            # Extract region from grid
            half_box = box_size // 2
            y1 = max(0, grid_y - half_box)
            y2 = min(grid_cv.shape[0], grid_y + half_box)
            x1 = max(0, grid_x - half_box)
            x2 = min(grid_cv.shape[1], grid_x + half_box)
            
            region = grid_cv[y1:y2, x1:x2]
            if region.size == 0:
                return 0.0
            
            # Convert to grayscale
            region_gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
            target_gray = cv2.cvtColor(target_cv, cv2.COLOR_BGR2GRAY)
            
            # Preprocess both images (invert target to match grid)
            region_proc = preprocess_image(region_gray, invert=False)
            target_proc = preprocess_image(target_gray, invert=True)  # Invert target
            
            # Resize target to match region
            target_resized = cv2.resize(target_proc, (region_proc.shape[1], region_proc.shape[0]))
            
            # Try multiple rotations and pick best SSIM
            best_score = 0
            for angle in range(0, 360, 30):
                rotated = ndimage.rotate(target_resized, angle, reshape=False)
                try:
                    score = ssim(region_proc, rotated)
                    best_score = max(best_score, score)
                except:
                    pass
            
            return best_score
        
        # Match each target to best grid detection with collision resolution
        final_sequence = [None] * target_count
        match_scores = []
        
        # Create visualization figure
        if _load_matplotlib():
            fig, axes = _plt.subplots(target_count, len(grid_yolo_detections) + 1, figsize=(15, target_count * 3))
            if target_count == 1:
                axes = axes.reshape(1, -1)
        else:
            fig = None
            axes = None
        
        # First pass: collect all scores
        all_scores = []  # (target_idx, det_idx, score)
        
        for target_idx in range(target_count):
            target_cv = target_icons_cv[target_idx]
            target_gray = cv2.cvtColor(target_cv, cv2.COLOR_BGR2GRAY)
            
            if _plt is not None and axes is not None:
                axes[target_idx, 0].imshow(target_gray, cmap='gray')
                axes[target_idx, 0].set_title(f'Target {target_idx+1}', fontsize=14, weight='bold')
                axes[target_idx, 0].axis('off')
            
            for det_idx, (grid_x, grid_y, conf) in enumerate(grid_yolo_detections):
                score = feature_match_score(target_cv, grid_cv, grid_x, grid_y)
                all_scores.append((target_idx, det_idx, score))
                
                half_box = 30
                y1 = max(0, grid_y - half_box)
                y2 = min(grid_cv.shape[0], grid_y + half_box)
                x1 = max(0, grid_x - half_box)
                x2 = min(grid_cv.shape[1], grid_x + half_box)
                region = grid_cv[y1:y2, x1:x2]
                region_gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
                
                if _plt is not None and axes is not None:
                    axes[target_idx, det_idx + 1].imshow(region_gray, cmap='gray')
                    axes[target_idx, det_idx + 1].set_title(f'Det {det_idx}\nSSIM={score:.3f}', fontsize=10)
                    axes[target_idx, det_idx + 1].axis('off')
                
                if verbose:
                    print(f"  Target {target_idx+1} vs Detection {det_idx}: score={score:.3f}")
        
        # Second pass: assign by highest score
        all_scores.sort(key=lambda x: x[2], reverse=True)
        used_detections = set()
        assigned_targets = set()
        
        for target_idx, det_idx, score in all_scores:
            if target_idx not in assigned_targets and det_idx not in used_detections:
                grid_x, grid_y, conf = grid_yolo_detections[det_idx]
                scaled_coords = [int(grid_x * 33), int(grid_y * 49)]
                final_sequence[target_idx] = scaled_coords
                match_scores.append((target_idx, score))
                used_detections.add(det_idx)
                assigned_targets.add(target_idx)
                if verbose:
                    print(f"  ✓ Target {target_idx+1}: matched detection {det_idx} score={score:.3f}")
        
        # Assign remaining
        for target_idx in range(target_count):
            if final_sequence[target_idx] is None:
                for det_idx in range(len(grid_yolo_detections)):
                    if det_idx not in used_detections:
                        grid_x, grid_y, conf = grid_yolo_detections[det_idx]
                        scaled_coords = [int(grid_x * 33), int(grid_y * 49)]
                        final_sequence[target_idx] = scaled_coords
                        match_scores.append((target_idx, 0.0))
                        used_detections.add(det_idx)
                        if verbose:
                            print(f"  → Target {target_idx+1}: assigned remaining detection {det_idx}")
                        break
        
        if _plt: _plt.tight_layout()
        if interactive and _load_matplotlib():
            _plt.show(block=False)
            input("Press Enter to continue...")
        if _plt:
            _plt.close()
        
        # Combine all detections for visualization
        all_detections = [(x, y, f"YOLO:{c:.2f}") for x, y, c in grid_yolo_detections]
        
        # Show visualization
        if interactive:
            visualize_detections(grid_image, all_detections, final_sequence, attempt_num, target_icons_pil)
        
        # Generate 2 coordinate sets: original + swap lowest 2 scores
        coord_set_1 = final_sequence.copy()
        coord_set_2 = final_sequence.copy()
        
        # Sort by score and swap the 2 lowest scoring matches
        if len(match_scores) >= 2:
            sorted_scores = sorted(match_scores, key=lambda x: x[1])
            idx1, score1 = sorted_scores[0]
            idx2, score2 = sorted_scores[1]
            coord_set_2[idx1], coord_set_2[idx2] = coord_set_2[idx2], coord_set_2[idx1]
            if verbose:
                print(f"\nAttempt 2 will swap targets {idx1+1} (score={score1:.3f}) and {idx2+1} (score={score2:.3f})")
        
        return [coord_set_1, coord_set_2]

if __name__ == "__main__":
    captcha_id = "YOUR_CAPTCHA_ID_HERE"
    
    # Load YOLO model
    try:
        model = YOLO('best.pt')
        if verbose:
            print("YOLO model loaded")
    except:
        if verbose:
            print("YOLO model not found, using fallback")
        model = None
    
    try:
        if verbose:
            print("Loading captcha...")
        captcha_data = load_geetest_captcha(captcha_id)
        if verbose:
            print(f"Loaded: {captcha_data['captcha_type']} with {len(captcha_data['ques'])} targets")
        
        # Skip single icon captchas
        while len(captcha_data['ques']) == 1:
            if verbose:
                print("⚠️  Single icon captcha - reloading...")
            time.sleep(2)
            captcha_data = load_geetest_captcha(captcha_id)
            if verbose:
                print(f"Loaded: {captcha_data['captcha_type']} with {len(captcha_data['ques'])} targets")
        
        # Single attempt only
        coordinates_list = hybrid_solve(captcha_data, model, attempt_num=1, interactive=True)
        
        if coordinates_list is None:
            if verbose:
                print("Captcha was skipped")
            exit(1)
        
        # Try up to 2 attempts
        for attempt in range(1, 3):
            if attempt == 1:
                coordinates = coordinates_list[0]
            else:
                if verbose:
                    print("\n" + "="*60)
                if verbose:
                    print("ATTEMPT 2: Swapping lowest scoring targets")
                if verbose:
                    print("="*60)
                coordinates = coordinates_list[1] if len(coordinates_list) > 1 else coordinates_list[0]
            
            if verbose:
                print(f"\n{'='*60}")
            if verbose:
                print(f"FINAL COORDINATES: {coordinates}")
            if verbose:
                print(f"{'='*60}\n")
            
            w_param = generate_w_parameter(captcha_data, coordinates)
            verify_response = submit_verify_request(captcha_data, w_param, captcha_id)
            
            if verify_response.startswith('geetest_'):
                json_start = verify_response.find('(') + 1
                json_end = verify_response.rfind(')')
                json_data = json.loads(verify_response[json_start:json_end])
                
                result = json_data['data']['result']
                fail_count = json_data['data'].get('fail_count', 'unknown')
                if verbose:
                    print(f"Result: {result} (fail_count: {fail_count})")
                
                if result == 'success':
                    if verbose:
                        print("✅ SUCCESS!")
                    if 'seccode' in json_data['data']:
                        seccode = json_data['data']['seccode']
                        if verbose:
                            print(f"\n🎉 SECCODE: {seccode}")
                    break
                else:
                    if verbose:
                        print("❌ Failed, trying next attempt...")
            else:
                if verbose:
                    print(f"Unexpected response: {verify_response[:100]}...")
        
    except Exception as e:
        if verbose:
            print(f"Error: {e}")