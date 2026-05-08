from .uploads import router as uploads_router
from .dashboard import router as dashboard_router
from .governance import router as governance_router
from .exports import router as exports_router
from .mail_photos import router as mail_photos_router

all_routers = [
    uploads_router,
    dashboard_router,
    governance_router,
    exports_router,
    mail_photos_router,
]
