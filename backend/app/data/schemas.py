from datetime import date, datetime

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    username: EmailStr
    password: str
    device: str = "Unknown device"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str
    device: str = "Unknown device"


class PasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class KPI(BaseModel):
    key: str
    label: str
    value: float
    unit: str
    delta: float


class DashboardResponse(BaseModel):
    kpis: list[KPI]
    trend: list[dict]
    risks: list[dict]
    departments: list[dict]


class OperationCenterResponse(BaseModel):
    active_operations: int
    projects: list[dict]
    incidents: list[dict]
    capacity: list[dict]
    sla: dict
    blockers: list[dict]


class ReportCreate(BaseModel):
    period: str
    title: str


class ExportResponse(BaseModel):
    filename: str
    content_type: str
    generated_at: datetime


class UserProfile(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    department: str


class AIChatRequest(BaseModel):
    message: str
    conversation_id: int | None = None


class AIChatMessage(BaseModel):
    id: int
    role: str
    content: str
    reasoning: str | None = None
    confidence: float | None = None
    created_at: datetime


class AIChatConversation(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[AIChatMessage] = []


class AIChatResponse(BaseModel):
    conversation_id: int
    answer: AIChatMessage
    context: dict
