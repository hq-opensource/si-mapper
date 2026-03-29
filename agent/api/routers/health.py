"""Health-check routes: GET /, HEAD /, GET /health."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
@router.head("/")
async def root():
    return {"status": "ok", "agent": "si_mapper_agent"}


@router.get("/health")
async def health():
    return {"status": "ok"}

