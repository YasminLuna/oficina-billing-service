# Oficina Billing Service — FIAP Tech Challenge Fase 4

Microsserviço de orçamentos e pagamentos, independente da Oficina API.

## Responsabilidades e arquitetura

- Criação e consulta de orçamentos, aprovação, rejeição e cancelamento.
- Solicitação de pagamento para orçamentos aprovados.
- Persistência própria **SQLite**, montada em volume persistente (PVC) no ambiente local.
- Integração de pagamentos em `app/payment_gateway.py`: modo `mock` sem rede por padrão; modo `mercadopago` com chamada à API oficial quando `PAYMENT_PROVIDER_MODE=mercadopago` e `MERCADOPAGO_ACCESS_TOKEN` estão configurados. **O mock não representa pagamento liquidado**; integração real não foi comprovada no E2E local.

O serviço expõe FastAPI em `app.persistent_api:app`, sem acesso direto ao banco de outro serviço. A Saga centralizada na Oficina API o chama via REST para coordenar a OS.

## Endpoints principais

`GET /health`, `GET /openapi.json`, `POST /quotes`, `GET /quotes/{order_id}`, `POST /quotes/{order_id}/approve`, `POST /quotes/{order_id}/reject`, `POST /quotes/{order_id}/cancel`, `POST /quotes/{order_id}/payments`. Swagger UI: `/docs` quando exposto pelo serviço.

## Testes e qualidade

Validação **local em 09/11/2026**: **43 testes aprovados, cobertura 91,24%, Ruff aprovado e YAML Kubernetes válido**. O workflow [Billing Phase 4 - quality and local Kubernetes manifests](https://github.com/YasminLuna/oficina-billing-service/actions/workflows/phase4-quality.yml) contém lint, pytest com cobertura mínima de 80%, validação YAML e build Docker. **O resultado remoto mais recente ainda precisa ser confirmado**; a existência do workflow não prova sucesso.

## Execução local

O ambiente integrado usa Kubernetes kind `fiap-fase4` e namespace `fiap-fase4`. A aplicação usa `BILLING_SQLITE_PATH` para definir o caminho do arquivo SQLite. Não execute testes E2E em produção.

Repositórios: [API](https://github.com/YasminLuna/oficina-api) · [Execution](https://github.com/YasminLuna/oficina-execution-service).

## Pendências de entrega

Confirmar GitHub Actions remoto, proteção da branch principal, deploy Kubernetes **automatizado** e evidências de observabilidade. O workflow de qualidade atual constrói a imagem, mas **não realiza deploy**. Não ativar infraestrutura AWS paga para esta demonstração.
