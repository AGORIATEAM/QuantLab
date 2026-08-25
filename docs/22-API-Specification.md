# 22 --- API Specification

**Projet : QuantLab**\
**Document : API Specification**\
**Version : 1.0**\
**Statut : Contrat d'interface de référence**

------------------------------------------------------------------------

# 1. Objectif

Ce document définit les principes, conventions et contrats API de
QuantLab.

L'API constitue la frontière structurée entre :

``` text
clients
services
engines
agents IA
interfaces opérateur
outils de recherche
infrastructure
```

Une API QuantLab ne doit pas être une simple couche HTTP placée devant
du code interne. Elle constitue un contrat versionné, validé, observable
et gouverné.

> **Toute opération critique doit être explicite, authentifiée,
> autorisée, idempotente lorsque nécessaire et entièrement traçable.**

------------------------------------------------------------------------

# 2. Principes fondamentaux

Les APIs QuantLab doivent être :

``` text
EXPLICIT
TYPED
VERSIONED
CONSISTENT
SECURE
OBSERVABLE
IDEMPOTENT WHERE REQUIRED
BACKWARD-COMPATIBLE WHERE POSSIBLE
```

------------------------------------------------------------------------

# 3. Architecture API

Architecture cible :

``` text
Client / UI / Agent
        ↓
    API Gateway
        ↓
Authentication
        ↓
Authorization
        ↓
Request Validation
        ↓
Application Service
        ↓
Domain Engine
        ↓
Storage / Event Bus
```

------------------------------------------------------------------------

# 4. API Gateway

Le gateway peut centraliser :

``` text
routing
authentication
rate limiting
request IDs
logging
TLS termination
```

Il ne doit pas contenir la logique métier principale.

------------------------------------------------------------------------

# 5. API Styles

QuantLab peut utiliser plusieurs styles selon le besoin :

``` text
REST
internal RPC
event-driven contracts
streaming APIs
```

Pour l'interface externe et administrative V1 :

``` text
REST + JSON
```

est le standard recommandé.

------------------------------------------------------------------------

# 6. Base Path

Format recommandé :

``` text
/api/v1/
```

Exemple :

``` text
GET /api/v1/strategies
```

------------------------------------------------------------------------

# 7. Versioning

Les breaking changes doivent produire une nouvelle version majeure
d'API.

Exemple :

``` text
/api/v1/
/api/v2/
```

------------------------------------------------------------------------

# 8. Backward Compatibility

Les changements non breaking doivent être privilégiés :

``` text
adding optional fields
adding endpoints
adding enum values when consumers tolerate them
```

------------------------------------------------------------------------

# 9. Breaking Changes

Exemples :

``` text
removing fields
renaming fields
changing semantic meaning
changing required fields
changing response type
```

------------------------------------------------------------------------

# 10. Deprecation

Avant suppression :

``` text
announce
mark deprecated
provide replacement
allow migration period
remove
```

------------------------------------------------------------------------

# 11. Resource Naming

Les ressources REST utilisent des noms pluriels :

``` text
/strategies
/experiments
/orders
/positions
/decisions
```

------------------------------------------------------------------------

# 12. Naming Convention

JSON :

``` text
snake_case
```

Exemple :

``` json
{
  "strategy_id": "STR-001",
  "created_at": "2026-08-24T12:00:00Z"
}
```

------------------------------------------------------------------------

# 13. Identifiers

Chaque ressource importante possède un ID stable.

Exemples :

``` text
strategy_id
decision_id
order_id
experiment_id
deployment_id
```

------------------------------------------------------------------------

# 14. ID Format

Les IDs doivent être :

``` text
unique
opaque where appropriate
non-reusable
```

------------------------------------------------------------------------

# 15. Timestamp Standard

Tous les timestamps API :

``` text
ISO 8601
UTC
timezone explicit
```

Exemple :

``` text
2026-08-24T12:34:56.123Z
```

------------------------------------------------------------------------

# 16. Monetary Values

Éviter les floats ambigus pour les montants critiques.

Format recommandé :

``` json
{
  "amount": "1250.50",
  "currency": "USD"
}
```

------------------------------------------------------------------------

# 17. Percentage Values

La convention doit être explicite.

Préférence :

``` text
fraction
```

Exemple :

``` json
{
  "risk_fraction": "0.01"
}
```

signifie :

``` text
1%
```

------------------------------------------------------------------------

# 18. Quantities

Les quantités doivent préciser leur unité lorsque nécessaire.

------------------------------------------------------------------------

# 19. Price

Exemple :

``` json
{
  "price": "63450.25",
  "currency": "USD"
}
```

------------------------------------------------------------------------

# 20. Pagination

Pour les collections :

``` text
cursor-based pagination
```

est recommandée lorsque les volumes deviennent importants.

------------------------------------------------------------------------

# 21. Pagination Request

Exemple :

``` text
GET /api/v1/orders?limit=100&cursor=abc123
```

------------------------------------------------------------------------

# 22. Pagination Response

``` json
{
  "items": [],
  "next_cursor": "def456",
  "has_more": true
}
```

------------------------------------------------------------------------

# 23. Filtering

Exemple :

``` text
GET /api/v1/orders?status=filled&symbol=BTCUSDT
```

------------------------------------------------------------------------

# 24. Sorting

Format :

``` text
?sort=-created_at
```

où `-` indique décroissant.

------------------------------------------------------------------------

# 25. Request ID

Chaque requête reçoit :

``` text
request_id
```

------------------------------------------------------------------------

# 26. Correlation ID

Les workflows distribués utilisent :

``` text
correlation_id
```

------------------------------------------------------------------------

# 27. Causation ID

Lorsque pertinent :

``` text
causation_id
```

permet d'identifier l'événement parent.

------------------------------------------------------------------------

# 28. Standard Success Response

Pour une ressource :

``` json
{
  "data": {},
  "meta": {
    "request_id": "req_123"
  }
}
```

------------------------------------------------------------------------

# 29. Standard Error Response

``` json
{
  "error": {
    "code": "RISK_LIMIT_EXCEEDED",
    "message": "Requested risk exceeds allowed limit.",
    "details": {},
    "request_id": "req_123"
  }
}
```

------------------------------------------------------------------------

# 30. Error Codes

Les erreurs doivent utiliser des codes stables et machine-readable.

------------------------------------------------------------------------

# 31. HTTP Status Codes

Utilisation recommandée :

``` text
200 OK
201 Created
202 Accepted
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
429 Too Many Requests
500 Internal Server Error
503 Service Unavailable
```

------------------------------------------------------------------------

# 32. 400 vs 422

`400` :

``` text
malformed request
```

`422` :

``` text
syntactically valid but domain-invalid
```

------------------------------------------------------------------------

# 33. 409 Conflict

Utiliser pour :

``` text
state transition conflict
duplicate resource
version conflict
```

------------------------------------------------------------------------

# 34. Validation Errors

Exemple :

``` json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed.",
    "details": {
      "fields": {
        "quantity": "must be greater than zero"
      }
    }
  }
}
```

------------------------------------------------------------------------

# 35. Authentication

Toutes les APIs non publiques doivent être authentifiées.

------------------------------------------------------------------------

# 36. Authentication Methods

Selon l'usage :

``` text
service identity
OAuth/OIDC
API token
short-lived credentials
```

------------------------------------------------------------------------

# 37. Service-to-Service Identity

Chaque service doit disposer de sa propre identité.

------------------------------------------------------------------------

# 38. Authorization

Après authentification :

``` text
Is this identity allowed to perform this action?
```

------------------------------------------------------------------------

# 39. RBAC

Les permissions peuvent utiliser :

``` text
role-based access control
```

------------------------------------------------------------------------

# 40. ABAC

Pour les politiques plus fines :

``` text
attribute-based access control
```

------------------------------------------------------------------------

# 41. Permission Example

``` text
strategy.read
strategy.write
risk.read
risk.modify
execution.submit
execution.cancel
governance.approve
```

------------------------------------------------------------------------

# 42. Least Privilege

Un client reçoit uniquement les permissions nécessaires.

------------------------------------------------------------------------

# 43. AI Agent Permissions

Chaque agent IA doit avoir un scope explicite.

------------------------------------------------------------------------

# 44. No Universal AI Token

Un agent de recherche ne doit jamais posséder un token universel
production.

------------------------------------------------------------------------

# 45. Production Authorization

Les endpoints live doivent appliquer des règles plus strictes.

------------------------------------------------------------------------

# 46. Environment Header

Lorsque nécessaire, l'environnement est déterminé côté serveur ou par
credentials.

Ne jamais faire confiance à un simple :

``` text
X-Environment: production
```

envoyé par le client comme autorisation.

------------------------------------------------------------------------

# 47. TLS

Toutes les communications réseau sensibles utilisent TLS.

------------------------------------------------------------------------

# 48. Secrets

Aucun secret ne doit apparaître dans :

``` text
URL
query string
logs
error messages
```

------------------------------------------------------------------------

# 49. Input Validation

Tous les inputs externes doivent être validés.

------------------------------------------------------------------------

# 50. Schema Validation

Chaque endpoint doit disposer d'un schéma formel.

------------------------------------------------------------------------

# 51. OpenAPI

La REST API doit être décrite via :

``` text
OpenAPI 3.x
```

------------------------------------------------------------------------

# 52. OpenAPI as Contract

La spécification doit servir à :

``` text
documentation
validation
client generation
contract testing
```

------------------------------------------------------------------------

# 53. API Documentation

Chaque endpoint documente :

``` text
purpose
permissions
request
response
errors
idempotency
side effects
```

------------------------------------------------------------------------

# 54. Idempotency

Les opérations créant des effets critiques doivent supporter
l'idempotence.

------------------------------------------------------------------------

# 55. Idempotency-Key

Exemple :

``` text
Idempotency-Key: 9fd...
```

------------------------------------------------------------------------

# 56. Idempotency Storage

Le serveur conserve :

``` text
key
request fingerprint
result
expiration
```

------------------------------------------------------------------------

# 57. Idempotency Conflict

Même clé + payload différent :

``` text
409 Conflict
```

------------------------------------------------------------------------

# 58. Order Submission

L'envoi d'un ordre doit être idempotent.

------------------------------------------------------------------------

# 59. Retry Safety

Un timeout client ne doit pas entraîner automatiquement un double ordre.

------------------------------------------------------------------------

# 60. Optimistic Concurrency

Pour les ressources modifiables :

``` text
version
```

ou :

``` text
ETag
```

peut empêcher l'écrasement concurrent.

------------------------------------------------------------------------

# 61. Resource Version

Exemple :

``` json
{
  "strategy_id": "STR-001",
  "version": 12
}
```

------------------------------------------------------------------------

# 62. Update Conflict

Si le client modifie une ancienne version :

``` text
409 Conflict
```

------------------------------------------------------------------------

# 63. State Machines

Les ressources avec lifecycle doivent valider leurs transitions.

------------------------------------------------------------------------

# 64. Strategy States

``` text
DISABLED
PAPER
SHADOW
LIMITED_LIVE
LIVE
PAUSED
```

------------------------------------------------------------------------

# 65. Order States

``` text
CREATED
SUBMITTED
ACKNOWLEDGED
PARTIALLY_FILLED
FILLED
CANCEL_PENDING
CANCELLED
REJECTED
UNKNOWN
```

------------------------------------------------------------------------

# 66. Experiment States

Selon `21-Experiment-Registry.md`.

------------------------------------------------------------------------

# 67. Governance States

Selon `16-Governance-Engine.md`.

------------------------------------------------------------------------

# 68. Invalid Transition

Exemple :

``` text
CANCELLED → FILLED
```

ne doit pas être accepté localement sans événement
externe/reconciliation explicitement traité.

------------------------------------------------------------------------

# 69. Asynchronous Operations

Les opérations longues peuvent retourner :

``` text
202 Accepted
```

------------------------------------------------------------------------

# 70. Operation Resource

Exemple :

``` json
{
  "operation_id": "op_123",
  "status": "PENDING"
}
```

------------------------------------------------------------------------

# 71. Operation Endpoint

``` text
GET /api/v1/operations/{operation_id}
```

------------------------------------------------------------------------

# 72. Operation Status

``` text
PENDING
RUNNING
SUCCEEDED
FAILED
CANCELLED
```

------------------------------------------------------------------------

# 73. Webhooks

Lorsque nécessaire, QuantLab peut publier des webhooks.

------------------------------------------------------------------------

# 74. Webhook Security

Les webhooks doivent être :

``` text
signed
timestamped
replay-protected
```

------------------------------------------------------------------------

# 75. Webhook Retry

Les deliveries doivent avoir une politique de retry contrôlée.

------------------------------------------------------------------------

# 76. Event API

Les événements internes doivent suivre un contrat versionné.

------------------------------------------------------------------------

# 77. Event Envelope

Format conceptuel :

``` json
{
  "event_id": "evt_123",
  "event_type": "decision.created",
  "event_version": 1,
  "occurred_at": "2026-08-24T12:00:00Z",
  "correlation_id": "corr_123",
  "causation_id": "evt_122",
  "producer": "decision-engine",
  "data": {}
}
```

------------------------------------------------------------------------

# 78. Event IDs

Chaque événement doit avoir un ID unique.

------------------------------------------------------------------------

# 79. Event Version

Les schemas événementiels doivent être versionnés.

------------------------------------------------------------------------

# 80. Event Immutability

Un événement publié ne doit pas être modifié.

------------------------------------------------------------------------

# 81. Duplicate Events

Les consumers doivent tolérer les doublons lorsque le transport peut les
produire.

------------------------------------------------------------------------

# 82. Out-of-Order Events

Les consumers ne doivent pas supposer un ordering global inexistant.

------------------------------------------------------------------------

# 83. Dead Letter

Les événements non traitables doivent pouvoir être isolés.

------------------------------------------------------------------------

# 84. Event Schema Registry

À maturité, les schemas peuvent être centralisés.

------------------------------------------------------------------------

# 85. Market Data API

Endpoints conceptuels :

``` text
GET /market-data/candles
GET /market-data/trades
GET /market-data/orderbook
GET /market-data/status
```

------------------------------------------------------------------------

# 86. Candles Endpoint

``` text
GET /api/v1/market-data/candles
```

Paramètres :

``` text
symbol
timeframe
start
end
limit
```

------------------------------------------------------------------------

# 87. Candle Schema

``` json
{
  "symbol": "BTCUSDT",
  "timeframe": "1m",
  "open_time": "2026-08-24T12:00:00Z",
  "open": "64000.00",
  "high": "64100.00",
  "low": "63950.00",
  "close": "64050.00",
  "volume": "123.45"
}
```

------------------------------------------------------------------------

# 88. Data Freshness

Les réponses live doivent exposer assez d'information pour évaluer la
fraîcheur.

------------------------------------------------------------------------

# 89. Market Analysis API

``` text
GET /analysis/{symbol}
GET /analysis/{symbol}/indicators
GET /analysis/{symbol}/context
```

------------------------------------------------------------------------

# 90. Market Structure API

``` text
GET /market-structure/{symbol}
```

------------------------------------------------------------------------

# 91. Market Structure Response

Exemple conceptuel :

``` json
{
  "symbol": "BTCUSDT",
  "timeframe": "15m",
  "trend": "BULLISH",
  "last_bos": {},
  "last_choch": {},
  "swings": [],
  "computed_at": "2026-08-24T12:00:00Z"
}
```

------------------------------------------------------------------------

# 92. Volume Profile API

``` text
GET /volume-profile/{symbol}
```

------------------------------------------------------------------------

# 93. Volume Profile Response

``` json
{
  "poc": "64000.00",
  "vah": "64500.00",
  "val": "63500.00",
  "value_area_percentage": "0.70"
}
```

------------------------------------------------------------------------

# 94. SMC API

``` text
GET /smc/{symbol}
```

------------------------------------------------------------------------

# 95. SMC Response

Peut exposer :

``` text
liquidity zones
sweeps
imbalances
order blocks
premium/discount state
```

avec version de méthodologie.

------------------------------------------------------------------------

# 96. Scoring API

``` text
POST /scores/evaluate
GET /scores/{score_id}
```

------------------------------------------------------------------------

# 97. Score Request

``` json
{
  "symbol": "BTCUSDT",
  "strategy_id": "STR-001",
  "context_id": "ctx_123"
}
```

------------------------------------------------------------------------

# 98. Score Response

``` json
{
  "score_id": "score_123",
  "total_score": "82.5",
  "components": {
    "market_structure": "20",
    "volume_profile": "17.5",
    "smc": "25",
    "momentum": "20"
  },
  "reason_codes": [
    "BULLISH_STRUCTURE",
    "LIQUIDITY_SWEEP_CONFIRMED"
  ]
}
```

------------------------------------------------------------------------

# 99. Decision API

``` text
POST /decisions/evaluate
GET /decisions/{decision_id}
GET /decisions
```

------------------------------------------------------------------------

# 100. Decision Response

``` json
{
  "decision_id": "dec_123",
  "strategy_id": "STR-001",
  "symbol": "BTCUSDT",
  "action": "ENTER_LONG",
  "confidence": "0.82",
  "score_id": "score_123",
  "reason_codes": [],
  "created_at": "2026-08-24T12:00:00Z",
  "expires_at": "2026-08-24T12:05:00Z"
}
```

------------------------------------------------------------------------

# 101. Decision Expiration

Toute décision live doit pouvoir avoir une durée de validité.

------------------------------------------------------------------------

# 102. Risk API

``` text
POST /risk/evaluate
GET /risk/status
GET /risk/limits
GET /risk/exposure
```

------------------------------------------------------------------------

# 103. Risk Evaluation Request

``` json
{
  "decision_id": "dec_123",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "requested_quantity": "0.10",
  "entry_price": "64000",
  "stop_price": "63500"
}
```

------------------------------------------------------------------------

# 104. Risk Evaluation Response

``` json
{
  "risk_decision_id": "risk_123",
  "status": "APPROVED",
  "approved_quantity": "0.08",
  "risk_amount": "40.00",
  "reason_codes": [
    "POSITION_SIZE_REDUCED"
  ]
}
```

------------------------------------------------------------------------

# 105. Risk Status Values

``` text
APPROVED
MODIFIED
REJECTED
```

------------------------------------------------------------------------

# 106. Risk Rejection

Exemple :

``` json
{
  "status": "REJECTED",
  "reason_codes": [
    "DAILY_LOSS_LIMIT"
  ]
}
```

------------------------------------------------------------------------

# 107. Risk Limits Endpoint

La lecture des limites est soumise aux permissions appropriées.

------------------------------------------------------------------------

# 108. Risk Modification Endpoint

Toute modification de limite doit passer par un endpoint distinct et
fortement gouverné.

------------------------------------------------------------------------

# 109. No Direct Strategy Risk Mutation

Une stratégie ne doit pas pouvoir modifier ses propres hard limits.

------------------------------------------------------------------------

# 110. Execution API

``` text
POST /orders
GET /orders/{order_id}
POST /orders/{order_id}/cancel
POST /orders/{order_id}/replace
GET /orders
```

------------------------------------------------------------------------

# 111. Order Submission Request

``` json
{
  "risk_decision_id": "risk_123",
  "symbol": "BTCUSDT",
  "side": "BUY",
  "order_type": "LIMIT",
  "quantity": "0.08",
  "limit_price": "64000.00"
}
```

------------------------------------------------------------------------

# 112. Required Execution Linkage

Un ordre stratégique live doit référencer une décision de risque valide.

------------------------------------------------------------------------

# 113. Execution Validation

Le serveur vérifie :

``` text
risk approval exists
approval not expired
quantity <= approved quantity
symbol matches
side matches
environment allowed
```

------------------------------------------------------------------------

# 114. Order Response

``` json
{
  "order_id": "ord_123",
  "client_order_id": "ql_abc",
  "status": "SUBMITTED",
  "venue": "example_exchange",
  "created_at": "2026-08-24T12:00:01Z"
}
```

------------------------------------------------------------------------

# 115. Order Cancellation

``` text
POST /api/v1/orders/{order_id}/cancel
```

------------------------------------------------------------------------

# 116. Cancel Idempotency

Plusieurs requêtes cancel doivent produire un comportement sûr.

------------------------------------------------------------------------

# 117. Unknown Order State

L'API doit pouvoir retourner :

``` text
UNKNOWN
```

si l'état exchange n'est pas encore réconcilié.

------------------------------------------------------------------------

# 118. Fills API

``` text
GET /fills
GET /fills/{fill_id}
```

------------------------------------------------------------------------

# 119. Positions API

``` text
GET /positions
GET /positions/{position_id}
```

------------------------------------------------------------------------

# 120. Position Response

``` json
{
  "position_id": "pos_123",
  "symbol": "BTCUSDT",
  "quantity": "0.08",
  "average_entry_price": "64000.00",
  "unrealized_pnl": "125.40",
  "updated_at": "2026-08-24T12:10:00Z"
}
```

------------------------------------------------------------------------

# 121. Portfolio API

``` text
GET /portfolio
GET /portfolio/exposure
GET /portfolio/performance
```

------------------------------------------------------------------------

# 122. Monitoring API

``` text
GET /health
GET /ready
GET /api/v1/system/status
GET /api/v1/incidents
GET /api/v1/alerts
```

------------------------------------------------------------------------

# 123. Public Health Endpoint

Le health endpoint ne doit pas exposer de détails sensibles.

------------------------------------------------------------------------

# 124. Internal Health Details

Les diagnostics détaillés nécessitent une permission interne.

------------------------------------------------------------------------

# 125. System Status

Peut retourner :

``` text
NORMAL
DEGRADED
HALTED
MAINTENANCE
```

------------------------------------------------------------------------

# 126. Kill Switch API

Endpoints fortement protégés :

``` text
POST /risk/kill-switch/activate
POST /risk/kill-switch/deactivate
GET /risk/kill-switch
```

------------------------------------------------------------------------

# 127. Kill Switch Activation

L'activation doit être simple, rapide et auditable.

------------------------------------------------------------------------

# 128. Kill Switch Deactivation

La désactivation doit être plus restrictive que l'activation.

------------------------------------------------------------------------

# 129. Strategy API

``` text
POST /strategies
GET /strategies
GET /strategies/{strategy_id}
PATCH /strategies/{strategy_id}
POST /strategies/{strategy_id}/activate
POST /strategies/{strategy_id}/pause
```

------------------------------------------------------------------------

# 130. Strategy Creation

Une stratégie créée n'est pas automatiquement live.

------------------------------------------------------------------------

# 131. Strategy Activation

L'activation dépend :

``` text
environment
governance
risk profile
validation state
```

------------------------------------------------------------------------

# 132. Experiment API

Selon `21-Experiment-Registry.md` :

``` text
POST /experiments
GET /experiments
GET /experiments/{experiment_id}
POST /experiments/{experiment_id}/runs
POST /experiments/{experiment_id}/review
POST /experiments/{experiment_id}/promote
```

------------------------------------------------------------------------

# 133. Knowledge API

``` text
GET /knowledge
GET /knowledge/{knowledge_id}
POST /knowledge/search
```

------------------------------------------------------------------------

# 134. Knowledge Search

Doit supporter des recherches structurées et, à terme, sémantiques.

------------------------------------------------------------------------

# 135. AI API

``` text
POST /ai/tasks
GET /ai/tasks/{task_id}
GET /ai/agents
```

------------------------------------------------------------------------

# 136. AI Task Request

``` json
{
  "agent_id": "research-agent",
  "task_type": "EXPERIMENT_ANALYSIS",
  "input": {},
  "permissions": []
}
```

------------------------------------------------------------------------

# 137. AI Permission Enforcement

Les permissions du payload ne peuvent pas augmenter les droits réels du
caller.

------------------------------------------------------------------------

# 138. AI Task Response

``` json
{
  "task_id": "aitask_123",
  "status": "PENDING"
}
```

------------------------------------------------------------------------

# 139. AI Structured Output

Les résultats automatisables doivent respecter un schéma.

------------------------------------------------------------------------

# 140. Governance API

``` text
POST /governance/proposals
GET /governance/proposals
GET /governance/proposals/{id}
POST /governance/proposals/{id}/approve
POST /governance/proposals/{id}/reject
```

------------------------------------------------------------------------

# 141. Approval API

Une approbation doit identifier :

``` text
approver
scope
environment
artifact hash
expiration
```

------------------------------------------------------------------------

# 142. Self-Approval Prevention

Le serveur doit appliquer les règles de séparation des responsabilités.

------------------------------------------------------------------------

# 143. Deployment API

``` text
POST /deployments
GET /deployments
GET /deployments/{deployment_id}
POST /deployments/{deployment_id}/rollback
```

------------------------------------------------------------------------

# 144. Deployment Request

Doit référencer :

``` text
artifact
environment
governance approval
configuration version
```

------------------------------------------------------------------------

# 145. Artifact Hash Validation

L'artefact demandé doit correspondre exactement à celui approuvé.

------------------------------------------------------------------------

# 146. Database API Boundary

Les clients ne doivent pas accéder directement à la base pour contourner
les règles métier.

------------------------------------------------------------------------

# 147. Internal Repository Layer

Les accès DB internes doivent passer par des interfaces clairement
définies.

------------------------------------------------------------------------

# 148. Search APIs

Les recherches complexes utilisent :

``` text
POST /resource/search
```

si les paramètres deviennent trop riches pour une query string
raisonnable.

------------------------------------------------------------------------

# 149. Bulk APIs

Les opérations bulk doivent être explicites.

Exemple :

``` text
POST /orders/bulk-cancel
```

------------------------------------------------------------------------

# 150. Bulk Safety

Les opérations bulk critiques nécessitent :

``` text
limits
permissions
audit
```

------------------------------------------------------------------------

# 151. Dry Run

Les opérations sensibles peuvent supporter :

``` text
dry_run=true
```

------------------------------------------------------------------------

# 152. Dry Run Response

Doit indiquer ce qui aurait été modifié sans appliquer l'action.

------------------------------------------------------------------------

# 153. Rate Limiting

Les APIs doivent protéger les ressources contre :

``` text
accidental loops
abuse
runaway agents
```

------------------------------------------------------------------------

# 154. Rate Limit Scope

Les limites peuvent être appliquées par :

``` text
identity
endpoint
environment
```

------------------------------------------------------------------------

# 155. Rate Limit Headers

Peuvent exposer :

``` text
limit
remaining
reset
```

------------------------------------------------------------------------

# 156. Trading Rate Limits

L'Execution Engine doit également respecter les limites des venues
externes.

------------------------------------------------------------------------

# 157. Timeouts

Tout client API doit utiliser des timeouts explicites.

------------------------------------------------------------------------

# 158. Server Timeout

Les opérations longues doivent être converties en tâches asynchrones
plutôt que bloquer indéfiniment.

------------------------------------------------------------------------

# 159. Retry Policy

Retry uniquement sur les erreurs considérées transitoires.

------------------------------------------------------------------------

# 160. Retryable Errors

Exemples potentiels :

``` text
503
selected 429
network timeout
```

selon contrat.

------------------------------------------------------------------------

# 161. Non-Retryable Errors

Exemples :

``` text
400
403
422
```

------------------------------------------------------------------------

# 162. Retry-After

Utiliser lorsque pertinent.

------------------------------------------------------------------------

# 163. Circuit Breaking

Les clients internes peuvent appliquer des circuit breakers.

------------------------------------------------------------------------

# 164. Caching

Les réponses cacheables doivent être explicitement identifiées.

------------------------------------------------------------------------

# 165. No Unsafe Caching

Ne pas cacher naïvement :

``` text
live positions
risk state
kill switch
```

------------------------------------------------------------------------

# 166. Cache Headers

Les APIs HTTP peuvent utiliser des headers standards lorsque pertinent.

------------------------------------------------------------------------

# 167. Streaming Market Data

Pour les données temps réel :

``` text
WebSocket
SSE
internal streaming bus
```

peuvent être utilisés.

------------------------------------------------------------------------

# 168. Streaming Contract

Un stream doit définir :

``` text
subscription
event schema
heartbeat
reconnect
sequence behavior
```

------------------------------------------------------------------------

# 169. Heartbeat

Les connexions longues doivent permettre de détecter une connexion
morte.

------------------------------------------------------------------------

# 170. Reconnect

Le client doit savoir comment récupérer après déconnexion.

------------------------------------------------------------------------

# 171. Snapshot + Delta

Pour certaines données :

``` text
snapshot
+
incremental updates
```

------------------------------------------------------------------------

# 172. Sequence Numbers

Lorsque la source le permet, utiliser des séquences pour détecter les
gaps.

------------------------------------------------------------------------

# 173. Gap Detection

Une rupture de séquence doit déclencher :

``` text
resync
```

------------------------------------------------------------------------

# 174. API Audit

Toute opération critique enregistre :

``` text
identity
action
resource
timestamp
request_id
result
```

------------------------------------------------------------------------

# 175. Sensitive Audit Fields

Les secrets et données sensibles doivent être masqués.

------------------------------------------------------------------------

# 176. API Metrics

Suivre :

``` text
request rate
error rate
latency
status codes
rate-limit events
```

------------------------------------------------------------------------

# 177. Endpoint Latency

Mesurer :

``` text
p50
p95
p99
```

pour les endpoints critiques.

------------------------------------------------------------------------

# 178. API Tracing

Les requêtes distribuées doivent pouvoir être tracées entre services.

------------------------------------------------------------------------

# 179. Domain Metrics

Ne pas se limiter à HTTP.

Exemple :

``` text
risk_rejections_total
orders_submitted_total
```

------------------------------------------------------------------------

# 180. API Logs

Les logs doivent inclure :

``` text
request_id
identity
endpoint
status
duration
```

sans secrets.

------------------------------------------------------------------------

# 181. Error Observability

Les erreurs `5xx` doivent être corrélables à une cause interne.

------------------------------------------------------------------------

# 182. API SLOs

À maturité, définir des objectifs de :

``` text
availability
latency
error rate
```

------------------------------------------------------------------------

# 183. Critical APIs

Priorité SLO :

``` text
risk
execution
market data status
```

------------------------------------------------------------------------

# 184. API Testing

Selon `18-Testing-Strategy.md` :

``` text
unit
schema
contract
integration
authorization
load
security
```

------------------------------------------------------------------------

# 185. Contract Tests

Les clients et serveurs doivent vérifier la compatibilité.

------------------------------------------------------------------------

# 186. OpenAPI Validation

La CI doit vérifier que l'implémentation reste compatible avec la spec.

------------------------------------------------------------------------

# 187. Breaking Change Detection

La CI doit détecter les changements incompatibles.

------------------------------------------------------------------------

# 188. Authorization Tests

Chaque endpoint sensible doit avoir des tests :

``` text
allowed identity
forbidden identity
```

------------------------------------------------------------------------

# 189. Idempotency Tests

Les endpoints critiques doivent être testés avec des requêtes
dupliquées.

------------------------------------------------------------------------

# 190. Concurrency Tests

Tester les mises à jour concurrentes.

------------------------------------------------------------------------

# 191. Fuzzing

Les endpoints exposés peuvent être soumis à du fuzzing contrôlé.

------------------------------------------------------------------------

# 192. Load Tests

Tester les endpoints critiques avec des volumes réalistes et stressés.

------------------------------------------------------------------------

# 193. API Security

La sécurité complète est définie dans :

``` text
24-Security.md
```

------------------------------------------------------------------------

# 194. Injection Defense

Tous les inputs doivent être traités comme non fiables.

------------------------------------------------------------------------

# 195. Object-Level Authorization

Vérifier non seulement le type d'action mais aussi la ressource ciblée.

------------------------------------------------------------------------

# 196. Mass Assignment

Ne jamais mapper aveuglément un JSON externe vers un modèle interne
privilégié.

------------------------------------------------------------------------

# 197. Sensitive Fields

Certains champs doivent être :

``` text
read-only
write-only
internal-only
```

------------------------------------------------------------------------

# 198. Response Minimization

Ne retourner que les données nécessaires.

------------------------------------------------------------------------

# 199. Error Information Leakage

Les erreurs externes ne doivent pas exposer :

``` text
stack traces
database internals
secret paths
```

------------------------------------------------------------------------

# 200. CORS

Configurer explicitement pour les interfaces web.

------------------------------------------------------------------------

# 201. CSRF

Protéger les workflows basés sur cookies/session lorsque applicable.

------------------------------------------------------------------------

# 202. Request Size Limits

Limiter la taille des payloads.

------------------------------------------------------------------------

# 203. File Uploads

Les uploads éventuels doivent être :

``` text
size-limited
type-validated
scanned where appropriate
```

------------------------------------------------------------------------

# 204. API Client SDK

Des SDK peuvent être générés depuis OpenAPI.

------------------------------------------------------------------------

# 205. Python SDK

Prioritaire pour :

``` text
research
automation
internal tooling
```

------------------------------------------------------------------------

# 206. CLI

Le CLI QuantLab doit consommer les mêmes APIs lorsque possible.

------------------------------------------------------------------------

# 207. UI

L'interface opérateur doit également utiliser les contrats officiels.

------------------------------------------------------------------------

# 208. No Secret Backdoor API

Pas d'endpoint interne non documenté permettant de contourner les
contrôles.

------------------------------------------------------------------------

# 209. Admin API

Les endpoints administratifs doivent être explicitement séparés et
fortement protégés.

------------------------------------------------------------------------

# 210. Operator API

Les actions opérateur critiques doivent produire des audits.

------------------------------------------------------------------------

# 211. Emergency API

Les actions d'urgence doivent être minimales, explicites et auditables.

------------------------------------------------------------------------

# 212. Kill Switch Priority

Le kill switch doit rester disponible même si certaines fonctions non
critiques sont dégradées.

------------------------------------------------------------------------

# 213. Safe Failure

Si l'API Risk est indisponible :

``` text
new exposure blocked
```

------------------------------------------------------------------------

# 214. Execution API Failure

Un timeout ne signifie pas que l'ordre n'existe pas.

Le client doit réconcilier.

------------------------------------------------------------------------

# 215. Reconciliation API

Endpoints conceptuels :

``` text
POST /reconciliation/run
GET /reconciliation/status
GET /reconciliation/mismatches
```

------------------------------------------------------------------------

# 216. Reconciliation Permissions

Ces endpoints sont internes/opérateur.

------------------------------------------------------------------------

# 217. Position Correction

Une correction manuelle de position interne doit être extrêmement
contrôlée et auditée.

------------------------------------------------------------------------

# 218. API Change Process

Tout changement important suit :

``` text
proposal
design
review
implementation
contract tests
documentation
release
```

------------------------------------------------------------------------

# 219. API ADR

Les décisions structurantes doivent être documentées en ADR.

------------------------------------------------------------------------

# 220. API Ownership

Chaque domaine API doit avoir un owner.

------------------------------------------------------------------------

# 221. API Catalog

À maturité, maintenir un catalogue :

``` text
endpoint
owner
version
SLO
consumers
```

------------------------------------------------------------------------

# 222. API Dependency Map

Permettre de connaître :

``` text
who consumes what
```

------------------------------------------------------------------------

# 223. Deprecation Usage Tracking

Avant suppression d'un endpoint, mesurer ses consommateurs.

------------------------------------------------------------------------

# 224. Internal vs External

Marquer les endpoints :

``` text
PUBLIC
INTERNAL
OPERATOR
ADMIN
```

------------------------------------------------------------------------

# 225. Public API

Si QuantLab expose un jour une API externe, elle doit avoir :

``` text
separate credentials
quotas
strong versioning
documentation
```

------------------------------------------------------------------------

# 226. Internal API

Peut évoluer plus rapidement mais reste contractuelle.

------------------------------------------------------------------------

# 227. Operator API

Destinée aux actions d'exploitation.

------------------------------------------------------------------------

# 228. Admin API

Destinée aux changements de configuration ou gouvernance à fort
privilège.

------------------------------------------------------------------------

# 229. V1 API Domains

La V1 doit couvrir au minimum :

``` text
system
market data
analysis
scores
decisions
risk
orders
fills
positions
strategies
experiments
governance
```

------------------------------------------------------------------------

# 230. V1 OpenAPI Structure

``` text
api/
├── openapi.yaml
├── schemas/
│   ├── common.yaml
│   ├── market_data.yaml
│   ├── decisions.yaml
│   ├── risk.yaml
│   ├── execution.yaml
│   └── experiments.yaml
└── examples/
```

------------------------------------------------------------------------

# 231. Common Schemas

Inclure :

``` text
Error
Money
Pagination
Timestamp
RequestMetadata
```

------------------------------------------------------------------------

# 232. V1 Middleware

Standardiser :

``` text
request ID
authentication
authorization
logging
validation
error handling
```

------------------------------------------------------------------------

# 233. V1 Error Taxonomy

Catégories :

``` text
VALIDATION_
AUTH_
PERMISSION_
DATA_
RISK_
EXECUTION_
GOVERNANCE_
SYSTEM_
```

------------------------------------------------------------------------

# 234. V1 Required Safety

Avant toute exposition live :

``` text
Decision
↓
Risk Approval
↓
Execution API
```

Aucun endpoint alternatif ne doit permettre :

``` text
Strategy
→ Exchange
```

------------------------------------------------------------------------

# 235. V1 Idempotency Requirements

Obligatoire sur :

``` text
order submission
order cancellation
critical state-changing requests
deployment requests
```

selon sémantique.

------------------------------------------------------------------------

# 236. V1 Audit Requirements

Obligatoire pour :

``` text
risk changes
orders
kill switch
strategy activation
governance approvals
deployments
```

------------------------------------------------------------------------

# 237. V1 Testing Requirements

Chaque endpoint critique doit avoir :

``` text
schema test
authorization test
happy path
invalid input
failure path
```

------------------------------------------------------------------------

# 238. V1 Documentation Requirements

Chaque endpoint doit apparaître dans OpenAPI.

------------------------------------------------------------------------

# 239. V2

Ajouter :

-   generated SDKs ;
-   event schema registry ;
-   richer streaming APIs ;
-   API catalog ;
-   automated compatibility checks ;
-   advanced quotas.

------------------------------------------------------------------------

# 240. V3

Ajouter :

-   policy-as-code gateway ;
-   signed service identities ;
-   richer external API capabilities ;
-   multi-region routing where justified ;
-   automated dependency mapping.

------------------------------------------------------------------------

# 241. V4

Ajouter :

-   governance-aware agent APIs ;
-   autonomous workflow APIs with constrained permissions ;
-   machine-verifiable policy contracts ;
-   adaptive rate and risk controls.

------------------------------------------------------------------------

# 242. Critères d'acceptation V1

L'API V1 est valide lorsque :

-   `/api/v1` constitue la version officielle ;
-   tous les endpoints sont documentés via OpenAPI ;
-   les inputs sont validés ;
-   les erreurs utilisent un format standard ;
-   les timestamps sont UTC ;
-   les valeurs financières évitent les floats ambigus ;
-   chaque requête possède un request ID ;
-   les workflows possèdent un correlation ID lorsque nécessaire ;
-   l'authentification est obligatoire ;
-   l'autorisation est appliquée par endpoint ;
-   les agents IA disposent de permissions limitées ;
-   l'envoi d'ordre est idempotent ;
-   aucun ordre stratégique live ne contourne le Risk Engine ;
-   les décisions et approvals peuvent expirer ;
-   les transitions d'état sont validées ;
-   les actions critiques sont auditées ;
-   les secrets ne sont jamais exposés ;
-   les APIs critiques sont observables ;
-   les breaking changes sont détectés et versionnés.

------------------------------------------------------------------------

# 243. Risques principaux

## Contract Drift

Le code et la documentation divergent.

## Authorization Bypass

Un endpoint secondaire contourne une politique métier.

## Duplicate Side Effects

Un retry crée deux ordres ou deux déploiements.

## Ambiguous Numeric Semantics

`1` signifie 1 %, 100 %, 1 USD ou 1 contrat selon l'imagination du
développeur. À éviter.

## Breaking Changes

Un service évolue sans coordination avec ses consumers.

## AI Over-Permission

Un agent reçoit plus de droits que sa tâche ne nécessite.

## Hidden Admin Paths

Un endpoint interne devient un contournement permanent de la
gouvernance.

------------------------------------------------------------------------

# 244. Workflow critique de référence

``` text
Market Context
↓
POST /scores/evaluate
↓
POST /decisions/evaluate
↓
POST /risk/evaluate
↓
Risk Approval
↓
POST /orders
↓
Execution Engine
↓
Exchange
↓
Fills
↓
Positions
↓
Monitoring + Reconciliation
```

Chaque transition doit être identifiable et auditée.

------------------------------------------------------------------------

# 245. Règle fondatrice

> **Une API QuantLab ne doit jamais permettre à un caller de demander
> directement un effet dangereux simplement parce qu'il connaît la bonne
> URL.**

L'autorité doit provenir de :

``` text
IDENTITY
+
PERMISSION
+
VALID STATE
+
VALID INPUT
+
RISK APPROVAL
+
GOVERNANCE WHERE REQUIRED
```

L'API n'est donc pas seulement une interface technique.

Elle constitue une frontière de contrôle du système.

------------------------------------------------------------------------

# 246. Statut

**Version : 1.0**

Documents directement liés :

-   `02-Architecture-Generale.md`
-   `03-Data-Engine.md`
-   `04-Storage-Engine.md`
-   `05-Market-Analysis-Engine.md`
-   `06-Market-Structure-Engine.md`
-   `07-Volume-Profile-Engine.md`
-   `08-Smart-Money-Concepts-Engine.md`
-   `09-Scoring-Engine.md`
-   `10-Decision-Engine.md`
-   `11-Risk-Engine.md`
-   `12-Execution-Engine.md`
-   `13-Monitoring-Engine.md`
-   `14-Knowledge-Engine.md`
-   `15-AI-and-Learning-Engine.md`
-   `16-Governance-Engine.md`
-   `17-AI-Development-Protocol.md`
-   `18-Testing-Strategy.md`
-   `19-Deployment-Guide.md`
-   `20-Engineering-Principles.md`
-   `21-Experiment-Registry.md`
-   `23-Database-Schema.md`
-   `24-Security.md`
-   `25-Roadmap.md`

**Prochain document : `23-Database-Schema.md`**
