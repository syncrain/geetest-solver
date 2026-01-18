from .solver import solve_captcha
from .hybrid_solver import load_geetest_captcha, generate_w_parameter, submit_verify_request
from .iconcrush_solver import iconcrush_solve_all, generate_w_parameter_iconcrush

__version__ = "1.0.0"
__all__ = ["solve_captcha", "load_geetest_captcha", "generate_w_parameter", "submit_verify_request", "iconcrush_solve_all", "generate_w_parameter_iconcrush"]
