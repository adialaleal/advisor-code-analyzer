# Advisor Code Analyzer Agent

Agente FastAPI que analisa trechos de código Python e sugere melhorias com base em boas práticas, persistindo histórico das análises em PostgreSQL, cacheando resultados em Redis e pronto para ser orquestrado via CrewAI.

## Sumário
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Configuração](#configuração)
- [Execução](#execução)
- [Endpoints](#endpoints)
- [Base de Dados](#base-de-dados)
- [Integração CrewAI](#integração-crewai)
- [Escalabilidade e Observabilidade](#escalabilidade-e-observabilidade)
- [Testes manuais sugeridos](#testes-manuais-sugeridos)

## Arquitetura
```
app/
├── api/                 # Camada HTTP (routers, deps)
├── config.py            # Configurações via Pydantic Settings
├── crewai_integration/  # Abstração de LLM e agente CrewAI
├── main.py              # Factory FastAPI
├── models/              # ORM + schemas Pydantic
└── services/            # Regras de negócio (analisador, cache, DB)
scripts/
└── init_db.sql          # Criação e índices da tabela analysis_history
```

Principais componentes:
- **CodeAnalyzer** (`app/services/code_analyzer.py`): usa `ast` para aplicar regras como importações/variáveis não utilizadas, complexidade ciclomática, funções longas, docstrings e convenções PEP 8.
- **AnalysisHistoryService** (`app/services/database_service.py`): persiste resultados em PostgreSQL usando SQLAlchemy.
- **CacheService** (`app/services/cache_service.py`): tenta Redis; se indisponível, faz fallback para cache em memória com TTL.
- **ModelProviderFactory** (`app/crewai_integration/model_provider.py`): abstrai provedores de LLM (OpenAI, Gemini, Anthropic, Azure OpenAI) permitindo alternância configurável.
- **AdvisorCrewIntegration** (`app/crewai_integration/agent.py`): exemplo de como expor o agente para um workflow CrewAI, incluindo tool que reutiliza o analisador.

## Pré-requisitos
- Python 3.11+
- PostgreSQL (ou container existente)
- Docker (para subir Redis via `docker-compose`)

## Configuração
1. Crie e ajuste o arquivo `.env` a partir do exemplo:
   ```bash
   cp .env.example .env
   ```
   - `DATABASE_URL`: string SQLAlchemy para seu PostgreSQL.
   - `REDIS_URL`: instância local ou remota do Redis.
   - `MODEL_PROVIDER`: `openai`, `gemini`, `anthropic` ou `azure_openai`.
   - `CREWAI_API_KEY`: chave reutilizada pelo provedor escolhido (considere variáveis específicas conforme docs oficiais da CrewAI [link](https://docs.crewai.com)).
   - Opcional: `AZURE_OPENAI_ENDPOINT` e `AZURE_OPENAI_DEPLOYMENT` para uso no Azure.

2. Instale as dependências Python (idealmente em um ambiente virtual):
   ```bash
   pip install -r requirements.txt
   ```

3. Suba o Redis localmente:
   ```bash
   docker-compose up -d
   ```

4. Execute o script de criação da tabela (ajuste host/porta se necessário):
   ```bash
   psql "$DATABASE_URL" -f scripts/init_db.sql
   ```

## Execução
Inicie a API com Uvicorn:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

A aplicação expõe os endpoints em `http://localhost:8000/api/v1`.

## Testes
- Guia completo: consulte `docs/testing.md` para pré-requisitos, exemplos de execução do `pytest` e roteiros de testes manuais (curl/Postman).
- Execução rápida: `python3 -m pytest` valida regras do analisador, serviço de cache, camada de persistência e endpoints principais.

## Endpoints
### `POST /api/v1/analyze-code`
Analisa código Python usando análise estática (AST). Retorna sugestões técnicas baseadas em regras pré-definidas.

**Corpo:**
```json
{
  "code": "def foo():\n    print('hello')\n",
  "language_version": "3.11"
}
```

**Resposta:**
```json
{
  "code_hash": "...sha256...",
  "suggestions": [
    {
      "rule_id": "print_statement",
      "message": "Considere utilizar logging em vez de print para saída em produção.",
      "severity": "info",
      "line": 2,
      "column": 4,
      "metadata": {}
    }
  ],
  "analysis_time_ms": 8,
  "cached": false
}
```

- Resultados repetidos são retornados do cache Redis (campo `cached` = `true`).
- Toda análise é registrada em `analysis_history`.

### `POST /api/v1/analyze-code-llm` 🆕
Analisa código Python usando CrewAI com LLM para gerar relatório priorizado e contextualizado. Simula a integração do agente com a plataforma CrewAI conforme descrito no desafio técnico.

**Corpo:**
```json
{
  "code": "def foo():\n    print('hello')\n    return 1",
  "language_version": "3.11"
}
```

**Resposta:**
```json
{
  "code_hash": "...sha256...",
  "raw_suggestions": [
    {
      "rule_id": "missing_docstring",
      "message": "Função 'foo' deveria conter docstring.",
      "severity": "info",
      "line": 1,
      "column": null,
      "metadata": {}
    },
    {
      "rule_id": "print_statement",
      "message": "Considere utilizar logging em vez de print para saída em produção.",
      "severity": "info",
      "line": 2,
      "column": 4,
      "metadata": {}
    }
  ],
  "prioritized_report": "Relatório do LLM priorizando e contextualizando as sugestões...",
  "model_used": "gemini",
  "analysis_time_ms": 1250,
  "cached": false
}
```

**Como Funciona:**
1. O código é analisado pelo `CodeAnalyzer` (análise estática).
2. As sugestões são enviadas para o LLM (Gemini, GPT, Claude, etc.) via CrewAI.
3. O LLM prioriza as sugestões, adiciona contexto e justificativas.
4. Retorna tanto as sugestões brutas quanto o relatório gerado pelo LLM.

**Requisitos:**
- `CREWAI_API_KEY` configurado no `.env`.
- `MODEL_PROVIDER` definido (`openai`, `gemini`, `anthropic`, ou `azure_openai`).

**⚠️ Nota:** A integração com CrewAI/LLM requer configuração adicional conforme documentação oficial do CrewAI. O endpoint `/api/v1/analyze-code` (análise estática) funciona sem dependências adicionais de LLM.

### `GET /api/v1/health`
Retorna status das dependências (`database`, `cache`, `model_provider`).

## Base de Dados
Tabela `analysis_history`:
- `id` (UUID, default `gen_random_uuid()`)
- `code_hash` (hash SHA-256 do snippet)
- `code_snippet` (texto bruto, opcional)
- `suggestions` (JSONB com lista de recomendações)
- `analysis_time_ms`, `language_version`
- `created_at` (`TIMESTAMPTZ`, default `NOW()`)

Índices:
- BTREE em `created_at`
- BTREE em `code_hash`
- GIN em `suggestions`

Recomendações adicionais documentadas:
- Particionamento por faixa de datas para alto volume.
- Ajuste de connection pooling (`pool_size`, `max_overflow`).
- Extensão `pgcrypto` habilitada pelo script para gerar UUID.

## Integração CrewAI

### Visão Geral da Arquitetura

Este agente foi desenvolvido para ser orquestrado pela plataforma **CrewAI** conforme especificado no desafio técnico. A arquitetura implementa duas camadas:

1. **Análise Estática** (`CodeAnalyzer`): Usa `ast.parse()` para aplicar regras pré-definidas
2. **Análise com LLM** (`AdvisorCrewIntegration`): Usa CrewAI para priorizar e contextualizar as sugestões

### Arquitetura de Integração

```
Usuario → API Endpoint → CrewAI Workflow
                          ↓
                    CodeAnalyzer (Tool)
                          ↓
                    LLM (Gemini/GPT/Claude)
                          ↓
                    Relatório Priorizado
```

### Como Funciona

**Endpoint com LLM (`/api/v1/analyze-code-llm`):**
- O código é primeiro analisado pelo `CodeAnalyzer` (análise estática)
- As sugestões são enviadas para o LLM via CrewAI
- O LLM prioriza as sugestões, adiciona contexto e justificativas
- Retorna tanto as sugestões brutas quanto o relatório gerado pelo LLM

**Tool CrewAI (`analyze_python_code`):**
- `CodeAnalyzer` é exposto como uma tool do CrewAI
- Pode ser reutilizado em outros workflows CrewAI
- Mantém consistência com a API REST

### Configuração

1. Selecione o provedor via `MODEL_PROVIDER` (`openai`, `gemini`, `anthropic`, ou `azure_openai`)
2. Defina `CREWAI_API_KEY` no `.env`
3. Utilize `AdvisorCrewIntegration` para criar o agente:
   ```python
   from app.config import get_settings
   from app.crewai_integration.agent import AdvisorCrewIntegration
   from app.services.code_analyzer import CodeAnalyzer

   settings = get_settings()
   integration = AdvisorCrewIntegration(settings, CodeAnalyzer())
   agent = integration.build_agent()
   workflow = integration.build_sample_workflow()
   crew = workflow["crew"]
   result = crew.kickoff(inputs={"code_snippet": "def foo():\n    print('hi')"})
   ```

### Benefícios da Integração

✅ **Análise Híbrida**: Combina análise estática precisa com contextualização inteligente do LLM
✅ **Priorização Inteligente**: O LLM identifica quais problemas são mais críticos
✅ **Contexto Adicionado**: Explica o "porquê" de cada sugestão
✅ **Flexibilidade**: Pode ser usado como API REST ou como tool no CrewAI
✅ **Escalabilidade**: Fácil adicionar novos provedores de LLM via `ModelProviderFactory`

### Documentação Adicional

Consulte a documentação oficial da CrewAI para conectar triggers e flows empresariais: [CrewAI Docs](https://docs.crewai.com)

## Escalabilidade e Observabilidade
- **Cache**: Redis com TTL de 1h. Fallback in-memory garante disponibilidade local.
- **Filas**: Utilize RabbitMQ ou Redis Streams para enviar análises volumosas a workers dedicados (ex.: Celery, RQ). O README inclui passos para evolução futura.
- **Horizontal Scaling**: API stateless; basta replicar instâncias atrás de um load balancer. Configure sticky sessions apenas se necessário.
- **Banco de Dados**: Indexação em `code_hash` e particionamento temporal reduz leituras pesadas; considerar compressão do campo `code_snippet` para históricos antigos.
- **Observabilidade**: Healthcheck consolidado, logging estruturado (ajustável via `LOG_LEVEL`), espaço reservado para métricas em `main.py` (lifespan). Integrar com Prometheus/OpenTelemetry em etapas posteriores.

## Testes manuais sugeridos
1. **Happy path**: enviar snippet válido e verificar gravação na tabela.
2. **Cache hit**: repetir o mesmo snippet e checar `cached=true`.
3. **Erro de sintaxe**: garantir que mensagens de erro sejam retornadas.
4. **Healthcheck**: desligar Redis e verificar que o endpoint indica `cache=fallback`.
5. **CrewAI**: executar `build_sample_workflow()` e validar chamadas da tool.

---

> Referência de documentação: CrewAI Docs em [docs.crewai.com](https://docs.crewai.com)
