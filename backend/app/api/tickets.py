from fastapi import APIRouter

from app.core.config import get_database_path
from app.db.database import list_ticket_records

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("")
def list_tickets() -> dict[str, list[dict[str, int | str]]]:
    return {"tickets": list_ticket_records(get_database_path())}
