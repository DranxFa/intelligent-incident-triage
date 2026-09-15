import argparse
import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto esté en sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.knowledge_service import parse_markdown_manuals, seed_knowledge_base


def main():
    parser = argparse.ArgumentParser(
        description="Script para poblar la tabla knowledge_manuals de PostgreSQL con pgvector."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Sobrescribe los manuales existentes si la tabla ya contiene datos.",
    )
    args = parser.parse_args()

    print("================================================================")
    print("  Poblador de Base de Conocimiento de TI (PostgreSQL + pgvector)")
    print("================================================================")

    manuals = parse_markdown_manuals()
    print(f"[+] Archivo Markdown leído correctamente. Total de soluciones: {len(manuals)}")
    for idx, m in enumerate(manuals, 1):
        print(f"    {idx}. [{m['categoria']}] {m['titulo']}")

    print("\n[+] Iniciando generación de embeddings y carga a PostgreSQL...")
    try:
        count = seed_knowledge_base(force=args.force)
        print(f"[OK] Proceso finalizado. Total de manuales en la base de datos: {count}")
    except Exception as exc:
        print(f"[ERROR] No se pudo conectar a la base de datos o falló el seed: {exc}")
        print("Asegúrate de que el contenedor de PostgreSQL esté iniciado con:")
        print("  docker compose up -d")
        sys.exit(1)


if __name__ == "__main__":
    main()
