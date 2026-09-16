import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from database import KnowledgeManual, get_db_context
from services.embeddings import get_embedding

logger = logging.getLogger("incident_triage.knowledge")

MANUALS_FILE_PATH = Path(__file__).resolve().parent.parent / "data" / "manuales_ti.md"


def parse_markdown_manuals(file_path: Path = MANUALS_FILE_PATH) -> List[Dict[str, str]]:
    """
    Parsea el archivo Markdown data/manuales_ti.md y extrae cada manual con
    su título, categoría y contenido paso a paso.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de manuales en {file_path}")

    text = file_path.read_text(encoding="utf-8")
    sections = text.split("---")

    manuals = []
    for section in sections:
        section = section.strip()
        if not section or not section.startswith("##"):
            continue

        lines = section.splitlines()
        titulo = lines[0].replace("##", "").strip()
        titulo = re.sub(r"^\d+\.\s*", "", titulo)

        categoria = "CONSULTA_OPERATIVA"
        contenido_lines = []
        is_content = False

        for line in lines[1:]:
            if line.startswith("**Categoría**:"):
                categoria = line.replace("**Categoría**:", "").strip()
            elif line.startswith("**Contenido**:"):
                is_content = True
            elif is_content:
                contenido_lines.append(line)

        contenido = "\n".join(contenido_lines).strip()
        if titulo and contenido:
            manuals.append(
                {
                    "titulo": titulo,
                    "categoria": categoria,
                    "contenido": contenido,
                }
            )

    return manuals


def seed_knowledge_base(force: bool = False) -> int:
    """
    Carga los manuales de data/manuales_ti.md a PostgreSQL generando sus embeddings vectoriales.
    Retorna el número de manuales insertados.
    """
    manuals_data = parse_markdown_manuals()
    logger.info(f"Parseados {len(manuals_data)} manuales desde {MANUALS_FILE_PATH}")

    inserted = 0
    with get_db_context() as db:
        existing_count = db.query(KnowledgeManual).count()
        if existing_count > 0 and not force:
            logger.info(f"La base de datos ya contiene {existing_count} manuales. Omitiendo seed.")
            return existing_count

        if force and existing_count > 0:
            db.query(KnowledgeManual).delete()
            db.commit()

        for item in manuals_data:
            text_to_embed = f"{item['titulo']}\n{item['categoria']}\n{item['contenido']}"
            embedding = get_embedding(text_to_embed)

            manual = KnowledgeManual(
                titulo=item["titulo"],
                categoria=item["categoria"],
                contenido=item["contenido"],
                vector_embedding=embedding,
            )
            db.add(manual)
            inserted += 1

        db.commit()

    logger.info(f"Se cargaron exitosamente {inserted} manuales en PostgreSQL con pgvector.")
    return inserted


def search_manuals_with_threshold(
    query_text: str,
    query_vector: Optional[List[float]] = None,
    max_distance: float = 0.38,
    limit: int = 2,
) -> List[str]:
    """
    Realiza una búsqueda semántica de manuales aplicando un umbral estricto de distancia coseno (<=>).
    - Distancia <= max_distance (ej. 0.55): Se considera coincidencia válida y se retornan los fragmentos.
    - Distancia > max_distance: Se considera que no hay manual relevante (retorna lista vacía []).
    """
    try:
        vector = query_vector or get_embedding(query_text)

        with get_db_context() as db:
            distance_expr = KnowledgeManual.vector_embedding.cosine_distance(vector)
            results = (
                db.query(KnowledgeManual, distance_expr.label("distance"))
                .order_by("distance")
                .limit(limit)
                .all()
            )

            if results:
                # Comprobar si el mejor resultado cumple con el umbral de similitud
                best_manual, best_distance = results[0]
                if best_distance > max_distance:
                    logger.info(
                        f"Mejor coincidencia ('{best_manual.titulo}') excede umbral de distancia: {best_distance:.4f} > {max_distance}. Fallback a soporte humano."
                    )
                    return []

                # Filtrar fragmentos que cumplan el umbral
                valid_fragments = [
                    f"Manual: {manual.titulo} [{manual.categoria}]\n{manual.contenido}"
                    for manual, dist in results
                    if dist <= max_distance
                ]
                return valid_fragments

    except Exception as exc:
        logger.warning(
            f"Consulta a pgvector no disponible ({exc}). Usando fallback de archivo Markdown."
        )

    # Fallback local usando el archivo Markdown con filtro de coincidencia de palabras
    try:
        manuals = parse_markdown_manuals()
        words = set(query_text.lower().split())
        scored = []
        for m in manuals:
            content_lower = f"{m['titulo']} {m['contenido']}".lower()
            score = sum(1 for w in words if len(w) > 3 and w in content_lower)
            if score > 0:
                scored.append((score, f"Manual: {m['titulo']} [{m['categoria']}]\n{m['contenido']}"))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [text for _, text in scored[:limit]]
    except Exception:
        return []


def search_manuals_vector(query_text: str, limit: int = 2) -> List[str]:
    """Compatibilidad hacia atrás con búsqueda sin umbral."""
    res = search_manuals_with_threshold(query_text, limit=limit, max_distance=1.0)
    return res if res else [
        "Manual de soporte técnico: Verifique conexiones y permisos.",
        "Manual de procedimientos de TI: Valide con su administrador de sistemas.",
    ]
