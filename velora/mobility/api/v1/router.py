"""API v1 router."""
from fastapi import APIRouter

from mobility.api.v1 import auth, bookings, dispatch, flights, ops, payments, pricing

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(pricing.router)
api_router.include_router(bookings.router)
api_router.include_router(dispatch.router)
api_router.include_router(payments.router)
api_router.include_router(flights.router)
api_router.include_router(ops.router)
