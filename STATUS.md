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
- Persistência de `app/generated` e `app/data` configurada.
- Execução local sem Docker preservada.
- Interface web básica funcional.
- O provider mock apenas gera áudio de teste local para validar o fluxo completo.
- Próximos passos:
  1. Autenticação simples.
  2. Tela de custos por provider.
  3. Comparação de vozes/providers.
  4. Opção para apagar arquivo físico junto com histórico.
  5. Publicação no GitHub.
