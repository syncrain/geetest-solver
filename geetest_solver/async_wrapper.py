"""Async wrapper for geetest_solver"""
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import partial

_executor = ThreadPoolExecutor(max_workers=4)

async def solve_captcha_async(captcha_id=None, captcha_type="icon", max_attempts=999, 
                               interactive=False, proxies=None, verbose=False, model=None):
    """Async wrapper for solve_captcha that runs in thread pool
    
    Args:
        model: Pre-loaded YOLO model (optional, for reuse across multiple solves)
    """
    from geetest_solver.solver import solve_captcha
    
    loop = asyncio.get_event_loop()
    func = partial(
        solve_captcha,
        captcha_id=captcha_id,
        captcha_type=captcha_type,
        max_attempts=max_attempts,
        interactive=interactive,
        proxies=proxies,
        verbose=verbose,
        model=model
    )
    
    result = await loop.run_in_executor(_executor, func)
    return result
