from fastapi import APIRouter
from app.routes import (
    auth,
    employees,
    health,
    activity_codes,
    machines,
    work_orders,
    job_cards,
    splits,
    efficiency,
    supervisor,
    reporting,
    import_routes,
    admin,
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(employees.router, prefix="/employees", tags=["employees"])
api_router.include_router(activity_codes.router, prefix="/activity-codes", tags=["activity-codes"])
api_router.include_router(machines.router, prefix="/machines", tags=["machines"])
api_router.include_router(work_orders.router, prefix="/work-orders", tags=["work-orders"])
api_router.include_router(job_cards.router, prefix="/jobcards", tags=["job-cards"])
api_router.include_router(splits.router, prefix="/splits", tags=["splits"])
api_router.include_router(efficiency.router, prefix="/efficiency", tags=["efficiency"])
api_router.include_router(supervisor.router, prefix="/supervisor", tags=["supervisor"])
api_router.include_router(reporting.router, prefix="/reporting", tags=["reporting"])
api_router.include_router(import_routes.router, prefix="/import", tags=["import"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
