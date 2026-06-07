import json
import unicodedata
from datetime import datetime
from urllib import request

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.domain.models import AIConversation, AIInsight, AIMessage, Department, Forecast, Incident, Operation, Project, Risk, Task, User, Workflow
from app.services import analytics_service


def generate_rule_based_insights(db: Session) -> None:
    db.query(AIInsight).delete()
    for risk in db.query(Risk).filter(Risk.score >= 55).order_by(Risk.score.desc()).limit(12):
        dept = db.get(Department, risk.department_id)
        incidents = db.query(Incident).filter(Incident.department_id == risk.department_id, Incident.status != "Resolved").count()
        productivity = (
            db.query(Operation.productivity)
            .filter(Operation.department_id == risk.department_id)
            .order_by(Operation.recorded_on.desc())
            .limit(30)
            .all()
        )
        avg_productivity = round(sum(row[0] for row in productivity) / len(productivity), 1) if productivity else 0
        priority = "High" if risk.score >= 75 else "Medium"
        db.add(
            AIInsight(
                department_id=risk.department_id,
                title=f"{dept.name if dept else 'Department'} shows elevated {risk.category.lower()}",
                reason=f"Risk score is {risk.score}/100 with {incidents} unresolved incidents and {avg_productivity}% recent productivity.",
                impact="Potential delay, cost pressure or SLA degradation if the current trend continues.",
                priority=priority,
                suggested_action="Review active blockers, rebalance workload and assign an owner for mitigation within 24 hours.",
                confidence=min(95, max(60, risk.score + 8)),
            )
        )
    db.commit()


def conversation_list(db: Session, user: User) -> list[AIConversation]:
    return db.query(AIConversation).filter(AIConversation.user_id == user.id).order_by(AIConversation.updated_at.desc()).limit(30).all()


def conversation_detail(db: Session, user: User, conversation_id: int) -> AIConversation | None:
    return db.query(AIConversation).filter(AIConversation.id == conversation_id, AIConversation.user_id == user.id).first()


def messages_for(db: Session, conversation_id: int, limit: int = 20) -> list[AIMessage]:
    rows = db.query(AIMessage).filter(AIMessage.conversation_id == conversation_id).order_by(AIMessage.id.desc()).limit(limit).all()
    return list(reversed(rows))


def operational_context(db: Session) -> dict:
    dashboard = analytics_service.dashboard(db)
    operations = analytics_service.operations_center(db)
    departments = analytics_service.department_analytics(db)
    forecasts = analytics_service.forecasts(db)
    open_incidents = db.query(Incident).filter(Incident.status != "Resolved").count()
    delayed_tasks = db.query(Task).filter(Task.status.in_(["Blocked", "Delayed"])).count()
    active_projects = db.query(Project).filter(Project.status != "Completed").count()
    avg_workflow_risk = float(db.query(func.coalesce(func.avg(Workflow.risk_score), 0)).scalar() or 0)
    return {
        "kpis": dashboard["kpis"],
        "trend": dashboard["trend"],
        "top_risks": dashboard["risks"][:5],
        "departments": sorted(departments, key=lambda item: item["risk"], reverse=True)[:8],
        "forecasts": forecasts[:12],
        "operations": {
            "active_operations": operations["active_operations"],
            "sla": operations["sla"],
            "open_incidents": open_incidents,
            "delayed_tasks": delayed_tasks,
            "active_projects": active_projects,
            "average_workflow_risk": round(avg_workflow_risk, 1),
        },
    }


def chat(db: Session, user: User, message: str, conversation_id: int | None = None) -> tuple[AIConversation, AIMessage, dict]:
    conversation = conversation_detail(db, user, conversation_id) if conversation_id else None
    if not conversation:
        title = _title_from_message(message)
        conversation = AIConversation(user_id=user.id, title=title)
        db.add(conversation)
        db.flush()

    db.add(AIMessage(conversation_id=conversation.id, role="user", content=message))
    memory = messages_for(db, conversation.id, limit=12)
    intent = _detect_intent(_normalize_text(message))
    should_use_data = _requires_business_data(intent, message, memory)
    context = operational_context(db) if should_use_data else _empty_context()
    answer_text, reasoning, confidence = _answer_with_openai_or_local(message, context, memory, intent, should_use_data)
    answer = AIMessage(conversation_id=conversation.id, role="assistant", content=answer_text, reasoning=reasoning, confidence=confidence)
    conversation.updated_at = datetime.utcnow()
    db.add(answer)
    db.commit()
    db.refresh(answer)
    db.refresh(conversation)
    return conversation, answer, context


def _title_from_message(message: str) -> str:
    clean = " ".join(message.strip().split())
    return clean[:70] if clean else "Operational analysis"


def _empty_context() -> dict:
    return {
        "kpis": [],
        "trend": [],
        "top_risks": [],
        "departments": [],
        "forecasts": [],
        "operations": {},
    }


def _answer_with_openai_or_local(message: str, context: dict, memory: list[AIMessage], intent: str, should_use_data: bool) -> tuple[str, str, float]:
    if not should_use_data:
        return _conversation_answer(intent, memory)
    if settings.openai_api_key:
        try:
            return _openai_answer(message, context, memory)
        except Exception:
            pass
    return _local_answer(message, context, memory, intent)


def _openai_answer(message: str, context: dict, memory: list[AIMessage]) -> tuple[str, str, float]:
    history = [{"role": item.role, "content": item.content} for item in memory[-10:]]
    payload = {
        "model": "gpt-4.1-mini",
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a senior Spanish-speaking business operations advisor. Do not behave like a talking dashboard. "
                    "First identify the user's intent. If the user only greets you, asks how you are, or says thanks, answer naturally without KPIs. "
                    "Use business data only for questions about risks, operations, departments, productivity, costs, KPIs, forecasts, sales, or follow-ups to those topics. "
                    "Do not invent data or metrics. If the supplied context is insufficient, say: No dispongo de suficiente informacion para responder con precision. "
                    "For recommendations, include: data used, why you reached the conclusion, and confidence level."
                ),
            },
            {"role": "user", "content": f"Business context JSON:\n{json.dumps(context, ensure_ascii=False)}"},
            *history,
            {"role": "user", "content": message},
        ],
        "temperature": 0.15,
    }
    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=20) as response:
        data = json.loads(response.read().decode("utf-8"))
    answer = data["choices"][0]["message"]["content"].strip()
    return answer, "Generated with OpenAI using current operational KPIs, risks, forecasts and recent conversation history.", 88.0


def _local_answer(message: str, context: dict, memory: list[AIMessage]) -> tuple[str, str, float]:
    clean_message = " ".join(message.strip().split())
    lower = clean_message.lower()
    kpis = {item["key"]: item for item in context["kpis"]}
    risky_departments = context["departments"][:3]
    top_risk = context["top_risks"][0] if context["top_risks"] else {"category": "Operational Risk", "score": 0, "reason": "No active risk records."}
    ops = context["operations"]
    forecasts = context["forecasts"][:5]
    recent_user_messages = [item.content for item in memory if item.role == "user"][-4:]

    intent = _detect_intent(lower)
    if intent == "greeting":
        return _small_talk_answer(
            "Hola. Me alegra verte por aqui. Puedes hablarme normal, como a una persona: preguntame por riesgos, departamentos, costes, forecast o simplemente dime que quieres entender de la plataforma.",
            "Intent=greeting; answered conversationally and kept operational context available.",
            memory,
            96.0,
        )
    if intent == "thanks":
        return _small_talk_answer(
            "De nada. Cuando quieras seguimos afinando el analisis. Puedo resumir, comparar areas, buscar riesgos o ayudarte a decidir el siguiente paso.",
            "Intent=thanks; answered conversationally and preserved chat continuity.",
            memory,
            95.0,
        )
    if intent == "identity":
        return _small_talk_answer(
            "Soy el asistente IA de esta plataforma. Puedo conversar contigo y tambien leer el contexto operativo: KPIs, riesgos, incidencias, departamentos, forecasts e historial de este chat. Si no hay una clave de OpenAI configurada, uso mi logica local con esos datos.",
            "Intent=identity; explained AI capabilities, data context and local reasoning mode.",
            memory,
            91.0,
        )
    if intent == "memory":
        remembered = "; ".join(recent_user_messages[:-1]) if len(recent_user_messages) > 1 else ""
        if remembered:
            answer = f"Si, mantengo el historial de este hilo. Lo ultimo que tengo presente es: {remembered}. Puedo usarlo para continuar sin que repitas todo."
        else:
            answer = "Todavia tengo poco historial en este hilo, pero desde ahora voy guardando la conversacion para responder con continuidad."
        return answer, f"Intent=memory; inspected {len(memory)} stored messages in the active conversation.", 88.0

    focus = "general"
    if any(word in lower for word in ["riesgo", "risk", "sla", "incidencia", "incident"]):
        focus = "risk"
    elif any(word in lower for word in ["forecast", "predic", "futuro", "proyect"]):
        focus = "forecast"
    elif any(word in lower for word in ["depart", "equipo", "area"]):
        focus = "department"
    elif any(word in lower for word in ["cost", "revenue", "ingreso", "gasto", "financ"]):
        focus = "finance"

    lines = [_opening_for(focus, bool(memory))]
    if focus == "risk":
        lines.extend(
            [
                f"El principal foco es {top_risk['category']} con score {top_risk['score']}/100.",
                f"SLA actual: {ops['sla']['attainment']}% frente a objetivo {ops['sla']['target']}%, con {ops['open_incidents']} incidencias no resueltas y {ops['delayed_tasks']} tareas bloqueadas o retrasadas.",
                "Mi recomendacion: priorizar mitigacion por departamento, revisar owners de bloqueos y abrir un plan de 24 horas para los procesos con riesgo alto.",
            ]
        )
    elif focus == "forecast":
        forecast_text = "; ".join(f"{item['metric']}: {item['prediction']} ({item['confidence']}%)" for item in forecasts)
        lines.extend(
            [
                f"Las senales predictivas mas relevantes son: {forecast_text}.",
                "La lectura ejecutiva es que la prediccion debe tratarse como alerta temprana, no como certeza: conviene contrastarla con capacidad, SLA y backlog antes de automatizar decisiones.",
            ]
        )
    elif focus == "department":
        dept_text = "; ".join(f"{item['name']} riesgo {item['risk']}, productividad {item['productivity']}%" for item in risky_departments)
        lines.extend(
            [
                f"Los departamentos que requieren mas atencion son: {dept_text}.",
                "La accion mas util es comparar workload, incidencias y presupuesto por owner para separar presion operativa real de ruido puntual.",
            ]
        )
    elif focus == "finance":
        revenue = kpis.get("revenue", {}).get("value", 0)
        costs = kpis.get("costs", {}).get("value", 0)
        efficiency = kpis.get("efficiency", {}).get("value", 0)
        lines.extend(
            [
                f"Revenue actual: {revenue:,.0f}. Costes: {costs:,.0f}. Eficiencia: {efficiency}%.",
                "La decision logica es proteger margen sin recortar capacidad critica: cruza coste por departamento con riesgo SLA antes de reducir recursos.",
            ]
        )
    else:
        lines.extend(
            [
                f"El estado general combina {kpis.get('projects', {}).get('value', 0)} proyectos activos, {ops['active_operations']} operaciones activas y un risk score medio de {kpis.get('risk', {}).get('value', 0)}/100.",
                f"El riesgo mas fuerte ahora es {top_risk['category']} ({top_risk['score']}/100).",
                "Mi recomendacion: enfocar la reunion ejecutiva en tres decisiones: riesgos SLA, capacidad por departamento y coste de retrasos.",
            ]
        )

    if memory:
        lines.append("Mantengo este hilo como contexto, asi que puedo seguir refinando el analisis con tus preguntas anteriores.")
    reasoning = f"Focus={focus}; derived from dashboard KPIs, operation center, top risks, department analytics, forecasts and {len(memory)} prior messages."
    confidence = 82.0 if context["kpis"] else 60.0
    return "\n\n".join(lines), reasoning, confidence


def _detect_intent(lower: str) -> str:
    compact = lower.strip(" .,!¡?¿")
    greetings = {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "hey", "hello", "hi"}
    thanks = {"gracias", "muchas gracias", "ok gracias", "vale gracias", "thank you", "thanks"}
    if compact in greetings or any(compact.startswith(item + " ") for item in greetings):
        return "greeting"
    if compact in thanks or any(item in compact for item in ["te lo agradezco", "gracias por"]):
        return "thanks"
    if any(phrase in compact for phrase in ["quien eres", "que eres", "como funcionas", "eres chatgpt", "eres una ia"]):
        return "identity"
    if any(phrase in compact for phrase in ["recuerdas", "que te dije", "historial", "hilo anterior", "conversacion"]):
        return "memory"
    return "analysis"


def _small_talk_answer(answer: str, reasoning: str, memory: list[AIMessage], confidence: float) -> tuple[str, str, float]:
    if memory:
        answer = f"{answer}\n\nTambien tengo en cuenta lo que venimos hablando en este chat."
    return answer, reasoning, confidence


def _opening_for(focus: str, has_memory: bool) -> str:
    if has_memory:
        return "Claro. Tomo el historial de este chat y lo cruzo con los datos actuales de la plataforma."
    if focus == "general":
        return "Claro. Te doy una lectura general con los KPIs actuales, riesgos, forecasts e historial operativo."
    return "Claro. Voy directo a lo importante usando los datos actuales de la plataforma."


_BUSINESS_TERMS = {
    "riesgo", "risk", "sla", "incidencia", "incident", "operacion", "operaciones", "departamento",
    "departamentos", "equipo", "area", "productividad", "productivity", "coste", "costes", "costo",
    "costos", "kpi", "kpis", "forecast", "prediccion", "futuro", "ventas", "venta", "revenue",
    "ingreso", "ingresos", "gasto", "gastos", "finanzas", "analiza", "analisis", "recomienda",
    "recomendacion", "mayor", "actual", "negocio",
}


def _local_answer(message: str, context: dict, memory: list[AIMessage], intent: str) -> tuple[str, str, float]:
    normalized = _normalize_text(message)
    focus = _business_focus(normalized, memory)
    if not _has_enough_context(context, focus):
        return _insufficient(intent, focus)

    kpis = {item["key"]: item for item in context["kpis"]}
    top_risk = context["top_risks"][0] if context["top_risks"] else None
    ops = context["operations"]
    confidence = 82.0

    if focus == "risk":
        if not top_risk:
            return _insufficient(intent, focus)
        impact = "Alto." if float(top_risk["score"]) >= 75 else "Medio."
        answer = [
            f"Actualmente el principal riesgo es {top_risk['category']}.",
            "",
            f"La causa principal es: {top_risk['reason']}",
            "",
            "Impacto estimado:",
            impact,
            "",
            "Accion recomendada:",
            "Incrementar capacidad de revision, reducir bloqueos activos y asignar un responsable de mitigacion en las proximas 24 horas.",
            "",
            "Datos utilizados:",
            f"- Riesgo superior: {top_risk['category']} con score {top_risk['score']}/100.",
            f"- Incidencias sin resolver: {ops.get('open_incidents', 0)}.",
            f"- Tareas bloqueadas o retrasadas: {ops.get('delayed_tasks', 0)}.",
            "",
            "Por que llego a esta conclusion:",
            "El score de riesgo es el mas alto disponible y esta respaldado por incidencias abiertas y trabajo bloqueado.",
            "",
            "Nivel de confianza:",
            "86%.",
        ]
        confidence = 86.0
    elif focus == "operations":
        answer = [
            "La prioridad operativa actual es reducir friccion en operaciones activas y bloqueos.",
            "",
            "Accion recomendada:",
            "Revisar operaciones abiertas por criticidad, desbloquear tareas retrasadas y reforzar el seguimiento de SLA.",
            "",
            "Datos utilizados:",
            f"- Operaciones activas: {ops.get('active_operations', 0)}.",
            f"- Incidencias sin resolver: {ops.get('open_incidents', 0)}.",
            f"- Tareas bloqueadas o retrasadas: {ops.get('delayed_tasks', 0)}.",
            "",
            "Por que llego a esta conclusion:",
            "Las operaciones activas combinadas con incidencias y bloqueos indican presion de ejecucion, no solo volumen de trabajo.",
            "",
            "Nivel de confianza:",
            "82%.",
        ]
    elif focus == "department":
        departments = context["departments"][:3]
        dept_text = "\n".join(f"- {item['name']}: riesgo {item['risk']}, productividad {item['productivity']}%" for item in departments)
        answer = [
            "Los departamentos que requieren mas atencion son los que combinan mayor riesgo con menor productividad relativa.",
            "",
            "Departamentos prioritarios:",
            dept_text,
            "",
            "Accion recomendada:",
            "Comparar workload, owners e incidencias por departamento antes de mover presupuesto o capacidad.",
            "",
            "Datos utilizados:",
            dept_text,
            "",
            "Por que llego a esta conclusion:",
            "El riesgo por departamento identifica exposicion; la productividad muestra si esa exposicion afecta la ejecucion.",
            "",
            "Nivel de confianza:",
            "83%.",
        ]
        confidence = 83.0
    elif focus == "productivity":
        productivity = kpis.get("productivity")
        if not productivity:
            return _insufficient(intent, focus)
        answer = [
            f"La productividad actual es {productivity['value']}{productivity['unit']}.",
            "",
            "Accion recomendada:",
            "Revisar los equipos con mayor workload y menor productividad para separar falta de capacidad de problemas de proceso.",
            "",
            "Datos utilizados:",
            f"- KPI Productivity: {productivity['value']}{productivity['unit']}.",
            f"- Tareas bloqueadas o retrasadas: {ops.get('delayed_tasks', 0)}.",
            "",
            "Por que llego a esta conclusion:",
            "La productividad por si sola no explica causa; al cruzarla con bloqueos se distingue si el problema viene de ejecucion o capacidad.",
            "",
            "Nivel de confianza:",
            "80%.",
        ]
        confidence = 80.0
    elif focus == "finance":
        revenue = kpis.get("revenue")
        costs = kpis.get("costs")
        efficiency = kpis.get("efficiency")
        if not revenue or not costs:
            return _insufficient(intent, focus)
        period_note = ""
        if any(term in normalized for term in ["mes pasado", "ultimo mes", "anterior"]):
            period_note = " Para el periodo anterior uso la variacion disponible frente a los ultimos 30 dias previos; no hay un desglose mensual mas fino en este contexto."
        answer = [
            f"En ventas/ingresos, el valor actual es {revenue['value']:,.0f} {revenue['unit']}. Los costes actuales son {costs['value']:,.0f} {costs['unit']}.{period_note}",
            "",
            "Accion recomendada:",
            "Proteger margen revisando coste por departamento antes de recortar capacidad operativa critica.",
            "",
            "Datos utilizados:",
            f"- Revenue: {revenue['value']:,.0f} {revenue['unit']} con variacion {revenue['delta']}%.",
            f"- Costs: {costs['value']:,.0f} {costs['unit']} con variacion {costs['delta']}%.",
            f"- Efficiency: {efficiency['value']}%." if efficiency else "- Efficiency: no disponible.",
            "",
            "Por que llego a esta conclusion:",
            "La relacion entre ingresos, costes y eficiencia muestra si el problema es crecimiento, margen o presion de gasto.",
            "",
            "Nivel de confianza:",
            "84%.",
        ]
        confidence = 84.0
    elif focus == "forecast":
        forecasts = context["forecasts"][:5]
        forecast_text = "\n".join(f"- {item['metric']}: {item['prediction']} con confianza {item['confidence']}%" for item in forecasts)
        answer = [
            "Las previsiones disponibles apuntan a estas senales principales:",
            forecast_text,
            "",
            "Accion recomendada:",
            "Usar el forecast como alerta temprana y contrastarlo con capacidad, SLA y backlog antes de tomar decisiones automaticas.",
            "",
            "Datos utilizados:",
            forecast_text,
            "",
            "Por que llego a esta conclusion:",
            "El forecast tiene valor direccional, pero su propia confianza exige validarlo con la carga operativa real.",
            "",
            "Nivel de confianza:",
            "78%.",
        ]
        confidence = 78.0
    else:
        risk = kpis.get("risk")
        projects = kpis.get("projects")
        answer = [
            "La lectura ejecutiva es que conviene priorizar riesgo operativo, capacidad y coste de retrasos.",
            "",
            "Accion recomendada:",
            "Empezar por el mayor riesgo, validar departamentos con mas presion y convertirlo en tres decisiones concretas para esta semana.",
            "",
            "Datos utilizados:",
            f"- Risk Score: {risk['value']}/100." if risk else "- Risk Score: no disponible.",
            f"- Proyectos activos: {projects['value']}." if projects else "- Proyectos activos: no disponible.",
            f"- Operaciones activas: {ops.get('active_operations', 0)}.",
            "",
            "Por que llego a esta conclusion:",
            "La combinacion de riesgo, operaciones activas y proyectos abiertos permite orientar una conversacion ejecutiva sin inventar metricas.",
            "",
            "Nivel de confianza:",
            "80%.",
        ]

    return "\n".join(answer), f"Intent={intent}; focus={focus}; used relevant platform context and {len(memory)} prior messages.", confidence


def _conversation_answer(intent: str, memory: list[AIMessage]) -> tuple[str, str, float]:
    if intent == "greeting":
        return (
            "Hola. Que te gustaria revisar hoy? Puedo ayudarte con riesgos, operaciones, departamentos, productividad o analisis de negocio.",
            "Intent=greeting; no business data used because the user only greeted the assistant.",
            99.0,
        )
    if intent == "wellbeing":
        return (
            "Muy bien, gracias. Estoy listo para ayudarte a analizar la informacion de la plataforma.",
            "Intent=wellbeing; no business data used because the user asked a conversational question.",
            99.0,
        )
    if intent == "thanks":
        return (
            "De nada. Estoy aqui para ayudarte.",
            "Intent=thanks; no business data used because the user expressed thanks.",
            99.0,
        )
    if intent == "identity":
        return (
            "Soy tu asesor empresarial dentro de la plataforma. Puedo conversar de forma natural y, cuando me preguntes por negocio, analizar riesgos, operaciones, departamentos, productividad, costes, KPIs y forecast usando los datos disponibles.",
            "Intent=identity; no business data required for this explanation.",
            94.0,
        )
    if intent == "memory":
        prior = [item.content for item in memory if item.role == "user"][:-1]
        if prior:
            return (
                f"Si. Tengo presente el historial de este hilo. Lo anterior mas relevante es: {'; '.join(prior[-3:])}.",
                f"Intent=memory; reviewed {len(memory)} prior messages in this conversation.",
                90.0,
            )
        return (
            "Todavia no hay suficiente historial previo en este hilo, pero a partir de ahora puedo seguir el contexto de tus preguntas.",
            f"Intent=memory; reviewed {len(memory)} prior messages in this conversation.",
            86.0,
        )
    return (
        "No dispongo de suficiente informacion para responder con precision.",
        f"Intent={intent}; no business data requested and no supported conversational intent matched.",
        35.0,
    )


def _normalize_text(text: str) -> str:
    clean = " ".join(text.strip().lower().split())
    normalized = unicodedata.normalize("NFKD", clean)
    return "".join(char for char in normalized if not unicodedata.combining(char)).strip(" .,!¡?¿")


def _detect_intent(normalized: str) -> str:
    greetings = {"hola", "buenas", "buenos dias", "buenas tardes", "buenas noches", "hey", "hello", "hi"}
    thanks = {"gracias", "muchas gracias", "ok gracias", "vale gracias", "thank you", "thanks"}
    if normalized in greetings or any(normalized.startswith(item + " ") for item in greetings):
        return "greeting"
    if normalized in {"como estas", "que tal", "como va", "como te encuentras"}:
        return "wellbeing"
    if normalized in thanks or any(item in normalized for item in ["te lo agradezco", "gracias por"]):
        return "thanks"
    if any(phrase in normalized for phrase in ["quien eres", "que eres", "como funcionas", "eres chatgpt", "eres una ia"]):
        return "identity"
    if any(phrase in normalized for phrase in ["recuerdas", "que te dije", "historial", "hilo anterior", "conversacion"]):
        return "memory"
    if any(term in normalized for term in _BUSINESS_TERMS) or _is_business_follow_up(normalized):
        return "analysis"
    return "unknown"


def _requires_business_data(intent: str, message: str, memory: list[AIMessage]) -> bool:
    if intent == "analysis":
        return True
    if intent == "unknown" and _business_focus(_normalize_text(message), memory) != "general":
        return True
    return False


def _is_business_follow_up(normalized: str) -> bool:
    follow_up_terms = {"y el mes pasado", "y ayer", "y esta semana", "y el anterior", "comparalo", "continua", "sigue"}
    return any(term in normalized for term in follow_up_terms)


def _business_focus(normalized: str, memory: list[AIMessage]) -> str:
    text = normalized
    if _is_business_follow_up(normalized):
        previous = " ".join(_normalize_text(item.content) for item in memory if item.role == "user")
        text = f"{previous} {normalized}"
    if any(word in text for word in ["riesgo", "risk", "sla", "incidencia", "incident"]):
        return "risk"
    if any(word in text for word in ["operacion", "operaciones", "workload", "capacidad", "bloqueo"]):
        return "operations"
    if any(word in text for word in ["departamento", "departamentos", "equipo", "area"]):
        return "department"
    if any(word in text for word in ["productividad", "productivity"]):
        return "productivity"
    if any(word in text for word in ["coste", "costes", "costo", "costos", "venta", "ventas", "revenue", "ingreso", "ingresos", "gasto", "gastos", "finanzas"]):
        return "finance"
    if any(word in text for word in ["forecast", "prediccion", "futuro", "proyect"]):
        return "forecast"
    return "general"


def _has_enough_context(context: dict, focus: str) -> bool:
    if not context["kpis"]:
        return False
    if focus == "risk":
        return bool(context["top_risks"]) and bool(context["operations"])
    if focus == "operations":
        return bool(context["operations"])
    if focus == "department":
        return bool(context["departments"])
    if focus == "forecast":
        return bool(context["forecasts"])
    return True


def _insufficient(intent: str, focus: str) -> tuple[str, str, float]:
    return (
        "No dispongo de suficiente informacion para responder con precision.",
        f"Intent={intent}; focus={focus}; relevant platform data was missing.",
        35.0,
    )
