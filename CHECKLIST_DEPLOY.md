# ✅ CHECKLIST DE DEPLOY - QUINTOU BACKEND v2.0

Use este checklist para garantir que todas as correções foram aplicadas e o sistema está pronto para produção.

---

## 📋 PRÉ-DEPLOY

### ✅ Verificação de Correções

- [ ] Executar `python verify_fixes.py`
- [ ] Resultado: 8/8 verificações passadas (100%)
- [ ] Sem erros no script de verificação

### ✅ Código

- [ ] Sistema de pagamento REAL implementado (sem mocks)
- [ ] Reset de senha funcionando
- [ ] Validação de CPF único implementada
- [ ] Validação de telefone único implementada
- [ ] Cálculo automático de rating funcionando
- [ ] Webhook do Stripe processando eventos
- [ ] Taxas padronizadas (Guest 10%, Host 15%)
- [ ] Serviço de email configurado

### ✅ Arquivos Criados

- [ ] `app/models/password_reset.py`
- [ ] `app/services/email_service.py`
- [ ] `app/constants.py`
- [ ] `alembic/versions/add_password_reset_tokens.py`
- [ ] Documentação completa (5+ arquivos .md)

### ✅ Configuração

- [ ] `.env` criado a partir de `.env.example`
- [ ] `DATABASE_URL` configurado
- [ ] `SECRET_KEY` gerado (64+ caracteres)
- [ ] `STRIPE_SECRET_KEY` configurado (live mode)
- [ ] `STRIPE_WEBHOOK_SECRET` configurado
- [ ] `AWS_ACCESS_KEY_ID` configurado
- [ ] `AWS_SECRET_ACCESS_KEY` configurado
- [ ] `S3_BUCKET_NAME` configurado
- [ ] `SENDGRID_API_KEY` ou SMTP configurado
- [ ] `EMAIL_FROM` definido
- [ ] `FRONTEND_URL` definido
- [ ] `FIREBASE_CREDENTIALS_PATH` configurado
- [ ] `MAPBOX_ACCESS_TOKEN` configurado (opcional)
- [ ] `CPFHUB_API_KEY` configurado (opcional)

---

## 🗄️ BANCO DE DADOS

### ✅ PostgreSQL

- [ ] Database criado
- [ ] Usuário com permissões adequadas
- [ ] Backup configurado
- [ ] Conexão testada

### ✅ Migrações Alembic

- [ ] `alembic upgrade head` executado
- [ ] Tabela `password_reset_tokens` criada
- [ ] Campo `users.fcm_token` existe
- [ ] Campo `users.stripe_account_status` existe
- [ ] Sem erros de migração
- [ ] `alembic current` mostra: `add_password_reset (head)`

### ✅ Dados Iniciais

- [ ] Categorias de espaços criadas
- [ ] Usuário admin criado (se necessário)
- [ ] Dados de teste removidos

---

## 🔌 INTEGRAÇÕES

### ✅ Stripe

- [ ] Conta Stripe verificada
- [ ] Modo live ativado
- [ ] Stripe Connect habilitado
- [ ] API keys de produção configuradas
- [ ] Webhook criado em https://dashboard.stripe.com/webhooks
- [ ] Webhook URL: `https://api.quintou.com/payments/webhook`
- [ ] Eventos configurados:
  - [ ] `account.updated`
  - [ ] `checkout.session.completed`
  - [ ] `payment_intent.succeeded`
- [ ] Signing secret copiado para `.env`
- [ ] Teste de webhook realizado
- [ ] Payment Intent testado (não retorna `pi_mocked`)

### ✅ AWS S3

- [ ] Bucket criado
- [ ] CORS configurado para domínio do frontend
- [ ] IAM user com permissões adequadas
- [ ] Access keys geradas
- [ ] Upload de imagem testado
- [ ] Política de bucket configurada (public-read para imagens)

### ✅ Email (SendGrid ou SMTP)

**SendGrid:**
- [ ] Conta criada
- [ ] API key gerada
- [ ] Domínio verificado
- [ ] Sender identity configurado
- [ ] Email de teste enviado com sucesso

**SMTP (alternativa):**
- [ ] Credenciais configuradas
- [ ] App password gerado (se Gmail)
- [ ] Porta e TLS configurados
- [ ] Email de teste enviado com sucesso

### ✅ Firebase (Notificações Push)

- [ ] Projeto Firebase criado
- [ ] FCM habilitado
- [ ] Service account JSON baixado
- [ ] Arquivo `firebase-credentials.json` no servidor
- [ ] Permissões corretas (600)
- [ ] Notificação de teste enviada

### ✅ APIs Externas (Opcionais)

**Mapbox:**
- [ ] API key configurada
- [ ] Geocoding testado
- [ ] Quota verificada

**CPFHub:**
- [ ] API key configurada
- [ ] Validação de CPF testada
- [ ] Quota verificada

---

## 🧪 TESTES

### ✅ Testes Automatizados

- [ ] `python verify_fixes.py` - 100% passou
- [ ] Pytest executado (se implementado)
- [ ] Testes de integração passando

### ✅ Testes Manuais - Autenticação

- [ ] Registro de usuário funciona
- [ ] CPF duplicado é rejeitado
- [ ] Telefone duplicado é rejeitado
- [ ] Login funciona
- [ ] JWT token válido retornado
- [ ] Refresh token funciona
- [ ] Reset de senha - email enviado
- [ ] Reset de senha - senha alterada
- [ ] Token expirado é rejeitado
- [ ] Token usado é rejeitado

### ✅ Testes Manuais - Espaços

- [ ] Criar espaço funciona
- [ ] Upload de imagem funciona
- [ ] Geocoding funciona (lat/lng preenchidos)
- [ ] Busca de espaços funciona
- [ ] Filtros funcionam
- [ ] Espaço é exibido corretamente

### ✅ Testes Manuais - Reservas

- [ ] Criar booking funciona
- [ ] Cálculo de preço correto
- [ ] Taxas corretas (Guest 10%, Host 15%)
- [ ] Detecção de conflito funciona
- [ ] Addons são calculados
- [ ] Promoções são aplicadas
- [ ] Status transitions funcionam

### ✅ Testes Manuais - Pagamentos

- [ ] Criar Payment Intent funciona
- [ ] Client secret é real (começa com `pi_`, não `pi_mocked`)
- [ ] Split payment configurado
- [ ] Application fee correto
- [ ] Metadata presente
- [ ] Pagamento processado no Stripe
- [ ] Webhook recebido
- [ ] Booking status atualizado para CONFIRMED
- [ ] Payment status atualizado para COMPLETED
- [ ] Notificações enviadas

### ✅ Testes Manuais - Reviews

- [ ] Criar review funciona
- [ ] Rating médio do usuário atualizado
- [ ] Rating médio do espaço atualizado
- [ ] Total de reviews atualizado
- [ ] Só permite review após booking completado
- [ ] Não permite review duplicado

### ✅ Testes Manuais - Chat

- [ ] Criar conversa funciona
- [ ] Enviar mensagem funciona
- [ ] WebSocket conecta
- [ ] Mensagens em tempo real
- [ ] Filtro de contato funciona
- [ ] Unread count atualizado

### ✅ Testes Manuais - Notificações

- [ ] Push notification enviada (FCM)
- [ ] Notificação salva no banco
- [ ] Mark as read funciona
- [ ] Deep linking data presente

---

## 🚀 DEPLOY

### ✅ Preparação

- [ ] Código commitado e pushed
- [ ] Tag de versão criada (`git tag v2.0`)
- [ ] Changelog atualizado
- [ ] Documentação revisada
- [ ] Equipe notificada

### ✅ Staging

- [ ] Deploy em ambiente de staging
- [ ] Migrações aplicadas
- [ ] Smoke tests executados
- [ ] Performance testada
- [ ] Testes de carga executados (opcional)
- [ ] Sem erros críticos

### ✅ Produção

**Backup:**
- [ ] Backup do banco de dados atual
- [ ] Backup dos arquivos de configuração
- [ ] Plano de rollback documentado

**Deploy:**
- [ ] Deploy iniciado
- [ ] Logs monitorados em tempo real
- [ ] Health check passa
- [ ] Métricas normais
- [ ] Sem erros nos logs

**Verificação:**
- [ ] API responde
- [ ] Swagger acessível
- [ ] Integração Stripe funcionando
- [ ] Emails sendo enviados
- [ ] Notificações funcionando
- [ ] Webhooks sendo recebidos

---

## 📊 MONITORAMENTO

### ✅ Logs

- [ ] Sistema de logs configurado
- [ ] Rotação de logs configurada
- [ ] Logs sendo coletados
- [ ] Sem erros críticos nos logs

### ✅ Métricas

- [ ] CPU < 70%
- [ ] Memória < 80%
- [ ] Latência API < 500ms
- [ ] Taxa de erro < 1%
- [ ] Database connections < 80% do pool

### ✅ Alertas

- [ ] Alertas de erro configurados
- [ ] Alertas de performance configurados
- [ ] Alertas de disponibilidade configurados
- [ ] Canais de notificação configurados (email, Slack, etc.)

### ✅ Sentry (Recomendado)

- [ ] Conta Sentry criada
- [ ] DSN configurado
- [ ] Integração testada
- [ ] Alertas configurados

---

## 🔒 SEGURANÇA

### ✅ Configurações

- [ ] HTTPS habilitado
- [ ] CORS configurado corretamente
- [ ] Rate limiting ativo
- [ ] Secrets não expostos no código
- [ ] .env não commitado (.gitignore)
- [ ] Firewall configurado
- [ ] Portas desnecessárias fechadas

### ✅ Credenciais

- [ ] Secret keys únicas e fortes
- [ ] Stripe keys de produção
- [ ] AWS keys com permissões mínimas
- [ ] Database password forte
- [ ] Credenciais rotacionadas periodicamente

### ✅ Compliance

- [ ] LGPD compliance revisado
- [ ] Termos de uso atualizados
- [ ] Política de privacidade atualizada
- [ ] Consentimentos configurados

---

## 📚 DOCUMENTAÇÃO

### ✅ Interna

- [ ] README.md atualizado
- [ ] AUDITORIA_BUGS_E_FIXES.md disponível
- [ ] CORREÇÕES_IMPLEMENTADAS.md disponível
- [ ] GUIA_DEPLOY.md disponível
- [ ] COMANDOS_UTEIS.md disponível
- [ ] API documentation (Swagger) acessível

### ✅ Externa

- [ ] Documentação da API publicada
- [ ] Guias de integração criados
- [ ] Exemplos de código disponíveis
- [ ] FAQ atualizado

---

## 👥 EQUIPE

### ✅ Treinamento

- [ ] Equipe de desenvolvimento treinada
- [ ] Equipe de suporte treinada
- [ ] Equipe de operações treinada
- [ ] Runbooks criados

### ✅ Responsabilidades

- [ ] On-call definido
- [ ] Escalation path definido
- [ ] Contatos de emergência atualizados
- [ ] Plano de incident response criado

---

## 📱 COMUNICAÇÃO

### ✅ Stakeholders

- [ ] Product owner notificado
- [ ] CTO notificado
- [ ] Time de marketing notificado
- [ ] Suporte ao cliente notificado

### ✅ Usuários

- [ ] Changelog publicado
- [ ] Release notes enviadas
- [ ] Blog post publicado (opcional)
- [ ] Social media atualizado (opcional)

---

## 🎯 PÓS-DEPLOY

### ✅ Monitoramento (Primeiras 24h)

- [ ] Hora 1: Verificação completa
- [ ] Hora 4: Verificação de métricas
- [ ] Hora 8: Verificação de logs
- [ ] Hora 24: Relatório de estabilidade

### ✅ Verificação (Primeira Semana)

- [ ] Dia 1: Monitoramento intensivo
- [ ] Dia 3: Análise de performance
- [ ] Dia 7: Retrospectiva do deploy

### ✅ Melhorias Contínuas

- [ ] Issues identificados documentados
- [ ] Backlog atualizado
- [ ] Próximas melhorias priorizadas
- [ ] Lessons learned documentadas

---

## 🏆 CRITÉRIOS DE SUCESSO

### ✅ Funcional

- [ ] Todos os endpoints respondem
- [ ] Todos os testes passam
- [ ] Todas as integrações funcionam
- [ ] Zero erros críticos

### ✅ Performance

- [ ] Latência dentro do SLA
- [ ] Throughput adequado
- [ ] Resource usage aceitável
- [ ] Sem memory leaks

### ✅ Negócio

- [ ] Pagamentos sendo processados
- [ ] Emails sendo entregues
- [ ] Usuários conseguem se cadastrar
- [ ] Hosts conseguem criar espaços
- [ ] Guests conseguem fazer reservas

---

## 📝 APROVAÇÕES

### Assinaturas

**Tech Lead:**
- [ ] Código revisado
- [ ] Testes aprovados
- [ ] Assinatura: _________________ Data: _______

**DevOps:**
- [ ] Infraestrutura validada
- [ ] Deploy testado
- [ ] Assinatura: _________________ Data: _______

**QA:**
- [ ] Testes completos executados
- [ ] Bugs críticos resolvidos
- [ ] Assinatura: _________________ Data: _______

**Product Owner:**
- [ ] Features validadas
- [ ] Business requirements atendidos
- [ ] Assinatura: _________________ Data: _______

**CTO:**
- [ ] Aprovação final
- [ ] Go/No-go decision
- [ ] Assinatura: _________________ Data: _______

---

## 🚦 STATUS FINAL

**Data do Deploy:** _______________________

**Versão:** v2.0

**Status:**
- [ ] ✅ APROVADO PARA PRODUÇÃO
- [ ] ⏳ PENDENTE (especificar motivo)
- [ ] ❌ REJEITADO (especificar motivo)

**Observações:**
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________

---

**Documento preparado por:** Kiro AI  
**Data de criação:** 13/07/2026  
**Última revisão:** _______________________

---

## 💡 DICA FINAL

✅ **Use este checklist como um guia progressivo.**  
✅ **Marque cada item à medida que completa.**  
✅ **Não pule etapas - cada uma é importante para um deploy seguro.**  
✅ **Em caso de dúvida, consulte os documentos de referência.**

**Boa sorte com o deploy! 🚀**
