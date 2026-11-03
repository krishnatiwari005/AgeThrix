from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.v1.auth import current_user
from app.database.session import get_db
from app.models.agents import Agent
from app.models.auth import EncryptedApiCredential, User
from app.models.builds import AgentConfiguration
from app.models.conversations import ConversationMessage, ConversationThread
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationMessageResponse,
    ConversationThreadResponse,
)
from app.services.groq_client import GroqProviderError, create_groq_client

router = APIRouter(prefix="/api/v1/agents", tags=["chat"])


def get_owned_agent(agent_id: UUID, user: User, db: Session) -> Agent:
    agent = db.scalar(select(Agent).where(Agent.id == agent_id, Agent.owner_id == user.id))
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.get("/{agent_id}/messages", response_model=list[ConversationMessageResponse])
def list_messages(
    agent_id: UUID,
    thread_id: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[ConversationMessageResponse]:
    get_owned_agent(agent_id, user, db)
    messages = db.scalars(
        select(ConversationMessage)
        .where(
            ConversationMessage.owner_id == user.id,
            ConversationMessage.agent_id == agent_id,
            ConversationMessage.thread_id == thread_id,
        )
        .order_by(ConversationMessage.created_at.asc())
    ).all()
    return [ConversationMessageResponse.model_validate(message, from_attributes=True) for message in messages]


@router.get("/{agent_id}/threads", response_model=list[ConversationThreadResponse])
def list_threads(
    agent_id: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> list[ConversationThreadResponse]:
    get_owned_agent(agent_id, user, db)
    has_threads = db.scalar(
        select(ConversationThread.id).where(
            ConversationThread.owner_id == user.id,
            ConversationThread.agent_id == agent_id,
        )
    )
    legacy_message = db.scalar(
        select(ConversationMessage.id).where(
            ConversationMessage.owner_id == user.id,
            ConversationMessage.agent_id == agent_id,
            ConversationMessage.thread_id.is_(None),
        )
    )
    if has_threads is None and legacy_message is not None:
        thread = ConversationThread(
            owner_id=user.id,
            agent_id=agent_id,
            title="Previous conversation",
        )
        db.add(thread)
        db.flush()
        db.query(ConversationMessage).filter(
            ConversationMessage.owner_id == user.id,
            ConversationMessage.agent_id == agent_id,
            ConversationMessage.thread_id.is_(None),
        ).update({"thread_id": thread.id}, synchronize_session=False)
        db.commit()
    threads = db.scalars(
        select(ConversationThread)
        .where(
            ConversationThread.owner_id == user.id,
            ConversationThread.agent_id == agent_id,
        )
        .order_by(ConversationThread.updated_at.desc())
    ).all()
    if not threads:
        thread = ConversationThread(owner_id=user.id, agent_id=agent_id)
        db.add(thread)
        db.commit()
        db.refresh(thread)
        threads = [thread]
    return [ConversationThreadResponse.model_validate(thread, from_attributes=True) for thread in threads]


@router.post("/{agent_id}/threads", response_model=ConversationThreadResponse, status_code=201)
def create_thread(
    agent_id: UUID,
    client_key: str | None = Query(default=None, max_length=100),
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ConversationThreadResponse:
    get_owned_agent(agent_id, user, db)
    if client_key:
        existing = db.scalar(
            select(ConversationThread).where(
                ConversationThread.owner_id == user.id,
                ConversationThread.agent_id == agent_id,
                ConversationThread.client_key == client_key,
            )
        )
        if existing is not None:
            return ConversationThreadResponse.model_validate(existing, from_attributes=True)
    thread = ConversationThread(owner_id=user.id, agent_id=agent_id, client_key=client_key)
    db.add(thread)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if not client_key:
            raise
        thread = db.scalar(
            select(ConversationThread).where(
                ConversationThread.owner_id == user.id,
                ConversationThread.agent_id == agent_id,
                ConversationThread.client_key == client_key,
            )
        )
        if thread is None:
            raise HTTPException(status_code=409, detail="Unable to create conversation") from None
    db.refresh(thread)
    return ConversationThreadResponse.model_validate(thread, from_attributes=True)


@router.delete("/{agent_id}/threads/{thread_id}", status_code=204)
def delete_thread(
    agent_id: UUID,
    thread_id: UUID,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> None:
    get_owned_agent(agent_id, user, db)
    thread = db.scalar(
        select(ConversationThread).where(
            ConversationThread.id == thread_id,
            ConversationThread.owner_id == user.id,
            ConversationThread.agent_id == agent_id,
        )
    )
    if thread is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(thread)
    db.commit()


@router.post("/{agent_id}/chat", response_model=ChatResponse)
def chat(
    agent_id: UUID,
    payload: ChatRequest,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
) -> ChatResponse:
    agent = get_owned_agent(agent_id, user, db)
    if agent.status != "active":
        raise HTTPException(status_code=409, detail="Agent is not active")

    configuration = db.scalar(
        select(AgentConfiguration).where(
            AgentConfiguration.agent_id == agent.id,
            AgentConfiguration.is_current.is_(True),
        )
    )
    credential = db.scalar(
        select(EncryptedApiCredential).where(
            EncryptedApiCredential.owner_id == user.id,
            EncryptedApiCredential.provider == "groq",
            EncryptedApiCredential.status.in_(("stored", "valid")),
        )
    )
    if configuration is None:
        raise HTTPException(status_code=409, detail="Agent configuration is missing")
    if credential is None:
        raise HTTPException(status_code=409, detail="Connect a valid Groq credential")

    spec = configuration.spec
    preferences = spec.get("model_preferences", {})
    preferred_models = preferences.get("preferred_models", []) if isinstance(preferences, dict) else []
    model = preferred_models[0] if preferred_models else "openai/gpt-oss-20b"
    thread_id = payload.thread_id
    thread = None
    if thread_id is not None:
        thread = db.scalar(
            select(ConversationThread).where(
                ConversationThread.id == thread_id,
                ConversationThread.owner_id == user.id,
                ConversationThread.agent_id == agent.id,
            )
        )
        if thread is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        thread = ConversationThread(
            owner_id=user.id,
            agent_id=agent.id,
            title=payload.message[:60],
        )
        db.add(thread)
        db.flush()
    history = db.scalars(
        select(ConversationMessage)
        .where(
            ConversationMessage.owner_id == user.id,
            ConversationMessage.agent_id == agent.id,
            ConversationMessage.thread_id == thread.id,
        )
        .order_by(ConversationMessage.created_at.asc())
        .limit(40)
    ).all()
    user_message = ConversationMessage(
        owner_id=user.id,
        agent_id=agent.id,
        thread_id=thread.id,
        role="user",
        content=payload.message,
    )
    db.add(user_message)
    try:
        client = create_groq_client(credential)
        response = client.complete(
            model=str(model),
            messages=[{"role": "system", "content": str(spec.get("system_prompt", "Be helpful and concise."))}]
            + [{"role": "user" if item.role == "user" else "assistant", "content": item.content} for item in history]
            + [{"role": "user", "content": payload.message}],
            max_tokens=1200,
        )
    except GroqProviderError as exc:
        db.rollback()
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    db.add(
        ConversationMessage(
            owner_id=user.id,
            agent_id=agent.id,
            thread_id=thread.id,
            role="agent",
            content=response,
        )
    )
    thread.updated_at = datetime.now(UTC)
    if thread.title == "New conversation":
        thread.title = payload.message[:60]
    db.commit()
    return ChatResponse(message=response)
