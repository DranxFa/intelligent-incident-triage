-- Habilitar extensión pgvector para búsquedas semánticas
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Tabla de Base de Conocimiento de Manuales de TI
CREATE TABLE IF NOT EXISTS knowledge_manuals (
    id SERIAL PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    contenido TEXT NOT NULL,
    vector_embedding vector(768)
);

-- Índice HNSW para acelerar búsquedas por distancia coseno
CREATE INDEX IF NOT EXISTS idx_knowledge_manuals_embedding 
ON knowledge_manuals USING hnsw (vector_embedding vector_cosine_ops);

-- 2. Tabla Operativa y Técnica de Incidentes (Diseñada para Power BI y Reportería)
CREATE TABLE IF NOT EXISTS incidents (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    usuario VARCHAR(100) NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT NOT NULL,
    prioridad VARCHAR(10) NOT NULL,
    sla_horas INT NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    estado VARCHAR(50) NOT NULL DEFAULT 'ABIERTO',
    tiempo_resolucion INT DEFAULT NULL,
    solucion_sugerida TEXT DEFAULT NULL,
    vector_embedding vector(768) DEFAULT NULL
);

-- Índices para optimizar filtros en Power BI
CREATE INDEX IF NOT EXISTS idx_incidents_prioridad ON incidents(prioridad);
CREATE INDEX IF NOT EXISTS idx_incidents_categoria ON incidents(categoria);
CREATE INDEX IF NOT EXISTS idx_incidents_estado ON incidents(estado);
CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);

-- 3. Tabla para Almacenar el Estado Completo de LangGraph
CREATE TABLE IF NOT EXISTS incident_states (
    id SERIAL PRIMARY KEY,
    incident_id INT NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    texto_original JSONB NOT NULL,
    triage_data JSONB NOT NULL,
    alert_sent BOOLEAN NOT NULL DEFAULT FALSE,
    rag_context JSONB DEFAULT NULL,
    final_response TEXT DEFAULT NULL,
    error TEXT DEFAULT NULL
);

CREATE INDEX IF NOT EXISTS idx_incident_states_incident_id ON incident_states(incident_id);
