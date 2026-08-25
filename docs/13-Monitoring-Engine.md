# 13 — Monitoring Engine

**Projet : QuantLab**  
**Document : Monitoring Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Monitoring Engine est la couche d'observabilité opérationnelle de QuantLab.

Sa mission est de permettre au système et à ses opérateurs de savoir, à tout moment :

```text
Que fait QuantLab ?
Est-ce que les composants fonctionnent ?
Les données sont-elles fraîches ?
Les décisions sont-elles cohérentes ?
Le risque reste-t-il sous contrôle ?
Les ordres sont-ils correctement exécutés ?
Existe-t-il une anomalie nécessitant une intervention ?
```

Le Monitoring Engine ne doit pas être considéré comme un simple dashboard.

Il constitue une couche de sécurité.

Un système de trading automatique que personne ne peut observer n'est pas réellement automatisé. C'est simplement une boîte noire disposant d'un accès au capital, ce qui est une nuance assez importante.

---

# 2. Principe fondamental

Le Monitoring Engine doit rendre QuantLab :

```text
observable
measurable
auditable
alertable
diagnosable
```

Il doit couvrir toute la chaîne :

```text
Data
↓
Analysis
↓
Scoring
↓
Decision
↓
Risk
↓
Execution
↓
Portfolio
↓
Infrastructure
```

---

# 3. Responsabilités

Le Monitoring Engine doit :

1. collecter les métriques ;
2. collecter les événements ;
3. centraliser les logs ;
4. suivre la santé des composants ;
5. mesurer la fraîcheur des données ;
6. surveiller les décisions ;
7. surveiller le risque ;
8. surveiller les ordres ;
9. surveiller les positions ;
10. surveiller les venues ;
11. surveiller les dépendances ;
12. détecter les anomalies ;
13. générer les alertes ;
14. gérer leur sévérité ;
15. éviter le spam d'alertes ;
16. fournir des dashboards ;
17. conserver un historique ;
18. permettre l'investigation ;
19. publier les incidents ;
20. alimenter le Knowledge Engine.

---

# 4. Hors périmètre

Le Monitoring Engine ne doit pas :

- générer des signaux ;
- prendre des décisions de trading ;
- modifier les scores ;
- augmenter les limites de risque ;
- envoyer des ordres ;
- réparer silencieusement une anomalie critique sans audit ;
- devenir une dépendance obligatoire pour permettre les sorties de sécurité.

---

# 5. Architecture générale

```text
Data Engine ──────────────┐
Storage Engine ───────────┤
Analysis Engines ─────────┤
Scoring Engine ───────────┤
Decision Engine ──────────┤
Risk Engine ──────────────┤
Execution Engine ─────────┤
Infrastructure ───────────┤
                         ↓
                ┌───────────────────┐
                │ MONITORING ENGINE │
                ├───────────────────┤
                │ Metrics           │
                │ Logs              │
                │ Events            │
                │ Health Checks     │
                │ Alerting          │
                │ Dashboards        │
                │ Incident Context  │
                └─────────┬─────────┘
                          ↓
                   Operators
                          ↓
                  Knowledge Engine
```

---

# 6. Trois piliers d'observabilité

Le système doit centraliser :

```text
METRICS
LOGS
TRACES
```

auxquels QuantLab ajoute :

```text
DOMAIN EVENTS
```

Les événements métier sont essentiels dans un système de trading.

---

# 7. Metrics

Les métriques répondent notamment à :

```text
Combien ?
À quelle fréquence ?
Avec quelle latence ?
Quel niveau ?
```

Exemples :

```text
data_lag_seconds
decision_latency_ms
portfolio_heat
orders_rejected_total
```

---

# 8. Logs

Les logs répondent :

```text
Que s'est-il passé précisément ?
```

Ils doivent être structurés et corrélables.

---

# 9. Traces

Les traces permettent de suivre une opération entre plusieurs composants.

Exemple :

```text
Market Event
↓
Scoring
↓
Decision
↓
Risk
↓
Execution
```

---

# 10. Domain Events

Exemples :

```text
CANDLE_CLOSED
STRUCTURE_CHANGED
SCORE_UPDATED
DECISION_CREATED
RISK_REJECTED
ORDER_FILLED
POSITION_CLOSED
```

Ils donnent un sens métier aux métriques techniques.

---

# 11. Health Model

Chaque composant doit exposer un état standardisé.

Valeurs recommandées :

```text
HEALTHY
DEGRADED
UNHEALTHY
UNKNOWN
```

---

# 12. HEALTHY

Le composant fonctionne dans les paramètres normaux.

---

# 13. DEGRADED

Le composant fonctionne partiellement mais présente une anomalie.

Exemple :

```text
market data delayed
```

---

# 14. UNHEALTHY

Le composant ne peut plus remplir correctement sa fonction.

---

# 15. UNKNOWN

Le système ne dispose pas de suffisamment d'informations pour connaître son état.

Pour les composants critiques :

```text
UNKNOWN
```

doit être traité avec prudence.

---

# 16. Global System State

Le Monitoring Engine doit construire un état global.

Exemple :

```text
SYSTEM_HEALTH:
HEALTHY
DEGRADED
CRITICAL
```

---

# 17. Critical Path

Le chemin critique est :

```text
Market Data
↓
Decision
↓
Risk
↓
Execution
```

Une défaillance d'un composant critique doit avoir un poids supérieur à une défaillance d'un composant secondaire.

---

# 18. Dependency Health

Chaque service doit connaître ses dépendances.

Exemple :

```text
Execution Engine:
- database
- Risk Engine
- exchange API
- websocket
```

---

# 19. Liveness

Un health check de type :

```text
liveness
```

répond :

> Le processus est-il vivant ?

---

# 20. Readiness

Un health check :

```text
readiness
```

répond :

> Le service est-il réellement prêt à traiter des requêtes ?

Un processus vivant mais déconnecté de sa base n'est pas prêt.

---

# 21. Data Engine Monitoring

Métriques principales :

```text
market_data_events_total
data_ingestion_rate
data_lag_seconds
missing_candles_total
duplicate_events_total
out_of_order_events_total
provider_errors_total
websocket_reconnects_total
```

---

# 22. Data Freshness

Pour chaque flux :

```text
freshness =
now - latest_event_timestamp
```

---

# 23. Data Freshness Thresholds

Exemple :

```text
NORMAL < 2s
WARNING 2–10s
CRITICAL > 10s
```

Les seuils doivent dépendre du timeframe et du fournisseur.

---

# 24. Missing Candle Detection

Pour un timeframe donné :

```text
expected candle
vs
received candle
```

Une absence doit produire un événement.

---

# 25. Duplicate Data

Surveiller :

```text
duplicate_candle
duplicate_trade
duplicate_orderbook_update
```

---

# 26. Out-of-Order Data

Compteur :

```text
out_of_order_events_total
```

Une augmentation soudaine peut signaler un problème fournisseur ou réseau.

---

# 27. Provider Health

Par provider :

```text
connection_status
message_rate
latency
error_rate
reconnect_count
```

---

# 28. Storage Engine Monitoring

Métriques :

```text
db_connections
db_query_latency
db_errors
write_latency
read_latency
storage_usage
replication_lag
backup_status
```

---

# 29. Database Availability

Une perte de base peut rendre impossible :

```text
state persistence
audit
reconciliation
```

Elle doit donc être fortement surveillée.

---

# 30. Database Saturation

Surveiller :

```text
connection_pool_usage
CPU
memory
disk I/O
locks
```

selon l'infrastructure utilisée.

---

# 31. Storage Growth

Mesurer :

```text
storage_bytes
daily_growth
retention_projection
```

afin d'éviter de découvrir que le disque est plein lorsque le système tente précisément d'enregistrer un incident. Les machines ont un sens du timing remarquable.

---

# 32. Backup Monitoring

État :

```text
last_successful_backup
backup_age
backup_failure_count
```

---

# 33. Market Analysis Monitoring

Mesurer :

```text
analysis_runs_total
analysis_latency
analysis_errors
market_regime_distribution
volatility_regime_distribution
```

---

# 34. Market Structure Monitoring

Mesurer :

```text
bos_detected_total
choch_detected_total
swing_points_total
structure_state_changes
structure_errors
```

---

# 35. Volume Profile Monitoring

Mesurer :

```text
profiles_computed
profile_latency
poc_updates
vah_updates
val_updates
profile_errors
```

---

# 36. SMC Monitoring

Mesurer :

```text
order_blocks_detected
fvgs_detected
liquidity_sweeps_detected
smc_invalidations
smc_processing_latency
```

---

# 37. Scoring Engine Monitoring

Métriques :

```text
scores_generated
score_latency
score_errors

average_long_score
average_short_score
average_confidence

score_distribution
```

---

# 38. Score Distribution

Une dérive soudaine peut signaler un problème.

Exemple :

```text
90% des scores passent soudainement > 95
```

Ce n'est probablement pas que le marché est devenu généreux.

---

# 39. Score Drift

Comparer :

```text
current score distribution
vs
historical baseline
```

---

# 40. Decision Engine Monitoring

Mesurer :

```text
decisions_total
no_trade_total
watch_total
long_candidates
short_candidates
enter_long_total
enter_short_total
exit_total
```

---

# 41. Decision Funnel

Exemple :

```text
10000 evaluations
↓
1500 WATCH
↓
500 candidates
↓
200 trade intents
↓
150 risk approved
↓
140 executed
```

---

# 42. Decision Rejection Reasons

Mesurer :

```text
SCORE_TOO_LOW
CONFIDENCE_TOO_LOW
DIRECTION_CONFLICT
COOLDOWN_ACTIVE
REGIME_NOT_ALLOWED
```

---

# 43. Decision State Monitoring

Détecter les stratégies bloquées trop longtemps dans :

```text
PENDING_ENTRY
PENDING_EXIT
RECONCILING
```

---

# 44. Risk Engine Monitoring

Le Risk Engine est une priorité absolue.

Métriques :

```text
risk_checks_total
risk_approved_total
risk_modified_total
risk_rejected_total

portfolio_heat
gross_exposure
net_exposure
open_risk
reserved_risk

daily_pnl
drawdown
```

---

# 45. Risk State

Afficher en permanence :

```text
NORMAL
CAUTION
REDUCED
REDUCE_ONLY
PAUSED
EMERGENCY
```

---

# 46. Risk Threshold Proximity

Ne pas alerter uniquement lorsque la limite est dépassée.

Mesurer :

```text
current_value / limit
```

Exemple :

```text
portfolio_heat = 3.8%
limit = 4.0%
```

doit déjà être visible.

---

# 47. Drawdown Monitoring

Afficher :

```text
current_equity
equity_peak
current_drawdown
drawdown_state
```

---

# 48. Daily Loss Monitoring

Afficher :

```text
daily_realized_pnl
daily_unrealized_pnl
daily_loss_limit
remaining_daily_risk
```

---

# 49. Risk Reservation Monitoring

Mesurer :

```text
reserved_risk
consumed_risk
expired_reservations
stale_reservations
```

---

# 50. Execution Engine Monitoring

Métriques :

```text
orders_created
orders_submitted
orders_acknowledged
orders_filled
orders_partially_filled
orders_cancelled
orders_rejected
orders_unknown
```

---

# 51. Execution Latency

Mesurer :

```text
submit_latency
ack_latency
fill_latency
cancel_latency
```

---

# 52. Slippage Monitoring

Mesurer :

```text
average_slippage_bps
median_slippage_bps
p95_slippage_bps
max_slippage_bps
```

---

# 53. Fee Monitoring

Mesurer :

```text
fees_total
fees_by_strategy
fees_by_symbol
fees_by_venue
```

---

# 54. Order Rejection Rate

```text
rejection_rate =
rejected_orders
/
submitted_orders
```

Une hausse soudaine doit déclencher une alerte.

---

# 55. Partial Fill Rate

```text
partial_fill_rate
```

peut révéler :

- mauvaise liquidité ;
- ordre trop important ;
- execution policy mal adaptée.

---

# 56. Unknown Orders

Toute augmentation de :

```text
orders_unknown
```

est critique.

---

# 57. Protective Order Monitoring

Pour chaque position qui exige une protection :

```text
position_open
AND
protective_stop_missing
```

doit produire une alerte critique.

---

# 58. Position Monitoring

Pour chaque position :

```text
symbol
direction
quantity
entry_price
current_price
unrealized_pnl
stop
targets
risk
```

---

# 59. Position Reconciliation

Comparer :

```text
internal_position
exchange_position
```

---

# 60. Position Mismatch

Une divergence doit produire :

```text
POSITION_RECONCILIATION_FAILED
```

avec haute sévérité.

---

# 61. Order Reconciliation

Comparer :

```text
internal_open_orders
exchange_open_orders
```

---

# 62. Orphan Order Monitoring

Détecter :

```text
exchange order
without internal record
```

---

# 63. Orphan Position Monitoring

Détecter :

```text
exchange position
without internal state
```

Sévérité :

```text
CRITICAL
```

---

# 64. Venue Monitoring

Par venue :

```text
REST health
WebSocket health
latency
authentication status
order rejection rate
reconnect count
rate limit usage
```

---

# 65. Venue Degradation

Exemple :

```text
WebSocket unstable
+
REST latency high
```

peut produire :

```text
VENUE_DEGRADED
```

---

# 66. Infrastructure Monitoring

Mesurer :

```text
CPU
memory
disk
network
process uptime
container restarts
```

---

# 67. Application Monitoring

Mesurer :

```text
request_rate
error_rate
latency
queue_depth
worker_utilization
```

---

# 68. Queue Monitoring

Pour les architectures événementielles :

```text
queue_depth
consumer_lag
oldest_message_age
dead_letter_count
```

---

# 69. Consumer Lag

Une accumulation peut signifier :

```text
processing slower than incoming events
```

---

# 70. Dead Letter Queue

Les événements impossibles à traiter doivent être conservés dans une :

```text
DLQ
```

plutôt que supprimés silencieusement.

---

# 71. Event Bus Monitoring

Mesurer :

```text
events_published
events_consumed
events_failed
consumer_lag
```

---

# 72. API Monitoring

Mesurer :

```text
requests_total
request_latency
4xx_rate
5xx_rate
```

---

# 73. Dependency Monitoring

Dépendances externes :

```text
market data provider
exchange
database
cache
message broker
AI provider
```

---

# 74. AI Provider Monitoring

Lorsque QuantLab utilisera des modèles externes :

```text
request_latency
errors
token usage
cost
model_version
```

Mais une panne d'IA ne doit jamais empêcher les mécanismes de sécurité fondamentaux.

---

# 75. Logging Standard

Tous les services doivent utiliser des logs structurés.

Exemple :

```json
{
  "timestamp": "...",
  "level": "INFO",
  "service": "execution-engine",
  "event": "ORDER_FILLED",
  "correlation_id": "...",
  "order_id": "...",
  "symbol": "BTC-USDT"
}
```

---

# 76. Log Levels

Utiliser :

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

---

# 77. DEBUG

Informations détaillées utiles au développement.

À limiter en production.

---

# 78. INFO

Événements opérationnels normaux.

---

# 79. WARNING

Anomalie non critique mais nécessitant attention.

---

# 80. ERROR

Une opération a échoué.

---

# 81. CRITICAL

L'intégrité financière, la sécurité ou la continuité du système peut être compromise.

---

# 82. No Secrets in Logs

Ne jamais logger :

```text
API keys
private keys
passwords
access tokens
secret headers
```

---

# 83. Sensitive Data Masking

Les données sensibles doivent être masquées avant ingestion dans la plateforme de logs.

---

# 84. Correlation IDs

Chaque workflow doit pouvoir être suivi.

Exemple :

```text
market_event_id
↓
analysis_id
↓
score_id
↓
decision_id
↓
risk_decision_id
↓
order_id
↓
fill_id
```

---

# 85. Trace ID

Un :

```text
trace_id
```

peut regrouper l'ensemble du workflow.

---

# 86. Distributed Tracing

Une implémentation future peut utiliser :

```text
OpenTelemetry
```

ou équivalent.

---

# 87. Alert Model

Structure conceptuelle :

```python
Alert:
    alert_id
    timestamp

    severity
    category
    source

    title
    description

    entity_type
    entity_id

    status

    first_seen
    last_seen
    occurrence_count

    correlation_id
```

---

# 88. Sévérités

Valeurs :

```text
INFO
WARNING
HIGH
CRITICAL
```

---

# 89. INFO Alert

Événement utile sans intervention urgente.

---

# 90. WARNING Alert

Anomalie à surveiller.

---

# 91. HIGH Alert

Intervention probablement nécessaire.

---

# 92. CRITICAL Alert

Risque immédiat pour :

```text
capital
positions
execution integrity
system integrity
```

---

# 93. Alert Categories

Exemples :

```text
DATA
STORAGE
ANALYSIS
DECISION
RISK
EXECUTION
VENUE
INFRASTRUCTURE
SECURITY
AI
```

---

# 94. Alert Deduplication

Une même anomalie répétée ne doit pas générer 10 000 notifications.

Utiliser une clé :

```text
alert_fingerprint
```

---

# 95. Alert Fingerprint

Exemple :

```text
hash(
alert_type,
service,
symbol,
venue
)
```

---

# 96. Alert Aggregation

Au lieu de :

```text
100 alerts identiques
```

produire :

```text
1 alert
occurrence_count = 100
```

---

# 97. Alert Cooldown

Après notification :

```text
notification_cooldown
```

peut limiter les répétitions.

---

# 98. Escalation

Exemple :

```text
WARNING persists 10 min
↓
HIGH

HIGH persists 5 min
↓
CRITICAL
```

---

# 99. Recovery Notification

Lorsqu'un incident disparaît :

```text
RESOLVED
```

doit être publié.

---

# 100. Alert Lifecycle

États :

```text
OPEN
ACKNOWLEDGED
RESOLVED
SUPPRESSED
```

---

# 101. Acknowledgement

Un opérateur peut reconnaître :

```text
ACKNOWLEDGED
```

sans supprimer l'incident.

---

# 102. Suppression

Une suppression doit être :

```text
temporary
reasoned
audited
```

---

# 103. No Permanent Silent Alerts

Une alerte critique ne doit pas pouvoir être désactivée indéfiniment sans trace.

---

# 104. Notification Channels

Canaux possibles :

```text
dashboard
email
Slack
SMS
push
PagerDuty-like system
```

La sélection dépendra du déploiement.

---

# 105. Critical Notification

Les alertes critiques doivent utiliser un canal réellement visible par l'opérateur.

Un dashboard fermé dans un onglet n'est pas une stratégie d'incident particulièrement ambitieuse.

---

# 106. Dashboard Principal

Le dashboard global doit afficher :

```text
System Health
Trading State
Risk State
Execution State
Venue State
Data Freshness
Current Equity
Daily PnL
Drawdown
Portfolio Heat
Open Positions
Open Orders
Active Alerts
```

---

# 107. Data Dashboard

Afficher :

```text
providers
connections
event rates
data lag
missing candles
reconnects
```

---

# 108. Strategy Dashboard

Par stratégie :

```text
status
current state
signals
scores
decisions
risk approvals
positions
PnL
```

---

# 109. Risk Dashboard

Afficher :

```text
equity
open risk
reserved risk
portfolio heat
gross exposure
net exposure
daily PnL
drawdown
risk state
```

---

# 110. Execution Dashboard

Afficher :

```text
orders
fills
rejects
latency
slippage
fees
reconciliation
venue status
```

---

# 111. Incident Dashboard

Afficher :

```text
open alerts
severity
first seen
duration
affected components
related trace IDs
```

---

# 112. Strategy Comparison

Le Monitoring Engine peut afficher :

```text
strategy A
strategy B
```

mais l'analyse statistique approfondie appartient au Knowledge Engine.

---

# 113. SLI

Un Service Level Indicator mesure une propriété réelle.

Exemples :

```text
market_data_freshness
order_ack_latency
risk_engine_availability
```

---

# 114. SLO

Un Service Level Objective fixe une cible.

Exemple :

```text
99.9% des risk checks < 100 ms
```

---

# 115. Critical SLOs

QuantLab peut définir des SLOs pour :

```text
data freshness
risk availability
execution availability
reconciliation success
```

---

# 116. Error Budget

Une version mature peut suivre un :

```text
error budget
```

pour mesurer la fiabilité d'un service.

---

# 117. Monitoring des versions

Chaque métrique métier doit pouvoir être segmentée par :

```text
strategy_version
scoring_version
decision_version
risk_version
execution_version
```

---

# 118. Deployment Monitoring

Après un déploiement :

```text
error rate
latency
decision distribution
risk rejection rate
execution rejection rate
```

doivent être comparés à la baseline.

---

# 119. Canary Monitoring

Pour un déploiement progressif :

```text
old version
vs
new version
```

sur un sous-ensemble contrôlé.

---

# 120. Rollback Signal

Des seuils peuvent déclencher :

```text
automatic deployment rollback
```

pour les erreurs techniques.

Les modifications financières doivent respecter les règles de gouvernance.

---

# 121. Anomaly Detection

Le moteur peut détecter :

```text
sudden latency spike
score distribution shift
rejection spike
unexpected decision frequency
slippage spike
```

---

# 122. Static Thresholds

V1 :

```text
explicit thresholds
```

Ils sont simples, auditables et faciles à tester.

---

# 123. Dynamic Baselines

V2+ :

```text
rolling mean
rolling percentile
seasonal baseline
```

---

# 124. AI-Based Monitoring

Une version future pourra utiliser l'IA pour :

- résumer les incidents ;
- corréler plusieurs anomalies ;
- proposer une cause probable ;
- rechercher des événements similaires.

Elle ne doit pas masquer les alertes déterministes critiques.

---

# 125. Incident Correlation

Exemple :

```text
market data lag
+
score generation drop
+
decision rate drop
```

peuvent provenir d'un seul incident.

---

# 126. Root Cause Context

Une alerte doit idéalement fournir :

```text
what failed
when
affected services
recent deployments
related errors
related metrics
```

---

# 127. Incident Record

Structure :

```text
incident_id
started_at
resolved_at
severity
status
root_cause
affected_components
financial_impact
resolution
```

---

# 128. Financial Impact

Après incident :

```text
missed trades
unexpected fills
slippage impact
fees
position mismatch
realized loss
```

doivent pouvoir être analysés.

---

# 129. Postmortem

Les incidents critiques doivent produire un postmortem.

Sections :

```text
Summary
Timeline
Impact
Root Cause
Detection
Response
Resolution
Corrective Actions
Prevention
```

---

# 130. Blameless Principle

Le postmortem doit chercher :

```text
why the system allowed the failure
```

plutôt que :

```text
who made the mistake
```

Les erreurs humaines sont des données de conception.

---

# 131. Audit Trail

Les actions opérateur doivent être enregistrées :

```text
ack alert
pause strategy
activate kill switch
resume trading
change monitoring threshold
```

---

# 132. Manual Intervention

Chaque intervention doit contenir :

```text
actor
timestamp
reason
action
previous_state
new_state
```

---

# 133. Monitoring Persistence

Tables potentielles :

```text
system_metrics
health_snapshots
alerts
incidents
audit_events
deployment_events
```

Les séries temporelles peuvent utiliser un stockage spécialisé.

---

# 134. Metrics Retention

Définir plusieurs niveaux :

```text
high resolution
medium resolution
long-term aggregates
```

---

# 135. Log Retention

La rétention doit équilibrer :

```text
audit needs
debugging needs
storage cost
security
```

---

# 136. Clock Synchronization

Tous les composants doivent utiliser une horloge correctement synchronisée.

Sinon :

```text
incident timeline
```

devient rapidement une œuvre de fiction.

---

# 137. Time Standard

Recommandation interne :

```text
UTC
```

pour tous les timestamps persistés.

---

# 138. Display Timezone

L'interface peut convertir vers la timezone de l'opérateur.

Mais le stockage reste en UTC.

---

# 139. Monitoring API

Endpoints conceptuels :

```text
GET /health
GET /health/components
GET /metrics
GET /alerts
GET /incidents
GET /system/state
```

Le détail sera défini dans `22-API-Specification.md`.

---

# 140. Security

L'accès aux dashboards doit être authentifié.

Les informations affichées peuvent révéler :

```text
positions
capital
strategies
infrastructure
```

---

# 141. Permission Levels

Exemples :

```text
MONITOR_READ
ALERT_ACK
INCIDENT_MANAGE
SYSTEM_PAUSE
KILL_SWITCH
```

---

# 142. Monitoring Isolation

Une panne du Monitoring Engine ne doit pas :

```text
disable emergency exits
```

Le Risk et l'Execution Engine doivent conserver leurs mécanismes de sécurité locaux.

---

# 143. Monitoring Failure

Si le monitoring principal est indisponible :

```text
MONITORING_DEGRADED
```

doit être détecté par un mécanisme externe ou indépendant lorsque possible.

---

# 144. Dead Man's Switch

Un mécanisme externe peut vérifier :

```text
QuantLab heartbeat
```

Si aucun heartbeat n'est reçu :

```text
external alert
```

---

# 145. Heartbeat

Chaque service critique peut publier :

```text
SERVICE_HEARTBEAT
```

avec :

```text
service
version
timestamp
state
```

---

# 146. Heartbeat Timeout

Exemple :

```text
last heartbeat > threshold
```

→ service considéré `UNKNOWN` ou `UNHEALTHY`.

---

# 147. Monitoring du Kill Switch

Le dashboard doit afficher de manière impossible à manquer :

```text
GLOBAL_KILL_SWITCH:
ACTIVE / INACTIVE
```

---

# 148. Monitoring des stratégies

Chaque stratégie :

```text
RESEARCH
BACKTEST
PAPER
SHADOW
LIVE
DISABLED
```

doit être clairement identifiée.

---

# 149. Environment Identification

L'interface doit distinguer visuellement :

```text
DEVELOPMENT
STAGING
PAPER
PRODUCTION
```

pour réduire les erreurs humaines.

---

# 150. Monitoring Costs

Surveiller également :

```text
data provider cost
AI API cost
infrastructure cost
storage cost
exchange fees
```

---

# 151. Cost per Strategy

À terme :

```text
strategy revenue
-
execution fees
-
data costs
-
infrastructure allocation
```

peut donner une vision économique plus réelle.

---

# 152. Knowledge Engine Integration

Les données de monitoring doivent alimenter :

```text
incident analysis
execution quality
strategy reliability
model drift
```

---

# 153. AI & Learning Integration

L'AI Engine peut recevoir :

```text
aggregated metrics
incident summaries
anomaly history
```

pour proposer des améliorations.

---

# 154. Governance Integration

Les modifications de seuils critiques doivent être versionnées.

Exemple :

```text
POSITION_MISMATCH severity
```

ne doit pas être abaissée silencieusement pour faire disparaître une alerte gênante.

---

# 155. Testing

Le Monitoring Engine doit lui-même être testé.

Un système d'alerte qui n'est jamais testé possède cette charmante propriété de révéler ses défauts uniquement pendant les incidents.

---

# 156. Unit Tests

Tester :

- health aggregation ;
- threshold evaluation ;
- alert severity ;
- deduplication ;
- escalation ;
- resolution ;
- fingerprints.

---

# 157. Alert Tests

Pour chaque alerte critique :

```text
inject failure
↓
verify alert created
↓
verify notification
↓
verify resolution
```

---

# 158. Synthetic Monitoring

Créer des contrôles actifs.

Exemple :

```text
synthetic health request
```

vers les services critiques.

---

# 159. Execution Synthetic Test

En environnement paper/staging :

```text
submit tiny synthetic order
↓
ACK
↓
cancel
```

peut vérifier la chaîne d'exécution.

Jamais de test synthétique live non contrôlé avec capital réel.

---

# 160. Chaos Tests

Simuler :

```text
database failure
exchange disconnect
market data freeze
message queue lag
service crash
```

et vérifier les alertes.

---

# 161. Alert Delivery Test

Tester périodiquement que les canaux de notification fonctionnent réellement.

---

# 162. Dashboard Tests

Vérifier :

```text
correct metrics
correct units
correct timezone
correct environment
```

---

# 163. Metric Naming Convention

Format recommandé :

```text
quantlab_<domain>_<metric>_<unit>
```

Exemple :

```text
quantlab_execution_ack_latency_ms
```

---

# 164. Labels

Labels utiles :

```text
environment
service
strategy
symbol
venue
version
```

---

# 165. Cardinality Control

Éviter les labels à cardinalité énorme comme :

```text
order_id
trade_id
```

dans les systèmes de métriques.

Ces identifiants appartiennent plutôt aux logs/traces.

---

# 166. Golden Signals

Pour chaque service :

```text
latency
traffic
errors
saturation
```

---

# 167. Trading-Specific Golden Signals

Ajouter :

```text
data freshness
risk state
position reconciliation
execution integrity
```

---

# 168. V1 Priorities

Implémenter :

- health checks ;
- structured logs ;
- core metrics ;
- data freshness ;
- Risk Engine metrics ;
- Execution Engine metrics ;
- position reconciliation alerts ;
- protective order alerts ;
- alert severity ;
- deduplication ;
- global dashboard ;
- incident records ;
- audit logs.

---

# 169. V2 Priorities

Ajouter :

- distributed tracing ;
- advanced dashboards ;
- SLOs ;
- escalation ;
- deployment comparison ;
- dynamic baselines.

---

# 170. V3 Priorities

Ajouter :

- automated anomaly detection ;
- incident correlation ;
- cost observability ;
- strategy reliability scoring ;
- external heartbeat monitoring.

---

# 171. V4 Priorities

Ajouter :

- AI incident summaries ;
- probable root-cause suggestions ;
- anomaly clustering ;
- historical incident retrieval ;
- automated remediation proposals sous gouvernance.

---

# 172. Critères d'acceptation V1

La V1 est valide lorsque :

- tous les composants critiques exposent un health state ;
- les données obsolètes sont détectées ;
- les erreurs critiques produisent des alertes ;
- les alertes identiques sont dédupliquées ;
- les positions divergentes sont détectées ;
- les ordres inconnus sont détectés ;
- les stops protecteurs manquants sont détectés ;
- le Risk State est visible ;
- le Kill Switch est visible ;
- les métriques de latence sont disponibles ;
- les logs sont structurés ;
- les workflows disposent de correlation IDs ;
- les actions opérateur sont auditées ;
- les incidents peuvent être reconstruits chronologiquement.

---

# 173. Risques principaux

## Alert Fatigue

Trop d'alertes rendent les vraies alertes invisibles.

## Silent Failure

Une erreur sans alerte peut persister longtemps.

## False Positive

Des seuils trop agressifs créent du bruit.

## Missing Context

Une alerte sans contexte ralentit le diagnostic.

## Monitoring Blind Spot

Le monitoring peut lui-même tomber en panne.

## High Cardinality

De mauvais labels peuvent rendre le système de métriques coûteux ou inutilisable.

---

# 174. Principe de conception

Une bonne alerte doit répondre immédiatement à :

```text
Qu'est-ce qui ne va pas ?
Quelle est la gravité ?
Depuis quand ?
Qu'est-ce qui est affecté ?
Le capital est-il exposé ?
Quelle action est attendue ?
```

---

# 175. Architecture cible

```text
All QuantLab Components
        ↓
Telemetry SDK
        ↓
Metrics + Logs + Traces + Events
        ↓
Monitoring Pipeline
        ↓
Health Evaluation
        ↓
Alert Rules
        ↓
Deduplication
        ↓
Incident Management
        ↓
Dashboards + Notifications
        ↓
Operators
        ↓
Knowledge Engine
```

---

# 176. Résultat attendu

Le Monitoring Engine doit permettre de voir immédiatement une situation telle que :

```text
SYSTEM HEALTH:
DEGRADED

DATA:
HEALTHY

RISK:
NORMAL
Portfolio Heat: 2.8%

EXECUTION:
DEGRADED

Venue:
Binance

Problem:
WebSocket disconnected

REST:
Healthy

Open Positions:
2

Protective Orders:
Verified

New Entries:
Paused

Reconciliation:
Running

Alert:
HIGH
```

L'opérateur doit comprendre la situation sans reconstruire manuellement vingt logs provenant de six services.

---

# 177. Règle fondatrice

> **Ce qui n'est pas observable n'est pas réellement sous contrôle.**

QuantLab doit pouvoir expliquer non seulement :

```text
ce qu'il a décidé
```

mais aussi :

```text
ce qu'il fait maintenant
ce qui fonctionne
ce qui échoue
et si le capital est en sécurité
```

Le Monitoring Engine transforme donc QuantLab d'un ensemble de moteurs en un système exploitable en production.

---

# 178. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `03-Data-Engine.md`
- `04-Storage-Engine.md`
- `05-Market-Analysis-Engine.md`
- `06-Market-Structure-Engine.md`
- `07-Volume-Profile-Engine.md`
- `08-Smart-Money-Concepts-Engine.md`
- `09-Scoring-Engine.md`
- `10-Decision-Engine.md`
- `11-Risk-Engine.md`
- `12-Execution-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `16-Governance-Engine.md`
- `17-AI-Development-Protocol.md`
- `18-Testing-Strategy.md`
- `19-Deployment-Guide.md`
- `20-Engineering-Principles.md`
- `21-Experiment-Registry.md`
- `22-API-Specification.md`
- `23-Database-Schema.md`
- `24-Security.md`

**Prochain document : `14-Knowledge-Engine.md`**
