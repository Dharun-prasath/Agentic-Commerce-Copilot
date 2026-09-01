from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.models.models import (
    CustomerSession, IntentAssessment, OrchestratorJob, 
    BehaviorEvent, CommerceAction, AgentExecution
)

async def build_execution_graph(session_id: str, db: AsyncSession):
    # Fetch session
    result = await db.execute(
        select(CustomerSession)
        .options(
            selectinload(CustomerSession.events),
            selectinload(CustomerSession.intents),
            selectinload(CustomerSession.conversations)
        )
        .where(CustomerSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"nodes": [], "edges": [], "timeline": [], "active_edges": []}

    # Fetch Orchestrator job
    job_result = await db.execute(
        select(OrchestratorJob).where(OrchestratorJob.session_id == session_id)
    )
    job = job_result.scalar_one_or_none()

    # Fetch Agent Executions (PI / others)
    exec_result = await db.execute(
        select(AgentExecution).where(AgentExecution.session_id == session_id).order_by(AgentExecution.created_at)
    )
    executions = exec_result.scalars().all()

    # Fetch Commerce Actions
    commerce_result = await db.execute(
        select(CommerceAction).where(CommerceAction.session_id == session_id).order_by(CommerceAction.created_at)
    )
    commerce_actions = commerce_result.scalars().all()

    # Initialize fixed nodes with IDLE state
    nodes = {
        "n_session": {"id": "n_session", "type": "component", "label": "CUSTOMER SESSION", "status": "COMPLETED", "details": {}},
        "n_rule_intent": {"id": "n_rule_intent", "type": "component", "label": "RULE-BASED INTENT", "status": "IDLE", "details": {}},
        "n_orchestrator": {"id": "n_orchestrator", "type": "orchestrator", "label": "ORCHESTRATOR", "status": "IDLE", "details": {}},
        "n_intent_agent": {"id": "n_intent_agent", "type": "agent", "label": "INTENT AGENT", "status": "IDLE", "details": {}},
        "n_sales_consultant": {"id": "n_sales_consultant", "type": "agent", "label": "SALES CONSULTANT", "status": "IDLE", "details": {}},
        "n_product_intelligence": {"id": "n_product_intelligence", "type": "agent", "label": "PRODUCT INTELLIGENCE", "status": "IDLE", "details": {}},
        "n_telegram": {"id": "n_telegram", "type": "engine", "label": "TELEGRAM ENGINE", "status": "IDLE", "details": {}},
        "n_commerce": {"id": "n_commerce", "type": "engine", "label": "COMMERCE ENGINE", "status": "IDLE", "details": {}}
    }
    
    # Initialize fixed edges
    edges = [
        {"id": "e_sess_to_rule", "source": "n_session", "target": "n_rule_intent"},
        {"id": "e_rule_to_orch", "source": "n_rule_intent", "target": "n_orchestrator"},
        
        {"id": "e_orch_to_ia", "source": "n_orchestrator", "target": "n_intent_agent"},
        {"id": "e_ia_to_orch", "source": "n_intent_agent", "target": "n_orchestrator"},
        
        {"id": "e_orch_to_sc", "source": "n_orchestrator", "target": "n_sales_consultant"},
        {"id": "e_sc_to_orch", "source": "n_sales_consultant", "target": "n_orchestrator"},
        
        {"id": "e_orch_to_pi", "source": "n_orchestrator", "target": "n_product_intelligence"},
        {"id": "e_pi_to_orch", "source": "n_product_intelligence", "target": "n_orchestrator"},
        
        {"id": "e_orch_to_tg", "source": "n_orchestrator", "target": "n_telegram"},
        {"id": "e_orch_to_com", "source": "n_orchestrator", "target": "n_commerce"}
    ]
    
    timeline = []
    active_edges = []
    
    def add_event(time, event_name, desc=""):
        time_str = time.strftime("%H:%M:%S") if time else ""
        timeline.append({"time": time_str, "event": event_name, "description": desc})

    # Timeline from session creation
    add_event(session.created_at, "SESSION_STARTED")
    
    # Rule intent
    if session.threshold_reached:
        nodes["n_rule_intent"]["status"] = "COMPLETED"
        add_event(session.updated_at, "INTENT_DETECTED", "High intent threshold reached")
        
        # Orchestrator is ALWAYS active as the central controller
        nodes["n_orchestrator"]["status"] = "RUNNING"
        
        if job:
            add_event(job.created_at, "ORCHESTRATOR_STARTED", f"Job: {job.id}")
            
            # Map job status to node states and active edges
            
            # Forward propagation rule intent -> orchestrator
            if job.status == "INTENT_RECEIVED":
                active_edges.append("e_rule_to_orch")
                
            # INTENT AGENT
            if job.status == "TRIGGERING_INTENT_AGENT":
                nodes["n_intent_agent"]["status"] = "RUNNING"
                active_edges.append("e_orch_to_ia")
                add_event(job.updated_at, "INTENT_AGENT_TRIGGERED")
            elif job.status in ["FAILED_TO_START_INTENT_AGENT", "FAILED_DURING_INTENT"]:
                nodes["n_intent_agent"]["status"] = "FAILED"
            elif job.status not in ["QUEUED", "INTENT_RECEIVED", "TRIGGERING_INTENT_AGENT", "FAILED"]:
                # Returns to IDLE after its task
                nodes["n_intent_agent"]["status"] = "IDLE"

            # SALES CONSULTANT
            # Sales consultant remains PROCESSING throughout the conversation lifecycle
            if job.status in ["TRIGGERING_SALES_CONSULTANT", "SALES_CONSULTANT_TRIGGERED", "PRODUCT_RECOMMENDATION_REQUESTED", "PRODUCT_INTELLIGENCE_PROCESSING", "PRODUCT_RECOMMENDATIONS_READY", "COMMERCE_PROCESSING", "COMMERCE_COMPLETED"]:
                nodes["n_sales_consultant"]["status"] = "RUNNING"
                if job.status in ["TRIGGERING_SALES_CONSULTANT", "SALES_CONSULTANT_TRIGGERED"]:
                    active_edges.append("e_orch_to_sc")
                if job.status == "PRODUCT_RECOMMENDATION_REQUESTED":
                    active_edges.append("e_sc_to_orch")
                    add_event(job.updated_at, "PRODUCT_RECOMMENDATION_REQUESTED")
                
            # PRODUCT INTELLIGENCE
            if job.status == "PRODUCT_INTELLIGENCE_PROCESSING":
                nodes["n_product_intelligence"]["status"] = "RUNNING"
                active_edges.append("e_orch_to_pi")
                add_event(job.updated_at, "PRODUCT_INTELLIGENCE_RUNNING")
                
            if job.status == "PRODUCT_RECOMMENDATIONS_READY":
                nodes["n_product_intelligence"]["status"] = "IDLE"
                active_edges.append("e_pi_to_orch")
                add_event(job.updated_at, "PRODUCT_RECOMMENDATIONS_READY")
                
                # Check telegram
                nodes["n_telegram"]["status"] = "RUNNING"
                active_edges.append("e_orch_to_tg") # Actually e_orch_to_tel doesn't exist, we use e_pi_to_tel in the old code, wait, I re-wired it in frontend to n_orchestrator -> n_telegram, but let's just emit an edge ID the frontend knows.
                # In ExecutionGraph we mapped e.target === 'n_telegram' to e.source = 'n_orchestrator'
                # Let's emit e_orch_to_tel. Wait, the fixed edges list in this file has e_pi_to_tel.
                
            # COMMERCE
            if job.status == "COMMERCE_PROCESSING":
                nodes["n_commerce"]["status"] = "RUNNING"
                active_edges.append("e_orch_to_com")
                add_event(job.updated_at, "COMMERCE_PROCESSING")
                
            if job.status == "COMMERCE_COMPLETED":
                nodes["n_commerce"]["status"] = "IDLE"
                # Use the same edge for backward prop, per user request
                active_edges.append("e_orch_to_com")
                add_event(job.updated_at, "COMMERCE_COMPLETED")
                
            if commerce_actions:
                for c in commerce_actions:
                    add_event(c.created_at, c.action_type, f"Product {c.product_id}")

            # JOB COMPLETED / WORKFLOW ENDED
            if job.status in ["COMPLETED", "CUSTOMER_NOT_INTERESTED"]:
                # Sales consultant finishes and goes IDLE
                nodes["n_sales_consultant"]["status"] = "IDLE"
                nodes["n_commerce"]["status"] = "IDLE"
                nodes["n_telegram"]["status"] = "IDLE"
                add_event(job.updated_at, "WORKFLOW_COMPLETED", "Orchestrator workflow ended.")

            # Error catching
            if "FAILED" in job.status:
                nodes["n_orchestrator"]["status"] = "FAILED"
                add_event(job.updated_at, "ORCHESTRATOR_FAILED", job.error)
                
    else:
        nodes["n_rule_intent"]["status"] = "RUNNING"
        active_edges.append("e_sess_to_rule")

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
        "timeline": timeline,
        "active_edges": active_edges
    }
