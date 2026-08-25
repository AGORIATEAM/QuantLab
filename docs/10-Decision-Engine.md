# 10 — Decision Engine

**Projet : QuantLab**  
**Document : Decision Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Decision Engine transforme les observations et scores produits par QuantLab en intentions de trading explicites, déterministes, auditables et contrôlables.

Il constitue la frontière entre :

```text
Analyse
↓
Scoring
↓
Décision
```

et :

```text
Risque
↓
Exécution
```

Sa question centrale est :

> Compte tenu du contexte disponible maintenant, une stratégie autorise-t-elle une action, laquelle, et pourquoi ?

Le moteur peut produire notamment :

```text
NO_TRADE
WATCH
LONG_CANDIDATE
SHORT_CANDIDATE
ENTER_LONG
ENTER_SHORT
HOLD
REDUCE
EXIT
CANCEL
```

Une décision positive n'est jamais une autorisation directe d'envoyer un ordre. Toute intention exposant du capital doit ensuite être validée par le Risk Engine.

---

# 2. Principe fondamental

Le Decision Engine doit séparer quatre notions souvent mélangées :

```text
Signal
≠
Décision
≠
Autorisation de risque
≠
Ordre
```

Exemple :

```text
Bullish BOS
+
Sell-side sweep
+
Long score = 86
```

peut produire :

```text
LONG_CANDIDATE
```

mais pas nécessairement :

```text
ENTER_LONG
```

et encore moins :

```text
BUY MARKET
```

Cette séparation est indispensable à la sécurité du système.

---

# 3. Responsabilités

Le Decision Engine doit :

1. recevoir les ScoreContext ;
2. recevoir le contexte de stratégie ;
3. vérifier l'éligibilité du setup ;
4. appliquer les règles de décision ;
5. résoudre les conflits long/short ;
6. appliquer les seuils ;
7. gérer les états de stratégie ;
8. gérer les cooldowns ;
9. éviter les décisions dupliquées ;
10. produire une intention explicite ;
11. fournir les niveaux structurels utiles ;
12. fournir les reason codes ;
13. calculer une confiance décisionnelle ;
14. enregistrer la décision ;
15. transmettre les intentions admissibles au Risk Engine.

---

# 4. Hors périmètre

Le moteur ne doit pas :

- calculer directement la quantité finale ;
- dépasser les limites de risque ;
- envoyer des ordres à un exchange ;
- gérer les clés API ;
- supposer qu'un score élevé garantit un trade rentable ;
- modifier une stratégie en production ;
- apprendre directement de ses propres résultats ;
- masquer les raisons d'un rejet.

---

# 5. Position dans l'architecture

```text
Market Analysis
      ↓
Market Structure
      ↓
Volume Profile
      ↓
SMC
      ↓
Scoring Engine
      ↓
┌─────────────────────┐
│   DECISION ENGINE   │
└──────────┬──────────┘
           ↓
      TradeIntent
           ↓
      Risk Engine
           ↓
    ApprovedIntent
           ↓
    Execution Engine
```

---

# 6. Entrées principales

Le moteur peut recevoir :

```text
ScoreContext
MarketContext
StructureContext
SMCContext
VolumeProfileContext
StrategyState
PortfolioStateSummary
SystemState
```

Il doit cependant éviter de recalculer les analyses déjà produites en amont.

---

# 7. DecisionContext

Structure conceptuelle :

```python
DecisionContext:
    decision_id
    timestamp
    symbol
    strategy_id

    long_score
    short_score
    score_confidence

    market_regime
    structure_state

    strategy_state
    position_state

    decision
    direction

    entry_thesis
    invalidation_reference
    target_references

    reason_codes
    rejection_codes

    decision_confidence

    scoring_version
    decision_version
```

---

# 8. TradeIntent

Lorsqu'une nouvelle exposition est proposée :

```python
TradeIntent:
    intent_id
    decision_id

    strategy_id
    symbol
    direction

    entry_type
    entry_reference

    invalidation_reference
    target_references

    score
    confidence

    expires_at

    reason_codes

    status
```

Le Risk Engine enrichira ensuite cet objet avec les paramètres financiers.

---

# 9. États de décision

Valeurs recommandées :

```text
NO_TRADE
WATCH
LONG_CANDIDATE
SHORT_CANDIDATE
ENTER_LONG
ENTER_SHORT
HOLD
REDUCE_LONG
REDUCE_SHORT
EXIT_LONG
EXIT_SHORT
CANCEL_PENDING
```

Ces états doivent être finis et documentés.

---

# 10. NO_TRADE

`NO_TRADE` est une décision valide, pas une absence de résultat.

Elle doit être produite lorsqu'aucune condition ne justifie une action.

Exemples :

```text
score insuffisant
contexte ambigu
conflit multi-timeframe
données dégradées
setup incomplet
```

---

# 11. WATCH

`WATCH` indique qu'un contexte mérite d'être surveillé mais que les conditions d'entrée ne sont pas encore satisfaites.

Exemple :

```text
4H bullish
1H bullish
15m approaching zone
trigger absent
```

Résultat :

```text
WATCH
```

Cela évite de confondre préparation et exécution.

---

# 12. Candidate State

Exemple :

```text
LONG_CANDIDATE
```

signifie que les conditions principales sont satisfaites, mais qu'un trigger ou une validation supplémentaire peut être nécessaire.

Cette étape est particulièrement utile pour les stratégies séquentielles.

---

# 13. ENTER_LONG / ENTER_SHORT

Ces décisions signifient :

> La logique de stratégie autorise maintenant la création d'une intention d'entrée.

Elles ne signifient toujours pas que l'ordre sera exécuté.

Flux obligatoire :

```text
ENTER_LONG
↓
Risk Engine
↓
APPROVE / MODIFY / REJECT
```

---

# 14. HOLD

`HOLD` s'applique à une position existante lorsque :

```text
aucune condition de sortie
aucune réduction
aucune invalidation
```

n'est détectée.

---

# 15. REDUCE

Le moteur peut proposer une réduction si la stratégie prévoit explicitement :

- prise partielle ;
- détérioration du contexte ;
- objectif intermédiaire ;
- changement structurel.

Le Risk Engine valide ensuite la faisabilité.

---

# 16. EXIT

Une décision de sortie peut provenir de :

```text
target reached
structural invalidation
time stop
strategy exit condition
opposite confirmed signal
```

Les sorties de sécurité imposées par le Risk Engine restent prioritaires.

---

# 17. Strategy Contract

Chaque stratégie doit fournir un contrat explicite.

Exemple :

```yaml
strategy:
  id: trend_following_v1

  allowed_directions:
    - long
    - short

  entry:
    minimum_score: 75
    minimum_confidence: 0.70

  market_regimes:
    allowed:
      - TRENDING
      - EXPANSION

  cooldown:
    bars: 3
```

---

# 18. Strategy Registry

Chaque stratégie doit être enregistrée avec :

```text
strategy_id
strategy_version
status
description
allowed_assets
allowed_timeframes
decision_rules_version
risk_profile_id
```

États :

```text
RESEARCH
BACKTEST
PAPER
SHADOW
LIVE
DISABLED
```

---

# 19. Decision Rules

Les règles doivent être déclaratives lorsque possible.

Exemple :

```text
IF
long_score >= 80
AND confidence >= 0.75
AND market_regime IN allowed_regimes
AND no_open_long
AND cooldown_complete

THEN
ENTER_LONG
```

---

# 20. Hard Conditions

Certaines conditions doivent être obligatoires.

Exemple :

```text
data_quality >= minimum
strategy_enabled = true
system_trading_enabled = true
```

Si une condition échoue :

```text
NO_TRADE
```

avec reason code.

---

# 21. Soft Conditions

Les conditions non obligatoires doivent généralement être absorbées par le Scoring Engine.

Le Decision Engine ne doit pas reproduire un second système de scoring caché sous forme de dizaines de règles arbitraires.

---

# 22. Score Threshold

Exemple :

```text
minimum_long_score = 78
minimum_short_score = 78
```

Les seuils doivent être :

- configurables ;
- versionnés ;
- testés ;
- spécifiques à la stratégie si nécessaire.

---

# 23. Confidence Threshold

Exemple :

```text
minimum_confidence = 0.70
```

Un score élevé avec une confiance faible peut être rejeté.

---

# 24. Score Separation

Un minimum de séparation peut être exigé.

Exemple :

```text
long_score = 82
short_score = 78
```

Le contexte est ambigu malgré deux scores élevés.

Condition possible :

```text
abs(long_score - short_score)
>= minimum_score_spread
```

---

# 25. Direction Conflict

Si :

```text
long_score >= long_threshold
AND
short_score >= short_threshold
```

le moteur doit appliquer une politique explicite.

Recommandation V1 :

```text
NO_TRADE
reason = DIRECTION_CONFLICT
```

plutôt que d'inventer une priorité.

---

# 26. Tie-Breaking

Si une stratégie autorise une résolution de conflit, elle doit être formalisée.

Exemple :

```text
higher-timeframe alignment
```

peut départager les directions.

La règle doit être testée et versionnée.

---

# 27. Market Regime Gate

Exemple :

```text
strategy = trend_following
market_regime = RANGE
```

Résultat possible :

```text
NO_TRADE
REGIME_NOT_ALLOWED
```

---

# 28. Volatility Gate

Exemple :

```text
volatility = EXTREME
```

La stratégie peut être désactivée dans ce régime.

Cela doit être déterminé par la recherche, pas par superstition de trader traumatisé par trois grosses bougies.

---

# 29. Liquidity Gate

Conditions possibles :

```text
minimum market liquidity
maximum spread
maximum estimated slippage
```

Certaines informations peuvent provenir du Risk ou Execution context.

La frontière doit être clairement définie.

---

# 30. Data Quality Gate

Si :

```text
data_quality < threshold
```

résultat :

```text
NO_TRADE
DATA_QUALITY_TOO_LOW
```

Une absence de données ne doit jamais devenir une permission implicite.

---

# 31. System State Gate

Le moteur doit respecter :

```text
TRADING_ENABLED
TRADING_PAUSED
REDUCE_ONLY
EMERGENCY_STOP
```

En `EMERGENCY_STOP`, aucune nouvelle entrée n'est admissible.

---

# 32. Strategy State Machine

Une stratégie peut suivre :

```text
IDLE
WATCHING
CANDIDATE
PENDING_ENTRY
IN_POSITION
PENDING_EXIT
COOLDOWN
DISABLED
```

Cela réduit les décisions incohérentes.

---

# 33. Transition IDLE → WATCHING

Exemple :

```text
context quality sufficient
but trigger incomplete
```

---

# 34. WATCHING → CANDIDATE

Exemple :

```text
minimum setup conditions satisfied
```

---

# 35. CANDIDATE → PENDING_ENTRY

Lorsque :

```text
entry trigger confirmed
```

une intention peut être créée.

---

# 36. PENDING_ENTRY → IN_POSITION

Cette transition ne doit se produire qu'après confirmation d'exécution provenant de l'Execution Engine.

Une décision n'est pas un fill.

---

# 37. IN_POSITION → PENDING_EXIT

Lorsque :

```text
exit condition detected
```

le moteur génère une intention de sortie.

---

# 38. COOLDOWN

Après une sortie ou une invalidation, la stratégie peut entrer en cooldown.

Objectifs :

- éviter le sur-trading ;
- éviter les répétitions du même signal ;
- respecter une logique stratégique.

---

# 39. Cooldown Types

Possibilités :

```text
TIME_BASED
BAR_BASED
EVENT_BASED
UNTIL_NEW_STRUCTURE
```

---

# 40. Cooldown Configuration

Exemple :

```yaml
cooldown:
  type: bar_based
  bars: 3
```

ou :

```yaml
cooldown:
  type: until_new_structure
```

---

# 41. Duplicate Signal Protection

Le même événement ne doit pas créer plusieurs intentions.

Exemple :

```text
same BOS
same FVG
same score threshold crossing
```

doit produire au maximum une décision logique selon la stratégie.

---

# 42. Idempotency

Chaque décision doit pouvoir disposer d'une clé :

```text
decision_key
```

Exemple :

```text
hash(
strategy_id,
symbol,
setup_id,
direction,
trigger_event_id
)
```

Une même clé ne doit pas créer plusieurs entrées.

---

# 43. Decision Expiration

Une intention peut expirer.

Exemple :

```text
LONG_CANDIDATE
valid for 5 candles
```

Si aucune exécution n'a lieu :

```text
EXPIRED
```

---

# 44. Setup Identity

Un setup doit disposer d'un identifiant stable.

```text
setup_id
```

Il peut regrouper :

```text
structure event
liquidity event
zone
strategy
```

Cela permet de suivre toute sa vie.

---

# 45. Entry Trigger

Les triggers doivent être distincts des conditions de contexte.

Exemple :

```text
Context:
4H bullish
1H discount
15m bullish OB
```

Trigger :

```text
5m bullish BOS
```

La séparation réduit le risque d'entrée prématurée.

---

# 46. Trigger Types

Exemples :

```text
SCORE_CROSS
BOS_CONFIRMATION
CHOCH_CONFIRMATION
ZONE_RECLAIM
LIQUIDITY_SWEEP_CONFIRMATION
PRICE_BREAK
LIMIT_ZONE_TOUCH
```

Chaque stratégie définit les triggers qu'elle accepte.

---

# 47. Trigger Timestamp

La décision ne peut utiliser un trigger qu'après :

```text
trigger.available_at
```

C'est une protection anti look-ahead fondamentale.

---

# 48. Entry Type Intent

Le Decision Engine peut proposer une préférence :

```text
MARKET
LIMIT
STOP
```

mais l'Execution Engine reste responsable de la construction opérationnelle de l'ordre.

---

# 49. Entry Reference

Exemples :

```text
current_market_price
order_block_midpoint
fvg_midpoint
breakout_level
```

Le moteur doit transmettre une référence, pas supposer le prix final d'exécution.

---

# 50. Invalidation Reference

Le moteur doit fournir un niveau conceptuel d'invalidation.

Exemples :

```text
swing low
order block low
structure invalidation
range low
```

Le Risk Engine décide ensuite du stop réel.

---

# 51. Target References

Le moteur peut fournir des objectifs structurels :

```text
previous high
liquidity zone
VAH
POC
swing high
```

Le Risk Engine et la stratégie déterminent si ces niveaux sont admissibles.

---

# 52. No Arbitrary Stop

Le Decision Engine ne doit pas produire :

```text
stop = 1%
```

sans justification stratégique.

Les niveaux de décision doivent rester structurels.

La conversion en risque financier appartient au Risk Engine.

---

# 53. Position Awareness

Avant une nouvelle entrée, le moteur doit connaître au minimum :

```text
NO_POSITION
LONG
SHORT
PENDING_LONG
PENDING_SHORT
```

afin d'éviter des intentions contradictoires.

---

# 54. Existing Position Policy

Une stratégie doit préciser :

```text
allow_pyramiding
allow_hedging
allow_reverse
```

Par défaut V1 :

```text
allow_pyramiding = false
allow_hedging = false
```

sauf stratégie explicitement conçue autrement.

---

# 55. Pyramiding

Si activé, les conditions doivent être strictes.

Exemple :

```text
maximum_entries
minimum_price_distance
minimum_new_score
maximum_total_risk
```

Le Risk Engine conserve le dernier mot.

---

# 56. Reversal

Passer directement :

```text
LONG → SHORT
```

doit être traité comme :

```text
EXIT_LONG
↓
confirmation
↓
new SHORT decision
```

en V1.

Cela simplifie l'audit.

---

# 57. Exit Rules

Les sorties peuvent être :

```text
STRUCTURAL
TARGET
TIME
SIGNAL
REGIME_CHANGE
```

Chaque raison doit être enregistrée.

---

# 58. Structural Exit

Exemple :

```text
bullish setup
+
protected low broken
```

peut produire :

```text
EXIT_LONG
```

si la stratégie le prévoit.

---

# 59. Opposite Signal Exit

Un signal opposé ne doit pas automatiquement provoquer un reverse.

Il peut simplement déclencher :

```text
EXIT
```

ou :

```text
REDUCE
```

selon la stratégie.

---

# 60. Time Stop

Exemple :

```text
position has not progressed after N bars
```

Le moteur peut proposer une sortie.

Cette règle doit être validée expérimentalement.

---

# 61. Target-Based Exit

Le moteur peut suivre :

```text
target_1
target_2
target_3
```

et produire :

```text
REDUCE
```

ou :

```text
EXIT
```

selon les règles.

---

# 62. Trailing Logic

Une stratégie peut demander une mise à jour d'invalidation logique.

Exemple :

```text
new protected swing low
```

Le Decision Engine peut publier :

```text
UPDATE_PROTECTIVE_REFERENCE
```

Le Risk/Execution Engine décide de la modification concrète de l'ordre.

---

# 63. Decision Priority

Lorsque plusieurs actions sont possibles simultanément :

```text
EXIT
REDUCE
ENTER
```

une priorité doit exister.

Recommandation :

```text
EMERGENCY EXIT
>
EXIT
>
REDUCE
>
CANCEL
>
NEW ENTRY
```

La réduction du risque doit primer sur son augmentation.

---

# 64. Risk Override

Le Risk Engine peut répondre :

```text
APPROVED
MODIFIED
REJECTED
```

Le Decision Engine ne doit jamais contourner `REJECTED`.

---

# 65. Risk Feedback

Exemple :

```text
Decision:
ENTER_LONG

Risk:
REJECTED
reason:
DAILY_LOSS_LIMIT
```

Le résultat final doit conserver les deux niveaux d'information.

---

# 66. Modified Intent

Le Risk Engine peut modifier :

```text
position size
stop distance
allowed leverage
```

dans les limites définies.

La décision stratégique reste traçable séparément.

---

# 67. Decision Confidence

Une confiance décisionnelle peut combiner :

```text
score_confidence
rule completeness
context consistency
trigger quality
```

Elle ne représente pas une probabilité de gain.

---

# 68. Reason Codes

Exemples positifs :

```text
LONG_SCORE_THRESHOLD_MET
SHORT_SCORE_THRESHOLD_MET
HTF_ALIGNMENT
BULLISH_TRIGGER_CONFIRMED
BEARISH_TRIGGER_CONFIRMED
LIQUIDITY_SWEEP_CONFIRMED
STRUCTURE_CONFIRMATION
```

---

# 69. Rejection Codes

Exemples :

```text
SCORE_TOO_LOW
CONFIDENCE_TOO_LOW
DIRECTION_CONFLICT
REGIME_NOT_ALLOWED
DATA_QUALITY_TOO_LOW
COOLDOWN_ACTIVE
POSITION_ALREADY_OPEN
DUPLICATE_SETUP
TRIGGER_NOT_CONFIRMED
STRATEGY_DISABLED
SYSTEM_PAUSED
INTENT_EXPIRED
```

---

# 70. Explainability

Toute décision doit pouvoir être expliquée.

Exemple :

```yaml
decision: NO_TRADE

reason:
  - LONG_SCORE_TOO_LOW
  - HTF_CONFLICT

long_score: 69
required_long_score: 78
```

Un `NO_TRADE` silencieux est inutile pour la recherche.

---

# 71. Decision Trace

Le moteur doit conserver :

```text
input snapshot
rule evaluation
score values
thresholds
state before
state after
decision
reason codes
```

---

# 72. Rule Evaluation Trace

Exemple :

```text
long_score >= 78           PASS
confidence >= 0.70         PASS
regime allowed             PASS
cooldown complete          PASS
trigger confirmed          FAIL
```

Résultat :

```text
WATCH
```

---

# 73. Determinism

Avec :

```text
same inputs
same state
same strategy version
same decision version
```

le moteur doit produire la même décision.

---

# 74. Decision Versioning

Chaque règle doit être liée à :

```text
decision_engine_version
strategy_version
configuration_version
```

---

# 75. Immutable Historical Decisions

Une décision historique doit rester liée à la version qui l'a créée.

Une nouvelle version peut recalculer un scénario pour la recherche, mais ne doit pas réécrire silencieusement l'historique.

---

# 76. Event-Driven Operation

Événements déclencheurs possibles :

```text
SCORE_UPDATED
STRUCTURE_CHANGED
LIQUIDITY_SWEEP_DETECTED
FVG_UPDATED
POSITION_UPDATED
RISK_STATE_CHANGED
SYSTEM_STATE_CHANGED
```

Le moteur réévalue uniquement ce qui est nécessaire.

---

# 77. Decision Events

Événements produits :

```text
DECISION_CREATED
DECISION_CHANGED
TRADE_INTENT_CREATED
TRADE_INTENT_EXPIRED
ENTRY_REJECTED
EXIT_INTENT_CREATED
```

---

# 78. Persistence

Tables logiques potentielles :

```text
decisions
decision_reasons
trade_intents
strategy_states
setup_instances
```

Le détail sera défini dans `23-Database-Schema.md`.

---

# 79. Decision Record

Exemple :

```text
decision_id
timestamp
symbol
strategy_id
strategy_version
decision
direction
long_score
short_score
confidence
state_before
state_after
decision_version
```

---

# 80. Intent Record

Exemple :

```text
intent_id
decision_id
symbol
direction
intent_type
entry_reference
invalidation_reference
status
created_at
expires_at
```

---

# 81. Decision Idempotency

Un événement répété après reconnexion ne doit pas générer un deuxième TradeIntent.

La couche de persistance doit permettre de vérifier les identifiants déjà traités.

---

# 82. Concurrency

Deux événements peuvent arriver presque simultanément.

Exemple :

```text
SCORE_UPDATED
POSITION_FILLED
```

Le moteur doit protéger son état contre les race conditions.

Solutions possibles :

- optimistic locking ;
- versioned state ;
- transactional updates ;
- serialized processing par stratégie/symbole.

---

# 83. Recommended Concurrency Model

Pour la V1 :

```text
single logical decision stream
per strategy + symbol
```

Cela simplifie énormément la cohérence.

La parallélisation peut se faire entre symboles.

---

# 84. State Version

Chaque état peut inclure :

```text
state_version
```

Une mise à jour doit vérifier qu'elle travaille sur la dernière version.

---

# 85. Restart Recovery

Après redémarrage :

```text
load persisted strategy state
↓
load open positions
↓
load pending intents
↓
reconcile
↓
resume
```

Le moteur ne doit pas repartir aveuglement en `IDLE`.

---

# 86. Reconciliation

Le système doit comparer :

```text
internal position state
```

avec :

```text
execution / broker state
```

Les divergences doivent déclencher une alerte.

---

# 87. Fail Closed

En cas d'incertitude critique :

```text
unknown position state
unknown risk state
invalid score version
corrupted strategy state
```

la politique par défaut doit empêcher les nouvelles entrées.

---

# 88. Fail-Safe Exit

La restriction sur les nouvelles entrées ne doit pas empêcher les actions nécessaires pour réduire ou fermer une exposition existante.

Principe :

```text
fail closed for new risk
fail safe for risk reduction
```

---

# 89. Backtest Mode

Le même Decision Engine doit idéalement être utilisable en :

```text
BACKTEST
PAPER
LIVE
```

avec les mêmes règles métier.

Les différences doivent être confinées aux adapters et au temps simulé.

---

# 90. Clock Abstraction

Le moteur ne doit pas appeler directement l'heure système partout.

Il doit utiliser une abstraction :

```text
Clock
```

En backtest :

```text
SimulatedClock
```

En live :

```text
SystemClock
```

Cela améliore la reproductibilité.

---

# 91. Replay Testing

Le Decision Engine doit pouvoir rejouer :

```text
event 1
event 2
event 3
...
```

et reproduire exactement les décisions historiques.

---

# 92. Anti Look-Ahead

Aucune donnée avec :

```text
available_at > decision_timestamp
```

ne peut être utilisée.

Le moteur doit idéalement refuser explicitement l'input.

---

# 93. Unit Tests

Tester :

- score threshold ;
- confidence threshold ;
- regime gate ;
- conflict handling ;
- cooldown ;
- duplicate prevention ;
- state transitions ;
- entry ;
- exit ;
- reduction ;
- expiration.

---

# 94. State Machine Tests

Chaque transition autorisée doit être testée.

Exemple :

```text
IDLE → PENDING_EXIT
```

doit être impossible.

Les transitions invalides doivent lever une erreur contrôlée.

---

# 95. Synthetic Scenario Tests

Exemple :

```text
long_score = 85
short_score = 20
confidence = 0.90
regime = TRENDING
trigger = confirmed
position = none
```

Résultat attendu :

```text
ENTER_LONG
```

avant validation du Risk Engine.

---

# 96. Conflict Test

```text
long_score = 85
short_score = 83
```

Résultat V1 recommandé :

```text
NO_TRADE
DIRECTION_CONFLICT
```

---

# 97. Cooldown Test

Après sortie :

```text
cooldown = 3 bars
```

Un nouveau signal à la bougie suivante doit être rejeté.

---

# 98. Duplicate Test

Deux traitements du même événement doivent produire :

```text
1 intent
```

et non deux.

---

# 99. Integration Tests

Tester :

```text
Scoring
↓
Decision
↓
Risk
```

Cas :

```text
valid decision + risk approved
valid decision + risk modified
valid decision + risk rejected
```

---

# 100. Execution Feedback Tests

Tester :

```text
intent approved
↓
order submitted
↓
partial fill
↓
full fill
```

Le StrategyState doit rester cohérent.

---

# 101. Performance

Le moteur doit mesurer :

```text
decision_latency
rule_evaluation_latency
state_load_latency
state_persistence_latency
```

Les p50/p95/p99 doivent être observables.

---

# 102. Monitoring

Métriques :

```text
decisions_total
no_trade_total
watch_total
long_intents
short_intents
exit_intents
rejections
direction_conflicts
duplicate_events
expired_intents
decision_errors
```

---

# 103. Strategy Metrics

Par stratégie :

```text
candidate_rate
entry_rate
rejection_rate
average_score_at_entry
average_confidence_at_entry
time_in_watch_state
```

---

# 104. Decision Funnel

QuantLab doit pouvoir mesurer :

```text
10000 market evaluations
↓
1200 WATCH
↓
400 candidates
↓
180 entry intents
↓
140 risk approved
↓
132 executed
```

Ce funnel est précieux pour comprendre où les opportunités disparaissent.

---

# 105. Rejection Analytics

Exemple :

```text
SCORE_TOO_LOW          42%
REGIME_NOT_ALLOWED     20%
COOLDOWN_ACTIVE        12%
RISK_REJECTED          10%
DIRECTION_CONFLICT      8%
OTHER                    8%
```

Cela aide à détecter une stratégie trop restrictive ou mal calibrée.

---

# 106. Decision Quality Analysis

Le Knowledge Engine doit relier :

```text
decision
↓
execution
↓
outcome
```

afin de mesurer :

```text
expectancy by decision reason
expectancy by score
expectancy by regime
expectancy by trigger
```

---

# 107. Counterfactual Logging

Pour la recherche, il peut être utile de conserver certains setups rejetés.

Exemple :

```text
NO_TRADE because score = 74
threshold = 75
```

Le Knowledge Engine pourra ensuite mesurer ce qui se serait passé.

---

# 108. Counterfactual Caution

Un résultat contrefactuel ne doit pas être confondu avec une exécution réelle.

Il faut modéliser :

- spread ;
- slippage ;
- disponibilité de liquidité ;
- timing.

Sinon le « trade qu'on aurait pu prendre » devient cette créature mythologique toujours parfaitement exécutée.

---

# 109. Shadow Strategies

Une stratégie expérimentale peut tourner en :

```text
SHADOW
```

Elle produit :

```text
decisions
trade intents
simulated outcomes
```

sans transmettre d'ordres réels.

---

# 110. Champion / Challenger

Le système peut comparer :

```text
Champion Decision Policy
```

et :

```text
Challenger Decision Policy
```

sur les mêmes inputs.

---

# 111. Strategy Isolation

Une erreur dans :

```text
strategy_A
```

ne doit pas affecter :

```text
strategy_B
```

Les états et configurations doivent être isolés.

---

# 112. Portfolio Interaction

Le Decision Engine peut connaître un résumé du portefeuille pour éviter des intentions manifestement incompatibles.

Mais les contraintes financières globales appartiennent au Risk Engine.

---

# 113. Correlated Signals

Exemple :

```text
BTC LONG
ETH LONG
```

peuvent représenter une exposition fortement corrélée.

Le Decision Engine peut produire les deux intentions.

Le Risk Engine décide si le portefeuille peut accepter les deux.

---

# 114. Decision Policy Interface

Interface conceptuelle :

```python
class DecisionPolicy:

    def evaluate(
        self,
        score_context,
        strategy_state,
        system_state
    ) -> DecisionContext:
        ...
```

Chaque stratégie peut implémenter sa propre policy.

---

# 115. Rule Composition

Les règles peuvent être organisées :

```text
Eligibility Rules
↓
Context Rules
↓
Trigger Rules
↓
State Rules
↓
Decision
```

Cette structure facilite les tests.

---

# 116. Rule Result

Chaque règle retourne :

```python
RuleResult:
    rule_id
    passed
    observed_value
    expected_condition
    reason_code
```

---

# 117. Configuration Example

```yaml
decision_engine:

  strategy_id: trend_following_v1
  version: 1.0.0

  entry:
    long_score_min: 78
    short_score_min: 78
    confidence_min: 0.70
    score_spread_min: 10

  regime:
    allowed:
      - TRENDING
      - EXPANSION

  state:
    allow_pyramiding: false
    allow_hedging: false

  cooldown:
    type: bar_based
    bars: 3

  intent:
    expiration_bars: 2
```

---

# 118. Configuration Validation

Au démarrage, vérifier :

```text
known strategy
valid score thresholds
valid state transitions
known trigger types
compatible scoring version
compatible risk profile
```

Une configuration incohérente doit bloquer l'activation de la stratégie.

---

# 119. Decision API

Le moteur doit pouvoir exposer conceptuellement :

```text
evaluate(context)
get_decision(decision_id)
get_strategy_state(strategy_id, symbol)
list_active_intents()
```

Le détail des endpoints sera défini dans `22-API-Specification.md`.

---

# 120. Audit API

Il doit être possible de récupérer :

```text
decision
+
inputs
+
rule trace
+
reason codes
+
versions
```

pour chaque décision.

---

# 121. Security

Les droits doivent distinguer :

```text
read decisions
manage strategy config
enable strategy
disable strategy
```

Une modification de stratégie live doit être fortement contrôlée.

---

# 122. Manual Override

Un opérateur autorisé peut devoir :

```text
disable strategy
pause new entries
force reduce-only
```

En revanche, permettre de forcer arbitrairement une entrée contre les règles de risque est déconseillé.

---

# 123. Kill Switch

Le Decision Engine doit respecter immédiatement un :

```text
GLOBAL_KILL_SWITCH
```

Aucune nouvelle exposition ne doit être générée après activation.

---

# 124. Governance

Toute modification de règle doit passer par :

```text
proposal
experiment
validation
approval
versioning
deployment
```

Les changements improvisés directement en live doivent être interdits.

---

# 125. Interaction avec Scoring Engine

Le Scoring Engine répond :

```text
Quelle est la qualité du contexte ?
```

Le Decision Engine répond :

```text
Que permet la stratégie dans ce contexte ?
```

Les deux responsabilités ne doivent pas fusionner.

---

# 126. Interaction avec Risk Engine

Le Decision Engine fournit :

```text
direction
entry thesis
invalidation reference
targets
score
confidence
```

Le Risk Engine calcule ensuite :

```text
risk budget
position size
stop constraints
portfolio constraints
approval
```

---

# 127. Interaction avec Execution Engine

Le Decision Engine ne devrait jamais appeler directement une API d'exchange.

L'Execution Engine reçoit uniquement une intention déjà validée par le Risk Engine.

---

# 128. Interaction avec Monitoring Engine

Le Monitoring Engine surveille :

- décisions anormales ;
- fréquence ;
- conflits ;
- erreurs ;
- latence ;
- états bloqués ;
- intents expirés.

---

# 129. Interaction avec Knowledge Engine

Le Knowledge Engine doit pouvoir répondre :

> Quels reason codes sont associés aux meilleurs résultats ?

ou :

> Les setups rejetés juste sous le seuil auraient-ils eu une expectancy différente ?

---

# 130. Interaction avec AI & Learning Engine

L'IA pourra proposer :

- nouveaux seuils ;
- nouvelles règles ;
- simplification des policies ;
- nouveaux triggers ;
- suppression de règles inutiles.

Elle ne doit pas modifier directement la policy live.

---

# 131. Testing des nouvelles policies

Toute policy proposée doit être comparée à la baseline sur :

```text
in-sample
validation
out-of-sample
walk-forward
shadow mode
```

avant toute promotion.

---

# 132. Priorités V1

Implémenter :

- DecisionContext ;
- TradeIntent ;
- Strategy Registry ;
- rules déterministes ;
- long/short thresholds ;
- confidence threshold ;
- regime gates ;
- state machine ;
- cooldown ;
- duplicate protection ;
- intent expiration ;
- reason codes ;
- persistence ;
- replay déterministe.

---

# 133. Priorités V2

Ajouter :

- triggers séquentiels avancés ;
- partial exits ;
- trailing references ;
- counterfactual logging ;
- advanced strategy state ;
- shadow policies.

---

# 134. Priorités V3

Ajouter :

- champion/challenger ;
- portfolio-aware decision context ;
- policy comparison ;
- adaptive thresholds expérimentaux.

---

# 135. Priorités V4

Ajouter :

- ML-assisted decision policies ;
- contextual policy selection ;
- AI-generated policy proposals sous gouvernance.

---

# 136. Critères d'acceptation V1

La V1 est valide lorsque :

- toute décision possède une raison ;
- `NO_TRADE` est explicitement représenté ;
- le score n'est pas confondu avec la décision ;
- la décision n'est pas confondue avec l'ordre ;
- les conflits long/short sont gérés ;
- les états de stratégie sont déterministes ;
- les doublons sont empêchés ;
- les cooldowns fonctionnent ;
- les intentions expirent ;
- le Risk Engine reste obligatoire ;
- aucun look-ahead n'est possible ;
- les décisions sont persistées ;
- le replay reproduit les mêmes résultats ;
- les tests unitaires et d'intégration passent.

---

# 137. Risques principaux

## Overtrading

Un moteur trop permissif transforme chaque variation en décision.

## Rule Explosion

Des centaines de conditions deviennent impossibles à comprendre et à tester.

## State Desynchronization

L'état interne peut diverger de l'état réel des positions.

## Duplicate Orders

Un événement rejoué peut générer plusieurs intentions si l'idempotence est mal conçue.

## Look-Ahead

Un trigger confirmé rétrospectivement peut contaminer le backtest.

## Hidden Scoring

Ajouter trop de règles souples dans le Decision Engine recrée un deuxième Scoring Engine invisible.

---

# 138. Principe de simplicité

La V1 doit préférer :

```text
few explicit rules
clear state machine
strict separation of concerns
strong audit trail
```

à :

```text
complex discretionary logic
nested exceptions
implicit state
```

---

# 139. Architecture cible

```text
ScoreContext
      ↓
Eligibility Gates
      ↓
Strategy State
      ↓
Direction Resolution
      ↓
Trigger Validation
      ↓
Decision Policy
      ↓
DecisionContext
      ↓
TradeIntent
      ↓
Risk Engine
      ↓
APPROVE / MODIFY / REJECT
```

---

# 140. Résultat attendu

Le Decision Engine doit permettre à QuantLab de passer de :

```text
« Le setup semble bon »
```

à :

```text
Decision:
ENTER_LONG

Strategy:
trend_following_v1

Why:
- long score threshold passed
- confidence threshold passed
- regime allowed
- bullish trigger confirmed
- no direction conflict
- cooldown complete

State:
CANDIDATE → PENDING_ENTRY

Next:
Risk Engine validation required
```

La décision devient ainsi explicable, reproductible et testable.

---

# 141. Règle fondatrice

> **Une bonne analyse n'est pas encore une décision, et une bonne décision n'est pas encore une permission de risquer du capital.**

Le Decision Engine doit transformer les analyses en intentions disciplinées tout en restant strictement séparé du risque et de l'exécution.

Cette séparation est l'une des protections centrales de QuantLab.

---

# 142. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `05-Market-Analysis-Engine.md`
- `06-Market-Structure-Engine.md`
- `07-Volume-Profile-Engine.md`
- `08-Smart-Money-Concepts-Engine.md`
- `09-Scoring-Engine.md`
- `11-Risk-Engine.md`
- `12-Execution-Engine.md`
- `13-Monitoring-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `16-Governance-Engine.md`
- `18-Testing-Strategy.md`
- `21-Experiment-Registry.md`
- `22-API-Specification.md`
- `23-Database-Schema.md`
- `24-Security.md`

**Prochain document : `11-Risk-Engine.md`**
