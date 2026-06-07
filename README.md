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

## Demo


https://enterprise-operations-intelligence.vercel.app

## Notes

The product intentionally avoids fake frontend-only metrics. The seeded dataset is deterministic and relational, and every displayed KPI is calculated through backend services.
