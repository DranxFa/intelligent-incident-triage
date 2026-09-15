import hashlib
import logging
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("incident_triage.embeddings")


def get_embedding(text: str) -> List[float]:
    """
    Genera un embedding vectorial de 768 dimensiones para el texto dado.
    Utiliza el SDK oficial de Google GenAI (gemini-embedding-001 con output_dimensionality=768)
    si GEMINI_API_KEY está configurada.
    Si no está configurada o hay error de red, utiliza un fallback determinista.
    """
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if api_key and api_key != "tu_clave_de_gemini_aqui":
        try:
            import google.genai as genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=768),
            )
            if response.embeddings and len(response.embeddings) > 0:
                vector = list(response.embeddings[0].values)
                if len(vector) == 768:
                    return vector
        except Exception as exc:
            logger.warning(
                f"No se pudo generar embedding con Google Gemini: {exc}. Usando fallback determinista de 768d."
            )

    # Fallback determinista de 768 dimensiones
    return _generate_fallback_vector(text, dimension=768)


def get_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """Genera embeddings para una lista de textos."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    if api_key and api_key != "tu_clave_de_gemini_aqui":
        try:
            import google.genai as genai
            from google.genai import types

            client = genai.Client(api_key=api_key)
            response = client.models.embed_content(
                model="gemini-embedding-001",
                contents=texts,
                config=types.EmbedContentConfig(output_dimensionality=768),
            )
            if response.embeddings:
                return [list(e.values) for e in response.embeddings]
        except Exception as exc:
            logger.warning(
                f"Falla en embed_content batch de Google Gemini: {exc}. Usando fallback."
            )

    return [_generate_fallback_vector(t, dimension=768) for t in texts]


def _generate_fallback_vector(text: str, dimension: int = 768) -> List[float]:
    """
    Genera un vector normalizado determinista de 768 dimensiones a partir del texto
    para garantizar que las operaciones vectoriales en pgvector funcionen en tests offline.
    """
    import math

    vector = []
    for i in range(dimension):
        h = hashlib.sha256(f"{text}:{i}".encode("utf-8")).hexdigest()
        val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
        vector.append(val)

    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]

    return vector
