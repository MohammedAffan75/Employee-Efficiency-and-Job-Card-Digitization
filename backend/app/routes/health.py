from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Status of the API
    """
    return {"status": "ok"}
