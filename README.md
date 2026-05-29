# tts-api-switcher

Aplicação web simples para converter texto em áudio usando múltiplos provedores de Text-to-Speech via API.

## O que é

MVP com:

- interface web simples em HTML, CSS e JavaScript puro;
- backend em FastAPI;
- provider `mock` local para testar o fluxo sem credenciais;
- estrutura preparada para OpenAI e Google TTS.
- histórico local em SQLite para acompanhar as últimas gerações.

## Estrutura

- `app/main.py`: servidor FastAPI e rotas.
- `app/config.py`: leitura de configuração via `.env`.
- `app/providers/`: providers de TTS.
- `app/static/`: interface web.
- `app/generated/`: arquivos de áudio gerados.
- `app/data/tts_history.sqlite3`: histórico local em SQLite.

## Instalação

```bash
cd ~/projetos/tts-api-switcher
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuração

`.env.example` é a base para desenvolvimento local.

`.env.production.example` é a base para produção.

Copie um deles para `.env` e ajuste o necessário.

```bash
cp .env.example .env
```

O arquivo real `.env` não deve ser commitado.

Variáveis principais:

- `APP_HOST`: host da aplicação, padrão `127.0.0.1`.
- `APP_PORT`: porta da aplicação, padrão `8090`.
- `GENERATED_DIR`: diretório dos arquivos gerados.
- `OPENAI_API_KEY`: chave da OpenAI, quando for usar o provider.
- `OPENAI_TTS_MODEL`: modelo de TTS da OpenAI.
- `OPENAI_TTS_VOICE`: voz padrão da OpenAI.
- `OPENAI_TTS_FORMAT`: formato de saída da OpenAI, padrão `mp3`.
- `GOOGLE_TTS_ENABLED`: habilita o provider Google.
- `GOOGLE_APPLICATION_CREDENTIALS`: caminho para credenciais do Google.
- `GOOGLE_TTS_VOICE`: voz padrão do Google.

Em produção, `OPENAI_API_KEY` e a credencial do Google devem vir de secret ou arquivo seguro.

## Histórico local

A aplicação registra localmente as gerações de áudio em SQLite.

- banco: `app/data/tts_history.sqlite3`
- tabela: `generation_history`
- texto salvo no histórico: apenas uma prévia dos primeiros 300 caracteres

Endpoints:

- `GET /api/history?limit=20`
- `GET /api/history/{id}`
- `DELETE /api/history/{id}`
- `DELETE /api/history`

Observações:

- os arquivos gerados continuam em `app/generated/`;
- apagar o histórico não apaga o arquivo físico nesta etapa.

## Execução

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8090
```

Acesse:

```text
http://127.0.0.1:8090
```

## Docker

Crie o arquivo `.env` a partir do exemplo, se ainda não existir:

```bash
cp .env.example .env
```

Subir com build:

```bash
docker compose up --build
```

Subir em background:

```bash
docker compose up -d --build
```

Ver logs:

```bash
docker compose logs -f
```

Parar a aplicação:

```bash
docker compose down
```

Acesse:

```text
http://127.0.0.1:8090
```

Persistência:

- `./app/generated` guarda os áudios gerados.
- `./app/data` guarda o SQLite do histórico.

Google TTS no Docker:

- mantenha o JSON de credencial fora do repositório, por exemplo em `/srv/secrets/google-tts-service-account.json`;
- o `docker-compose.yml` monta `/srv/secrets` como leitura apenas;
- configure `GOOGLE_APPLICATION_CREDENTIALS=/srv/secrets/google-tts-service-account.json` no `.env`.

Aviso:

- nunca commite `.env`;
- nunca commite o JSON de credencial do Google.

## Operação mínima

```bash
docker compose up -d --build
docker compose ps
docker compose logs -f
curl http://127.0.0.1:8090/health
docker inspect --format='{{json .State.Health}}' tts-api-switcher
```

O endpoint `/health` pode ser usado por Docker, proxy reverso ou monitoramento.

## Backup simples

Para backup mínimo, preserve:

- `app/data/tts_history.sqlite3`
- `app/generated/`

Exemplo:

```bash
tar -czf tts-api-switcher-backup-$(date +%Y%m%d%H%M%S).tar.gz app/data app/generated
```

## Restore simples

1. Pare o container.
2. Restaure `app/data` e `app/generated`.
3. Suba o container novamente.

## Teste com provider mock

Use o provedor `mock` para validar o fluxo completo sem API externa.

```bash
curl -X POST http://127.0.0.1:8090/api/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text":"Teste de geração de áudio","provider":"mock","language":"pt-BR","voice":"","speed":1.0}'
```

O mock gera um WAV local simples com tom de teste, suficiente para validar:

- geração do arquivo;
- player HTML5;
- link de download.

## Futuro OpenAI

Para ativar o provider OpenAI:

- defina `OPENAI_API_KEY`;
- ajuste `OPENAI_TTS_MODEL` se quiser trocar o modelo;
- ajuste `OPENAI_TTS_VOICE` se quiser trocar a voz;
- ajuste `OPENAI_TTS_FORMAT=mp3` se quiser manter a saída em MP3;
- instale a dependência do SDK da OpenAI se for necessário no ambiente alvo.

Teste com OpenAI:

```bash
curl -X POST http://127.0.0.1:8090/api/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text":"Olá, este é um teste real de geração de voz usando OpenAI.","provider":"openai","language":"pt-BR","voice":"alloy","speed":1.0}'
```

## Futuro Google

Para ativar o provider Google:

1. Instale as dependências:

```bash
pip install -r requirements.txt
```

2. Crie uma service account no Google Cloud com acesso ao Text-to-Speech.

3. Baixe o JSON de credencial para um caminho local fora do Git, por exemplo:

```text
/srv/secrets/google-tts-service-account.json
```

4. Configure o `.env`:

```env
GOOGLE_TTS_ENABLED=true
GOOGLE_APPLICATION_CREDENTIALS=/srv/secrets/google-tts-service-account.json
GOOGLE_TTS_LANGUAGE_CODE=pt-BR
GOOGLE_TTS_VOICE=pt-BR-Neural2-B
GOOGLE_TTS_AUDIO_ENCODING=MP3
```

5. Rode a aplicação:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8090
```

Avisos:

- nunca commite o JSON de credencial;
- o caminho do JSON deve ficar só no `.env` local;
- a aplicação não expõe credenciais em nenhum endpoint.

Teste com Google:

```bash
curl -X POST http://127.0.0.1:8090/api/generate-audio \
  -H "Content-Type: application/json" \
  -d '{"text":"Olá, este é um teste real usando Google Text-to-Speech.","provider":"google","language":"pt-BR","voice":"pt-BR-Neural2-B","speed":1.0}'
```

## Arquitetura dos providers

Os providers seguem uma interface comum em `app/providers/base.py`.

- `mock`: gera WAV local sem dependências externas.
- `openai`: usa `client.audio.speech.create()` e salva MP3 em `app/generated/`.
- `google`: preparado para integração isolada com Google Cloud Text-to-Speech.

Isso mantém o backend simples e permite adicionar novos providers sem mexer na interface.

## Próximos passos

1. Implementar Google TTS real.
2. Adicionar opção de apagar arquivo físico junto com histórico.
3. Adicionar Docker.
4. Adicionar autenticação simples.
