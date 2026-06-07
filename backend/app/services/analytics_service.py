from datetime import date, timedelta
from statistics import mean

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models import Department, Forecast, Incident, Operation, Project, Risk, Task, Workflow


def _window(db: Session, days: int):
    start = date.today() - timedelta(days=days)
    return db.query(Operation).filter(Operation.recorded_on >= start)


def _sum(query, column):
    return float(query.with_entities(func.coalesce(func.sum(column), 0)).scalar() or 0)


def _avg(query, column):
    return float(query.with_entities(func.coalesce(func.avg(column), 0)).scalar() or 0)


def dashboard(db: Session) -> dict:
    current = _window(db, 30)
    previous = db.query(Operation).filter(
        Operation.recorded_on >= date.today() - timedelta(days=60),
        Operation.recorded_on < date.today() - timedelta(days=30),
    )
    revenue = _sum(current, Operation.revenue)
    prev_revenue = _sum(previous, Operation.revenue) or 1
    costs = _sum(current, Operation.cost)
    prev_costs = _sum(previous, Operation.cost) or 1
    orders = _sum(current, Operation.orders)
    incidents = db.query(Incident).filter(Incident.created_at >= date.today() - timedelta(days=30)).count()
    projects = db.query(Project).filter(Project.status != "Completed").count()
    workflows = db.query(Workflow).filter(Workflow.status != "Completed").count()
    efficiency = ((revenue - costs) / revenue * 100) if revenue else 0
    productivity = _avg(current, Operation.productivity)
    satisfaction = _avg(current, Operation.customer_satisfaction)
    risk_score = float(db.query(func.coalesce(func.avg(Risk.score), 0)).scalar() or 0)

    trend_rows = (
        db.query(Operation.recorded_on, func.sum(Operation.revenue), func.sum(Operation.cost), func.avg(Operation.productivity))
        .filter(Operation.recorded_on >= date.today() - timedelta(days=180))
        .group_by(Operation.recorded_on)
        .order_by(Operation.recorded_on)
        .all()
    )
    trend = [
        {"date": row[0].isoformat(), "revenue": round(row[1] or 0, 2), "cost": round(row[2] or 0, 2), "productivity": round(row[3] or 0, 2)}
        for row in trend_rows[:: max(1, len(trend_rows) // 24 or 1)]
    ]

    dept_rows = (
        db.query(Department.name, func.sum(Operation.revenue), func.sum(Operation.cost), func.avg(Operation.productivity), func.avg(Operation.customer_satisfaction))
        .join(Operation, Operation.department_id == Department.id)
        .filter(Operation.recorded_on >= date.today() - timedelta(days=30))
        .group_by(Department.name)
        .all()
    )
    departments = [
        {"name": r[0], "revenue": round(r[1] or 0, 2), "cost": round(r[2] or 0, 2), "productivity": round(r[3] or 0, 2), "satisfaction": round(r[4] or 0, 2)}
        for r in dept_rows
    ]

    risks = [
        {"category": r.category, "score": r.score, "reason": r.reason}
        for r in db.query(Risk).order_by(Risk.score.desc()).limit(6)
    ]

    return {
        "kpis": [
            {"key": "revenue", "label": "Revenue", "value": round(revenue, 2), "unit": "USD", "delta": round((revenue - prev_revenue) / prev_revenue * 100, 1)},
            {"key": "costs", "label": "Costs", "value": round(costs, 2), "unit": "USD", "delta": round((costs - prev_costs) / prev_costs * 100, 1)},
            {"key": "orders", "label": "Orders", "value": orders, "unit": "orders", "delta": 0},
            {"key": "incidents", "label": "Incidents", "value": incidents, "unit": "open/closed", "delta": 0},
            {"key": "projects", "label": "Projects", "value": projects, "unit": "active", "delta": 0},
            {"key": "workflows", "label": "Workflows", "value": workflows, "unit": "active", "delta": 0},
            {"key": "efficiency", "label": "Efficiency", "value": round(efficiency, 1), "unit": "%", "delta": 0},
            {"key": "productivity", "label": "Productivity", "value": round(productivity, 1), "unit": "%", "delta": 0},
            {"key": "satisfaction", "label": "Customer Satisfaction", "value": round(satisfaction, 1), "unit": "/100", "delta": 0},
            {"key": "risk", "label": "Risk Score", "value": round(risk_score, 1), "unit": "/100", "delta": 0},
        ],
        "trend": trend,
        "risks": risks,
        "departments": departments,
    }


def operations_center(db: Session) -> dict:
    open_incidents = db.query(Incident).filter(Incident.status != "Resolved").order_by(Incident.created_at.desc()).limit(12).all()
    projects = db.query(Project).order_by(Project.due_date).limit(10).all()
    capacity_rows = (
        db.query(Department.name, func.avg(Operation.workload), func.avg(Operation.productivity))
        .join(Operation, Operation.department_id == Department.id)
        .filter(Operation.recorded_on >= date.today() - timedelta(days=14))
        .group_by(Department.name)
        .all()
    )
    total_incidents = db.query(Incident).count() or 1
    breached = db.query(Incident).filter(Incident.resolved_at != None, Incident.resolved_at > Incident.sla_due_at).count()
    blockers = db.query(Task).filter(Task.status.in_(["Blocked", "Delayed"])).order_by(Task.due_date).limit(10).all()
    return {
        "active_operations": db.query(Operation).filter(Operation.status == "Active").count(),
        "projects": [{"name": p.name, "status": p.status, "budget": p.budget, "spent": p.spent, "due_date": p.due_date.isoformat()} for p in projects],
        "incidents": [{"title": i.title, "severity": i.severity, "status": i.status, "sla_due_at": i.sla_due_at.isoformat()} for i in open_incidents],
        "capacity": [{"department": r[0], "workload": round(r[1] or 0, 1), "productivity": round(r[2] or 0, 1)} for r in capacity_rows],
        "sla": {"target": 95, "attainment": round((1 - breached / total_incidents) * 100, 1), "breached": breached},
        "blockers": [{"title": t.title, "status": t.status, "due_date": t.due_date.isoformat(), "variance_hours": round(t.actual_hours - t.estimated_hours, 1)} for t in blockers],
    }


def workflows(db: Session) -> list[dict]:
    return [
        {
            "id": item.id,
            "name": item.name,
            "status": item.status,
            "duration_hours": item.duration_hours,
            "owner_id": item.owner_id,
            "average_time_hours": item.average_time_hours,
            "delay_hours": item.delay_hours,
            "risk_score": item.risk_score,
        }
        for item in db.query(Workflow).order_by(Workflow.risk_score.desc()).limit(100)
    ]


def forecasts(db: Session) -> list[dict]:
    items = db.query(Forecast).order_by(Forecast.forecast_for, Forecast.metric).all()
    return [
        {
            "metric": item.metric,
            "department_id": item.department_id,
            "prediction": item.prediction,
            "confidence": item.confidence,
            "explanation": item.explanation,
            "forecast_for": item.forecast_for.isoformat(),
        }
        for item in items
    ]


def department_analytics(db: Session) -> list[dict]:
    rows = (
        db.query(Department.id, Department.name, Department.budget, func.sum(Operation.revenue), func.sum(Operation.cost), func.avg(Operation.productivity), func.count(Incident.id))
        .join(Operation, Operation.department_id == Department.id)
        .outerjoin(Incident, Incident.department_id == Department.id)
        .filter(Operation.recorded_on >= date.today() - timedelta(days=30))
        .group_by(Department.id, Department.name, Department.budget)
        .all()
    )
    return [
        {
            "id": r[0],
            "name": r[1],
            "budget": r[2],
            "revenue": round(r[3] or 0, 2),
            "cost": round(r[4] or 0, 2),
            "productivity": round(r[5] or 0, 1),
            "incidents": r[6],
            "risk": round(mean([risk.score for risk in db.query(Risk).filter(Risk.department_id == r[0]).all()] or [0]), 1),
        }
        for r in rows
    ]
