from sqlalchemy import Column, String, Integer, Float, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from app.models.base import Base, TimestampMixin

class Customer(Base, TimestampMixin):
    __tablename__ = "customers"
    
    id = Column(String, primary_key=True, index=True) # Usually mapping to user_id
    name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    telegram_chat_id = Column(String, nullable=True, index=True)
    
    sessions = relationship("CustomerSession", back_populates="customer", cascade="all, delete-orphan")

class CustomerSession(Base, TimestampMixin):
    __tablename__ = "customer_sessions"
    
    session_id = Column(String, primary_key=True, index=True)
    user_id = Column(String, ForeignKey("customers.id"), nullable=True, index=True)
    last_active = Column(String, nullable=True) # ISO format string for simplicity
    
    # Intent Intelligence Fields
    current_intent_score = Column(Float, default=0.0)
    intent_threshold = Column(Float, default=50.0)
    threshold_reached = Column(Boolean, default=False)
    status = Column(String, default="ACTIVE") # ACTIVE, TERMINATED
    finalized_at = Column(String, nullable=True)
    
    customer = relationship("Customer", back_populates="sessions")
    events = relationship("BehaviorEvent", back_populates="session", cascade="all, delete-orphan")
    intents = relationship("IntentAssessment", back_populates="session")
    conversations = relationship("Conversation", back_populates="session")
    score_history = relationship("IntentScoreHistory", back_populates="session", cascade="all, delete-orphan")

class IntentScoreHistory(Base, TimestampMixin):
    __tablename__ = "intent_score_history"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("customer_sessions.session_id"), nullable=False, index=True)
    event_id = Column(String, nullable=True)
    previous_score = Column(Float, nullable=False, default=0.0)
    score_delta = Column(Float, nullable=False, default=0.0)
    new_score = Column(Float, nullable=False, default=0.0)
    signal = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    
    session = relationship("CustomerSession", back_populates="score_history")


class BehaviorEvent(Base, TimestampMixin):
    __tablename__ = "behavior_events"
    
    id = Column(String, primary_key=True, index=True) # UUID
    session_id = Column(String, ForeignKey("customer_sessions.session_id"), nullable=False)
    user_id = Column(String, nullable=True)
    event_type = Column(String, nullable=False, index=True)
    product_id = Column(String, nullable=True)
    category_id = Column(String, nullable=True)
    order_id = Column(String, nullable=True)
    event_metadata = Column(JSON, default={})
    
    session = relationship("CustomerSession", back_populates="events")

class IntentAssessment(Base, TimestampMixin):
    __tablename__ = "intent_assessments"
    
    id = Column(String, primary_key=True, index=True) # UUID
    session_id = Column(String, ForeignKey("customer_sessions.session_id"), nullable=False)
    intent_score = Column(Float, nullable=False)
    intent_category = Column(String, nullable=False) # e.g. HIGH_PURCHASE_INTENT
    confidence = Column(Float, nullable=False)
    signals = Column(JSON, default=[]) # Array of string signals
    recommended_action = Column(String, nullable=True)
    agent_output = Column(JSON, nullable=True) # Full structured output from Intent Agent
    
    
    session = relationship("CustomerSession", back_populates="intents")

class IntentAgentJob(Base, TimestampMixin):
    __tablename__ = "intent_agent_jobs"
    
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    session_id = Column(String, ForeignKey("customer_sessions.session_id"), nullable=False, unique=True, index=True)
    status = Column(String, nullable=False, default="QUEUED") # QUEUED, PROCESSING, COMPLETED, FAILED
    priority = Column(Integer, nullable=False, default=0)
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    error = Column(String, nullable=True)
    lease_until = Column(String, nullable=True)
    worker_id = Column(String, nullable=True)
    idempotency_key = Column(String, unique=True, nullable=True, index=True)
    
    session = relationship("CustomerSession")

class ExecutionTrace(Base, TimestampMixin):
    __tablename__ = "execution_traces"
    
    id = Column(String, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("customer_sessions.session_id"), nullable=False, index=True)
    request_id = Column(String, nullable=True, index=True)
    component_id = Column(String, nullable=False, index=True) # e.g. n_product_intelligence
    component_type = Column(String, nullable=False) # e.g. agent, engine
    status = Column(String, nullable=False) # RUNNING, SUCCESS, FAILED
    
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=True)
    duration_ms = Column(Float, nullable=True)
    
    inputs = Column(JSON, default={})
    outputs = Column(JSON, default={})
    events = Column(JSON, default=[]) # Array of {timestamp, event, description}
    tool_calls = Column(JSON, default=[]) # Array of {tool_name, function, args, start, end, duration, status, result, error}
    error_details = Column(JSON, nullable=True) # {error_type, message, stack_trace}
    
    session = relationship("CustomerSession")

class Conversation(Base, TimestampMixin):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True, index=True) # UUID
    session_id = Column(String, ForeignKey("customer_sessions.session_id"), nullable=False)
    channel = Column(String, nullable=False) # ELECTRON_CALL, WHATSAPP
    status = Column(String, nullable=False) # ACTIVE, COMPLETED, ABANDONED
    
    session = relationship("CustomerSession", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")

class ConversationMessage(Base, TimestampMixin):
    __tablename__ = "conversation_messages"
    
    id = Column(String, primary_key=True, index=True) # UUID
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    sender_type = Column(String, nullable=False) # USER, AGENT, SYSTEM
    content = Column(String, nullable=False)
    metadata_json = Column(JSON, default={})
    
    conversation = relationship("Conversation", back_populates="messages")

class CommerceAction(Base, TimestampMixin):
    __tablename__ = "commerce_actions"
    
    id = Column(String, primary_key=True, index=True) # UUID
    session_id = Column(String, nullable=False, index=True)
    action_type = Column(String, nullable=False) # ADD_TO_CART, UPDATE_CART
    product_id = Column(String, nullable=True)
    api_response = Column(JSON, default={})
    status = Column(String, nullable=False)

class AgentConfig(Base, TimestampMixin):
    __tablename__ = "agent_configs"
    
    id = Column(String, primary_key=True, index=True)
    agent_id = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    model_name = Column(String, nullable=False, default="gemini-3.6-flash")
    temperature = Column(Float, nullable=False, default=0.0)
    top_p = Column(Float, nullable=False, default=0.9)
    top_k = Column(Integer, nullable=False, default=40)
    max_output_tokens = Column(Integer, nullable=False, default=1024)
    system_prompt = Column(String, nullable=True)
    capabilities = Column(JSON, default={}) 
    context_memory_size = Column(Integer, nullable=False, default=10)
    fallback_behavior = Column(String, nullable=False, default="return_default")
    output_formatting = Column(String, nullable=False, default="markdown")
    processing_timeout_ms = Column(Integer, nullable=False, default=30000)

class OrchestratorJob(Base, TimestampMixin):
    __tablename__ = "orchestrator_jobs"
    
    id = Column(String, primary_key=True, index=True) # UUID
    session_id = Column(String, ForeignKey("customer_sessions.session_id"), nullable=False, index=True)
    status = Column(String, nullable=False, default="INTENT_RECEIVED")
    mock_customer_requirement = Column(JSON, nullable=True)
    product_recommendations = Column(JSON, nullable=True)
    commerce_actions = Column(JSON, nullable=True)
    error = Column(String, nullable=True)
    
    session = relationship("CustomerSession")
