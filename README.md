# Formare Price Intelligence

## Dashboard publicado

Acesso do cliente: [formare-competitive-pricing.streamlit.app](https://formare-competitive-pricing.streamlit.app).
O acesso utiliza a senha de cliente configurada nos segredos do Streamlit.

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
PostgreSQL/Supabase            Historico central usado pelo coletor e dashboard
src/collectors/              Coletores eticos por fonte
src/config/                  products.yaml e competitors.yaml
src/database/                SQLAlchemy, schema e repositorio
src/processing/              Parser, normalizacao, conversao e hash de item
src/analytics/               Variacao, CMV, scoring e alertas
src/scheduler/               Orquestracao da coleta
tests/                       Testes unitarios
```

## Instalar e rodar localmente

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python run.py --init-db
streamlit run app/dashboard.py
python -m pytest -q tests
```

Sem `DATABASE_URL`, o projeto usa SQLite local apenas para desenvolvimento.
Para a operacao publicada, configure `DATABASE_URL` com PostgreSQL/Supabase;
veja [DEPLOYMENT.md](DEPLOYMENT.md).

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

`price_observations.customer_segment` separa o mercado em:

- `b2b_atacado`: referencia competitiva usada em minimo de mercado, media B2B e risco comercial.
- `b2c_varejo`: teto de mercado informativo. Aparece separado no dashboard e nunca entra na mesma media B2B.

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

`risco_comercial` usa somente precos `b2b_atacado` como referencia competitiva:

```text
0.30 * gap_vs_menor_preco
+ 0.20 * tendencia_queda_7d
+ 0.15 * disponibilidade_concorrente_mais_barato
+ 0.15 * similaridade_tecnica_do_item
+ 0.10 * (100 - confidence_score)
+ 0.10 * peso_tier_concorrente
```

Classificacao: 0-25 Baixo, 26-50 Moderado, 51-75 Alto, 76-100 Critico.

Precos `b2c_varejo` sao exibidos como teto varejo separado para leitura comercial,
sem compor o menor preco competitivo nem a media B2B.

## GitHub Actions e deploy

`.github/workflows/update_prices.yml` tem alvo de execucao a cada 30 minutos
(`7,37 * * * *`), aceita `workflow_dispatch`, usa `concurrency` e salva logs
como artefato. Ele grava diretamente no banco hospedado por meio do segredo
`DATABASE_URL`; nao comita dados de runtime no Git.

O dashboard Streamlit e a coleta usam o mesmo PostgreSQL. A configuracao de
Supabase, GitHub Actions, senha do cliente e Streamlit Community Cloud esta em
[DEPLOYMENT.md](DEPLOYMENT.md). GitHub Actions e adequado para MVP, mas nao
garante inicio exatamente no minuto programado.

## Manutencao

Para adicionar fonte:

1. Cadastre produto em `src/config/products.yaml` se necessario.
2. Cadastre concorrente e URL em `src/config/competitors.yaml`.
3. Use `collection_method: quote_probe`, `html` ou `mercado_livre_api`.
4. Se houver parser especifico, crie um collector em `src/collectors/` e registre em `src/scheduler/run_collection.py`.

## Estrutura e escalabilidade

O repositorio segue uma arquitetura em camadas: Streamlit em `app/`, dominio e
infraestrutura em `src/`, testes isolados em `tests/`, e analises exploratorias
em `notebooks/`. Os detalhes e convencoes estao em [ARCHITECTURE.md](ARCHITECTURE.md).

Snapshots HTML nao vao para o Git. Para SLA contratual de atualizacao, migre o
agendador para Cloud Scheduler + Cloud Run Job, mantendo o PostgreSQL gerenciado.
