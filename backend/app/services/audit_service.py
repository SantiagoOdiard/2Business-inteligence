from sqlalchemy.orm import Session

from app.domain.models import AuditLog


def audit(db: Session, action: str, result: str, ip_address: str, detail: str, user_id: int | None = None) -> None:
    db.add(AuditLog(action=action, result=result, ip_address=ip_address, detail=detail, user_id=user_id))
    db.commit()
