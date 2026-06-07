# Enterprise Operations Intelligence Suite

A full-stack enterprise operations intelligence platform built with React, Vite, TailwindCSS, React Query, Recharts, FastAPI, SQLAlchemy, JWT auth and PostgreSQL.

## Architecture

- Presentation Layer: React routes, data panels, charts, tables, loading/error/empty/success states.
- Business Layer: analytics, risk, forecast, AI advisor and audit services.
- Domain Layer: users, roles, permissions, departments, projects, tasks, operations, workflows, incidents, risks, forecasts, reports, notifications and AI insights.
- Data Layer: SQLAlchemy models and repositories through FastAPI dependencies.
- AI Layer: explainable advisor service using operational history and risk scores, with OpenAI key reserved for production enhancement.
- Infrastructure Layer: Docker, Docker Compose, PostgreSQL, CORS, environment configuration.

## Business Flows

- Executive dashboard derives revenue, costs, orders, incidents, projects, workflows, efficiency, productivity, satisfaction and risk from stored operational records.
- Operations Center tracks active operations, open incidents, project delivery, workload, capacity, blockers and SLA attainment.
- Workflow Engine models Pending, Review, Approval, Execution, Completed and Rejected process states.
- Risk Engine calculates SLA, budget, resource, operational, performance and delivery risks from historical records.
- AI Operations Advisor creates analyst-style recommendations with reason, impact, priority, suggested action and confidence.
- Forecasting predicts workload, incidents, costs, productivity and revenue using recent historical trends.
- Executive Reports can be generated and export actions are audited.

## Permissions

Roles: Admin, Executive, Manager, Analyst, Employee, Viewer.

Every protected backend route uses permission checks. The frontend also gates user flows through authenticated routing. Database-level integrity is represented through relational constraints and role-permission join tables.

## Seed Data

On startup the backend seeds:

- 500 users
- 15 departments
- 180 projects
- 5,000 operations
- 2,000 incidents
- 10,000 tasks
- 320 workflows
- 24 months of related historical records

Default login:

- Email: `admin@enterprise-ops.com`
- Password: `Enterprise123!`

## Run With Docker

```bash
docker compose up --build
```

Frontend: http://127.0.0.1:5173  
Backend: http://127.0.0.1:8000  
API docs: http://127.0.0.1:8000/docs

## Run Locally

Backend:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Local development uses the system temporary directory for SQLite by default so login auditing and session writes work reliably across Windows launch modes. Docker uses PostgreSQL through `DATABASE_URL`.

Frontend:

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

## API Surface

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/forgot-password`
- `POST /api/v1/auth/reset-password`
- `POST /api/v1/auth/change-password`
- `GET /api/v1/dashboard`
- `GET /api/v1/operations-center`
- `GET /api/v1/workflows`
- `GET /api/v1/risks`
- `GET /api/v1/forecasts`
- `GET /api/v1/analytics/departments`
- `GET /api/v1/ai-insights`
- `GET /api/v1/reports`
- `POST /api/v1/reports`
- `GET /api/v1/reports/export/{format}`
- `GET /api/v1/audit-logs`

## Notes

The product intentionally avoids fake frontend-only metrics. The seeded dataset is deterministic and relational, and every displayed KPI is calculated through backend services.
