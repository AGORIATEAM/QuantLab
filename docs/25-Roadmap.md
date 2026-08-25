# 25 --- Roadmap

**Projet : QuantLab**\
**Document : Roadmap**\
**Version : 1.0**\
**Statut : Plan directeur de développement**

------------------------------------------------------------------------

# 1. Objectif

Cette roadmap définit l'ordre de construction de QuantLab.

Elle transforme l'architecture décrite dans les documents `01` à `24` en
séquence d'exécution concrète.

L'objectif n'est pas de construire immédiatement toutes les
fonctionnalités imaginables.

L'objectif est de construire, dans le bon ordre, un système :

``` text
REPRODUCTIBLE
TESTABLE
OBSERVABLE
SAFE
AUDITABLE
EXTENSIBLE
```

capable de progresser progressivement :

``` text
RESEARCH
→ BACKTEST
→ PAPER
→ SHADOW
→ LIMITED LIVE
→ PRODUCTION
→ LEARNING
```

------------------------------------------------------------------------

# 2. Principe directeur

La roadmap suit une règle simple :

> **Chaque couche doit produire suffisamment de preuves avant que la
> couche suivante puisse augmenter le niveau d'autonomie ou de risque.**

Ainsi :

``` text
No reliable data
→ no reliable analysis

No reliable analysis
→ no reliable decision

No reliable decision
→ no meaningful risk validation

No reliable risk
→ no live execution
```

------------------------------------------------------------------------

# 3. Anti-Roadmap

QuantLab ne doit pas commencer par :

-   une interface spectaculaire ;
-   des dizaines de stratégies ;
-   un système multi-agent autonome ;
-   une infrastructure distribuée prématurée ;
-   du machine learning sans baseline ;
-   une optimisation massive de paramètres ;
-   du live trading avant observabilité et contrôle du risque.

Construire d'abord ce qui empêche le système de se mentir.

------------------------------------------------------------------------

# 4. Phases principales

``` text
PHASE 0 — Foundation
PHASE 1 — Data Platform
PHASE 2 — Research & Analysis
PHASE 3 — Decision System
PHASE 4 — Risk System
PHASE 5 — Backtesting & Experiments
PHASE 6 — Paper Trading
PHASE 7 — Shadow Trading
PHASE 8 — Limited Live
PHASE 9 — Production Hardening
PHASE 10 — AI & Learning
PHASE 11 — Scale & Advanced Research
```

------------------------------------------------------------------------

# 5. Phase 0 --- Foundation

## Objectif

Créer les fondations du projet.

------------------------------------------------------------------------

# 6. Repository

Structure initiale :

``` text
quantlab/
├── README.md
├── docs/
├── src/
├── tests/
├── configs/
├── migrations/
├── experiments/
├── scripts/
├── infra/
└── .github/
```

------------------------------------------------------------------------

# 7. Documentation

Importer les documents :

``` text
01 → 25
annexes
ADR
```

dans :

``` text
docs/
```

------------------------------------------------------------------------

# 8. Development Environment

Standardiser :

``` text
Python version
package manager
virtual environment
linting
formatting
type checking
testing
```

------------------------------------------------------------------------

# 9. Dependency Management

Créer :

``` text
lock file
dependency policy
security scanning
```

------------------------------------------------------------------------

# 10. Git Standards

Mettre en place :

``` text
main branch protection
pull requests
commit conventions
CODEOWNERS
```

------------------------------------------------------------------------

# 11. CI V1

Pipeline minimal :

``` text
lint
type check
unit tests
security scan
secret scan
```

------------------------------------------------------------------------

# 12. Configuration

Créer un système de configuration versionné.

------------------------------------------------------------------------

# 13. Environment Separation

Définir :

``` text
development
test
research
paper
shadow
production
```

------------------------------------------------------------------------

# 14. Logging

Mettre en place les logs structurés dès le début.

------------------------------------------------------------------------

# 15. Request / Correlation IDs

Standardiser :

``` text
request_id
correlation_id
```

------------------------------------------------------------------------

# 16. Database Foundation

Installer PostgreSQL et migrations.

------------------------------------------------------------------------

# 17. Initial Schema

Créer les tables essentielles :

``` text
assets
venues
instruments
candles
strategies
audit_events
```

------------------------------------------------------------------------

# 18. Security Baseline

Mettre en place :

``` text
secret manager
no secrets in Git
separate credentials
MFA for critical accounts
```

------------------------------------------------------------------------

# 19. Definition of Done --- Phase 0

Phase 0 terminée lorsque :

``` text
[ ] repository operational
[ ] docs versioned
[ ] CI passing
[ ] tests executable
[ ] migrations working
[ ] configuration versioned
[ ] logs structured
[ ] secrets protected
[ ] environments defined
```

------------------------------------------------------------------------

# 20. Phase 1 --- Data Platform

## Objectif

Construire une source de données fiable et reproductible.

------------------------------------------------------------------------

# 21. Data Connectors

Implémenter les premiers connecteurs de marché.

Commencer avec un nombre limité de venues.

------------------------------------------------------------------------

# 22. Canonical Market Schema

Normaliser :

``` text
trades
candles
symbols
timestamps
volume
```

------------------------------------------------------------------------

# 23. Symbol Registry

Créer la résolution :

``` text
internal instrument
↔
venue symbol
```

------------------------------------------------------------------------

# 24. Historical Data

Permettre :

``` text
download
validation
storage
replay
```

------------------------------------------------------------------------

# 25. Live Data

Créer ingestion live séparée.

------------------------------------------------------------------------

# 26. Data Quality

Détecter :

``` text
gaps
duplicates
out-of-order data
stale data
invalid prices
invalid volumes
```

------------------------------------------------------------------------

# 27. Data Versioning

Chaque dataset de recherche doit être versionnable.

------------------------------------------------------------------------

# 28. Dataset Registry

Créer :

``` text
dataset ID
version
hash
source
time range
```

------------------------------------------------------------------------

# 29. Storage

Utiliser :

``` text
PostgreSQL
+
Parquet/object storage
```

selon volume.

------------------------------------------------------------------------

# 30. Replay Engine

Créer un moteur permettant :

``` text
historical events
→ deterministic replay
```

------------------------------------------------------------------------

# 31. Time Handling

Standard :

``` text
UTC internally
```

------------------------------------------------------------------------

# 32. Data Tests

Créer :

``` text
schema tests
quality tests
replay tests
connector tests
```

------------------------------------------------------------------------

# 33. Data Monitoring

Mesurer :

``` text
freshness
ingestion latency
missing events
connector health
```

------------------------------------------------------------------------

# 34. Definition of Done --- Phase 1

``` text
[ ] historical data reproducible
[ ] live data normalized
[ ] quality checks active
[ ] datasets versioned
[ ] replay deterministic
[ ] monitoring operational
```

------------------------------------------------------------------------

# 35. Phase 2 --- Research & Analysis

## Objectif

Construire les moteurs analytiques indépendamment du trading live.

------------------------------------------------------------------------

# 36. Market Analysis Engine

Implémenter les indicateurs fondamentaux nécessaires.

------------------------------------------------------------------------

# 37. Indicator Registry

Chaque indicateur doit avoir :

``` text
name
version
parameters
inputs
outputs
```

------------------------------------------------------------------------

# 38. Market Structure Engine

Implémenter :

``` text
swings
trend
BOS
CHoCH
```

avec définitions strictes.

------------------------------------------------------------------------

# 39. Volume Profile Engine

Implémenter :

``` text
POC
VAH
VAL
value area
HVN/LVN
```

------------------------------------------------------------------------

# 40. Smart Money Concepts Engine

Implémenter progressivement :

``` text
liquidity pools
liquidity sweeps
imbalances
FVG
order blocks
premium/discount
```

------------------------------------------------------------------------

# 41. No Ambiguous Concepts

Chaque concept discrétionnaire doit être converti en règle algorithmique
testable.

------------------------------------------------------------------------

# 42. Analysis Versioning

Chaque moteur doit enregistrer :

``` text
engine_version
config_version
```

------------------------------------------------------------------------

# 43. Analysis Runs

Créer la table et le workflow :

``` text
input data
→ analysis run
→ outputs
```

------------------------------------------------------------------------

# 44. Market Context

Construire un objet unifié :

``` text
MarketContext
```

------------------------------------------------------------------------

# 45. Multi-Timeframe Context

Ajouter progressivement la consolidation multi-timeframe.

------------------------------------------------------------------------

# 46. Analysis Visualization

Créer des outils simples permettant d'inspecter :

``` text
candles
swings
BOS
CHoCH
profiles
SMC zones
```

------------------------------------------------------------------------

# 47. Golden Datasets

Créer des datasets annotés servant de référence.

------------------------------------------------------------------------

# 48. Analysis Tests

Pour chaque moteur :

``` text
unit
golden cases
edge cases
regression
```

------------------------------------------------------------------------

# 49. Definition of Done --- Phase 2

``` text
[ ] analysis deterministic
[ ] outputs versioned
[ ] concepts formally defined
[ ] golden datasets available
[ ] MarketContext generated
[ ] regression tests passing
```

------------------------------------------------------------------------

# 50. Phase 3 --- Scoring & Decision System

## Objectif

Transformer l'analyse en décisions explicites.

------------------------------------------------------------------------

# 51. Scoring Engine V1

Créer un système simple, déterministe et explicable.

------------------------------------------------------------------------

# 52. Score Components

Exemple :

``` text
market structure
volume profile
SMC
momentum
regime
```

------------------------------------------------------------------------

# 53. Score Normalization

Standardiser le score :

``` text
0 → 100
```

------------------------------------------------------------------------

# 54. Reason Codes

Chaque contribution doit produire des reason codes.

------------------------------------------------------------------------

# 55. Decision Engine V1

Actions :

``` text
ENTER_LONG
ENTER_SHORT
EXIT
REDUCE
HOLD
NO_TRADE
```

------------------------------------------------------------------------

# 56. Decision Record

Chaque décision doit conserver :

``` text
context
score
strategy version
reasons
timestamp
expiration
```

------------------------------------------------------------------------

# 57. Decision Expiration

Les signaux live doivent expirer.

------------------------------------------------------------------------

# 58. No Execution Yet

À cette phase :

``` text
Decision Engine
≠
Execution Engine
```

------------------------------------------------------------------------

# 59. Strategy Registry

Créer :

``` text
strategy
strategy version
configuration
```

------------------------------------------------------------------------

# 60. Strategy Interface

Standardiser :

``` text
MarketContext
→ Strategy
→ Score
→ Decision
```

------------------------------------------------------------------------

# 61. Decision Tests

Tester :

``` text
determinism
thresholds
invalid contexts
edge cases
```

------------------------------------------------------------------------

# 62. Explainability

Pouvoir répondre :

``` text
Why did the strategy decide this?
```

------------------------------------------------------------------------

# 63. Definition of Done --- Phase 3

``` text
[ ] strategies versioned
[ ] scoring deterministic
[ ] decisions persisted
[ ] reason codes available
[ ] no direct execution path
[ ] decision replay works
```

------------------------------------------------------------------------

# 64. Phase 4 --- Risk System

## Objectif

Créer une frontière indépendante entre décision et capital.

------------------------------------------------------------------------

# 65. Risk Engine V1

Implémenter :

``` text
position sizing
max risk per trade
max daily loss
max exposure
max concurrent positions
```

------------------------------------------------------------------------

# 66. Risk Profiles

Créer des profils versionnés.

------------------------------------------------------------------------

# 67. Risk Evaluation

Workflow :

``` text
Decision
↓
Risk Evaluation
↓
APPROVED / MODIFIED / REJECTED
```

------------------------------------------------------------------------

# 68. Position Sizing

Le sizing doit être calculé côté Risk Engine.

------------------------------------------------------------------------

# 69. Portfolio Risk

Ajouter :

``` text
gross exposure
net exposure
portfolio heat
```

------------------------------------------------------------------------

# 70. Daily Loss Limit

Créer une limite dure.

------------------------------------------------------------------------

# 71. Drawdown Protection

Créer des règles de réduction ou halt.

------------------------------------------------------------------------

# 72. Kill Switch

Implémenter avant live.

------------------------------------------------------------------------

# 73. Risk State

États :

``` text
NORMAL
REDUCED
HALTED
```

------------------------------------------------------------------------

# 74. Fail Closed

Si le risque ne peut pas être calculé :

``` text
NO NEW EXPOSURE
```

------------------------------------------------------------------------

# 75. Risk Audit

Toute décision de risque doit être persistée.

------------------------------------------------------------------------

# 76. Risk Configuration Governance

Les limites critiques ne peuvent pas être modifiées par une stratégie.

------------------------------------------------------------------------

# 77. Risk Tests

Tester :

``` text
boundary values
portfolio limits
daily loss
drawdown
stale data
dependency failures
```

------------------------------------------------------------------------

# 78. Definition of Done --- Phase 4

``` text
[ ] every decision passes Risk Engine
[ ] hard limits tested
[ ] kill switch operational
[ ] fail-closed behavior tested
[ ] risk audit complete
```

------------------------------------------------------------------------

# 79. Phase 5 --- Backtesting & Experimentation

## Objectif

Construire une infrastructure de preuve avant toute exécution live.

------------------------------------------------------------------------

# 80. Backtest Engine

Créer un moteur événementiel réutilisant autant que possible la logique
production.

------------------------------------------------------------------------

# 81. Avoid Separate Strategy Logic

La stratégie ne doit pas avoir une version « backtest » et une version «
live » différentes.

------------------------------------------------------------------------

# 82. Execution Simulation

Simuler :

``` text
fees
slippage
latency
partial fills where needed
```

------------------------------------------------------------------------

# 83. Experiment Registry

Implémenter `21-Experiment-Registry.md`.

------------------------------------------------------------------------

# 84. Experiment Specification

Chaque expérience contient :

``` text
hypothesis
baseline
dataset
code commit
config
metrics
acceptance criteria
```

------------------------------------------------------------------------

# 85. Experiment Runner

Automatiser :

``` text
metadata capture
execution
metrics
artifacts
report
```

------------------------------------------------------------------------

# 86. Out-of-Sample Testing

Créer une discipline OOS.

------------------------------------------------------------------------

# 87. Walk-Forward

Ajouter pour les stratégies adaptées.

------------------------------------------------------------------------

# 88. Robustness Suite

Tester :

``` text
parameter sensitivity
fees
slippage
regimes
assets
time periods
```

------------------------------------------------------------------------

# 89. Monte Carlo

Ajouter pour :

``` text
trade ordering
drawdown distribution
```

------------------------------------------------------------------------

# 90. Baselines

Comparer toute stratégie à une baseline.

------------------------------------------------------------------------

# 91. Negative Results

Conserver les expériences rejetées.

------------------------------------------------------------------------

# 92. Champion / Challenger

Créer le modèle :

``` text
current champion
vs
candidate challenger
```

------------------------------------------------------------------------

# 93. Research Reports

Générer automatiquement :

``` text
metrics
equity
drawdown
trades
robustness
limitations
```

------------------------------------------------------------------------

# 94. Definition of Done --- Phase 5

``` text
[ ] experiments reproducible
[ ] OOS mandatory
[ ] costs included
[ ] robustness suite exists
[ ] results versioned
[ ] negative experiments retained
[ ] champion/challenger supported
```

------------------------------------------------------------------------

# 95. Phase 6 --- Paper Trading

## Objectif

Tester le système complet sur données live sans capital réel.

------------------------------------------------------------------------

# 96. Execution Engine V1

Créer l'interface d'exécution.

------------------------------------------------------------------------

# 97. Paper Broker

Implémenter un adaptateur simulé.

------------------------------------------------------------------------

# 98. Order State Machine

Supporter :

``` text
CREATED
SUBMITTED
ACKNOWLEDGED
PARTIALLY_FILLED
FILLED
CANCELLED
REJECTED
UNKNOWN
```

------------------------------------------------------------------------

# 99. Idempotency

Implémenter avant connexion live.

------------------------------------------------------------------------

# 100. Position Engine

Construire les positions depuis les fills.

------------------------------------------------------------------------

# 101. Portfolio State

Maintenir :

``` text
cash
equity
positions
PnL
exposure
```

------------------------------------------------------------------------

# 102. Monitoring

Créer dashboards et alertes pour :

``` text
data
decisions
risk
orders
positions
system health
```

------------------------------------------------------------------------

# 103. Reconciliation

Même en paper :

``` text
expected state
vs
broker state
```

------------------------------------------------------------------------

# 104. Incident Workflow

Tester :

``` text
halt
restart
recovery
```

------------------------------------------------------------------------

# 105. Paper Duration

Ne pas promouvoir après quelques heures de fonctionnement.

Le système doit traverser suffisamment de conditions de marché.

------------------------------------------------------------------------

# 106. Paper Metrics

Comparer :

``` text
backtest expectation
vs
paper results
```

------------------------------------------------------------------------

# 107. Definition of Done --- Phase 6

``` text
[ ] full pipeline runs live
[ ] no real capital
[ ] execution state machine stable
[ ] monitoring active
[ ] alerts tested
[ ] reconciliation works
[ ] restart/recovery tested
```

------------------------------------------------------------------------

# 108. Phase 7 --- Shadow Trading

## Objectif

Connecter le système aux conditions réelles d'exécution sans envoyer les
ordres proposés.

------------------------------------------------------------------------

# 109. Shadow Decisions

Le système calcule :

``` text
what it would trade
```

sans exécution.

------------------------------------------------------------------------

# 110. Real Venue State

Consommer :

``` text
real order books
real trades
real latency conditions
```

------------------------------------------------------------------------

# 111. Execution Feasibility

Comparer :

``` text
theoretical fills
vs
real market availability
```

------------------------------------------------------------------------

# 112. Slippage Calibration

Utiliser les données shadow pour améliorer les modèles.

------------------------------------------------------------------------

# 113. Latency Measurement

Mesurer :

``` text
market event
→ context
→ decision
→ risk
→ hypothetical order
```

------------------------------------------------------------------------

# 114. Drift Analysis

Comparer :

``` text
backtest
paper
shadow
```

------------------------------------------------------------------------

# 115. Definition of Done --- Phase 7

``` text
[ ] shadow stable
[ ] realistic slippage calibrated
[ ] latency measured
[ ] execution assumptions validated
[ ] no critical divergence unexplained
```

------------------------------------------------------------------------

# 116. Phase 8 --- Limited Live

## Objectif

Introduire du capital réel avec exposition volontairement faible.

------------------------------------------------------------------------

# 117. Preconditions

Avant activation :

``` text
governance approval
security checklist
risk checklist
deployment checklist
tested kill switch
tested reconciliation
```

------------------------------------------------------------------------

# 118. Minimal Capital

Commencer avec une taille suffisamment faible pour que les erreurs
restent supportables.

------------------------------------------------------------------------

# 119. Restricted Universe

Limiter :

``` text
symbols
strategies
sessions
order types
```

------------------------------------------------------------------------

# 120. Conservative Risk

Utiliser des limites plus strictes que la cible finale.

------------------------------------------------------------------------

# 121. No Leverage Expansion

Ne pas augmenter simultanément :

``` text
capital
leverage
strategy count
asset count
```

------------------------------------------------------------------------

# 122. Live Execution Adapter

Connecter une première venue.

------------------------------------------------------------------------

# 123. Exchange Credentials

Permissions :

``` text
trade only
no withdrawal
IP restricted where possible
```

------------------------------------------------------------------------

# 124. Live Reconciliation

Fréquence élevée.

------------------------------------------------------------------------

# 125. Live Alerts

Alertes critiques sur :

``` text
unknown order
position mismatch
risk breach
credential failure
stale data
execution anomalies
```

------------------------------------------------------------------------

# 126. Manual Oversight

La première phase live doit être supervisée.

------------------------------------------------------------------------

# 127. Live Experiment

Le limited-live doit être traité comme une expérience.

------------------------------------------------------------------------

# 128. Promotion Metrics

Mesurer :

``` text
slippage
fill quality
latency
PnL
risk behavior
operational incidents
```

------------------------------------------------------------------------

# 129. Stop Conditions

Définir avant lancement :

``` text
max loss
max mismatch
max incident severity
```

------------------------------------------------------------------------

# 130. Definition of Done --- Phase 8

``` text
[ ] live trading works at low exposure
[ ] no uncontrolled risk events
[ ] reconciliation reliable
[ ] real slippage understood
[ ] kill switch proven
[ ] operational procedures validated
```

------------------------------------------------------------------------

# 131. Phase 9 --- Production Hardening

## Objectif

Transformer un prototype live contrôlé en système de production robuste.

------------------------------------------------------------------------

# 132. High Availability

Ajouter uniquement là où nécessaire.

------------------------------------------------------------------------

# 133. Database Reliability

Mettre en place :

``` text
PITR
restore tests
replication where justified
```

------------------------------------------------------------------------

# 134. Service Recovery

Automatiser les redémarrages sûrs.

------------------------------------------------------------------------

# 135. State Recovery

Après restart :

``` text
load state
reconcile venue
resume safely
```

------------------------------------------------------------------------

# 136. Disaster Recovery

Documenter et tester.

------------------------------------------------------------------------

# 137. Security Hardening

Ajouter :

``` text
strong workload identity
artifact signing
SBOM
access reviews
```

------------------------------------------------------------------------

# 138. Observability Hardening

Ajouter :

``` text
SLO
p95/p99
distributed tracing
capacity metrics
```

------------------------------------------------------------------------

# 139. Incident Drills

Simuler :

``` text
exchange outage
database failure
network partition
stale data
credential revocation
```

------------------------------------------------------------------------

# 140. Operational Runbooks

Créer :

``` text
halt trading
restart service
rotate key
restore DB
reconcile positions
rollback deployment
```

------------------------------------------------------------------------

# 141. Definition of Done --- Phase 9

``` text
[ ] recovery tested
[ ] security hardened
[ ] SLO defined
[ ] incident drills completed
[ ] runbooks available
[ ] production operations repeatable
```

------------------------------------------------------------------------

# 142. Phase 10 --- AI & Learning

## Objectif

Ajouter l'IA seulement après que le système déterministe dispose d'une
base fiable.

------------------------------------------------------------------------

# 143. Knowledge Engine

Construire la mémoire structurée :

``` text
experiments
findings
strategies
incidents
decisions
```

------------------------------------------------------------------------

# 144. Research Assistant

Premier agent recommandé :

``` text
READ-ONLY RESEARCH AGENT
```

------------------------------------------------------------------------

# 145. Agent Capabilities V1

Autoriser :

``` text
search docs
analyze experiments
compare results
generate research proposals
```

------------------------------------------------------------------------

# 146. No Production Write

V1 IA :

``` text
production write = forbidden
```

------------------------------------------------------------------------

# 147. Experiment Proposal Agent

L'IA peut proposer :

``` text
hypothesis
experiment design
metrics
```

------------------------------------------------------------------------

# 148. Experiment Execution Agent

Ensuite, permettre l'exécution en sandbox avec budgets.

------------------------------------------------------------------------

# 149. AI Evaluation

Mesurer :

``` text
accuracy
usefulness
cost
latency
reproducibility
```

------------------------------------------------------------------------

# 150. Prompt Registry

Versionner les prompts.

------------------------------------------------------------------------

# 151. Model Registry

Versionner les modèles utilisés.

------------------------------------------------------------------------

# 152. AI Audit

Enregistrer :

``` text
agent
model
prompt
tools
actions
```

------------------------------------------------------------------------

# 153. AI Governance

Toute augmentation de permissions passe par Governance Engine.

------------------------------------------------------------------------

# 154. AI Code Agent

Peut proposer du code via PR.

------------------------------------------------------------------------

# 155. AI Merge Restriction

L'agent ne merge pas seul les changements critiques.

------------------------------------------------------------------------

# 156. AI Deployment Restriction

L'agent ne déploie pas seul en production.

------------------------------------------------------------------------

# 157. AI Trading Restriction

L'agent ne contourne jamais :

``` text
Decision
→ Risk
→ Execution
```

------------------------------------------------------------------------

# 158. Learning Loop

Architecture :

``` text
Production
↓
Monitoring
↓
Evidence
↓
Knowledge
↓
Hypothesis
↓
Experiment
↓
Validation
↓
Governance
↓
Production
```

------------------------------------------------------------------------

# 159. Definition of Done --- Phase 10

``` text
[ ] knowledge registry operational
[ ] read-only agent useful
[ ] prompts versioned
[ ] AI actions audited
[ ] sandbox experiments controlled
[ ] no direct production authority
```

------------------------------------------------------------------------

# 160. Phase 11 --- Scale & Advanced Research

## Objectif

Augmenter la sophistication seulement après preuve de stabilité.

------------------------------------------------------------------------

# 161. Multi-Asset

Étendre progressivement :

``` text
crypto
equities
futures
FX
```

selon besoin.

------------------------------------------------------------------------

# 162. Multi-Venue

Ajouter plusieurs venues.

------------------------------------------------------------------------

# 163. Portfolio Optimization

Ajouter :

``` text
correlation
capital allocation
portfolio constraints
```

------------------------------------------------------------------------

# 164. Advanced Risk

Ajouter :

``` text
stress testing
tail risk
scenario analysis
dynamic exposure
```

------------------------------------------------------------------------

# 165. Machine Learning

Introduire uniquement lorsque :

``` text
baseline deterministic exists
dataset quality proven
evaluation framework mature
```

------------------------------------------------------------------------

# 166. Feature Store

Ajouter si le nombre de modèles le justifie.

------------------------------------------------------------------------

# 167. Model Monitoring

Surveiller :

``` text
drift
calibration
performance
```

------------------------------------------------------------------------

# 168. Distributed Backtesting

Ajouter lorsque les expériences locales deviennent réellement
limitantes.

------------------------------------------------------------------------

# 169. Compute Scheduling

Gérer :

``` text
CPU
GPU
budgets
priority
```

------------------------------------------------------------------------

# 170. Autonomous Research

Permettre aux agents de :

``` text
propose
run
compare
iterate
```

dans un environnement strictement contrôlé.

------------------------------------------------------------------------

# 171. Autonomous Promotion

Ne pas automatiser entièrement la promotion live tant que le niveau de
preuve et de gouvernance ne le justifie pas.

------------------------------------------------------------------------

# 172. Multi-Agent Architecture

Introduire uniquement si des rôles séparés apportent une valeur
démontrée.

------------------------------------------------------------------------

# 173. Potential Agents

``` text
Research Agent
Data Quality Agent
Experiment Agent
Risk Analysis Agent
Code Review Agent
Monitoring Agent
Security Agent
```

------------------------------------------------------------------------

# 174. Agent Coordination

Les agents communiquent via :

``` text
structured tasks
artifacts
events
```

et non via un bavardage opaque impossible à auditer.

------------------------------------------------------------------------

# 175. Scaling Principle

Scaler :

``` text
evidence
before
complexity
```

------------------------------------------------------------------------

# 176. Milestone M0

## Foundation Ready

Livrables :

``` text
repository
CI
docs
database
security baseline
```

------------------------------------------------------------------------

# 177. Milestone M1

## Reliable Data

Livrables :

``` text
historical data
live ingestion
quality
dataset registry
replay
```

------------------------------------------------------------------------

# 178. Milestone M2

## Deterministic Analysis

Livrables :

``` text
Market Analysis
Market Structure
Volume Profile
SMC
MarketContext
```

------------------------------------------------------------------------

# 179. Milestone M3

## Decision Pipeline

Livrables :

``` text
Scoring
Decision Engine
Strategy Registry
reason codes
```

------------------------------------------------------------------------

# 180. Milestone M4

## Risk Boundary

Livrables :

``` text
Risk Engine
hard limits
kill switch
risk audit
```

------------------------------------------------------------------------

# 181. Milestone M5

## Research Platform

Livrables :

``` text
Backtester
Experiment Registry
OOS
robustness
reports
```

------------------------------------------------------------------------

# 182. Milestone M6

## Paper Trading

Livrables :

``` text
Execution Engine
paper adapter
positions
reconciliation
monitoring
```

------------------------------------------------------------------------

# 183. Milestone M7

## Shadow Ready

Livrables :

``` text
real-time shadow
latency measurement
slippage calibration
```

------------------------------------------------------------------------

# 184. Milestone M8

## Limited Live

Livrables :

``` text
first venue
low capital
live reconciliation
production alerts
```

------------------------------------------------------------------------

# 185. Milestone M9

## Production Hardened

Livrables :

``` text
DR
security hardening
SLO
runbooks
incident drills
```

------------------------------------------------------------------------

# 186. Milestone M10

## AI Research Layer

Livrables :

``` text
Knowledge Engine
research agent
experiment agent
AI audit
```

------------------------------------------------------------------------

# 187. Priority Framework

Chaque nouvelle fonctionnalité doit être évaluée selon :

``` text
VALUE
RISK REDUCTION
DEPENDENCIES
COMPLEXITY
EVIDENCE
```

------------------------------------------------------------------------

# 188. Priority 0

Bloque :

``` text
correctness
capital safety
security
data integrity
```

------------------------------------------------------------------------

# 189. Priority 1

Nécessaire au prochain milestone.

------------------------------------------------------------------------

# 190. Priority 2

Amélioration utile mais non bloquante.

------------------------------------------------------------------------

# 191. Priority 3

Optimisation ou confort.

------------------------------------------------------------------------

# 192. Backlog Discipline

Une idée intéressante n'est pas automatiquement une priorité.

Le cimetière des projets techniques est rempli de fonctionnalités «
intéressantes ».

------------------------------------------------------------------------

# 193. Technical Debt

La dette doit être enregistrée explicitement.

------------------------------------------------------------------------

# 194. Debt Categories

``` text
architecture
testing
security
observability
performance
documentation
```

------------------------------------------------------------------------

# 195. Debt Budget

Réserver une partie de chaque cycle à la réduction de dette.

------------------------------------------------------------------------

# 196. No Hidden Debt

Un workaround temporaire doit être tracé.

------------------------------------------------------------------------

# 197. Release Strategy

Préférer des releases petites et fréquentes.

------------------------------------------------------------------------

# 198. Semantic Versioning

Utiliser lorsque pertinent :

``` text
MAJOR.MINOR.PATCH
```

------------------------------------------------------------------------

# 199. Release Notes

Chaque release documente :

``` text
changes
risk
migrations
rollback
```

------------------------------------------------------------------------

# 200. Feature Flags

Utiliser pour les changements progressifs.

------------------------------------------------------------------------

# 201. Dark Launch

Déployer un composant sans l'activer pour observer son comportement.

------------------------------------------------------------------------

# 202. Canary

Pour certains services :

``` text
small traffic
→ observe
→ expand
```

------------------------------------------------------------------------

# 203. Strategy Rollout

Équivalent trading :

``` text
backtest
→ paper
→ shadow
→ limited live
→ full allocation
```

------------------------------------------------------------------------

# 204. Capital Scaling

Le capital doit augmenter progressivement.

------------------------------------------------------------------------

# 205. Capital Promotion Rule

Une augmentation de capital nécessite :

``` text
evidence
stable execution
risk compliance
no unresolved critical incidents
```

------------------------------------------------------------------------

# 206. Scale One Dimension at a Time

Éviter d'augmenter simultanément :

``` text
capital
assets
strategies
venues
autonomy
```

------------------------------------------------------------------------

# 207. Research Roadmap

Ordre recommandé :

``` text
simple deterministic baseline
↓
market structure
↓
volume profile
↓
SMC
↓
combined scoring
↓
regime adaptation
↓
portfolio layer
↓
ML where justified
```

------------------------------------------------------------------------

# 208. ML Gate

Avant ML :

``` text
[ ] clean dataset
[ ] strong baseline
[ ] OOS framework
[ ] experiment registry
[ ] feature versioning
[ ] model registry
```

------------------------------------------------------------------------

# 209. AI Gate

Avant agents autonomes :

``` text
[ ] tool permissions
[ ] sandbox
[ ] audit
[ ] budgets
[ ] governance
[ ] kill switch
```

------------------------------------------------------------------------

# 210. Live Gate

Avant trading live :

``` text
[ ] reliable data
[ ] deterministic decisions
[ ] independent Risk Engine
[ ] tested Execution Engine
[ ] monitoring
[ ] reconciliation
[ ] security baseline
[ ] kill switch
[ ] governance approval
```

------------------------------------------------------------------------

# 211. Production Gate

Avant augmentation significative de capital :

``` text
[ ] limited-live evidence
[ ] incident drills
[ ] backup restore test
[ ] security review
[ ] operational runbooks
[ ] performance stability
```

------------------------------------------------------------------------

# 212. Success Metrics

La roadmap ne doit pas être mesurée uniquement par le nombre de
fonctionnalités.

------------------------------------------------------------------------

# 213. Engineering Metrics

``` text
test pass rate
deployment failure rate
MTTR
incident count
data quality
```

------------------------------------------------------------------------

# 214. Research Metrics

``` text
experiments completed
reproduction rate
OOS survival
promotion rate
```

------------------------------------------------------------------------

# 215. Trading Metrics

``` text
net expectancy
drawdown
risk-adjusted return
execution quality
```

------------------------------------------------------------------------

# 216. Operational Metrics

``` text
uptime
reconciliation mismatches
order errors
alert response
```

------------------------------------------------------------------------

# 217. AI Metrics

``` text
useful proposal rate
experiment quality
cost
tool failure rate
human override rate
```

------------------------------------------------------------------------

# 218. Security Metrics

``` text
critical vulnerabilities
credential incidents
unauthorized actions
time to remediation
```

------------------------------------------------------------------------

# 219. Stop Conditions

Le projet doit pouvoir suspendre une phase si :

``` text
data unreliable
risk controls failing
security issue unresolved
execution mismatch unexplained
```

------------------------------------------------------------------------

# 220. No Deadline Overrides Safety

Une date de lancement ne justifie pas de contourner les gates.

------------------------------------------------------------------------

# 221. Roadmap Review

Réviser régulièrement la roadmap.

------------------------------------------------------------------------

# 222. Evidence-Based Reprioritization

Les priorités peuvent changer selon :

``` text
experiment results
incidents
new constraints
market realities
```

------------------------------------------------------------------------

# 223. Architecture Review

À chaque milestone majeur, vérifier si les hypothèses d'architecture
restent valides.

------------------------------------------------------------------------

# 224. ADR Review

Créer de nouveaux ADR lorsque des décisions structurantes apparaissent.

------------------------------------------------------------------------

# 225. Documentation Maintenance

Les documents `01` à `25` doivent évoluer avec le système.

------------------------------------------------------------------------

# 226. Documentation Drift

Une documentation fausse est parfois pire qu'une documentation absente.

La CI et les reviews doivent réduire ce risque.

------------------------------------------------------------------------

# 227. V1 Target

La V1 de QuantLab doit viser :

``` text
one or few venues
limited asset universe
deterministic strategies
reproducible backtests
paper trading
shadow trading
limited live capability
```

------------------------------------------------------------------------

# 228. V1 Non-Goals

Pas nécessaire pour V1 :

``` text
massive multi-agent autonomy
multi-region architecture
dozens of exchanges
high-frequency trading
complex ML ensemble
fully autonomous capital allocation
```

------------------------------------------------------------------------

# 229. V2 Target

V2 :

``` text
production hardening
multiple strategies
portfolio risk
richer experiment automation
knowledge engine
AI research assistant
```

------------------------------------------------------------------------

# 230. V3 Target

V3 :

``` text
multi-venue
advanced portfolio allocation
ML models
distributed research
advanced monitoring
security automation
```

------------------------------------------------------------------------

# 231. V4 Target

V4 :

``` text
controlled autonomous research
multi-agent workflows
continuous learning
automated hypothesis generation
governance-aware AI operations
```

------------------------------------------------------------------------

# 232. Long-Term Vision

QuantLab doit progressivement devenir :

``` text
Market Data Platform
+
Quantitative Research Platform
+
Decision System
+
Risk Control System
+
Execution Platform
+
Knowledge System
+
Controlled AI Research Environment
```

------------------------------------------------------------------------

# 233. Long-Term Constraint

L'autonomie ne doit jamais progresser plus vite que :

``` text
observability
risk control
security
governance
```

------------------------------------------------------------------------

# 234. Recommended Immediate Build Order

Ordre concret :

``` text
1. Repository + CI
2. PostgreSQL + migrations
3. Data model
4. Historical data connector
5. Dataset registry
6. Replay engine
7. Market Analysis Engine
8. Market Structure Engine
9. Volume Profile Engine
10. SMC Engine
11. MarketContext
12. Scoring Engine
13. Decision Engine
14. Risk Engine
15. Backtester
16. Experiment Registry
17. Paper Execution Engine
18. Position Engine
19. Monitoring
20. Reconciliation
21. Shadow mode
22. Security hardening
23. Limited live
24. Knowledge Engine
25. AI research agents
```

------------------------------------------------------------------------

# 235. First 30-Day Objective

Objectif raisonnable :

``` text
Foundation
+
Data Platform V1
+
first deterministic analysis
```

Pas besoin de prétendre avoir construit une société de trading autonome
en quatre week-ends. Les marchés ne distribuent pas de points bonus pour
vitesse narrative.

------------------------------------------------------------------------

# 236. First 60-Day Objective

Viser :

``` text
analysis engines
+
MarketContext
+
Scoring
+
Decision
+
initial backtesting
```

------------------------------------------------------------------------

# 237. First 90-Day Objective

Viser :

``` text
Risk Engine
+
Experiment Registry
+
robust backtesting
+
paper pipeline
```

Les délais restent indicatifs et doivent dépendre des ressources
réelles.

------------------------------------------------------------------------

# 238. Pre-Live Objective

Avant live :

``` text
paper
+
shadow
+
monitoring
+
reconciliation
+
security
+
governance
+
kill switch
```

------------------------------------------------------------------------

# 239. Critical Path

Le chemin critique est :

``` text
DATA
↓
ANALYSIS
↓
DECISION
↓
RISK
↓
BACKTEST
↓
PAPER
↓
SHADOW
↓
LIMITED LIVE
```

------------------------------------------------------------------------

# 240. Parallel Workstreams

Certains travaux peuvent avancer en parallèle :

``` text
documentation
testing
security
monitoring
database
```

mais ils doivent converger avant live.

------------------------------------------------------------------------

# 241. Governance Throughout

Le Governance Engine ne doit pas apparaître seulement à la fin.

Il doit accompagner :

``` text
architecture
experiments
risk changes
deployments
AI permissions
```

------------------------------------------------------------------------

# 242. Testing Throughout

Les tests ne constituent pas une phase finale.

Chaque moteur doit être construit avec ses tests.

------------------------------------------------------------------------

# 243. Security Throughout

Même principe pour la sécurité.

------------------------------------------------------------------------

# 244. Monitoring Throughout

Tout nouveau composant critique doit produire ses métriques et logs.

------------------------------------------------------------------------

# 245. Knowledge Throughout

Les décisions et résultats importants doivent être conservés dès les
premières phases.

------------------------------------------------------------------------

# 246. Definition of Project Success

QuantLab est réussi lorsque le système peut répondre de manière fiable :

``` text
What did we know?
What did we decide?
Why?
What risk did we accept?
What did we execute?
What actually happened?
What did we learn?
```

------------------------------------------------------------------------

# 247. Failure Mode to Avoid

Le pire résultat n'est pas :

``` text
a strategy loses money
```

Le pire résultat est :

``` text
the system loses money
and nobody can reliably explain why.
```

------------------------------------------------------------------------

# 248. Roadmap Governance

Chaque milestone doit produire :

``` text
deliverables
tests
evidence
known limitations
go/no-go decision
```

------------------------------------------------------------------------

# 249. Go / No-Go

La progression vers une phase plus risquée doit être une décision
explicite.

------------------------------------------------------------------------

# 250. Final Roadmap

``` text
FOUNDATION
↓
RELIABLE DATA
↓
DETERMINISTIC ANALYSIS
↓
EXPLAINABLE DECISIONS
↓
INDEPENDENT RISK
↓
REPRODUCIBLE RESEARCH
↓
PAPER EXECUTION
↓
SHADOW VALIDATION
↓
LIMITED LIVE
↓
PRODUCTION HARDENING
↓
KNOWLEDGE SYSTEM
↓
CONTROLLED AI
↓
ADVANCED AUTONOMY
```

------------------------------------------------------------------------

# 251. Règle fondatrice

> **QuantLab doit gagner le droit d'augmenter sa complexité, son capital
> et son autonomie.**

Chaque étape doit être justifiée par la précédente.

La séquence fondamentale reste :

``` text
CORRECTNESS
↓
REPRODUCIBILITY
↓
OBSERVABILITY
↓
RISK CONTROL
↓
REAL-WORLD VALIDATION
↓
CAPITAL
↓
AUTONOMY
```

L'objectif final n'est pas de construire le système le plus compliqué.

L'objectif est de construire un système qui puisse devenir plus
intelligent sans devenir plus dangereux à chaque amélioration.

------------------------------------------------------------------------

# 252. Statut

**Version : 1.0**

Ce document clôt la série principale :

-   `01-Vision-du-Projet.md`
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
-   `22-API-Specification.md`
-   `23-Database-Schema.md`
-   `24-Security.md`
-   `25-Roadmap.md`

Prochaine série recommandée :

``` text
ANNEXES
├── Glossaire
├── ADR
├── Conventions Git
├── Standards Markdown
├── Diagrammes d’architecture
└── Checklists opérationnelles
```
