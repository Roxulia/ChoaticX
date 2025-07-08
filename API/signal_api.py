from fastapi import APIRouter

router = APIRouter()

@router.get("/zones")
def get_zones():
    pass

@router.get("/signals")
def get_signals():
    pass
