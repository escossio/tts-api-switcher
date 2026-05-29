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
- Próximos passos:
  1. Publicação no GitHub.
  2. Autenticação simples.
  3. Tela de custos por provider.
  4. Comparação de vozes/providers.
  5. Opção para apagar arquivo físico junto com histórico.
