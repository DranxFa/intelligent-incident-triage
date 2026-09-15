import os
from contextlib import contextmanager
from typing import Generator
from dotenv import load_dotenv
from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://admin:password123@localhost:5432/triage_db",
)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 2},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class KnowledgeManual(Base):
    """Tabla para almacenar los manuales de la base de conocimiento con embeddings pgvector."""

    __tablename__ = "knowledge_manuals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(255), nullable=False)
    categoria = Column(String(100), nullable=False)
    contenido = Column(Text, nullable=False)
    vector_embedding = Column(Vector(768), nullable=True)


class Incident(Base):
    """
    Tabla de Incidentes para analítica en Power BI y gestión operativa.
    Contiene campos de negocio (prioridad, sla, categoria, estado) y técnicos.
    """

    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    usuario = Column(String(100), nullable=False)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    prioridad = Column(String(10), nullable=False)
    sla_horas = Column(Integer, nullable=False)
    categoria = Column(String(100), nullable=False)
    estado = Column(String(50), nullable=False, default="ABIERTO")
    tiempo_resolucion = Column(Integer, nullable=True)
    solucion_sugerida = Column(Text, nullable=True)
    vector_embedding = Column(Vector(768), nullable=True)

    states = relationship(
        "IncidentStateRecord",
        back_populates="incident",
        cascade="all, delete-orphan",
    )


class IncidentStateRecord(Base):
    """
    Tabla para almacenar el diccionario tipado completo del estado de LangGraph
    asociado a un incidente específico.
    """

    __tablename__ = "incident_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(
        Integer, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    texto_original = Column(JSON, nullable=False)
    triage_data = Column(JSON, nullable=False)
    alert_sent = Column(Boolean, nullable=False, default=False)
    rag_context = Column(JSON, nullable=True)
    final_response = Column(Text, nullable=True)
    error = Column(Text, nullable=True)

    incident = relationship("Incident", back_populates="states")


def get_db() -> Generator[Session, None, None]:
    """Generador de sesiones de base de datos para FastAPI o scripts."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """Context manager para operaciones síncronas de base de datos."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
