from collections.abc import Generator

from uuid import UUID

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings


class Base(DeclarativeBase):
    pass


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "name" not in user_columns:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN name VARCHAR(120) NOT NULL DEFAULT ''"
            ))
    columns = {column["name"] for column in inspect(engine).get_columns("conversation_messages")}
    if "thread_id" not in columns:
        with engine.begin() as connection:
            connection.execute(text(
                "ALTER TABLE conversation_messages ADD COLUMN thread_id "
                + ("UUID" if engine.dialect.name == "postgresql" else "TEXT")
            ))
    thread_columns = {column["name"] for column in inspect(engine).get_columns("conversation_threads")}
    if "client_key" not in thread_columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE conversation_threads ADD COLUMN client_key VARCHAR(100)"))
    with engine.begin() as connection:
        connection.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_conversation_threads_client_key "
            "ON conversation_threads (owner_id, agent_id, client_key) "
            "WHERE client_key IS NOT NULL"
        ))


def set_tenant_context(session: Session, user_id: UUID) -> None:
    if engine.dialect.name == "postgresql":
        session.execute(
            text("SELECT set_config('app.user_id', :user_id, true)"),
            {"user_id": str(user_id)},
        )
