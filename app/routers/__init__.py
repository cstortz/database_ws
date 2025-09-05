"""
Routers package for the database service.

This package contains all the router classes for different API endpoints:
- AdminRouter: Database service management endpoints
- RawRouter: Raw SQL execution endpoints  
- CrudRouter: CRUD operations endpoints
- PreparedRouter: Advanced prepared SQL operations endpoints
"""

from .admin_router import admin_router
from .raw_router import raw_router
from .crud_router import crud_router
from .prepared_router import prepared_router

__all__ = [
    'admin_router',
    'raw_router', 
    'crud_router',
    'prepared_router'
]
