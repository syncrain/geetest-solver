#!/usr/bin/env python3
import hashlib
import random

def iconcrush_solve_all(captcha_data, verbose=False):
    """Find all possible solutions for iconCrush captcha"""
    grid = captcha_data['ques']
    rows = len(grid)
    cols = len(grid[0])
    solutions = []
    
    for r1 in range(rows):
        for c1 in range(cols):
            adjacent = []
            if c1 + 1 < cols:
                adjacent.append((r1, c1 + 1))
            if r1 + 1 < rows:
                adjacent.append((r1 + 1, c1))
            
            for r2, c2 in adjacent:
                test_grid = [row[:] for row in grid]
                test_grid[r1][c1], test_grid[r2][c2] = test_grid[r2][c2], test_grid[r1][c1]
                
                for emoji in range(0, 4):
                    if has_three_in_row(test_grid, emoji):
                        sol = [[r1, c1], [r2, c2]]
                        if sol not in solutions:
                            solutions.append(sol)
    
    return solutions

def has_three_in_row(grid, emoji):
    """Check if grid has 3 of the same emoji in a row"""
    rows = len(grid)
    cols = len(grid[0])
    
    for r in range(rows):
        for c in range(cols - 2):
            if grid[r][c] == emoji and grid[r][c+1] == emoji and grid[r][c+2] == emoji:
                return True
    
    for r in range(rows - 2):
        for c in range(cols):
            if grid[r][c] == emoji and grid[r+1][c] == emoji and grid[r+2][c] == emoji:
                return True
    
    return False

def solve_pow(captcha_id, lot_number, pow_detail):
    """Solve PoW challenge"""
    for attempt in range(100000):
        nonce = ''.join(random.choices('0123456789abcdef', k=16))
        pow_msg = f"{pow_detail['version']}|{pow_detail['bits']}|{pow_detail['hashfunc']}|{pow_detail['datetime']}|{captcha_id}|{lot_number}||{nonce}"
        pow_sign = hashlib.sha256(pow_msg.encode()).hexdigest()
        required_zeros = pow_detail['bits'] // 4
        if pow_sign.startswith('0' * required_zeros):
            return pow_msg, pow_sign
    return pow_msg, pow_sign

def generate_w_parameter_iconcrush(captcha_data, coordinates):
    """Generate W parameter for iconcrush"""
    import json
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
        return '0f762c0358af2d8e'
    
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
    captcha_id = captcha_data.get('captcha_id', '')
    pow_detail = captcha_data.get('pow_detail', {})
    
    pow_msg, pow_sign = solve_pow(captcha_id, lot_number, pow_detail) if pow_detail else (None, None)
    
    key_top = lot_number[5] + lot_number[6] + lot_number[7] + lot_number[4] + lot_number[5] + lot_number[6]
    key_mid = lot_number[22] + lot_number[23] + lot_number[5] + lot_number[6]
    key_inner = lot_number[11] + lot_number[12] + lot_number[13] + lot_number[14] + lot_number[15] + lot_number[16] + lot_number[17] + lot_number[18]
    val_inner = lot_number[18] + lot_number[19] + lot_number[20] + lot_number[21] + lot_number[22] + lot_number[23] + lot_number[24] + lot_number[25]
    
    base = {
        key_top: {key_mid: {key_inner: val_inner}},
        "passtime": random.randint(500, 900),
        "userresponse": coordinates,
        "device_id": "",
        "lot_number": lot_number,
        "pow_msg": pow_msg,
        "pow_sign": pow_sign,
        "geetest": "captcha",
        "lang": "zh",
        "ep": "123",
        "biht": "1426265548",
        "gee_guard": {"roe": {"aup": "3", "sep": "3", "egp": "3", "auh": "3", "rew": "3", "snh": "3", "res": "3", "cdc": "3"}},
        "ypbF": "0P3G",
        "em": {"ph": 0, "cp": 0, "ek": "11", "wd": 1, "nt": 0, "si": 0, "sc": 0}
    }
    
    return encrypt_w(json.dumps(base, separators=(',', ':')), captcha_data.get('pt', '1'))
