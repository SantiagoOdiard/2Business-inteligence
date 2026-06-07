from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.dependencies import require_permission
from app.data.schemas import AIChatConversation, AIChatRequest, AIChatResponse, DashboardResponse, ExportResponse, OperationCenterResponse, ReportCreate
from app.data.seed import seed
from app.domain.models import AIInsight, AIMessage, AuditLog, Report, User
from app.infrastructure.database import get_db
from app.services import ai_service, analytics_service
from app.services.audit_service import audit

router = APIRouter(tags=["Enterprise Operations"])


@router.post("/admin/seed")
def seed_database(db: Session = Depends(get_db), _: User = Depends(require_permission("admin:*"))):
    return seed(db, force=True)


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(db: Session = Depends(get_db), _: User = Depends(require_permission("dashboard:read"))):
    return analytics_service.dashboard(db)


@router.get("/operations-center", response_model=OperationCenterResponse)
def operations_center(db: Session = Depends(get_db), _: User = Depends(require_permission("operations:read"))):
    return analytics_service.operations_center(db)


@router.get("/workflows")
def workflows(db: Session = Depends(get_db), _: User = Depends(require_permission("workflows:read"))):
    return analytics_service.workflows(db)


@router.get("/risks")
def risks(db: Session = Depends(get_db), _: User = Depends(require_permission("risks:read"))):
    return analytics_service.dashboard(db)["risks"]


@router.get("/forecasts")
def forecasts(db: Session = Depends(get_db), _: User = Depends(require_permission("analytics:read"))):
    return analytics_service.forecasts(db)


@router.get("/analytics/departments")
def departments(db: Session = Depends(get_db), _: User = Depends(require_permission("analytics:read"))):
    return analytics_service.department_analytics(db)


@router.get("/ai-insights")
def insights(db: Session = Depends(get_db), _: User = Depends(require_permission("analytics:read"))):
    return [
        {
            "title": item.title,
            "reason": item.reason,
            "impact": item.impact,
            "priority": item.priority,
            "suggested_action": item.suggested_action,
            "confidence": item.confidence,
        }
        for item in db.query(AIInsight).order_by(AIInsight.confidence.desc()).all()
    ]


def _message_payload(message: AIMessage) -> dict:
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "reasoning": message.reasoning,
        "confidence": message.confidence,
        "created_at": message.created_at,
    }


@router.get("/ai-chat/conversations", response_model=list[AIChatConversation])
def ai_chat_conversations(db: Session = Depends(get_db), user: User = Depends(require_permission("analytics:read"))):
    return [
        {
            "id": item.id,
            "title": item.title,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
            "messages": [],
        }
        for item in ai_service.conversation_list(db, user)
    ]


@router.get("/ai-chat/conversations/{conversation_id}", response_model=AIChatConversation)
def ai_chat_conversation(conversation_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission("analytics:read"))):
    conversation = ai_service.conversation_detail(db, user, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": conversation.id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": [_message_payload(item) for item in ai_service.messages_for(db, conversation.id, limit=80)],
    }


@router.post("/ai-chat", response_model=AIChatResponse)
def ai_chat(payload: AIChatRequest, db: Session = Depends(get_db), user: User = Depends(require_permission("analytics:read"))):
    conversation, answer, context = ai_service.chat(db, user, payload.message, payload.conversation_id)
    return {
        "conversation_id": conversation.id,
        "answer": _message_payload(answer),
        "context": {
            "kpis": len(context["kpis"]),
            "risks": len(context["top_risks"]),
            "departments": len(context["departments"]),
            "forecasts": len(context["forecasts"]),
        },
    }


@router.post("/reports")
def create_report(payload: ReportCreate, db: Session = Depends(get_db), _: User = Depends(require_permission("reports:read"))):
    snapshot = analytics_service.dashboard(db)
    summary = f"{payload.period} report generated from {len(snapshot['trend'])} trend points and {len(snapshot['departments'])} departments."
    report = Report(period=payload.period, title=payload.title, summary=summary)
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "period": report.period, "title": report.title, "summary": report.summary, "created_at": report.created_at}


@router.get("/reports")
def reports(db: Session = Depends(get_db), _: User = Depends(require_permission("reports:read"))):
    return [
        {"id": r.id, "period": r.period, "title": r.title, "summary": r.summary, "created_at": r.created_at.isoformat()}
        for r in db.query(Report).order_by(Report.created_at.desc()).limit(30)
    ]


@router.get("/reports/export/{format}", response_model=ExportResponse)
def export_report(format: str, request: Request, db: Session = Depends(get_db), user: User = Depends(require_permission("reports:export"))):
    audit(db, "Export", "Success", request.client.host if request.client else "unknown", f"Executive report exported as {format}", user.id)
    content_types = {"pdf": "application/pdf", "excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "csv": "text/csv"}
    return ExportResponse(filename=f"executive-report.{format}", content_type=content_types.get(format, "application/octet-stream"), generated_at=datetime.utcnow())


@router.get("/audit-logs")
def audit_logs(db: Session = Depends(get_db), _: User = Depends(require_permission("admin:*"))):
    return [
        {"action": a.action, "result": a.result, "ip_address": a.ip_address, "detail": a.detail, "created_at": a.created_at.isoformat()}
        for a in db.query(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)
    ]
