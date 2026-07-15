# Arquitetura e convencoes

O repositorio usa uma estrutura em camadas, mais segura para evolucao do que um
unico `app.py` com coleta, regra comercial e interface misturadas.

```text
app/                 interface Streamlit e paginas
src/collectors/      adaptadores de fontes externas
src/processing/      limpeza, parsing, matching e normalizacao
src/analytics/       regras e indicadores comerciais
src/database/        modelos, conexao e repositorios
src/scheduler/       orquestracao da coleta
src/config/          catalogo canonico de produtos e fontes
tests/               testes unitarios isolados de sites externos
data/raw/            snapshots locais, ignorados pelo Git
data/processed/      saidas locais e temporarias
notebooks/           analises exploratorias, fora do caminho de producao
```

As dependencias seguem `requirements.txt`; a configuracao de ferramentas fica em
`pyproject.toml`; segredos ficam apenas no ambiente ou no gerenciador de secrets.
O ponto de entrada da aplicacao continua `app/dashboard.py` para preservar o
roteamento multipagina nativo do Streamlit (`app/pages/`).

Fluxo de producao: GitHub Actions -> coletores -> PostgreSQL/Supabase ->
Streamlit. Nenhuma pagina do dashboard executa scraping.
