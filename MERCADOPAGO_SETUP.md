# Pagamentos Mercado Pago — preparação sem credenciais

## Implementado

- Adaptador `app/payment_gateway.py` com modo padrão `PAYMENT_PROVIDER_MODE=mock`.
- `POST /quotes/{order_id}/payments`: inicia pagamento somente para orçamento aprovado.
- Resposta mock retorna `status=pending`, `simulated=true`, `provider=mock`.
- Validação de valores finitos e positivos, modo inválido e ausência de credenciais.
- O fluxo de Saga existente continua aprovando o **orçamento**, não o pagamento.

## Executar sem conta Mercado Pago

```bash
cd ~/fiap-local/oficina-billing-service
git pull --ff-only
python -m pip install -r requirements-dev.txt
python -m pytest tests/test_payment_gateway.py -v
```

No ambiente Docker Compose do repositório `oficina-api`, o Billing usa o mock por padrão. Para experimentar, primeiro crie um orçamento e aprove-o, depois chame:

```bash
curl -X POST http://localhost:8001/quotes/SEU_ORDER_ID/payments \
  -H 'Content-Type: application/json' -d '{}'
```

## Quando as credenciais de teste estiverem disponíveis

- Configure `PAYMENT_PROVIDER_MODE=mercadopago` e `MERCADOPAGO_ACCESS_TOKEN` **somente** em variável de ambiente ou secret manager.
- Obtenha token de cartão de teste no frontend/SDK apropriado e email de comprador de teste; não use cartões reais.
- A integração real faz `POST https://api.mercadopago.com/v1/payments` com chave de idempotência baseada na OS.
- **Não habilite modo real sem revisar o fluxo de pagamento e autorização**: este adaptador é uma preparação e ainda não persiste pagamentos, não valida webhook, não verifica status via API e não implementa reembolso.
- A resposta mock nunca prova quitação; pagamentos só podem ser confirmados após consulta autenticada ao provedor.
- O endpoint de demonstração não possui autenticação de serviço; proteger antes de qualquer exposição pública.

## Pendências do edital

1. Integrar pagamento real de teste e confirmação por consulta ao Mercado Pago.
2. Persistir estado do pagamento e garantir idempotência na criação e no webhook.
3. Verificar assinatura de webhook e evitar confiar em payload de notificação para confirmação financeira.
4. Conectar o evento de pagamento confirmado à Saga e ao estado da OS.
5. Demonstrar testes e evidências sem transações reais.
