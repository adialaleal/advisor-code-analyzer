#!/usr/bin/env python3
"""
Script para inicializar o banco de dados com as tabelas necessárias.
Execute este script antes de rodar a aplicação pela primeira vez.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar os módulos da aplicação
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from app.models.database import Base, engine
from app.config import get_settings


def init_database():
    """Cria todas as tabelas no banco de dados."""
    print("Inicializando banco de dados...")
    
    # Verifica se as variáveis de ambiente estão configuradas
    settings = get_settings()
    print(f"Usando banco: {settings.database_url}")
    
    try:
        # Cria todas as tabelas definidas nos modelos
        Base.metadata.create_all(bind=engine)
        print("✅ Tabelas criadas com sucesso!")
        
        # Lista as tabelas criadas
        inspector = engine.dialect.inspector(engine)
        tables = inspector.get_table_names()
        print(f"Tabelas criadas: {', '.join(tables)}")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        sys.exit(1)


if __name__ == "__main__":
    init_database()
