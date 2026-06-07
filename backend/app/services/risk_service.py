from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.domain.models import Department, Forecast, Incident, Operation, Project, Risk


RISK_CATEGORIES = ["SLA Risk", "Budget Risk", "Resource Risk", "Operational Risk", "Performance Risk", "Delivery Risk"]


def recalculate_risks(db: Session) -> None:
    db.query(Risk).delete()
    departments = db.query(Department).all()
    for dept in departments:
        incidents = db.query(Incident).filter(Incident.department_id == dept.id, Incident.status != "Resolved").count()
        workload = db.query(func.coalesce(func.avg(Operation.workload), 0)).filter(Operation.department_id == dept.id, Operation.recorded_on >= date.today() - timedelta(days=30)).scalar()
        productivity = db.query(func.coalesce(func.avg(Operation.productivity), 0)).filter(Operation.department_id == dept.id, Operation.recorded_on >= date.today() - timedelta(days=30)).scalar()
        budget_rows = db.query(Project).filter(Project.department_id == dept.id).all()
        budget_pressure = max([p.spent / p.budget * 100 for p in budget_rows if p.budget] or [0])
        delivery_pressure = len([p for p in budget_rows if p.due_date < date.today() + timedelta(days=21) and p.status != "Completed"]) * 12
        scores = {
            "SLA Risk": min(100, incidents * 7),
            "Budget Risk": min(100, budget_pressure),
            "Resource Risk": min(100, float(workload or 0)),
            "Operational Risk": min(100, incidents * 4 + float(workload or 0) * 0.4),
            "Performance Risk": min(100, 100 - float(productivity or 0)),
            "Delivery Risk": min(100, delivery_pressure),
        }
        for category, score in scores.items():
            db.add(Risk(department_id=dept.id, category=category, score=round(score, 1), reason=f"{category} calculated from department workload, incidents, project budget and delivery history."))
    db.commit()


def recalculate_forecasts(db: Session) -> None:
    db.query(Forecast).delete()
    next_month = date.today().replace(day=1) + timedelta(days=32)
    next_month = next_month.replace(day=1)
    metrics = [
        ("Workload", Operation.workload),
        ("Incidents", None),
        ("Costs", Operation.cost),
        ("Productivity", Operation.productivity),
        ("Revenue", Operation.revenue),
    ]
    for dept in db.query(Department).all():
        for metric, column in metrics:
            if metric == "Incidents":
                current = db.query(Incident).filter(Incident.department_id == dept.id, Incident.created_at >= datetime.utcnow() - timedelta(days=30)).count()
                previous = db.query(Incident).filter(Incident.department_id == dept.id, Incident.created_at >= datetime.utcnow() - timedelta(days=60), Incident.created_at < datetime.utcnow() - timedelta(days=30)).count()
            else:
                current = db.query(func.coalesce(func.avg(column), 0)).filter(Operation.department_id == dept.id, Operation.recorded_on >= date.today() - timedelta(days=30)).scalar()
                previous = db.query(func.coalesce(func.avg(column), 0)).filter(Operation.department_id == dept.id, Operation.recorded_on >= date.today() - timedelta(days=60), Operation.recorded_on < date.today() - timedelta(days=30)).scalar()
            prediction = float(current or 0) + (float(current or 0) - float(previous or 0)) * 0.5
            confidence = max(55, min(92, 78 - abs(float(current or 0) - float(previous or 0)) * 0.05))
            db.add(Forecast(metric=metric, department_id=dept.id, prediction=round(prediction, 2), confidence=round(confidence, 1), explanation="Linear month-over-month trend based on the last 60 days of related operational records.", forecast_for=next_month))
    db.commit()
