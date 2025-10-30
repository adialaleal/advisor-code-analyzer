# Guia de Testes

Este documento descreve como validar a aplicação Advisor Code Analyzer em diferentes camadas — desde testes automatizados com `pytest` até verificações manuais dos endpoints FastAPI.

## Pré-requisitos

- Python 3.11 ou superior (o projeto é validado em Python 3.13).
- Dependências instaladas via `pip install -r requirements.txt`.
- Variáveis de ambiente mínimas:
  - `DATABASE_URL` (pode usar SQLite, ex.: `sqlite+pysqlite:///./dev.db`).
  - `REDIS_URL` (ex.: `redis://localhost:6379/0`).
- Opcional: Docker para subir Redis com `docker-compose up -d`.

## Configuração do Ambiente

1. Crie e configure o arquivo `.env` conforme descrito no `README.md`.
2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Inicialize serviços externos se necessário:
   - Redis: `docker-compose up -d`
   - PostgreSQL: aplique `scripts/init_db.sql` se for usar o banco real.

## Testes Automatizados (pytest)

Os testes residem na pasta `tests/` e cobrem:

- **Unidade**: regras do `CodeAnalyzer`, cache in-memory/Redis de fallback e camada de persistência (`AnalysisHistoryService`).
- **Integração leve**: endpoints `/api/v1/analyze-code` e `/api/v1/health` com FastAPI `TestClient`, usando banco SQLite em memória e cache em memória.

Execute toda a suíte:

```bash
python3 -m pytest
```

Saída esperada (resumida):

```
============================= test session starts ==============================
platform darwin -- Python 3.13.5, pytest-8.4.1
collected 8 items

tests/test_api.py ...
tests/test_cache_service.py ..
tests/test_code_analyzer.py ..
tests/test_database_service.py .

======================== 8 passed, 6 warnings in 0.03s =========================
```

### Tratamento de Warnings

- **Pydantic**: avisos sobre `Config` podem ser ignorados por ora; acompanhe a migração para `ConfigDict`.
- **`datetime.utcnow()`**: o fallback de cache usa UTC naive. Esta é uma decisão consciente; ao migrar para `datetime.UTC`, atualize os testes correspondentes.

Para ocultar warnings durante o desenvolvimento:

```bash
python3 -m pytest -W ignore::DeprecationWarning
```

### Executando subconjuntos

- Somente testes de API: `python3 -m pytest tests/test_api.py`
- Rodar com verbose: `python3 -m pytest -vv`

## Testes Manuais de API

Com a aplicação em execução (`uvicorn app.main:app --reload`), valide fluxos principais:

### 1. Análise de Código (happy path)

```bash
curl -X POST http://localhost:8000/api/v1/analyze-code \
  -H "Content-Type: application/json" \
  -d '{
        "code": "def foo():\n    return 1\n",
        "language_version": "3.11"
      }'
```

Resposta esperada:

```json
{
  "code_hash": "<sha256>",
  "suggestions": [],
  "analysis_time_ms": 3,
  "cached": false
}
```

Reenvie o mesmo payload e verifique `"cached": true` (resultado veio do Redis/fallback).

### 2. Erro de Sintaxe

```bash
curl -X POST http://localhost:8000/api/v1/analyze-code \
  -H "Content-Type: application/json" \
  -d '{"code": "def broken(:\n    pass"}'
```

Deve retornar sugestão com `rule_id` igual a `syntax_error` e `severity` = `error`.

### 3. Health Check

```bash
curl http://localhost:8000/api/v1/health
```

Se o Redis real estiver indisponível, o campo `cache` exibirá `fallback`, confirmando que o in-memory cache está ativo.

## Boas Práticas

- Sempre execute os testes automatizados antes de abrir pull requests.
- Em alterações sensíveis ao desempenho, monitore o campo `analysis_time_ms` nas respostas.
- Adapte os testes para bancos externos (PostgreSQL/Redis) configurando variáveis de ambiente e removendo overrides em `tests/conftest.py` se necessário.
- Considere adicionar testes de carga ou linting futuro usando ferramentas como `locust` ou `ruff`.

## Recursos Relacionados

- `README.md` — visão geral e configuração inicial.
- `scripts/init_db.sql` — definição do schema da tabela `analysis_history`.
- `tests/conftest.py` — fixtures e overrides utilizados nos testes.

