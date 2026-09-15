import os
from dotenv import load_dotenv
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()


def get_llm() -> BaseChatModel:
    """
    Inicializa y devuelve el modelo LLM configurado (Gemini o Groq).
    Permite configuración vía variables de entorno:
    - LLM_PROVIDER: 'gemini' o 'groq'
    - GEMINI_API_KEY / GOOGLE_API_KEY
    - GROQ_API_KEY
    """
    provider = os.getenv("LLM_PROVIDER", "").lower()

    # Si no se especifica proveedor explícito, detectar por API keys presentes
    if not provider:
        if os.getenv("GROQ_API_KEY"):
            provider = "groq"
        elif os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
            provider = "gemini"
        else:
            # Proveedor por defecto sugerido
            provider = "gemini"

    if provider == "groq":
        from langchain_groq import ChatGroq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Se seleccionó el proveedor 'groq' pero la variable de entorno GROQ_API_KEY no está configurada."
            )
        model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        return ChatGroq(
            model=model_name,
            temperature=0,
            api_key=api_key,
        )

    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Se seleccionó el proveedor 'gemini' pero la variable de entorno GEMINI_API_KEY no está configurada."
            )
        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            google_api_key=api_key,
        )

    else:
        raise ValueError(
            f"Proveedor de LLM desconocido: '{provider}'. Opciones válidas: 'gemini' o 'groq'."
        )
