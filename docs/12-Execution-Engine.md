# 12 — Execution Engine

**Projet : QuantLab**  
**Document : Execution Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

L'Execution Engine est la couche responsable de transformer une intention de trading **déjà validée par le Risk Engine** en actions concrètes sur une venue d'exécution : exchange, broker, DEX ou environnement simulé.

Il constitue la frontière entre :

```text
Décision interne
```

et :

```text
Marché réel
```

Son rôle n'est pas de décider si un trade est intéressant.

Son rôle est de répondre à la question :

> **Comment exécuter de manière fiable, contrôlée, traçable et reproductible l'intention qui a été autorisée ?**

Le moteur doit notamment gérer :

- construction des ordres ;
- validation finale avant envoi ;
- routage ;
- soumission ;
- accusés de réception ;
- fills ;
- partial fills ;
- annulations ;
- modifications ;
- retries contrôlés ;
- idempotence ;
- slippage ;
- frais ;
- état des ordres ;
- synchronisation avec la venue ;
- reconciliation ;
- reprise après incident.

---

# 2. Principe fondamental

La chaîne d'autorité doit rester :

```text
Decision Engine
↓
Risk Engine
↓
Execution Engine
↓
Venue
```

L'Execution Engine ne doit jamais créer une nouvelle exposition qui n'a pas été explicitement autorisée.

Une bonne architecture interdit donc :

```text
Strategy
→ Exchange API
```

et :

```text
AI Engine
→ Exchange API
```

Le seul chemin normal vers le marché passe par une autorisation de risque valide.

---

# 3. Responsabilités

L'Execution Engine doit :

1. recevoir les intentions approuvées ;
2. vérifier leur validité ;
3. vérifier leur expiration ;
4. vérifier la fraîcheur des prix ;
5. construire les ordres ;
6. respecter tick size et quantity step ;
7. choisir le type d'ordre autorisé ;
8. envoyer l'ordre ;
9. gérer les identifiants client ;
10. garantir l'idempotence ;
11. suivre l'état de l'ordre ;
12. traiter les fills ;
13. traiter les partial fills ;
14. gérer les annulations ;
15. gérer les rejets ;
16. gérer les timeouts ;
17. appliquer les politiques de retry ;
18. mesurer le slippage ;
19. mesurer les frais ;
20. mettre à jour les positions ;
21. notifier le Risk Engine ;
22. effectuer la reconciliation ;
23. détecter les divergences ;
24. gérer les modes paper/shadow/live ;
25. produire un audit complet.

---

# 4. Hors périmètre

L'Execution Engine ne doit pas :

- détecter des setups ;
- produire un score ;
- choisir une direction ;
- augmenter une taille approuvée ;
- déplacer arbitrairement un stop ;
- dépasser une limite de risque ;
- apprendre en production ;
- décider qu'un trade refusé mérite quand même d'être exécuté.

---

# 5. Architecture générale

```text
Decision Engine
      ↓
Risk Engine
      ↓
ApprovedIntent
      ↓
┌────────────────────────────┐
│      EXECUTION ENGINE      │
├────────────────────────────┤
│ Pre-Trade Validation       │
│ Order Builder              │
│ Order Router               │
│ Venue Adapter              │
│ Order State Machine        │
│ Fill Processor             │
│ Position Reconciliation    │
│ Execution Analytics        │
└──────────────┬─────────────┘
               ↓
        Exchange / Broker
               ↓
     ACK / FILL / CANCEL
               ↓
        Execution Events
```

---

# 6. Entrée principale

L'entrée standard est :

```text
ApprovedIntent
```

Structure conceptuelle :

```python
ApprovedIntent:
    intent_id
    risk_decision_id

    strategy_id
    symbol
    direction

    approved_quantity
    approved_notional

    entry_type
    entry_reference

    stop_price
    target_references

    max_slippage
    leverage

    approved_at
    valid_until

    risk_version
```

---

# 7. Règle d'autorisation

Avant toute soumission, le moteur doit vérifier :

```text
risk_decision.status
IN
[APPROVED, MODIFIED]
```

Sinon :

```text
EXECUTION_REJECTED
```

---

# 8. Expiration de l'autorisation

Une autorisation de risque ne doit pas être valable indéfiniment.

Condition :

```text
current_time <= valid_until
```

Sinon :

```text
RISK_APPROVAL_EXPIRED
```

et une nouvelle validation est requise.

---

# 9. Validation pré-trade

Avant l'envoi :

```text
ApprovedIntent valid
↓
Risk approval valid
↓
Symbol enabled
↓
Venue available
↓
Price fresh
↓
Quantity valid
↓
Order constraints valid
↓
Execution allowed
```

Seulement ensuite :

```text
SUBMIT
```

---

# 10. Price Freshness

Le moteur doit vérifier l'âge du prix utilisé.

Exemple :

```text
price_age <= max_price_age
```

Si le marché s'est déplacé trop rapidement :

```text
REVALIDATION_REQUIRED
```

---

# 11. Entry Deviation

Condition possible :

```text
abs(current_price - approved_reference_price)
/
approved_reference_price
<= max_entry_deviation
```

Sinon le Risk Engine doit recalculer le risque.

---

# 12. Venue Adapter

Chaque venue doit être isolée derrière une interface commune.

Exemple :

```python
class ExecutionVenue:

    submit_order(...)
    cancel_order(...)
    modify_order(...)
    get_order(...)
    get_open_orders(...)
    get_positions(...)
    get_balances(...)
```

---

# 13. Pourquoi utiliser des adapters

Sans adapter :

```text
strategy logic
+
Binance specifics
+
broker specifics
+
simulation specifics
```

finissent mélangés.

Avec adapter :

```text
Execution Engine
↓
Common Interface
↓
BinanceAdapter
KrakenAdapter
IBKRAdapter
PaperAdapter
```

---

# 14. Modes d'exécution

Le moteur doit supporter :

```text
BACKTEST
PAPER
SHADOW
LIVE
```

---

# 15. BACKTEST

Les ordres sont simulés à partir des données historiques.

Aucune connexion externe.

---

# 16. PAPER

Le système fonctionne avec les données live mais les ordres sont simulés.

---

# 17. SHADOW

La stratégie et le moteur produisent les décisions qu'ils auraient exécutées, mais aucune exposition réelle n'est créée.

---

# 18. LIVE

Les ordres sont réellement transmis à la venue.

Le passage vers `LIVE` doit être explicitement contrôlé.

---

# 19. Même interface

Le code métier doit autant que possible utiliser :

```text
ExecutionVenue
```

indépendamment du mode.

Cela réduit les différences entre test et production.

---

# 20. Order Request

Structure conceptuelle :

```python
OrderRequest:
    client_order_id
    intent_id

    venue
    symbol

    side
    order_type

    quantity
    price

    stop_price
    time_in_force

    reduce_only
    post_only

    created_at
```

---

# 21. Client Order ID

Chaque ordre doit avoir un identifiant généré par QuantLab.

Exemple :

```text
QL-{strategy}-{intent}-{sequence}
```

Cet identifiant doit être stable pour permettre l'idempotence.

---

# 22. Exchange Order ID

Après acceptation, la venue retourne généralement :

```text
exchange_order_id
```

QuantLab doit conserver les deux :

```text
client_order_id
exchange_order_id
```

---

# 23. Idempotence

Une nouvelle tentative ne doit pas créer accidentellement deux ordres.

Exemple dangereux :

```text
submit order
↓
network timeout
↓
unknown response
↓
submit again
```

Le premier ordre peut déjà exister.

---

# 24. Politique après timeout

Après un timeout :

```text
DO NOT blindly resubmit
```

Procédure :

```text
query by client_order_id
↓
if found:
    reconcile
else:
    retry according to policy
```

---

# 25. Exactly-Once Illusion

Dans un système distribué, garantir une exécution réellement « exactly once » est difficile.

L'objectif pratique est :

```text
at-least-once communication
+
idempotent processing
+
reconciliation
```

---

# 26. Order Types

Types potentiels :

```text
MARKET
LIMIT
STOP
STOP_LIMIT
TAKE_PROFIT
```

La V1 doit supporter seulement les types réellement nécessaires.

---

# 27. MARKET

Avantage :

```text
probabilité d'exécution élevée
```

Inconvénient :

```text
prix non garanti
slippage
```

---

# 28. LIMIT

Avantage :

```text
prix contrôlé
```

Inconvénient :

```text
fill non garanti
```

---

# 29. STOP

Utilisé pour déclencher une action lorsque le marché atteint un niveau.

Les comportements exacts varient selon les venues.

---

# 30. Venue Semantics

Le même nom d'ordre peut avoir des comportements différents selon les plateformes.

Les adapters doivent normaliser ces différences autant que possible.

---

# 31. Time In Force

Valeurs courantes :

```text
GTC
IOC
FOK
```

La stratégie doit définir ce qu'elle autorise.

---

# 32. Post Only

Pour certaines stratégies :

```text
post_only = true
```

peut éviter un taker fill.

Mais cela peut également provoquer un rejet si l'ordre croise immédiatement le book.

---

# 33. Reduce Only

Les ordres de sortie sur dérivés doivent utiliser :

```text
reduce_only
```

lorsque disponible.

Objectif :

```text
une sortie ne doit jamais ouvrir accidentellement une position inverse
```

---

# 34. Position Side

Le moteur doit gérer explicitement :

```text
LONG
SHORT
FLAT
```

et les particularités de la venue :

```text
one-way mode
hedge mode
```

---

# 35. Recommended V1

Choisir un mode unique par venue et le documenter.

Supporter toutes les variantes dès le départ est une manière très efficace de transformer un moteur d'exécution en musée des cas particuliers.

---

# 36. Order State Machine

États recommandés :

```text
CREATED
VALIDATING
READY
SUBMITTING
SUBMITTED
ACKNOWLEDGED
PARTIALLY_FILLED
FILLED
CANCEL_PENDING
CANCELLED
REJECTED
EXPIRED
UNKNOWN
```

---

# 37. CREATED

L'ordre existe localement mais n'a pas encore été validé.

---

# 38. VALIDATING

Les contrôles pré-trade sont en cours.

---

# 39. READY

L'ordre est prêt à être envoyé.

---

# 40. SUBMITTING

La requête est en transit.

---

# 41. SUBMITTED

La requête a été envoyée mais la confirmation finale peut ne pas être disponible.

---

# 42. ACKNOWLEDGED

La venue confirme que l'ordre existe.

---

# 43. PARTIALLY_FILLED

Une partie de la quantité a été exécutée.

---

# 44. FILLED

La quantité attendue a été entièrement exécutée.

---

# 45. CANCEL_PENDING

Une annulation a été demandée.

---

# 46. CANCELLED

La venue confirme l'annulation.

---

# 47. REJECTED

La venue refuse l'ordre.

---

# 48. EXPIRED

L'ordre n'est plus actif à cause d'une expiration.

---

# 49. UNKNOWN

QuantLab ne peut pas déterminer l'état réel.

`UNKNOWN` doit être traité comme un état sérieux nécessitant reconciliation.

---

# 50. State Transition Validation

Les transitions doivent être contrôlées.

Exemple :

```text
CREATED → FILLED
```

ne devrait pas apparaître sans événements intermédiaires ou reconstruction explicite.

---

# 51. Fill

Structure :

```python
Fill:
    fill_id
    client_order_id
    exchange_order_id

    symbol
    side

    quantity
    price

    fee
    fee_currency

    timestamp
```

---

# 52. Partial Fill

Exemple :

```text
requested = 1 BTC
filled = 0.35 BTC
remaining = 0.65 BTC
```

Le système doit immédiatement mettre à jour :

```text
position
risk consumed
remaining risk reservation
```

---

# 53. Weighted Average Fill Price

Calcul :

```text
average_fill_price =
Σ(price_i × quantity_i)
/
Σ(quantity_i)
```

---

# 54. Fill Deduplication

Un même fill reçu via :

```text
websocket
```

puis :

```text
REST reconciliation
```

ne doit pas être compté deux fois.

Utiliser :

```text
fill_id
```

ou une clé déterministe.

---

# 55. Fees

Les frais réels doivent être enregistrés par fill.

Ne pas se contenter d'une estimation théorique.

---

# 56. Maker / Taker

Lorsque disponible, enregistrer :

```text
liquidity_role:
MAKER
TAKER
```

Cela permet d'analyser les coûts d'exécution.

---

# 57. Slippage

Pour une entrée :

```text
slippage =
actual_fill_price
-
reference_price
```

avec convention directionnelle adaptée.

---

# 58. Slippage en basis points

```text
slippage_bps =
(actual_price - reference_price)
/
reference_price
× 10000
```

Le signe doit être normalisé pour que :

```text
positive = adverse
negative = favorable
```

si cette convention est retenue.

---

# 59. Implementation Shortfall

Une mesure plus complète peut comparer :

```text
decision/reference price
```

au coût réellement obtenu.

Cela capture mieux le coût d'exécution qu'un simple spread.

---

# 60. Expected vs Realized Slippage

Le système doit conserver :

```text
estimated_slippage
realized_slippage
```

afin de calibrer les modèles du Risk Engine.

---

# 61. Order Routing

Si plusieurs venues sont disponibles, une version future pourra choisir selon :

```text
price
liquidity
fees
latency
venue risk
```

---

# 62. V1 Routing

Pour la V1 :

```text
strategy / symbol
→ predefined venue
```

est préférable.

Le Smart Order Routing peut venir plus tard.

---

# 63. Smart Order Routing futur

Une version avancée pourra répartir :

```text
large order
```

sur plusieurs venues.

Mais cela introduit :

- fragmentation ;
- synchronisation ;
- frais multiples ;
- partial fills ;
- risque de venue ;
- complexité de reconciliation.

---

# 64. Order Splitting

Pour limiter l'impact marché :

```text
parent order
↓
child orders
```

peut être utilisé.

---

# 65. Parent Order

Structure conceptuelle :

```text
parent_order_id
approved_quantity
execution_policy
```

---

# 66. Child Orders

Chaque child order doit être relié au parent.

La somme des fills ne doit jamais dépasser la quantité autorisée.

---

# 67. TWAP futur

Une stratégie d'exécution future peut utiliser :

```text
TWAP
```

pour répartir un ordre dans le temps.

---

# 68. VWAP futur

Une autre approche peut suivre le profil de volume attendu.

---

# 69. Participation Rate

Exemple :

```text
do not exceed X% of observed market volume
```

Cette politique est surtout pertinente pour les tailles significatives.

---

# 70. Execution Policy

Chaque intention peut référencer :

```text
execution_policy_id
```

Exemples :

```text
MARKET_IMMEDIATE
PASSIVE_LIMIT
LIMIT_WITH_TIMEOUT
TWAP
```

---

# 71. Limit With Timeout

Exemple :

```text
place limit
↓
wait N seconds/bars
↓
if not filled:
    cancel
```

Une conversion en market doit nécessiter une policy explicite et éventuellement une nouvelle validation de risque.

---

# 72. Repricing

Le moteur peut déplacer un limit order selon une règle définie.

Mais il doit respecter :

```text
max_entry_deviation
max_slippage
risk approval
```

---

# 73. No Unlimited Chase

Un ordre ne doit pas suivre le marché indéfiniment.

Sinon une intention validée à un prix peut finir exécutée dans un contexte complètement différent.

---

# 74. Intent Expiration

Chaque intention doit posséder :

```text
expires_at
```

Une fois expirée :

```text
cancel remaining orders
```

selon la policy.

---

# 75. Protective Orders

Après entrée, le système peut créer :

```text
stop loss
take profit
```

selon le plan approuvé.

---

# 76. Protection Priority

Une position réelle sans protection attendue est une anomalie critique.

Après un fill d'entrée :

```text
position detected
↓
verify protective orders
```

---

# 77. Atomic Brackets

Si la venue supporte :

```text
bracket order
OCO
```

le système peut les utiliser.

Sinon, QuantLab doit gérer la séquence de façon robuste.

---

# 78. OCO

Concept :

```text
stop
+
take profit
```

Lorsque l'un est exécuté, l'autre doit être annulé.

---

# 79. Synthetic OCO

Si la venue ne supporte pas OCO nativement, QuantLab peut l'émuler.

Cela introduit un risque supplémentaire de race condition.

---

# 80. Race Condition Example

```text
take profit fills
```

pendant que :

```text
stop also triggers
```

Le système doit éviter une position inverse accidentelle.

---

# 81. Reduce-Only Protection

Lorsque disponible, les ordres de sortie doivent être `reduce_only`.

C'est une protection importante contre les doubles exécutions.

---

# 82. Stop Update

Une modification de stop doit suivre :

```text
new approved protective reference
↓
risk validation if required
↓
execution modification
```

---

# 83. Never Widen Risk Silently

L'Execution Engine ne doit jamais éloigner un stop pour éviter une exécution.

Toute augmentation de risque nécessite une nouvelle autorisation.

---

# 84. Stop Failure

Si un stop protecteur est rejeté :

```text
CRITICAL_EXECUTION_ALERT
```

Le système doit appliquer une policy de sécurité.

Possibilités :

```text
retry
alternative order
force exit
```

selon la venue et la configuration.

---

# 85. Cancel/Replace

Certaines venues utilisent :

```text
cancel old order
↓
submit new order
```

plutôt qu'une modification atomique.

La période intermédiaire doit être gérée explicitement.

---

# 86. Retry Policy

Les retries doivent dépendre du type d'erreur.

Exemples :

```text
NETWORK_TIMEOUT
→ retry/reconcile

INVALID_QUANTITY
→ do not retry blindly

INSUFFICIENT_MARGIN
→ reject and alert

RATE_LIMIT
→ backoff
```

---

# 87. Exponential Backoff

Pour certaines erreurs temporaires :

```text
delay_n =
min(max_delay, base_delay × 2^n)
```

avec jitter éventuel.

---

# 88. Retry Limit

Toute opération doit avoir :

```text
max_retry_count
```

Une boucle infinie de soumission est évidemment une manière créative, mais peu recommandée, de découvrir les limites d'une API d'exchange.

---

# 89. Error Classification

Catégories :

```text
TRANSIENT
PERMANENT
AUTHENTICATION
RATE_LIMIT
VALIDATION
UNKNOWN
```

---

# 90. Authentication Error

Une erreur d'authentification doit généralement :

```text
disable new submissions
alert
```

et non déclencher des retries agressifs.

---

# 91. Rate Limits

Chaque adapter doit connaître :

```text
request limits
order limits
websocket limits
```

---

# 92. Rate Limit Manager

Le moteur doit centraliser :

```text
request budget
```

pour éviter que plusieurs composants saturent la venue.

---

# 93. WebSocket

Pour les événements live :

```text
orders
fills
positions
```

le WebSocket est généralement préférable à un polling uniquement REST.

---

# 94. REST

REST reste utile pour :

```text
submission
reconciliation
snapshot
recovery
```

selon la venue.

---

# 95. Dual Channel

Architecture recommandée :

```text
WebSocket
→ low-latency events

REST
→ authoritative reconciliation
```

---

# 96. WebSocket Disconnect

En cas de déconnexion :

```text
mark stream degraded
↓
reconnect
↓
fetch REST snapshot
↓
reconcile missed events
```

---

# 97. Sequence Numbers

Si la venue fournit :

```text
sequence_id
```

le moteur doit les utiliser pour détecter les événements manquants.

---

# 98. Event Ordering

Les événements réseau peuvent arriver dans un ordre différent.

Le système doit utiliser :

```text
venue timestamps
sequence numbers
state rules
```

plutôt que supposer que l'ordre de réception est parfait.

---

# 99. Reconciliation

La reconciliation est une fonction centrale.

Comparer :

```text
local orders
vs
venue orders
```

et :

```text
local positions
vs
venue positions
```

---

# 100. Reconciliation Frequency

Elle peut être déclenchée :

```text
periodically
after reconnect
after timeout
after unknown state
before enabling live trading
```

---

# 101. Order Reconciliation

Pour chaque ordre :

```text
local state
exchange state
```

doivent converger.

---

# 102. Position Reconciliation

Comparer :

```text
local quantity
exchange quantity
average price
```

---

# 103. Balance Reconciliation

Comparer :

```text
cash
margin
equity
```

avec l'état utilisé par le Risk Engine.

---

# 104. Reconciliation Failure

Une divergence critique doit produire :

```text
EXECUTION_DEGRADED
```

et potentiellement :

```text
NEW_ENTRIES_DISABLED
```

---

# 105. Unknown Order

Si un ordre existe sur la venue mais pas localement :

```text
ORPHAN_ORDER
```

Le système doit le traiter selon une policy.

---

# 106. Missing Remote Order

Si QuantLab pense qu'un ordre est ouvert mais que la venue ne le connaît plus :

```text
REMOTE_ORDER_MISSING
```

Une investigation/reconstruction est nécessaire.

---

# 107. Orphan Position

Une position sur la venue sans position correspondante dans QuantLab est critique.

```text
ORPHAN_POSITION
```

---

# 108. Fail Closed

Si l'état d'exécution est inconnu :

```text
new exposure = blocked
```

---

# 109. Risk-Reducing Actions

Même en état dégradé, le système doit conserver autant que possible un chemin permettant :

```text
cancel risk-increasing orders
reduce positions
close positions
```

---

# 110. Execution States

État global possible :

```text
HEALTHY
DEGRADED
RECONCILING
PAUSED
EMERGENCY
```

---

# 111. HEALTHY

Toutes les fonctions nécessaires sont opérationnelles.

---

# 112. DEGRADED

Certaines données ou fonctions sont instables.

Les nouvelles entrées peuvent être limitées.

---

# 113. RECONCILING

Le système reconstruit son état.

Les nouvelles entrées doivent généralement être bloquées.

---

# 114. PAUSED

Aucun nouvel ordre augmentant le risque.

---

# 115. EMERGENCY

Le système applique la procédure de sécurité configurée.

---

# 116. Startup Sequence

Avant d'activer le live :

```text
load configuration
↓
connect venue
↓
authenticate
↓
load balances
↓
load positions
↓
load open orders
↓
reconcile local state
↓
validate Risk Engine
↓
enable execution
```

---

# 117. No Blind Startup

Après redémarrage, le moteur ne doit jamais supposer :

```text
no local position
=
no exchange position
```

Il doit vérifier.

---

# 118. Graceful Shutdown

Procédure :

```text
stop accepting new intents
↓
persist state
↓
reconcile pending operations
↓
close streams
```

Selon la policy, les ordres existants peuvent rester ou être annulés.

---

# 119. Crash Recovery

Après crash :

```text
load persisted orders
↓
fetch venue state
↓
match client IDs
↓
rebuild fills
↓
rebuild positions
↓
reconcile risk reservations
```

---

# 120. Persistence

Tables logiques potentielles :

```text
execution_orders
execution_fills
execution_events
execution_positions
execution_reconciliation
venue_status
```

---

# 121. Order Record

Champs :

```text
order_id
client_order_id
exchange_order_id
intent_id
risk_decision_id

venue
symbol
side
type

requested_quantity
filled_quantity
remaining_quantity

limit_price
average_fill_price

status

created_at
submitted_at
acknowledged_at
completed_at
```

---

# 122. Execution Event

Exemples :

```text
ORDER_CREATED
ORDER_SUBMITTED
ORDER_ACKNOWLEDGED
ORDER_PARTIALLY_FILLED
ORDER_FILLED
ORDER_CANCEL_REQUESTED
ORDER_CANCELLED
ORDER_REJECTED
ORDER_EXPIRED
ORDER_UNKNOWN
```

---

# 123. Event Payload

Chaque événement doit contenir :

```text
event_id
order_id
timestamp
source
previous_state
new_state
raw_venue_reference
```

---

# 124. Raw Venue Payload

Les réponses brutes importantes peuvent être archivées pour audit.

Attention :

- ne jamais logger les secrets ;
- gérer la rétention ;
- masquer les informations sensibles.

---

# 125. Event Sourcing partiel

L'état d'un ordre peut être reconstruit à partir des événements.

Cela facilite :

```text
debugging
audit
replay
```

---

# 126. Determinism

Les décisions de construction d'ordre doivent être déterministes pour un même :

```text
ApprovedIntent
ExecutionPolicy
VenueMetadata
```

Les fills réels, eux, dépendent du marché.

---

# 127. Clock

Comme les autres moteurs, utiliser :

```text
Clock
```

plutôt que des appels dispersés à l'heure système.

---

# 128. Simulation Clock

En backtest :

```text
SimulatedClock
```

doit permettre un replay cohérent.

---

# 129. Paper Fill Model

Le paper trading doit définir comment un ordre est considéré comme exécuté.

Exemple limit :

```text
market trades through limit
```

Mais ce modèle doit éviter les hypothèses trop optimistes.

---

# 130. Conservative Fill Simulation

Une V1 doit préférer une simulation légèrement conservatrice à :

```text
touch = guaranteed fill
```

qui surestime souvent les performances.

---

# 131. Queue Position

Pour les ordres passifs, le simple fait que le marché touche le prix ne garantit pas le fill.

Une version avancée pourra modéliser :

```text
queue position
```

---

# 132. Backtest Slippage

Le backtest doit intégrer :

```text
spread
slippage model
fees
```

---

# 133. Backtest vs Live

Les mêmes objets doivent être utilisés :

```text
OrderRequest
OrderEvent
Fill
```

même si leur source diffère.

---

# 134. Execution Analytics

Le moteur doit mesurer :

```text
fill_rate
partial_fill_rate
cancel_rate
reject_rate
average_slippage
median_slippage
p95_slippage
fees
execution_latency
```

---

# 135. Latency Breakdown

Mesurer :

```text
decision_to_risk
risk_to_execution
order_build
network_submit
venue_ack
ack_to_fill
```

---

# 136. Timestamp Discipline

Conserver :

```text
decision_at
risk_approved_at
execution_received_at
submitted_at
venue_ack_at
fill_at
```

---

# 137. Clock Synchronization

Les serveurs doivent maintenir une horloge correctement synchronisée.

Des timestamps incohérents détruisent rapidement les analyses de latence.

---

# 138. Slippage Analytics

Analyser par :

```text
venue
symbol
order_type
strategy
time_of_day
volatility regime
order size
```

---

# 139. Fill Quality

Comparer :

```text
reference price
arrival price
fill price
mid price
```

selon les données disponibles.

---

# 140. Execution Cost

Coût total conceptuel :

```text
fees
+
spread cost
+
slippage
+
market impact
```

---

# 141. Market Impact

Pour les tailles importantes, le moteur devra distinguer :

```text
slippage
```

de :

```text
impact caused by our own order
```

---

# 142. Execution Benchmark

Benchmarks possibles :

```text
arrival price
mid price
VWAP
decision price
```

---

# 143. Strategy Feedback

Le Knowledge Engine doit pouvoir mesurer si une stratégie théoriquement rentable reste rentable après coûts réels.

C'est là que beaucoup de stratégies « excellentes » découvrent avec une certaine tristesse que les marchés facturent l'entrée.

---

# 144. Monitoring

Métriques opérationnelles :

```text
orders_created
orders_submitted
orders_filled
orders_rejected
orders_cancelled
partial_fills

execution_latency
ack_latency
fill_latency

slippage_bps
fees

websocket_status
rest_status
reconciliation_status
```

---

# 145. Alertes

Exemples :

```text
EXECUTION_ENGINE_DOWN
VENUE_UNAVAILABLE
AUTHENTICATION_FAILED
ORDER_STATE_UNKNOWN
ORPHAN_ORDER
ORPHAN_POSITION
PROTECTIVE_ORDER_MISSING
SLIPPAGE_LIMIT_EXCEEDED
RECONCILIATION_FAILED
ORDER_REJECTION_SPIKE
WEBSOCKET_DISCONNECTED
```

---

# 146. Critical Alerts

Doivent être prioritaires :

```text
POSITION_UNPROTECTED
POSITION_MISMATCH
GLOBAL_EXECUTION_FAILURE
UNKNOWN_LIVE_EXPOSURE
```

---

# 147. Circuit Breaker

Le moteur peut arrêter les nouvelles soumissions si :

```text
rejection rate too high
latency too high
venue unstable
reconciliation failing
```

---

# 148. Circuit Breaker State

Exemple :

```text
CLOSED
OPEN
HALF_OPEN
```

comme dans les architectures distribuées classiques.

---

# 149. CLOSED

Exécution normale.

---

# 150. OPEN

Nouvelles soumissions bloquées.

---

# 151. HALF_OPEN

Un nombre limité d'opérations de test peut être autorisé avant retour à `CLOSED`.

Pour le trading live, ce mécanisme doit rester très conservateur.

---

# 152. Kill Switch

L'Execution Engine doit respecter immédiatement :

```text
GLOBAL_KILL_SWITCH
```

et les kill switches :

```text
strategy
asset
venue
```

---

# 153. Cancel All

Une opération contrôlée doit permettre :

```text
cancel_all_open_orders
```

par :

```text
global
venue
symbol
strategy
```

selon les permissions.

---

# 154. Emergency Flatten

Une procédure séparée peut permettre :

```text
close all positions
```

Elle doit être extrêmement protégée et auditée.

---

# 155. Security

Les credentials de venue ne doivent jamais être :

```text
hardcoded
committed to Git
logged
returned through API
```

---

# 156. Secret Management

Utiliser un mécanisme dédié :

```text
environment secrets
secret manager
vault
```

selon le déploiement.

---

# 157. API Key Permissions

Les clés live doivent avoir uniquement les permissions nécessaires.

Si possible :

```text
trading = enabled
withdrawals = disabled
```

---

# 158. IP Restrictions

Lorsque la venue le permet :

```text
IP whitelist
```

doit être utilisée.

---

# 159. Credential Separation

Séparer :

```text
paper credentials
staging credentials
production credentials
```

---

# 160. Environment Guard

Le moteur doit rendre difficile l'exécution live accidentelle.

Exemple :

```text
EXECUTION_MODE=LIVE
```

doit nécessiter une configuration explicite.

---

# 161. Live Startup Confirmation

Dans certains environnements, un contrôle supplémentaire peut exiger :

```text
production flag
+
valid credentials
+
risk engine healthy
+
manual deployment approval
```

---

# 162. Logging

Chaque opération doit être loggée avec :

```text
correlation_id
intent_id
risk_decision_id
order_id
venue
symbol
status
```

---

# 163. Correlation ID

Le même identifiant doit permettre de suivre :

```text
Decision
↓
Risk
↓
Order
↓
Fill
↓
Position
```

---

# 164. Structured Logs

Préférer :

```json
{
  "event": "ORDER_FILLED",
  "symbol": "BTC-USDT",
  "order_id": "...",
  "quantity": 0.25,
  "price": 100000
}
```

à des chaînes de texte impossibles à analyser automatiquement.

---

# 165. Audit

Pour chaque position, QuantLab doit pouvoir reconstruire :

```text
Signal
↓
Score
↓
Decision
↓
Risk Approval
↓
Order
↓
Venue ACK
↓
Fill(s)
↓
Fees
↓
Slippage
↓
Position
↓
Exit
```

---

# 166. Execution Versioning

Enregistrer :

```text
execution_engine_version
execution_policy_version
venue_adapter_version
```

---

# 167. Adapter Versioning

Une modification du comportement d'un adapter peut changer les résultats réels.

Elle doit donc être versionnée et testée.

---

# 168. Sandbox Testing

Lorsque la venue propose un environnement sandbox/testnet, il doit être utilisé avant live.

Mais un testnet ne reproduit pas nécessairement :

```text
real liquidity
real slippage
real latency
```

---

# 169. Unit Tests

Tester :

- order construction ;
- tick rounding ;
- quantity rounding ;
- state transitions ;
- idempotence ;
- retry policy ;
- expiration ;
- reduce-only ;
- fill aggregation ;
- fee calculations ;
- slippage calculations.

---

# 170. Mock Venue

Créer un :

```text
MockVenueAdapter
```

capable de simuler :

```text
ACK
REJECT
PARTIAL_FILL
FILL
TIMEOUT
DISCONNECT
```

---

# 171. Integration Tests

Tester :

```text
ApprovedIntent
↓
Execution
↓
Mock Venue
↓
Fill
↓
Risk update
```

---

# 172. Timeout Test

Simuler :

```text
submit
↓
timeout
↓
order actually exists remotely
```

Le système doit retrouver l'ordre sans en créer un second.

---

# 173. Duplicate Event Test

Envoyer deux fois le même fill.

Résultat attendu :

```text
position updated once
```

---

# 174. Partial Fill Test

Simuler :

```text
25%
25%
50%
```

et vérifier :

```text
average fill
remaining quantity
risk reservation
position
```

---

# 175. Disconnect Test

Simuler :

```text
WebSocket disconnect
```

pendant un fill.

Après reconnexion :

```text
REST reconciliation
```

doit reconstruire l'état.

---

# 176. Crash Test

Simuler un crash :

```text
after submission
before local ACK persistence
```

Au restart, le client order ID doit permettre de retrouver l'ordre.

---

# 177. Protective Order Test

Simuler :

```text
entry filled
stop rejected
```

et vérifier que la procédure critique est déclenchée.

---

# 178. Reconciliation Tests

Cas :

```text
local order missing remotely
remote order missing locally
position mismatch
balance mismatch
```

---

# 179. Load Tests

Tester :

```text
many symbols
many events
simultaneous fills
```

sans compromettre la cohérence.

---

# 180. Rate Limit Tests

Le système doit respecter les limites même sous charge.

---

# 181. Chaos Testing

Une version avancée peut injecter :

```text
latency
packet loss
timeouts
API errors
process restart
database delay
```

pour vérifier la résilience.

---

# 182. Paper-to-Live Promotion

Une stratégie ne doit pas passer directement de :

```text
BACKTEST
```

à :

```text
FULL LIVE
```

Flux recommandé :

```text
BACKTEST
↓
PAPER
↓
SHADOW
↓
LIMITED LIVE
↓
LIVE
```

---

# 183. Limited Live

Le Risk Engine applique :

```text
small capital
strict exposure
strict order size
```

pendant la phase initiale.

---

# 184. Execution Quality Gate

Une stratégie ne doit pas être promue si :

```text
realized slippage
```

rend son expectancy réelle insuffisante.

---

# 185. Interaction avec Risk Engine

Avant exécution :

```text
RiskDecision required
```

Après exécution :

```text
fills
positions
fees
```

doivent être renvoyés au Risk Engine.

---

# 186. Interaction avec Decision Engine

Le Decision Engine reçoit les changements importants :

```text
entry filled
entry expired
exit filled
order rejected
```

afin de mettre à jour le StrategyState.

---

# 187. Interaction avec Monitoring Engine

Le Monitoring Engine doit recevoir :

```text
venue health
order states
execution latency
slippage
reconciliation status
```

---

# 188. Interaction avec Knowledge Engine

Le Knowledge Engine conserve :

```text
expected execution
actual execution
```

afin d'analyser les coûts.

---

# 189. Interaction avec AI & Learning Engine

L'IA pourra proposer :

- meilleur choix market/limit ;
- estimation de fill probability ;
- modèles de slippage ;
- execution timing ;
- venue selection.

Elle ne doit jamais envoyer directement un ordre.

---

# 190. AI Execution Boundary

Flux futur autorisé :

```text
AI proposal
↓
experiment
↓
validation
↓
approved execution policy
↓
Execution Engine
```

et non :

```text
AI
↓
Exchange
```

---

# 191. Governance

Toute modification de policy live doit enregistrer :

```text
author
reason
experiment_id
approval
previous_version
new_version
deployment_time
```

---

# 192. API Conceptuelle

Fonctions :

```text
submit_approved_intent(...)
cancel_order(...)
get_order(...)
list_open_orders(...)
get_execution_state(...)
reconcile(...)
```

Le détail sera défini dans `22-API-Specification.md`.

---

# 193. Database

Le schéma détaillé sera défini dans :

```text
23-Database-Schema.md
```

Tables attendues :

```text
orders
fills
positions
execution_events
reconciliation_runs
venue_health
```

---

# 194. Priorités V1

Implémenter :

- common venue interface ;
- paper adapter ;
- premier live adapter ;
- pre-trade validation ;
- MARKET/LIMIT ;
- client order IDs ;
- idempotence ;
- order state machine ;
- fills ;
- partial fills ;
- cancel ;
- retry contrôlé ;
- fees ;
- slippage ;
- persistence ;
- reconciliation ;
- Risk Engine feedback ;
- structured logging.

---

# 195. Priorités V2

Ajouter :

- protective order management avancé ;
- OCO ;
- limit timeout policies ;
- execution analytics ;
- venue health scoring ;
- circuit breakers ;
- stronger recovery.

---

# 196. Priorités V3

Ajouter :

- multiple venues ;
- smart routing ;
- order splitting ;
- TWAP ;
- participation algorithms ;
- advanced paper fill models.

---

# 197. Priorités V4

Ajouter :

- ML slippage models ;
- fill probability models ;
- adaptive execution policies ;
- intelligent venue routing sous gouvernance.

---

# 198. Critères d'acceptation V1

La V1 est valide lorsque :

- aucun ordre live n'est possible sans RiskDecision valide ;
- les intentions expirées sont refusées ;
- tick size et quantity step sont respectés ;
- les client order IDs sont uniques et stables ;
- les retries sont idempotents ;
- les partial fills sont correctement agrégés ;
- les fills dupliqués ne sont pas comptés deux fois ;
- les frais réels sont stockés ;
- le slippage est mesuré ;
- les positions sont reconciliées ;
- les états inconnus bloquent les nouvelles expositions ;
- les sorties restent possibles en mode restrictif ;
- le restart recovery fonctionne ;
- les tests de timeout passent ;
- les tests de crash passent ;
- les événements sont persistés et auditables.

---

# 199. Risques principaux

## Duplicate Orders

Un retry naïf peut créer deux expositions.

## State Desynchronization

QuantLab peut croire qu'un ordre est annulé alors qu'il est toujours actif.

## Partial Fill Risk

Une position partiellement exécutée modifie immédiatement le risque réel.

## Slippage

Une stratégie rentable théoriquement peut devenir perdante après coûts.

## Protective Order Failure

Une position réelle peut se retrouver sans stop opérationnel.

## Venue Failure

L'exchange peut devenir indisponible au pire moment.

## Race Conditions

Deux événements simultanés peuvent produire des états incohérents.

---

# 200. Principe de simplicité

La V1 doit privilégier :

```text
one venue
few order types
strict state machine
strong idempotence
aggressive reconciliation
```

plutôt que :

```text
many venues
smart routing
complex execution algorithms
```

La sophistication vient après la fiabilité.

---

# 201. Architecture cible

```text
ApprovedIntent
      ↓
Pre-Trade Validation
      ↓
Execution Policy
      ↓
Order Builder
      ↓
Idempotency Check
      ↓
Venue Adapter
      ↓
Exchange
      ↓
ACK / FILL / CANCEL
      ↓
Order State Machine
      ↓
Fill Processor
      ↓
Position Update
      ↓
Risk Update
      ↓
Reconciliation
      ↓
Monitoring + Knowledge
```

---

# 202. Résultat attendu

L'Execution Engine doit permettre à QuantLab de passer de :

```text
RiskDecision:
APPROVED
BUY 0.47 BTC
```

à :

```text
Order:
LIMIT BUY
0.47 BTC
client_order_id = QL-...

Venue:
ACKNOWLEDGED

Fills:
0.20 BTC @ 100000
0.27 BTC @ 100010

Average fill:
100005.74

Fees:
recorded

Slippage:
measured

Position:
0.47 BTC LONG

Risk reservation:
consumed

Protective order:
verified

Reconciliation:
OK
```

sans perte d'information entre les couches.

---

# 203. Règle fondatrice

> **L'Execution Engine ne doit jamais être intelligent au point de devenir imprévisible.**

Son objectif prioritaire est :

```text
reliable
deterministic
idempotent
observable
recoverable
```

Une stratégie peut être brillante.

Un moteur d'exécution, lui, doit surtout être ennuyeusement fiable.

Sur les marchés, « ennuyeusement fiable » est un compliment rare et extrêmement rentable.

---

# 204. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `03-Data-Engine.md`
- `04-Storage-Engine.md`
- `09-Scoring-Engine.md`
- `10-Decision-Engine.md`
- `11-Risk-Engine.md`
- `13-Monitoring-Engine.md`
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

**Prochain document : `13-Monitoring-Engine.md`**
