from datetime import date, datetime, timedelta
from random import Random

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.domain.models import Department, Incident, Operation, Permission, Project, Role, RolePermission, Task, User, Workflow
from app.services.ai_service import generate_rule_based_insights
from app.services.risk_service import recalculate_forecasts, recalculate_risks


DEPARTMENT_NAMES = [
    "Operations", "Sales", "Finance", "Support", "IT", "HR", "Procurement", "Legal",
    "Marketing", "Customer Success", "Logistics", "Manufacturing", "Data", "Security", "Strategy",
]
ROLE_NAMES = ["Admin", "Executive", "Manager", "Analyst", "Employee", "Viewer"]
PERMISSIONS = [
    "admin:*", "dashboard:read", "operations:read", "workflows:read", "risks:read",
    "analytics:read", "reports:read", "reports:export", "users:manage", "permissions:manage",
]


def seed(db: Session, force: bool = False) -> dict:
    if db.query(User).count() and not force:
        return {"status": "skipped", "reason": "Database already contains users"}

    for table in [Task, Incident, Workflow, Operation, Project, User, RolePermission, Permission, Role, Department]:
        db.query(table).delete()
    db.commit()

    permissions = [Permission(action=p, description=f"Allows {p}") for p in PERMISSIONS]
    roles = [Role(name=name, description=f"{name} role") for name in ROLE_NAMES]
    db.add_all(permissions + roles)
    db.flush()
    permission_map = {p.action: p for p in permissions}
    for role in roles:
        allowed = PERMISSIONS if role.name == "Admin" else PERMISSIONS[1:8]
        if role.name in ["Employee", "Viewer"]:
            allowed = ["dashboard:read", "operations:read", "workflows:read"]
        for action in allowed:
            db.add(RolePermission(role_id=role.id, permission_id=permission_map[action].id))

    departments = [Department(name=name, budget=750_000 + i * 125_000, target_sla=92 + (i % 4)) for i, name in enumerate(DEPARTMENT_NAMES)]
    db.add_all(departments)
    db.flush()

    rnd = Random(42)
    users: list[User] = []
    password = hash_password("Enterprise123!")
    for i in range(500):
        dept = departments[i % len(departments)]
        role = roles[i % len(roles)]
        users.append(
            User(
                email=f"user{i + 1}@enterprise-ops.com",
                full_name=f"Enterprise User {i + 1}",
                hashed_password=password,
                role_id=role.id,
                department_id=dept.id,
            )
        )
    users[0].email = "admin@enterprise-ops.com"
    users[0].full_name = "Alicia Morgan"
    users[0].role_id = roles[0].id
    db.add_all(users)
    db.flush()

    projects: list[Project] = []
    for i in range(180):
        dept = departments[i % len(departments)]
        budget = 60_000 + (i % 18) * 12_500
        spent = budget * (0.35 + (i % 9) * 0.08)
        projects.append(
            Project(
                name=f"{dept.name} Initiative {i + 1}",
                department_id=dept.id,
                owner_id=users[(i * 7) % len(users)].id,
                budget=budget,
                spent=round(spent, 2),
                due_date=date.today() + timedelta(days=(i % 120) - 20),
                status=["Discovery", "Active", "At Risk", "Completed"][i % 4],
            )
        )
    db.add_all(projects)
    db.flush()

    start = date.today() - timedelta(days=730)
    operations: list[Operation] = []
    for i in range(5000):
        dept = departments[i % len(departments)]
        day = start + timedelta(days=i % 730)
        season = 1 + ((day.month - 6) / 60)
        dept_factor = 1 + (dept.id % 5) * 0.04
        revenue = (9_000 + (i % 31) * 420) * season * dept_factor
        cost = revenue * (0.48 + (i % 11) * 0.015)
        operations.append(
            Operation(
                department_id=dept.id,
                project_id=projects[i % len(projects)].id,
                name=f"{dept.name} Operation {i + 1}",
                status=["Active", "Delayed", "Blocked", "Completed"][i % 4],
                revenue=round(revenue, 2),
                cost=round(cost, 2),
                orders=18 + (i % 60),
                productivity=round(68 + (i % 24) * 1.1 - (4 if i % 19 == 0 else 0), 1),
                customer_satisfaction=round(72 + (i % 20) * 0.9 - (6 if i % 23 == 0 else 0), 1),
                workload=round(45 + (i % 48) * 1.2 + (8 if i % 17 == 0 else 0), 1),
                recorded_on=day,
            )
        )
    db.add_all(operations)

    incidents: list[Incident] = []
    for i in range(2000):
        dept = departments[(i * 3) % len(departments)]
        created = datetime.utcnow() - timedelta(days=i % 730, hours=i % 24)
        resolved = None if i % 5 == 0 else created + timedelta(hours=6 + (i % 60))
        incidents.append(
            Incident(
                department_id=dept.id,
                title=f"{dept.name} incident {i + 1}",
                severity=["Low", "Medium", "High", "Critical"][i % 4],
                status=["Open", "Investigating", "Resolved", "Blocked"][i % 4],
                sla_due_at=created + timedelta(hours=24 + (i % 24)),
                resolved_at=resolved,
                created_at=created,
            )
        )
    db.add_all(incidents)

    tasks: list[Task] = []
    for i in range(10000):
        estimated = 2 + (i % 14)
        actual = estimated + ((i % 9) - 3) * 0.8
        tasks.append(
            Task(
                project_id=projects[i % len(projects)].id,
                assignee_id=users[(i * 5) % len(users)].id,
                title=f"Operational task {i + 1}",
                status=["Todo", "In Progress", "Review", "Blocked", "Delayed", "Done"][i % 6],
                estimated_hours=estimated,
                actual_hours=max(0.5, round(actual, 1)),
                due_date=date.today() + timedelta(days=(i % 90) - 15),
            )
        )
    db.add_all(tasks)

    workflows = []
    statuses = ["Pending", "Review", "Approval", "Execution", "Completed", "Rejected"]
    for i in range(320):
        dept = departments[i % len(departments)]
        duration = 12 + (i % 80)
        average = 36 + (i % 32)
        delay = max(0, duration - average)
        workflows.append(
            Workflow(
                name=f"{dept.name} workflow {i + 1}",
                department_id=dept.id,
                owner_id=users[(i * 11) % len(users)].id,
                status=statuses[i % len(statuses)],
                duration_hours=duration,
                average_time_hours=average,
                delay_hours=delay,
                risk_score=min(100, round(delay * 1.7 + (i % 30), 1)),
            )
        )
    db.add_all(workflows)
    db.commit()
    recalculate_risks(db)
    recalculate_forecasts(db)
    generate_rule_based_insights(db)
    return {"status": "seeded", "users": 500, "departments": 15, "operations": 5000, "incidents": 2000, "tasks": 10000, "history_months": 24}
