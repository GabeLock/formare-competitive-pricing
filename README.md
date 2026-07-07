# formare-price-intelligence

Aplicacao local de inteligencia competitiva para a Formare Metais, focada em
precos publicos, cotacoes manuais, CMV e posicionamento comercial nos produtos:

- Rolinho galvalume
- Rolinho galvanizado zincado fosco
- Rolinho galvanizado zincado brilhante
- Telha termoacustica sanduiche trapezio
- Divisoria de gesso drywall
- Perfil montante drywall
- Perfil guia drywall

O projeto prioriza Grande BH e Minas Gerais. Benchmarks nacionais entram como
referencia, nao como concorrentes diretos.

## Regras eticas

- Nunca preencher ou enviar formulario de orcamento, contato ou WhatsApp.
- Respeitar `robots.txt` sempre.
- Nunca burlar CAPTCHA, login, paywall, 403 ou 429.
- Usar cooldown minimo de 3 a 5 segundos por dominio, inclusive em disparos manuais.
- Uma fonte quebrada gera log/status e nao derruba a rodada.
- Dado simulado e opt-in explicito via `--allow-simulated-fallback` e fica marcado como `simulated=true`, `estimated_price` e confianca baixa.
- Google Shopping fica fora da automacao. Use somente como consulta manual ou API compativel com os termos.

## Arquitetura

```text
app/                         Dashboard Streamlit e paginas
data/raw/                    Snapshots HTML locais, nao versionados
data/database/prices.db       SQLite versionavel
src/collectors/              Coletores eticos por fonte
src/config/                  products.yaml e competitors.yaml
src/database/                SQLAlchemy, schema e repositorio
src/processing/              Parser, normalizacao, conversao e hash de item
src/analytics/               Variacao, CMV, scoring e alertas
src/scheduler/               Orquestracao e APScheduler local
tests/                       Testes unitarios
```

## Instalar e rodar

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py --init-db
python run.py --collect
streamlit run app/dashboard.py
pytest
```

Comandos uteis:

```bash
python run.py --collect --source galvaminas
python run.py --collect --dry-run
python run.py --update-all
python run.py --collect --allow-simulated-fallback
```

## Concorrentes e tiers

Os concorrentes ficam em `src/config/competitors.yaml` com `tier`:

- `regional_direto`: Formare baseline, Perfil Telhas, Galvaminas, Telhas Barreiro, Suri Metais.
- `tecnico_referencia`: Acotel, Ananda Metais, Multiperfil.
- `benchmark_publico`: Telhas Online/Fenix Acos, Grupo Pizzinatto, Servicorte, Mercado Livre.

O Mercado Livre usa a API publica oficial:

```text
GET https://api.mercadolibre.com/sites/MLB/search?q={termo}
```

## Banco de dados

Tabelas principais:

- `competitors`
- `products`
- `monitored_urls`
- `price_observations`
- `formare_costs`
- `alerts`

Datas sao gravadas em UTC. O dashboard converte a exibicao para o contexto local
quando necessario.

## Cotacoes manuais

Fontes `quote_required` apenas confirmam que a pagina publica esta no ar. O
preco deve ser registrado manualmente no dashboard em **CMV e Comercial**.
Isso separa preco publico, preco cotado manualmente e preco simulado.

## Indicadores

`confidence_score` comeca em 100 e aplica penalidades:

- -40 se `collection_status != success`
- -25 se o preco veio de regex generica
- -15 se a unidade foi assumida por heuristica
- -15 se o match de produto foi fuzzy
- -10 se snapshot estiver desatualizado

`risco_comercial`:

```text
0.30 * gap_vs_menor_preco
+ 0.20 * tendencia_queda_7d
+ 0.15 * disponibilidade_concorrente_mais_barato
+ 0.15 * similaridade_tecnica_do_item
+ 0.10 * (100 - confidence_score)
+ 0.10 * peso_tier_concorrente
```

Classificacao: 0-25 Baixo, 26-50 Moderado, 51-75 Alto, 76-100 Critico.

## GitHub Actions

`.github/workflows/update_prices.yml` roda as 08:00 e 17:00 de Brasilia
(`0 11,20 * * *` UTC), aceita `workflow_dispatch`, usa `concurrency`, salva logs
como artefato e comita `data/database/prices.db` quando houver mudanca.

## Manutencao

Para adicionar fonte:

1. Cadastre produto em `src/config/products.yaml` se necessario.
2. Cadastre concorrente e URL em `src/config/competitors.yaml`.
3. Use `collection_method: quote_probe`, `html` ou `mercado_livre_api`.
4. Se houver parser especifico, crie um collector em `src/collectors/` e registre em `src/scheduler/run_collection.py`.

## Escalabilidade

Snapshots HTML nao vao para o Git. Se o SQLite crescer demais, exporte
observacoes antigas para CSV compactado em `data/processed/archive/` e mantenha
o banco quente enxuto. Para uso maior, migrar para Postgres, Turso ou Supabase.
