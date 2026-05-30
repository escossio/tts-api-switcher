# STATUS

- MVP criado.
- Provider mock funcional.
- Provider OpenAI implementado.
- OpenAI depende de `OPENAI_API_KEY` no `.env`.
- Provider Google implementado.
- Google depende de `GOOGLE_TTS_ENABLED=true` e `GOOGLE_APPLICATION_CREDENTIALS`.
- Histórico local implementado com SQLite.
- Dockerfile criado.
- docker-compose.yml criado.
- Endpoint /health implementado.
- Docker healthcheck configurado.
- .env.production.example criado.
- GitHub Actions CI criado.
- CI valida app com provider mock sem chaves externas.
- Docker build validado no CI.
- Persistência de `app/generated` e `app/data` configurada.
- Execução local sem Docker preservada.
- Documentação de backup/restore simples adicionada.
- Interface web básica funcional.
- O provider mock apenas gera áudio de teste local para validar o fluxo completo.
- Diagnóstico de acesso LAN validado: o serviço estava parado quando o acesso remoto falhou; com `docker compose up -d --build`, a porta 8090 passou a responder em `0.0.0.0`.
- Suporte real adicionado para ElevenLabs, Azure Speech e Amazon Polly, mantendo mock, OpenAI, Google, histórico, Docker e CI.
- Front atualizado para listar e bloquear providers desabilitados com aviso contextual.
- Variáveis de ambiente novas documentadas em `.env.example`, `.env.production.example` e `README.md`.
- Seleção de vozes por provider implementada no backend e no painel web.
- ElevenLabs agora pode listar vozes reais da conta via `GET /api/providers/elevenlabs/voices`.
- Campo manual preservado como fallback quando a lista dinâmica falhar ou estiver vazia.
- Credenciais/validação atual:
  - Azure Speech: recurso `tts-api-switcher-speech` em `eastus`; geração de áudio validada com sucesso.
  - Google TTS: provider aparece habilitado, mas a geração falhou porque o arquivo de credencial configurado não foi encontrado no caminho esperado; depende de `GOOGLE_TTS_ENABLED=true` e do JSON em `/srv/secrets/google-tts-service-account.json`.
  - Google TTS: a credencial foi colocada em `/srv/secrets/google-tts-service-account.json` e carregou no container; a chamada de síntese agora falha com `SERVICE_DISABLED`, indicando que a API Cloud Text-to-Speech precisa ser habilitada no projeto Google.
- ElevenLabs: provider aparece habilitado, mas a listagem/geração falharam com `401`; depende de `ELEVENLABS_API_KEY` e, idealmente, `ELEVENLABS_VOICE_ID`.
- OpenAI: a chave antiga exposta no chat deve ser revogada e substituída por uma chave nova no `.env`; não registrar o valor.
- AWS Polly: implementação existe, mas as credenciais ficam para depois.
- Próximos passos:
  1. Busca dinâmica real de vozes Google/Azure/Polly.
  2. Comparação lado a lado de providers.
  3. Autenticação simples.
  4. Estimativa de custo por geração.

## Provider validation 2026-05-30

- mock: OK, gerou WAV de teste.
- azure: OK, gerou MP3 de teste.
- google: enabled, JSON presente em `/srv/secrets/google-tts-service-account.json`, mas a geração ainda falhou com erro genérico do provider.
- elevenlabs: enabled, listagem de vozes falhou com HTTP 401 e a geração segue sem validar.
- openai: enabled, geração falhou com erro genérico do provider.
- polly: disabled por falta de credenciais AWS no `.env`.
