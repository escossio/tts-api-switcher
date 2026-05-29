# tts-api-switcher

Aplicação web simples para converter texto em áudio usando múltiplos provedores de Text-to-Speech via API.

## O que é

MVP com:

- interface web simples em HTML, CSS e JavaScript puro;
- backend em FastAPI;
- provider `mock` local para testar o fluxo sem credenciais;
- estrutura preparada para OpenAI e Google TTS.

## Estrutura

- `app/main.py`: servidor FastAPI e rotas.
- `app/config.py`: leitura de configuração via `.env`.
- `app/providers/`: providers de TTS.
- `app/static/`: interface web.
- `app/generated/`: arquivos de áudio gerados.

## Instalação

```bash
cd ~/projetos/tts-api-switcher
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuração

Copie `.env.example` para `.env` e ajuste o necessário.

```bash
cp .env.example .env
```

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

## Execução

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8090
```

Acesse:

```text
http://127.0.0.1:8090
```

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

- defina `GOOGLE_TTS_ENABLED=true`;
- configure `GOOGLE_APPLICATION_CREDENTIALS`;
- defina `GOOGLE_TTS_VOICE` se quiser trocar a voz;
- instale a biblioteca do Google TTS no ambiente alvo.

## Arquitetura dos providers

Os providers seguem uma interface comum em `app/providers/base.py`.

- `mock`: gera WAV local sem dependências externas.
- `openai`: usa `client.audio.speech.create()` e salva MP3 em `app/generated/`.
- `google`: preparado para integração isolada com Google Cloud Text-to-Speech.

Isso mantém o backend simples e permite adicionar novos providers sem mexer na interface.

## Próximos passos

1. Autenticação.
2. Histórico de gerações.
3. Custos por provider.
4. Escolha avançada de voz.
5. Suporte a MP3 real.
6. Docker.
7. Deploy.
