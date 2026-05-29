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
- Próximos passos:
  1. Publicação no GitHub.
  2. Autenticação simples.
  3. Tela de custos por provider.
  4. Comparação de vozes/providers.
  5. Opção para apagar arquivo físico junto com histórico.
