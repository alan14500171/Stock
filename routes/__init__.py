"""
路由包
包含所有路由蓝图
"""

from .auth import auth_bp
from .stock import stock_bp
from .profit import profit_bp

__all__ = ['auth_bp', 'stock_bp', 'profit_bp'] 