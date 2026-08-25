# 18 --- Testing Strategy

**Projet : QuantLab**\
**Document : Testing Strategy**\
**Version : 1.0**\
**Statut : Standard d'ingénierie obligatoire**

------------------------------------------------------------------------

# 1. Objectif

La Testing Strategy définit comment QuantLab prouve qu'un composant, une
stratégie ou une modification fonctionne correctement avant de lui
confier des données critiques, des décisions de trading ou du capital
réel.

Le principe central est :

> **Un système quantitatif n'est pas fiable parce que son code
> fonctionne. Il est fiable lorsque ses hypothèses, ses données, ses
> décisions, ses risques et ses comportements en situation dégradée ont
> été testés.**

La stratégie de test doit couvrir simultanément :

``` text
SOFTWARE CORRECTNESS
DATA CORRECTNESS
QUANTITATIVE VALIDITY
RISK SAFETY
EXECUTION SAFETY
OPERATIONAL RESILIENCE
AI SAFETY
GOVERNANCE COMPLIANCE
```

------------------------------------------------------------------------

# 2. Philosophie générale

QuantLab suit une approche de défense en profondeur.

Aucun test unique ne suffit.

``` text
Static Checks
↓
Unit Tests
↓
Property / Invariant Tests
↓
Contract Tests
↓
Integration Tests
↓
Replay Tests
↓
Backtests
↓
Robustness Tests
↓
Paper Trading
↓
Shadow Mode
↓
Limited Live
↓
Production Monitoring
```

Chaque couche détecte une catégorie différente d'erreurs.

------------------------------------------------------------------------

# 3. Ce que les tests doivent empêcher

Le système doit notamment détecter :

-   données futures utilisées accidentellement ;
-   doublons de données ;
-   timestamps incorrects ;
-   mauvais calcul d'indicateur ;
-   divergence entre backtest et production ;
-   signaux non reproductibles ;
-   dépassement de risque ;
-   double envoi d'ordre ;
-   mauvaise réconciliation ;
-   mauvaise gestion d'un fill partiel ;
-   modèle ML surajusté ;
-   fuite de données ;
-   changement de comportement non documenté ;
-   permission IA excessive ;
-   déploiement d'un artefact non approuvé ;
-   régression silencieuse.

------------------------------------------------------------------------

# 4. Pyramide de tests

La base doit contenir beaucoup de tests rapides.

``` text
              E2E / LIVE SAFETY
             /                 \
            PAPER / SHADOW TESTS
           /                    \
          INTEGRATION / REPLAY
         /                       \
        CONTRACT / PROPERTY TESTS
       /                          \
      UNIT / STATIC / TYPE CHECKS
```

Les tests coûteux complètent les tests rapides. Ils ne les remplacent
pas.

------------------------------------------------------------------------

# 5. Static Checks

Avant même d'exécuter le code :

``` text
formatting
linting
type checking
security analysis
dependency checks
secret scanning
```

doivent détecter les défauts simples.

------------------------------------------------------------------------

# 6. Formatting

Le formatage doit être automatisé et reproductible.

Aucun débat humain n'est requis pour décider si une virgule mérite sa
propre ligne. Nous avons déjà assez de vrais problèmes.

------------------------------------------------------------------------

# 7. Linting

Le lint doit détecter notamment :

``` text
unused imports
unreachable code
suspicious constructs
shadowed variables
common programming errors
```

------------------------------------------------------------------------

# 8. Type Checking

Les modules critiques doivent être fortement typés lorsque le langage le
permet.

Priorité :

``` text
risk
execution
decision
data contracts
API contracts
```

------------------------------------------------------------------------

# 9. Secret Scanning

La CI doit empêcher autant que possible l'introduction de :

``` text
API keys
private keys
passwords
tokens
exchange credentials
```

dans Git.

------------------------------------------------------------------------

# 10. Dependency Scanning

Les dépendances doivent être analysées pour identifier :

``` text
known vulnerabilities
unsupported versions
unexpected transitive dependencies
```

------------------------------------------------------------------------

# 11. Unit Tests

Les tests unitaires valident une unité logique isolée.

Ils doivent être :

``` text
FAST
DETERMINISTIC
ISOLATED
READABLE
```

------------------------------------------------------------------------

# 12. Cibles prioritaires des Unit Tests

Tester particulièrement :

``` text
indicator calculations
market structure rules
volume profile calculations
SMC detection
scoring formulas
decision rules
risk calculations
order transformations
normalization
serialization
```

------------------------------------------------------------------------

# 13. Unit Test Example

Exemple conceptuel :

``` python
def test_risk_engine_rejects_trade_above_position_limit():
    decision = risk_engine.evaluate(
        requested_risk=0.03,
        max_position_risk=0.01,
    )

    assert decision.status == "REJECTED"
    assert decision.reason == "POSITION_RISK_LIMIT"
```

------------------------------------------------------------------------

# 14. Boundary Testing

Toute règle avec seuil doit tester :

``` text
below threshold
exact threshold
above threshold
```

Exemple :

``` text
score = 79
score = 80
score = 81
```

si le seuil est `80`.

------------------------------------------------------------------------

# 15. Invalid Inputs

Tester :

``` text
None
NaN
infinity
negative quantity
zero price
unknown symbol
invalid timestamp
malformed payload
```

selon le contrat.

------------------------------------------------------------------------

# 16. Property-Based Testing

Les tests par propriétés permettent de vérifier des invariants sur de
nombreux inputs générés.

Ils sont particulièrement utiles pour :

``` text
risk
numerical calculations
serialization
state transitions
```

------------------------------------------------------------------------

# 17. Invariants

Un invariant est une propriété qui ne doit jamais être violée.

Exemples :

``` text
position_risk <= approved_position_risk
portfolio_heat <= hard_portfolio_limit
filled_quantity <= executable_quantity
order_quantity >= 0
```

------------------------------------------------------------------------

# 18. Risk Invariants

Invariants critiques :

``` text
NO order may bypass Risk Engine
NO trade may exceed hard risk caps
NO risk increase after kill switch
NO new exposure in HALTED state
```

------------------------------------------------------------------------

# 19. Execution Invariants

``` text
one logical intent must not create duplicate live exposure
fills must map to known orders
cancelled orders cannot create new fills locally without reconciliation
```

------------------------------------------------------------------------

# 20. Accounting Invariants

Lorsque applicable :

``` text
position_before
+
fills
=
position_after
```

à tolérance et conventions explicitement définies.

------------------------------------------------------------------------

# 21. Contract Tests

Les interfaces entre services doivent être testées comme des contrats.

------------------------------------------------------------------------

# 22. API Contract Tests

Valider :

``` text
request schema
response schema
status codes
error format
versioning
```

------------------------------------------------------------------------

# 23. Event Contract Tests

Pour chaque événement :

``` text
required fields
types
schema version
serialization
deserialization
backward compatibility
```

------------------------------------------------------------------------

# 24. Producer / Consumer Compatibility

Un producteur ne doit pas pouvoir publier silencieusement un événement
que ses consommateurs ne comprennent plus.

------------------------------------------------------------------------

# 25. Database Contract Tests

Tester :

``` text
constraints
indexes
foreign keys
migrations
serialization
```

------------------------------------------------------------------------

# 26. Integration Tests

Les tests d'intégration valident plusieurs composants ensemble.

Exemple :

``` text
Data Engine
↓
Market Analysis
↓
Scoring
↓
Decision
↓
Risk
```

------------------------------------------------------------------------

# 27. Integration Test Scope

Les tests doivent rester ciblés.

Une suite d'intégration qui démarre toute l'infrastructure pour vérifier
une addition de deux nombres est surtout une façon créative de ralentir
la CI.

------------------------------------------------------------------------

# 28. Storage Integration

Tester :

``` text
write
read
update where allowed
transaction
rollback
concurrency
```

------------------------------------------------------------------------

# 29. Event Bus Integration

Tester :

``` text
publish
consume
retry
duplicate delivery
ordering assumptions
dead-letter handling
```

------------------------------------------------------------------------

# 30. Exchange Adapter Integration

Avec sandbox/mock réaliste :

``` text
submit
acknowledge
reject
partial fill
full fill
cancel
replace
timeout
```

------------------------------------------------------------------------

# 31. Replay Tests

QuantLab doit pouvoir rejouer des séquences historiques d'événements.

Objectif :

``` text
same inputs
+
same versions
+
same configuration
=
same deterministic outputs
```

pour les composants déterministes.

------------------------------------------------------------------------

# 32. Golden Replay Dataset

Créer un petit ensemble de sessions de marché représentatives.

Exemples :

``` text
trend day
range day
high volatility
gap
liquidity sweep
low liquidity
```

------------------------------------------------------------------------

# 33. Golden Outputs

Pour chaque replay stable, conserver les outputs attendus :

``` text
market structure
levels
scores
decisions
risk decisions
```

------------------------------------------------------------------------

# 34. Replay Regression

Une modification qui change les golden outputs doit expliquer pourquoi.

------------------------------------------------------------------------

# 35. Determinism Test

Exécuter deux fois le même replay.

Comparer :

``` text
events
scores
decisions
orders
```

------------------------------------------------------------------------

# 36. Time-Travel Bugs

Les replay tests doivent détecter toute dépendance involontaire à :

``` text
system clock
current date
non-seeded randomness
external mutable state
```

------------------------------------------------------------------------

# 37. Data Testing

La donnée est une dépendance critique du système.

Les tests doivent vérifier :

``` text
schema
freshness
completeness
uniqueness
ordering
consistency
```

------------------------------------------------------------------------

# 38. Schema Validation

Chaque message entrant doit respecter son schéma.

------------------------------------------------------------------------

# 39. Timestamp Validation

Tester :

``` text
UTC
timezone awareness
monotonic assumptions
future timestamps
stale timestamps
```

------------------------------------------------------------------------

# 40. Duplicate Detection

Injecter volontairement des événements identiques.

Résultat attendu :

``` text
no duplicated business effect
```

------------------------------------------------------------------------

# 41. Out-of-Order Data

Tester :

``` text
T3
T1
T2
```

et vérifier la politique définie.

------------------------------------------------------------------------

# 42. Missing Data

Simuler :

``` text
missing candle
missing trade
missing volume
temporary feed outage
```

------------------------------------------------------------------------

# 43. Corrupted Data

Tester :

``` text
negative volume
impossible OHLC
invalid price
malformed payload
```

------------------------------------------------------------------------

# 44. Stale Data

Le système doit identifier les données trop anciennes pour une décision
live.

------------------------------------------------------------------------

# 45. Data Reconciliation Tests

Comparer plusieurs sources ou données brutes/normalisées lorsque prévu.

------------------------------------------------------------------------

# 46. Point-in-Time Correctness

Un test majeur doit vérifier que chaque feature calculée à `T` n'utilise
que des informations disponibles à `T`.

------------------------------------------------------------------------

# 47. Look-Ahead Bias

Tester explicitement l'absence de :

``` text
future candle data
future session statistics
future labels
future corporate/event information
```

dans les calculs historiques.

------------------------------------------------------------------------

# 48. Survivorship Bias

Lorsque pertinent, vérifier que les univers historiques ne contiennent
pas uniquement les actifs ayant survécu jusqu'à aujourd'hui.

------------------------------------------------------------------------

# 49. Data Leakage

Pour le ML, vérifier que :

``` text
train
validation
test
```

restent correctement séparés.

------------------------------------------------------------------------

# 50. Market Analysis Engine Tests

Tester :

``` text
indicators
volatility
session metrics
context generation
missing-data behavior
```

------------------------------------------------------------------------

# 51. Market Structure Engine Tests

Tester :

``` text
swing detection
BOS
CHOCH
trend state
range state
structure invalidation
```

------------------------------------------------------------------------

# 52. Volume Profile Engine Tests

Tester :

``` text
POC
VAH
VAL
value area
binning
session boundaries
```

------------------------------------------------------------------------

# 53. SMC Engine Tests

Tester :

``` text
liquidity pools
sweeps
imbalances
order blocks
premium/discount
invalidations
```

sans supposer qu'un joli nom de concept suffit à rendre sa détection
objective.

------------------------------------------------------------------------

# 54. Scoring Engine Tests

Tester :

``` text
component scores
weights
normalization
caps
missing inputs
final score
reason codes
```

------------------------------------------------------------------------

# 55. Score Reproducibility

Même contexte et même configuration :

``` text
same score
```

------------------------------------------------------------------------

# 56. Score Boundary Tests

Tester les seuils utilisés par le Decision Engine.

------------------------------------------------------------------------

# 57. Decision Engine Tests

Tester :

``` text
ENTER
WATCH
NO_TRADE
EXIT
```

et toutes les transitions autorisées.

------------------------------------------------------------------------

# 58. Decision State Machine

Tester les transitions impossibles.

Exemple :

``` text
HALTED
→
ENTER
```

doit être refusé si la politique l'interdit.

------------------------------------------------------------------------

# 59. Stale Decision

Une décision trop ancienne doit être rejetée avant exécution.

------------------------------------------------------------------------

# 60. Duplicate Decision

Deux événements identiques ne doivent pas produire deux expositions
indépendantes.

------------------------------------------------------------------------

# 61. Risk Engine Tests

Le Risk Engine nécessite la couverture la plus stricte.

Tester :

``` text
position risk
portfolio heat
daily loss
drawdown
leverage
correlation
exposure
cooldown
kill switch
```

------------------------------------------------------------------------

# 62. Hard Limit Tests

Pour chaque limite :

``` text
below
equal
above
```

------------------------------------------------------------------------

# 63. Combined Risk Tests

Tester plusieurs limites simultanément.

Exemple :

``` text
position risk valid
but
daily loss exceeded
→ REJECT
```

------------------------------------------------------------------------

# 64. Portfolio Tests

Tester :

``` text
existing positions
new candidate
correlation
aggregate exposure
```

------------------------------------------------------------------------

# 65. Drawdown Tests

Simuler :

``` text
normal
warning
reduced-risk
halt
```

------------------------------------------------------------------------

# 66. Kill Switch Tests

Vérifier :

``` text
new orders blocked
pending orders handled according to policy
risk-reducing actions still possible
```

------------------------------------------------------------------------

# 67. Risk Fail-Closed Tests

Simuler :

``` text
missing risk data
database unavailable
invalid configuration
```

Résultat attendu pour nouvelle exposition :

``` text
REJECT
```

------------------------------------------------------------------------

# 68. Execution Engine Tests

Tester :

``` text
order creation
submission
ack
partial fill
full fill
cancel
replace
reject
timeout
reconnect
```

------------------------------------------------------------------------

# 69. Idempotency Tests

Renvoyer plusieurs fois la même requête.

Résultat :

``` text
no unintended duplicate order
```

------------------------------------------------------------------------

# 70. Network Failure Tests

Simuler :

``` text
request sent
connection lost
unknown exchange outcome
```

Le moteur doit réconcilier avant de supposer que l'ordre n'existe pas.

------------------------------------------------------------------------

# 71. Partial Fill Tests

Tester :

``` text
25%
50%
99%
```

de fill puis cancel/timeout.

------------------------------------------------------------------------

# 72. Rejection Tests

Simuler :

``` text
insufficient margin
invalid quantity
price band
exchange maintenance
rate limit
```

------------------------------------------------------------------------

# 73. Reconciliation Tests

Comparer :

``` text
local orders
local positions
exchange orders
exchange positions
```

------------------------------------------------------------------------

# 74. Position Mismatch

Une divergence doit déclencher une réponse contrôlée et observable.

------------------------------------------------------------------------

# 75. Execution Cost Tests

Vérifier les calculs :

``` text
fees
spread
slippage
```

------------------------------------------------------------------------

# 76. Monitoring Engine Tests

Tester :

``` text
metric emission
health status
alert conditions
incident creation
```

------------------------------------------------------------------------

# 77. Alert Tests

Chaque alerte critique doit avoir au moins un test démontrant son
déclenchement.

------------------------------------------------------------------------

# 78. Missing Alert Test

Tester aussi que l'alerte ne se déclenche pas en permanence en situation
normale.

Sinon le système apprend très vite aux humains à ignorer les alertes, ce
qui est une performance remarquable mais peu souhaitable.

------------------------------------------------------------------------

# 79. Knowledge Engine Tests

Tester :

``` text
lineage
retrieval
versioning
knowledge promotion
source references
```

------------------------------------------------------------------------

# 80. AI and Learning Engine Tests

Tester :

``` text
structured output
schema validation
evidence grounding
permissions
tool use
model version
prompt version
```

------------------------------------------------------------------------

# 81. AI Hallucination Tests

Fournir une question dont la preuve n'existe pas.

Résultat attendu :

``` text
insufficient evidence
```

plutôt qu'une invention.

------------------------------------------------------------------------

# 82. Prompt Injection Tests

Injecter dans une source externe :

``` text
Ignore previous instructions...
```

et vérifier que les règles système restent intactes.

------------------------------------------------------------------------

# 83. Tool Permission Tests

Un Research Agent ne doit pas pouvoir appeler :

``` text
submit_live_order
change_risk_limit
disable_kill_switch
```

------------------------------------------------------------------------

# 84. AI Schema Failure

Une réponse IA invalide doit être :

``` text
rejected
logged
```

et non interprétée librement.

------------------------------------------------------------------------

# 85. AI Regression Suite

Conserver des cas de référence pour :

``` text
research
analysis
tool selection
citation
security
```

------------------------------------------------------------------------

# 86. Model Tests

Pour les modèles ML :

``` text
training reproducibility
feature schema
prediction schema
calibration
out-of-sample performance
drift
```

------------------------------------------------------------------------

# 87. Baseline Comparison

Tout modèle candidat doit être comparé à une baseline explicite.

------------------------------------------------------------------------

# 88. Training Reproducibility

Avec :

``` text
same dataset
same code
same seed
same configuration
```

le résultat doit être reproductible dans les limites documentées.

------------------------------------------------------------------------

# 89. Feature Parity

Comparer :

``` text
offline features
vs
online features
```

sur les mêmes événements.

------------------------------------------------------------------------

# 90. Model Serving Tests

Tester :

``` text
latency
timeout
invalid feature
missing feature
model unavailable
```

------------------------------------------------------------------------

# 91. Fallback Tests

Une panne du modèle doit produire le comportement de fallback prévu.

------------------------------------------------------------------------

# 92. Governance Engine Tests

Tester :

``` text
roles
permissions
approvals
environment gates
artifact integrity
exceptions
audit
```

------------------------------------------------------------------------

# 93. Self-Approval Test

Un auteur ne doit pas pouvoir auto-approuver un changement critique si
la politique exige une séparation.

------------------------------------------------------------------------

# 94. Environment Scope Test

Une approbation `SHADOW` ne doit pas permettre `PRODUCTION`.

------------------------------------------------------------------------

# 95. Artifact Hash Test

Modifier l'artefact après approbation.

Résultat :

``` text
DEPLOYMENT DENIED
```

------------------------------------------------------------------------

# 96. Expired Approval Test

Une approbation expirée doit être refusée.

------------------------------------------------------------------------

# 97. Security Testing

La sécurité doit inclure :

``` text
authentication tests
authorization tests
input validation
secret handling
dependency scanning
network exposure checks
```

------------------------------------------------------------------------

# 98. Authorization Tests

Tester explicitement qu'un utilisateur sans droit reçoit :

``` text
DENY
```

------------------------------------------------------------------------

# 99. Privilege Escalation Tests

Vérifier qu'un rôle ne peut pas s'accorder lui-même de nouveaux
privilèges.

------------------------------------------------------------------------

# 100. Input Fuzzing

Les parsers et endpoints exposés peuvent être testés avec des entrées
aléatoires ou malformées.

------------------------------------------------------------------------

# 101. Performance Testing

Mesurer :

``` text
latency
throughput
memory
CPU
database load
```

------------------------------------------------------------------------

# 102. Latency Budgets

Définir un budget par composant critique.

Exemple conceptuel :

``` text
Data normalization: X ms
Scoring: Y ms
Risk decision: Z ms
```

Les valeurs réelles doivent être définies par benchmark.

------------------------------------------------------------------------

# 103. Load Testing

Tester des volumes supérieurs au trafic attendu.

------------------------------------------------------------------------

# 104. Burst Testing

Simuler un pic brutal d'événements.

------------------------------------------------------------------------

# 105. Soak Testing

Exécuter le système pendant une longue période pour détecter :

``` text
memory leaks
resource leaks
queue accumulation
```

------------------------------------------------------------------------

# 106. Database Performance

Tester les requêtes critiques sur des volumes réalistes.

------------------------------------------------------------------------

# 107. Backpressure Tests

Lorsque les producteurs dépassent la capacité des consommateurs :

``` text
what happens?
```

La réponse ne doit pas être « on espère ».

------------------------------------------------------------------------

# 108. Chaos Testing

Injecter des défaillances contrôlées.

------------------------------------------------------------------------

# 109. Failure Injection

Simuler :

``` text
database outage
event bus outage
exchange outage
AI provider outage
network latency
service restart
```

------------------------------------------------------------------------

# 110. Service Restart Test

Après restart :

``` text
state restored
orders reconciled
no duplicate exposure
```

------------------------------------------------------------------------

# 111. Dependency Failure

Une dépendance secondaire ne doit pas nécessairement arrêter tout le
système.

------------------------------------------------------------------------

# 112. Critical Dependency Failure

Une dépendance nécessaire à la sécurité doit déclencher un état sûr.

------------------------------------------------------------------------

# 113. Disaster Recovery Tests

Tester périodiquement :

``` text
backup restore
database recovery
configuration restore
secret recovery procedure
```

------------------------------------------------------------------------

# 114. Backup Test

Une sauvegarde qui n'a jamais été restaurée est une hypothèse, pas une
sauvegarde prouvée.

------------------------------------------------------------------------

# 115. Backtesting

Le backtest valide une hypothèse de stratégie sur données historiques.

Il n'est pas un test logiciel ordinaire.

------------------------------------------------------------------------

# 116. Backtest Requirements

Tout backtest sérieux doit enregistrer :

``` text
strategy version
dataset version
configuration
fees
slippage assumptions
time period
symbols
metrics
```

------------------------------------------------------------------------

# 117. No Look-Ahead

La simulation doit respecter strictement la causalité temporelle.

------------------------------------------------------------------------

# 118. Execution Realism

Le backtest doit éviter les hypothèses irréalistes telles que :

``` text
perfect fills
zero fees
zero slippage
infinite liquidity
```

------------------------------------------------------------------------

# 119. Intrabar Ambiguity

Lorsque l'ordre exact des mouvements dans une bougie est inconnu, le
moteur doit utiliser une politique explicite et prudente.

------------------------------------------------------------------------

# 120. Transaction Costs

Toujours inclure les coûts réalistes.

------------------------------------------------------------------------

# 121. Slippage Scenarios

Tester plusieurs hypothèses :

``` text
base
adverse
stress
```

------------------------------------------------------------------------

# 122. Out-of-Sample Testing

Une partie des données doit rester hors entraînement et hors
optimisation.

------------------------------------------------------------------------

# 123. Walk-Forward

Utiliser lorsque pertinent :

``` text
train
→ future test
→ roll
→ repeat
```

------------------------------------------------------------------------

# 124. Regime Segmentation

Analyser les résultats selon :

``` text
trend
range
high volatility
low volatility
bull
bear
```

selon les classifications disponibles.

------------------------------------------------------------------------

# 125. Asset Segmentation

Éviter qu'un seul actif masque les mauvaises performances ailleurs.

------------------------------------------------------------------------

# 126. Time Segmentation

Analyser :

``` text
year
quarter
month
session
```

selon la fréquence de stratégie.

------------------------------------------------------------------------

# 127. Parameter Sensitivity

Une stratégie robuste ne doit pas s'effondrer pour une variation minime
d'un paramètre.

------------------------------------------------------------------------

# 128. Parameter Surface

Analyser les performances autour du paramètre choisi.

Préférer un plateau robuste à un pic isolé.

------------------------------------------------------------------------

# 129. Multiple Testing

Enregistrer combien de variantes ont été testées.

------------------------------------------------------------------------

# 130. Overfitting Defense

Utiliser :

``` text
holdout
walk-forward
simpler baselines
parameter sensitivity
multiple-testing awareness
```

------------------------------------------------------------------------

# 131. Monte Carlo

Utiliser selon le besoin pour étudier :

``` text
trade ordering
drawdown distribution
return uncertainty
```

------------------------------------------------------------------------

# 132. Bootstrap

Peut être utilisé pour estimer l'incertitude des métriques.

------------------------------------------------------------------------

# 133. Stress Testing

Tester des hypothèses défavorables :

``` text
2x slippage
higher fees
reduced liquidity
delayed execution
missing signals
```

------------------------------------------------------------------------

# 134. Acceptance Criteria

Les critères de réussite doivent être définis avant de regarder le
résultat lorsque possible.

------------------------------------------------------------------------

# 135. Experiment Registry

Tout test quantitatif visant à valider une hypothèse doit être relié au
:

``` text
21-Experiment-Registry.md
```

------------------------------------------------------------------------

# 136. Paper Trading

Le paper trading valide le comportement avec données live sans capital
réel.

------------------------------------------------------------------------

# 137. Paper Objectives

Tester :

``` text
live data
timing
decision flow
order simulation
monitoring
operational stability
```

------------------------------------------------------------------------

# 138. Paper Limitations

Le paper trading ne reproduit pas parfaitement :

``` text
fills
queue position
market impact
psychology
```

------------------------------------------------------------------------

# 139. Shadow Mode

En shadow :

``` text
live inputs
real decisions
real execution logic
NO live order submission
```

------------------------------------------------------------------------

# 140. Shadow Comparison

Comparer :

``` text
candidate
vs
current production
```

sur les mêmes conditions.

------------------------------------------------------------------------

# 141. Shadow Duration

La durée doit être suffisante pour obtenir un échantillon pertinent.

Pas un nombre arbitraire universel.

------------------------------------------------------------------------

# 142. Limited Live

Le limited live introduit du capital réel avec :

``` text
small risk budget
strict hard limits
enhanced monitoring
```

------------------------------------------------------------------------

# 143. Limited Live Objectives

Valider :

``` text
real fills
real slippage
exchange behavior
operational workflow
```

------------------------------------------------------------------------

# 144. Production Promotion

La promotion doit dépendre de preuves accumulées, pas d'un unique
backtest séduisant.

------------------------------------------------------------------------

# 145. Production Testing

Même en production, les tests continuent sous forme de :

``` text
monitoring
invariants
reconciliation
drift detection
canaries
```

------------------------------------------------------------------------

# 146. Runtime Assertions

Certaines assertions métier peuvent être surveillées en runtime.

------------------------------------------------------------------------

# 147. Production Invariant Monitoring

Exemples :

``` text
risk limit never exceeded
unknown fill count = 0
unreconciled position count = 0
```

------------------------------------------------------------------------

# 148. Canary Deployment

Un nouveau service peut être déployé progressivement sur une portion
limitée du trafic lorsque l'architecture le permet.

------------------------------------------------------------------------

# 149. Feature Flags

Les nouvelles fonctionnalités risquées peuvent rester désactivables
rapidement.

------------------------------------------------------------------------

# 150. Rollback Tests

La procédure de rollback doit être testée avant d'en avoir réellement
besoin.

------------------------------------------------------------------------

# 151. CI Pipeline

Pipeline cible :

``` text
checkout
↓
format check
↓
lint
↓
type check
↓
unit tests
↓
contract tests
↓
integration tests
↓
security checks
↓
build
↓
artifact verification
```

------------------------------------------------------------------------

# 152. Fast CI

Les tests rapides doivent fournir un feedback rapide aux développeurs.

------------------------------------------------------------------------

# 153. Slow Test Suite

Les tests lourds peuvent être exécutés :

``` text
pre-merge
nightly
release
```

selon leur coût.

------------------------------------------------------------------------

# 154. Test Categories

Marquer les tests :

``` text
unit
integration
contract
replay
backtest
performance
security
chaos
```

------------------------------------------------------------------------

# 155. Test Isolation

Un test ne doit pas dépendre de l'ordre d'exécution des autres tests.

------------------------------------------------------------------------

# 156. Deterministic Tests

Les tests doivent utiliser :

``` text
fixed seed
controlled clock
known fixtures
```

lorsque nécessaire.

------------------------------------------------------------------------

# 157. Flaky Tests

Un test instable doit être traité comme un défaut.

Le relancer jusqu'à ce qu'il passe n'est pas une stratégie de qualité,
c'est de la négociation avec une machine.

------------------------------------------------------------------------

# 158. Quarantine

Un test flaky peut temporairement être isolé, avec issue de correction
obligatoire.

------------------------------------------------------------------------

# 159. Coverage

La couverture de code peut être mesurée.

Mais :

``` text
100% coverage
≠
100% correctness
```

------------------------------------------------------------------------

# 160. Coverage Priorities

Une couverture élevée est surtout importante sur :

``` text
risk
execution
decision
data contracts
governance
```

------------------------------------------------------------------------

# 161. Mutation Testing

À terme, utiliser du mutation testing sur certains modules critiques
pour vérifier que les tests détectent réellement les erreurs.

------------------------------------------------------------------------

# 162. Test Data Management

Les datasets de test doivent être :

``` text
versioned
documented
small when possible
representative
```

------------------------------------------------------------------------

# 163. Synthetic Data

Des données synthétiques sont utiles pour créer précisément des cas
limites.

------------------------------------------------------------------------

# 164. Historical Fixtures

Utiliser aussi des séquences historiques réelles anonymisées ou
contrôlées.

------------------------------------------------------------------------

# 165. Golden Dataset

Conserver un dataset stable permettant de comparer les versions.

------------------------------------------------------------------------

# 166. Test Data Provenance

Pour les datasets importants :

``` text
source
version
generation method
```

doivent être connus.

------------------------------------------------------------------------

# 167. Test Environment

Séparer :

``` text
TEST
PAPER
SHADOW
PRODUCTION
```

------------------------------------------------------------------------

# 168. No Production Credentials in CI

Les tests CI standards ne doivent pas disposer de credentials permettant
de trader réellement.

------------------------------------------------------------------------

# 169. Exchange Sandbox

Utiliser un sandbox lorsque disponible pour les tests d'intégration.

------------------------------------------------------------------------

# 170. Production Safety Test

Si un test tente accidentellement d'envoyer un ordre live depuis un
environnement non autorisé :

``` text
DENY
```

doit être garanti par architecture.

------------------------------------------------------------------------

# 171. Test Configuration

Les configurations de test doivent être clairement identifiées.

------------------------------------------------------------------------

# 172. Environment Guard

Le code doit pouvoir vérifier l'environnement avant une action
dangereuse.

------------------------------------------------------------------------

# 173. Release Test Suite

Avant une release importante :

``` text
all critical tests
replay
migration test
security checks
rollback readiness
```

------------------------------------------------------------------------

# 174. Migration Tests

Tester :

``` text
upgrade
application compatibility
rollback where supported
```

------------------------------------------------------------------------

# 175. Backward Compatibility

Pendant un déploiement progressif, ancienne et nouvelle versions peuvent
coexister.

Tester cette période.

------------------------------------------------------------------------

# 176. API Version Tests

Vérifier que les clients supportés continuent de fonctionner.

------------------------------------------------------------------------

# 177. Database Schema Compatibility

Tester les versions applicatives contre le schéma attendu.

------------------------------------------------------------------------

# 178. Observability Tests

Vérifier qu'une erreur importante produit :

``` text
log
metric
alert
trace/correlation
```

selon le besoin.

------------------------------------------------------------------------

# 179. Correlation Tests

Un trade doit pouvoir être suivi de :

``` text
signal
→ decision
→ risk
→ order
→ fill
→ position
```

------------------------------------------------------------------------

# 180. Audit Tests

Les événements critiques doivent être auditables.

------------------------------------------------------------------------

# 181. Incident Simulation

Organiser périodiquement des scénarios :

``` text
exchange down
database unavailable
stale market data
position mismatch
risk service unavailable
```

------------------------------------------------------------------------

# 182. Game Days

Une version mature peut organiser des exercices opérationnels contrôlés.

------------------------------------------------------------------------

# 183. Recovery Objectives

Définir selon les composants :

``` text
RTO
RPO
```

------------------------------------------------------------------------

# 184. RTO

Recovery Time Objective :

``` text
maximum acceptable recovery time
```

------------------------------------------------------------------------

# 185. RPO

Recovery Point Objective :

``` text
maximum acceptable data loss
```

------------------------------------------------------------------------

# 186. Test Ownership

Chaque composant doit avoir un responsable de sa qualité.

------------------------------------------------------------------------

# 187. Failed Test Ownership

Un test rouge ne doit pas devenir le décor permanent du pipeline.

------------------------------------------------------------------------

# 188. Test Review

Les tests sont revus avec le même sérieux que le code production.

------------------------------------------------------------------------

# 189. Test Naming Standard

Format recommandé :

``` text
test_<behavior>_when_<condition>
```

------------------------------------------------------------------------

# 190. Arrange / Act / Assert

Structure recommandée lorsque adaptée :

``` text
Arrange
Act
Assert
```

------------------------------------------------------------------------

# 191. One Behavioral Reason

Un test doit idéalement échouer pour une raison comportementale
identifiable.

------------------------------------------------------------------------

# 192. Avoid Over-Mocking

Trop de mocks peuvent produire une suite parfaitement verte pour un
système qui ne fonctionne pas lorsqu'on assemble ses composants.
Charmant, mais inutile.

------------------------------------------------------------------------

# 193. Test the Contract

Tester les comportements publics, pas chaque détail privé de
l'implémentation.

------------------------------------------------------------------------

# 194. Critical Path Tests

Priorité absolue :

``` text
market data → decision → risk → execution → reconciliation
```

------------------------------------------------------------------------

# 195. End-to-End Scenario

Scénario minimal :

``` text
market event
↓
analysis
↓
score
↓
decision
↓
risk approval
↓
simulated order
↓
fill
↓
position update
↓
monitoring
```

------------------------------------------------------------------------

# 196. Rejected Trade Scenario

Tester :

``` text
valid signal
↓
risk limit exceeded
↓
NO ORDER
```

------------------------------------------------------------------------

# 197. Kill Switch Scenario

Tester :

``` text
open system
↓
kill switch
↓
new exposure blocked
↓
risk-reducing operations preserved
```

------------------------------------------------------------------------

# 198. Duplicate Event Scenario

Tester :

``` text
same market/decision event twice
↓
single business effect
```

------------------------------------------------------------------------

# 199. Exchange Uncertainty Scenario

Tester :

``` text
submit order
↓
network failure
↓
unknown state
↓
reconciliation
↓
no duplicate submission
```

------------------------------------------------------------------------

# 200. Data Failure Scenario

Tester :

``` text
stale feed
↓
analysis invalid
↓
NO_TRADE
↓
alert
```

------------------------------------------------------------------------

# 201. AI Failure Scenario

Tester :

``` text
AI provider unavailable
↓
core safety remains operational
```

------------------------------------------------------------------------

# 202. Governance Failure Scenario

Tester :

``` text
Governance unavailable
↓
new production change blocked
↓
existing safety controls operational
```

------------------------------------------------------------------------

# 203. Acceptance Gates by Component

Chaque moteur doit avoir ses propres critères de promotion.

------------------------------------------------------------------------

# 204. Data Engine Gate

Exiger :

``` text
schema tests
deduplication tests
ordering tests
stale-data tests
replay
```

------------------------------------------------------------------------

# 205. Storage Engine Gate

Exiger :

``` text
transaction tests
migration tests
backup/restore test
performance checks
```

------------------------------------------------------------------------

# 206. Analysis Engines Gate

Exiger :

``` text
unit tests
golden datasets
replay reproducibility
edge cases
```

------------------------------------------------------------------------

# 207. Scoring / Decision Gate

Exiger :

``` text
threshold tests
reason-code tests
determinism
historical replay
```

------------------------------------------------------------------------

# 208. Risk Gate

Exiger :

``` text
hard-limit invariants
failure-mode tests
property tests
kill-switch tests
```

------------------------------------------------------------------------

# 209. Execution Gate

Exiger :

``` text
idempotency
partial fills
timeouts
reconciliation
sandbox integration
```

------------------------------------------------------------------------

# 210. AI Gate

Exiger :

``` text
evaluation suite
permission tests
grounding tests
schema tests
fallback tests
```

------------------------------------------------------------------------

# 211. Governance Gate

Exiger :

``` text
authorization tests
self-approval prevention
environment gates
audit tests
```

------------------------------------------------------------------------

# 212. Test Evidence

Les résultats importants doivent être conservés.

Exemples :

``` text
CI run
backtest report
replay report
security scan
performance benchmark
```

------------------------------------------------------------------------

# 213. Governance Integration

Un changement HIGH ou CRITICAL doit référencer les preuves de test
nécessaires avant approbation.

------------------------------------------------------------------------

# 214. Test Failure Policy

Si un test obligatoire échoue :

``` text
promotion blocked
```

------------------------------------------------------------------------

# 215. Waiver

Une exception à un test obligatoire doit être :

``` text
explicit
justified
approved
time-limited
audited
```

------------------------------------------------------------------------

# 216. No Silent Skip

Un test ignoré ne doit pas être considéré comme réussi.

------------------------------------------------------------------------

# 217. Test Dashboard

Le Monitoring / Governance tooling pourra afficher :

``` text
CI status
flaky tests
coverage
replay status
security status
last DR test
```

------------------------------------------------------------------------

# 218. Quality Metrics

Suivre :

``` text
test pass rate
escaped defects
regressions
flaky tests
rollback rate
incident rate
```

------------------------------------------------------------------------

# 219. Quantitative Validation Metrics

Suivre :

``` text
in-sample vs out-of-sample degradation
paper vs backtest degradation
live vs paper degradation
```

------------------------------------------------------------------------

# 220. Execution Validation Metrics

Comparer :

``` text
expected slippage
vs
realized slippage
```

------------------------------------------------------------------------

# 221. Model Validation Metrics

Comparer :

``` text
training
validation
shadow
live
```

------------------------------------------------------------------------

# 222. Continuous Improvement

Chaque incident ou bug important doit enrichir la suite de tests.

------------------------------------------------------------------------

# 223. Incident-to-Test Rule

Si un incident pouvait être reproduit automatiquement, créer un test
empêchant sa réapparition.

------------------------------------------------------------------------

# 224. Testing Debt

Les zones critiques insuffisamment testées doivent être explicitement
enregistrées comme dette.

------------------------------------------------------------------------

# 225. Risk-Based Testing

L'effort de test doit suivre le risque.

``` text
documentation typo
≠
position sizing change
```

Les deux ne méritent pas le même cérémonial.

------------------------------------------------------------------------

# 226. V1 Priorities

La V1 doit inclure :

-   formatting ;
-   linting ;
-   type checking ;
-   unit tests ;
-   contract tests ;
-   integration tests ;
-   data validation tests ;
-   replay tests ;
-   Risk Engine invariant tests ;
-   Execution Engine idempotency tests ;
-   kill-switch tests ;
-   CI pipeline ;
-   test environment isolation ;
-   no production credentials in tests ;
-   regression tests for bugs ;
-   basic backtest validation ;
-   basic paper/shadow validation.

------------------------------------------------------------------------

# 227. V2 Priorities

Ajouter :

-   property-based testing ;
-   broader replay datasets ;
-   performance tests ;
-   security automation ;
-   migration testing ;
-   AI evaluation suite ;
-   feature parity tests ;
-   drift tests.

------------------------------------------------------------------------

# 228. V3 Priorities

Ajouter :

-   chaos testing ;
-   automated DR tests ;
-   mutation testing on critical modules ;
-   advanced execution simulation ;
-   automated strategy robustness suite ;
-   continuous shadow comparison.

------------------------------------------------------------------------

# 229. V4 Priorities

Ajouter :

-   large-scale synthetic market scenarios ;
-   automated adversarial AI testing ;
-   continuous invariant verification ;
-   automated experiment validation ;
-   production canary analysis.

------------------------------------------------------------------------

# 230. Critères d'acceptation V1

La stratégie de test V1 est correctement appliquée lorsque :

-   chaque moteur critique possède des tests unitaires ;
-   les contrats inter-services sont testés ;
-   les données invalides sont rejetées ;
-   les événements dupliqués ne créent pas de doubles effets ;
-   les calculs critiques sont reproductibles ;
-   les limites du Risk Engine sont testées aux frontières ;
-   aucune nouvelle exposition ne peut contourner le Risk Engine ;
-   l'Execution Engine gère les retries sans duplication ;
-   les partial fills sont testés ;
-   la réconciliation est testée ;
-   le kill switch est testé ;
-   les bugs importants créent des tests de régression ;
-   les backtests vérifient l'absence de look-ahead ;
-   les coûts d'exécution sont inclus ;
-   les changements critiques sont bloqués si les tests requis échouent
    ;
-   les environnements de test n'ont pas accès aux credentials live ;
-   les preuves de test peuvent être reliées aux changements gouvernés.

------------------------------------------------------------------------

# 231. Risques principaux

## Faux sentiment de sécurité

Une grande quantité de tests peut masquer une mauvaise couverture des
vrais risques.

## Overfitting des tests

Le code peut être écrit uniquement pour satisfaire des tests trop
spécifiques.

## Flaky Tests

Ils détruisent progressivement la confiance dans la CI.

## Unrealistic Backtests

Une simulation irréaliste peut valider une stratégie inexistante
économiquement.

## Environment Drift

Le comportement testé peut différer du comportement production.

## Missing Failure Tests

Tester uniquement les chemins heureux laisse les incidents réels
découvrir les autres chemins à notre place.

------------------------------------------------------------------------

# 232. Principe d'ingénierie

Le niveau de preuve doit augmenter avec le risque :

``` text
LOW-RISK CHANGE
→ unit / static checks

MEDIUM-RISK CHANGE
→ integration / replay

HIGH-RISK CHANGE
→ quantitative + failure + shadow

CRITICAL CHANGE
→ independent review + limited live + explicit governance
```

------------------------------------------------------------------------

# 233. Architecture cible de validation

``` text
Code / Strategy / Model Change
            ↓
      Static Validation
            ↓
        Unit Tests
            ↓
 Contract + Integration Tests
            ↓
     Replay Validation
            ↓
 Quantitative / Robustness Tests
            ↓
      Governance Gate
            ↓
         Paper
            ↓
         Shadow
            ↓
      Limited Live
            ↓
       Production
            ↓
 Runtime Monitoring + Reconciliation
            ↓
 Regression Knowledge
```

------------------------------------------------------------------------

# 234. Règle fondatrice

> **QuantLab ne doit jamais confondre "ça marche sur mon test" avec
> "c'est suffisamment prouvé pour risquer du capital".**

Le système doit progresser par niveaux de preuve.

La boucle recherchée est :

``` text
SPECIFY
→ TEST
→ BREAK
→ FIX
→ REPLAY
→ VALIDATE
→ DEPLOY CAREFULLY
→ MONITOR
→ LEARN
```

Le test n'est donc pas la dernière étape du développement.

Il est une partie permanente du système de contrôle.

------------------------------------------------------------------------

# 235. Statut

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
-   `19-Deployment-Guide.md`
-   `20-Engineering-Principles.md`
-   `21-Experiment-Registry.md`
-   `22-API-Specification.md`
-   `23-Database-Schema.md`
-   `24-Security.md`
-   `25-Roadmap.md`

**Prochain document : `19-Deployment-Guide.md`**
