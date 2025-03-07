"""
路由包
包含所有路由蓝图
"""

from .auth import auth_bp
from .stock import stock_bp
from .profit import profit_bp

__all__ = ['auth_bp', 'stock_bp', 'profit_bp']

#!/usr/bin/env python
# -*- coding: utf-8 -*-

def register_routes(app):
    from .auth import register_routes as register_auth_routes
    from .user import register_routes as register_user_routes
    from .role import register_routes as register_role_routes
    from .permission import register_routes as register_permission_routes
    from .stock import register_routes as register_stock_routes
    from .profit import register_routes as register_profit_routes
    from .transaction_split import register_routes as register_transaction_split_routes
    from .holder import register_routes as register_holder_routes
    
    register_auth_routes(app)
    register_user_routes(app)
    register_role_routes(app)
    register_permission_routes(app)
    register_stock_routes(app)
    register_profit_routes(app)
    register_transaction_split_routes(app)
    register_holder_routes(app) 