# Publicacao para o cliente

O dashboard e o coletor compartilham um PostgreSQL gerenciado. O GitHub Actions
executa somente a coleta; o Streamlit faz somente leitura e nunca dispara scraping.

## 1. Banco Supabase

1. Crie um projeto Supabase na regiao mais proxima da operacao.
2. Em **Connect**, copie a connection string do pooler (porta 6543) e acrescente
   `?sslmode=require` se necessario.
3. No terminal, defina `DATABASE_URL` e execute `python run.py --init-db` uma vez.
   Isso cria as tabelas e cadastra produtos e fontes.
4. Em GitHub > Settings > Secrets and variables > Actions, crie o segredo
   `DATABASE_URL` com a mesma connection string. Nunca use a chave anonima no
   coletor ou no dashboard.
5. Se a API publica do Mercado Livre responder HTTP 403, crie um aplicativo na
   plataforma de desenvolvedores do Mercado Livre e cadastre o token OAuth como
   `MERCADOLIVRE_ACCESS_TOKEN` nos GitHub Secrets. O dashboard nao recebe esse
   token: ele somente le o banco. Sem token valido, a fonte fica marcada como
   bloqueada e nao produz preco.

## 2. Coleta automatica

O workflow `.github/workflows/update_prices.yml` roda em `7,37 * * * *` UTC.
GitHub Actions e adequado para MVP, mas nao oferece SLA de inicio exatamente no
minuto programado. Para um SLA contratual, substitua-o por Cloud Scheduler +
Cloud Run Job, mantendo o mesmo `DATABASE_URL`.

## 3. Streamlit Community Cloud

1. Publique esta branch no GitHub e abra [share.streamlit.io](https://share.streamlit.io).
2. Selecione o repositorio `GabeLock/formare-competitive-pricing`, branch
   `codex/production-deploy-price-monitor` e arquivo `app/dashboard.py`.
3. Em **Advanced settings > Secrets**, informe:

```toml
DATABASE_URL = "postgresql://..."
FORMARE_ENVIRONMENT = "production"
FORMARE_DASHBOARD_PASSWORD = "senha-compartilhada-com-o-cliente"
FORMARE_ADMIN_PASSWORD = "senha-exclusiva-da-Formare"
```

4. Clique em Deploy. A plataforma exibira a URL final para ser enviada ao cliente.

O link nao pode ser criado pelo codigo: ele depende da autenticacao da conta
Streamlit e dos segredos do banco, que nao devem entrar no repositorio.

## Verificacao antes do envio

1. Execute manualmente o workflow **Update prices**.
2. Confirme uma execucao bem-sucedida e registros recentes no PostgreSQL.
3. Abra o link do Streamlit em janela anonima, valide a senha do cliente e confira
   o horario da ultima atualizacao.
4. Mantenha a senha administrativa apenas com a equipe Formare.
