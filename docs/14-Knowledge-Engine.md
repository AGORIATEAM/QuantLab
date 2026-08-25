# 14 — Knowledge Engine

**Projet : QuantLab**  
**Document : Knowledge Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Knowledge Engine est la couche chargée de transformer l'historique opérationnel de QuantLab en connaissance exploitable.

Les moteurs précédents produisent des données :

```text
marché
analyses
structures
scores
décisions
risques
ordres
fills
positions
résultats
incidents
```

Le Knowledge Engine doit relier ces éléments afin de répondre à une question plus importante :

> **Qu'est-ce que QuantLab a réellement appris de ce qui s'est passé ?**

Sa fonction n'est donc pas simplement de stocker l'historique.

Elle consiste à construire une mémoire analytique permettant :

- d'expliquer les résultats ;
- de comparer les stratégies ;
- de mesurer les performances réelles ;
- de comprendre les échecs ;
- d'identifier les conditions favorables ou défavorables ;
- de préparer les données pour la recherche et l'IA ;
- d'éviter que les mêmes expériences soient répétées sans raison.

---

# 2. Principe fondamental

QuantLab doit distinguer :

```text
DATA
↓
INFORMATION
↓
KNOWLEDGE
↓
DECISION IMPROVEMENT
```

Exemple :

```text
Data:
Trade #829 lost -0.5R
```

n'est pas encore de la connaissance.

Une connaissance serait plutôt :

```text
Bullish breakout setups
during low-liquidity range regimes
have negative expectancy
over 428 historical observations.
```

Le Knowledge Engine doit permettre ce passage.

---

# 3. Position dans l'architecture

```text
Data Engine
      ↓
Analysis Engines
      ↓
Scoring Engine
      ↓
Decision Engine
      ↓
Risk Engine
      ↓
Execution Engine
      ↓
Monitoring Engine
      ↓
┌──────────────────────────┐
│     KNOWLEDGE ENGINE     │
├──────────────────────────┤
│ Trade History            │
│ Feature Snapshots        │
│ Outcome Attribution      │
│ Performance Analytics    │
│ Pattern Analytics        │
│ Experiment Results       │
│ Knowledge Registry       │
└────────────┬─────────────┘
             ↓
AI & Learning Engine
             ↓
Research / Governance
```

---

# 4. Responsabilités

Le Knowledge Engine doit :

1. conserver l'historique analytique ;
2. relier les événements entre eux ;
3. reconstruire le cycle complet d'un trade ;
4. calculer les performances ;
5. calculer les métriques par stratégie ;
6. calculer les métriques par setup ;
7. calculer les métriques par régime ;
8. analyser les reason codes ;
9. analyser les décisions rejetées ;
10. analyser les coûts d'exécution ;
11. comparer expected vs realized ;
12. produire des datasets de recherche ;
13. enregistrer les expériences ;
14. conserver les versions utilisées ;
15. détecter les dérives statistiques ;
16. fournir des requêtes analytiques ;
17. alimenter l'AI & Learning Engine ;
18. conserver les conclusions validées ;
19. éviter les conclusions non reproductibles ;
20. maintenir une mémoire institutionnelle du projet.

---

# 5. Hors périmètre

Le Knowledge Engine ne doit pas :

- exécuter des trades ;
- modifier directement les stratégies live ;
- changer les limites de risque ;
- interpréter une corrélation comme une causalité ;
- considérer qu'un backtest positif constitue une preuve suffisante ;
- remplacer la validation statistique ;
- apprendre automatiquement à partir de quelques observations.

---

# 6. Sources de données

Le Knowledge Engine reçoit notamment :

```text
MarketData
MarketContext
StructureContext
VolumeProfileContext
SMCContext
ScoreContext
DecisionContext
RiskDecision
ExecutionOrder
Fill
Position
MonitoringEvent
Incident
Experiment
```

---

# 7. Trade Lineage

Chaque trade doit pouvoir être reconstruit de bout en bout.

```text
Market Snapshot
↓
Analysis
↓
Score
↓
Decision
↓
Risk Approval
↓
Execution
↓
Position
↓
Exit
↓
Outcome
```

---

# 8. Correlation IDs

Les identifiants doivent permettre de relier :

```text
setup_id
score_id
decision_id
intent_id
risk_decision_id
order_id
position_id
trade_id
experiment_id
```

---

# 9. Trade Record

Structure conceptuelle :

```python
TradeRecord:
    trade_id

    strategy_id
    strategy_version

    symbol
    direction

    setup_id

    decision_id
    risk_decision_id

    opened_at
    closed_at

    entry_price
    exit_price

    quantity

    realized_pnl
    realized_r

    fees
    slippage

    max_favorable_excursion
    max_adverse_excursion

    exit_reason

    feature_snapshot_id
```

---

# 10. Feature Snapshot

Au moment d'une décision importante, QuantLab doit pouvoir conserver un snapshot des caractéristiques utilisées.

Exemple :

```text
market_regime
volatility
trend
structure
BOS
CHoCH
POC
VAH
VAL
FVG
order_block
liquidity_sweep
long_score
short_score
confidence
```

---

# 11. Pourquoi les snapshots sont nécessaires

Si les features sont recalculées plusieurs mois plus tard avec une nouvelle version du moteur, elles peuvent différer.

Il faut donc distinguer :

```text
historical observed features
```

de :

```text
features recomputed with current code
```

---

# 12. Snapshot Versioning

Chaque snapshot doit conserver :

```text
data_version
analysis_version
structure_version
volume_profile_version
smc_version
scoring_version
```

---

# 13. Outcome

Structure conceptuelle :

```python
TradeOutcome:
    trade_id

    pnl_absolute
    pnl_percent
    pnl_r

    fees
    slippage_cost

    holding_time

    mfe
    mae

    exit_reason
```

---

# 14. R-Multiple

Une mesure importante :

```text
R =
realized_pnl
/
initial_risk
```

Exemple :

```text
initial risk = 500
profit = 1000
```

donne :

```text
+2R
```

---

# 15. Pourquoi utiliser R

Cela permet de comparer des trades de tailles différentes sans confondre performance et capital engagé.

---

# 16. Win Rate

```text
win_rate =
winning_trades
/
total_trades
```

Le win rate seul ne suffit pas.

---

# 17. Average Win

```text
average_win =
mean(R | R > 0)
```

---

# 18. Average Loss

```text
average_loss =
mean(abs(R) | R < 0)
```

---

# 19. Expectancy

Formule :

```text
expectancy =
P(win) × average_win
-
P(loss) × average_loss
```

---

# 20. Exemple

```text
win rate = 40%
average win = 2R
average loss = 1R
```

Alors :

```text
expectancy =
0.4 × 2
-
0.6 × 1
=
0.2R
```

---

# 21. Profit Factor

```text
profit_factor =
gross_profit
/
gross_loss
```

---

# 22. Payoff Ratio

```text
payoff_ratio =
average_win
/
average_loss
```

---

# 23. Sharpe Ratio

Peut être calculé pour certaines analyses, mais doit être utilisé avec prudence.

Les distributions de trading sont rarement aussi polies que les hypothèses statistiques aiment le supposer.

---

# 24. Sortino Ratio

Le Sortino peut être utile pour distinguer volatilité négative et volatilité totale.

---

# 25. Maximum Drawdown

Le Knowledge Engine doit calculer :

```text
maximum_drawdown
```

sur les equity curves.

---

# 26. Recovery Factor

Exemple :

```text
net_profit
/
maximum_drawdown
```

---

# 27. Trade Frequency

Mesurer :

```text
trades_per_day
trades_per_week
trades_per_month
```

---

# 28. Holding Time

Mesurer :

```text
median_holding_time
average_holding_time
```

par stratégie et setup.

---

# 29. MFE

Maximum Favorable Excursion :

```text
meilleur mouvement favorable
pendant le trade
```

---

# 30. MAE

Maximum Adverse Excursion :

```text
plus mauvais mouvement adverse
pendant le trade
```

---

# 31. Utilité MFE / MAE

Ils permettent d'étudier :

- qualité des stops ;
- qualité des targets ;
- sorties trop rapides ;
- positions qui passent trop longtemps en négatif.

---

# 32. Performance par stratégie

Calculer :

```text
expectancy
win rate
profit factor
drawdown
trade count
average R
```

par :

```text
strategy_id
strategy_version
```

---

# 33. Performance par symbole

Exemple :

```text
strategy A
BTC expectancy = +0.30R
ETH expectancy = +0.08R
SOL expectancy = -0.15R
```

---

# 34. Performance par timeframe

Comparer :

```text
5m
15m
1h
4h
```

sans mélanger les observations.

---

# 35. Performance par direction

Comparer :

```text
LONG
SHORT
```

---

# 36. Performance par régime

Exemples :

```text
TRENDING
RANGING
EXPANSION
COMPRESSION
HIGH_VOL
LOW_VOL
```

---

# 37. Performance par structure

Comparer :

```text
BOS setups
CHoCH setups
trend continuation
reversal
```

---

# 38. Performance SMC

Comparer :

```text
order block
FVG
liquidity sweep
premium/discount
```

et leurs combinaisons.

---

# 39. Performance Volume Profile

Comparer :

```text
above VAH
below VAL
POC reclaim
value area rotation
```

---

# 40. Performance par score

Créer des buckets :

```text
60–69
70–79
80–89
90–100
```

et mesurer l'expectancy réelle.

---

# 41. Score Calibration

Un score plus élevé devrait idéalement correspondre à une meilleure performance future.

Exemple :

```text
score 70:
expectancy +0.05R

score 80:
expectancy +0.20R

score 90:
expectancy +0.45R
```

Sinon le Scoring Engine doit être réévalué.

---

# 42. Confidence Calibration

Même analyse pour :

```text
confidence
```

Attention :

```text
confidence ≠ probability of win
```

sauf calibration explicite.

---

# 43. Reason Code Analytics

Analyser les performances associées aux reason codes.

Exemple :

```text
HTF_ALIGNMENT
+
LIQUIDITY_SWEEP
```

peut avoir une expectancy différente de :

```text
BOS_ONLY
```

---

# 44. Combination Analysis

Le moteur doit permettre d'étudier des combinaisons.

Mais le nombre de combinaisons augmente très vite.

Il faut donc contrôler :

```text
minimum sample size
multiple testing
overfitting
```

---

# 45. Minimum Sample Size

Une conclusion basée sur :

```text
4 trades
```

ne doit pas être présentée comme une connaissance robuste.

---

# 46. Statistical Confidence

Chaque résultat devrait idéalement être accompagné de :

```text
sample_size
confidence_interval
```

ou au minimum d'une indication de fiabilité.

---

# 47. Bootstrap

Le bootstrap peut être utilisé pour estimer l'incertitude sur certaines métriques.

---

# 48. Monte Carlo

Les séquences de trades peuvent être rééchantillonnées pour estimer :

```text
drawdown distribution
loss streak distribution
equity dispersion
```

---

# 49. Multiple Testing Risk

Si QuantLab teste des milliers de combinaisons, certaines sembleront excellentes uniquement par hasard.

Le système doit enregistrer le nombre d'hypothèses testées.

---

# 50. Overfitting Protection

Le Knowledge Engine doit favoriser :

```text
simple explanations
large samples
out-of-sample validation
walk-forward validation
```

---

# 51. In-Sample

Données utilisées pour développer l'hypothèse.

---

# 52. Validation Set

Données utilisées pour sélectionner ou ajuster raisonnablement les paramètres.

---

# 53. Out-of-Sample

Données jamais utilisées pendant le développement.

---

# 54. Walk-Forward

Processus :

```text
train
↓
validate future period
↓
move window
↓
repeat
```

---

# 55. Regime Stability

Une stratégie peut être rentable globalement mais dépendre d'un seul régime.

Le Knowledge Engine doit mesurer cette dépendance.

---

# 56. Temporal Stability

Comparer les résultats par période :

```text
month
quarter
year
```

---

# 57. Asset Stability

Comparer la stratégie sur plusieurs actifs.

---

# 58. Parameter Stability

Un bon paramètre ne devrait pas fonctionner uniquement à :

```text
threshold = 78
```

et s'effondrer à :

```text
77
79
```

Une telle sensibilité est suspecte.

---

# 59. Sensitivity Analysis

Tester les paramètres autour de leur valeur choisie.

---

# 60. Expected vs Realized

Le moteur doit comparer :

```text
backtest expectation
paper result
shadow result
live result
```

---

# 61. Backtest-to-Live Gap

Mesurer :

```text
live expectancy
-
backtest expectancy
```

et expliquer autant que possible la différence.

---

# 62. Execution Attribution

Décomposer :

```text
strategy theoretical PnL
↓
fees
↓
spread
↓
slippage
↓
actual PnL
```

---

# 63. Slippage Attribution

Analyser par :

```text
venue
symbol
strategy
order type
volatility
size
time of day
```

---

# 64. Risk Attribution

Comparer :

```text
requested risk
approved risk
realized loss
```

---

# 65. Decision Attribution

Comparer :

```text
candidate setups
accepted setups
rejected setups
```

---

# 66. Counterfactual Dataset

QuantLab doit pouvoir enregistrer certains setups rejetés.

Exemple :

```text
score = 74
threshold = 75
NO_TRADE
```

puis observer l'évolution future.

---

# 67. Counterfactual Warning

Un setup rejeté n'est pas un trade exécuté.

Son résultat simulé doit intégrer :

```text
entry assumptions
fees
slippage
liquidity
```

---

# 68. Missed Opportunity Analysis

Le moteur peut mesurer :

```text
rejected setup
that later moved favorably
```

mais cette métrique doit être équilibrée par :

```text
rejected setup
that would have lost
```

Sinon on obtient simplement une machine à regret rétrospectif.

---

# 69. Rejection Quality

Mesurer :

```text
expectancy of rejected setups
```

par reason code.

---

# 70. Risk Rejection Analytics

Exemple :

```text
trades rejected because DAILY_LOSS_LIMIT
```

peuvent être analysés pour comprendre le coût d'opportunité de la protection.

Cela ne signifie pas qu'il faut supprimer la protection.

---

# 71. Exit Analysis

Analyser :

```text
exit reason
realized R
MFE after exit
```

---

# 72. Early Exit Analysis

Si :

```text
position exited at +0.5R
```

puis atteint :

```text
+3R
```

cela peut indiquer une sortie trop agressive.

Mais l'analyse doit être faite sur un ensemble de trades, pas sur le trade qui nous agace le plus.

---

# 73. Stop Analysis

Comparer :

```text
initial stop
MAE
eventual outcome
```

---

# 74. Stop Efficiency

Mesurer combien de trades :

```text
touch stop
then reverse strongly
```

Cela peut suggérer un problème de stop, mais pas automatiquement.

---

# 75. Target Analysis

Comparer :

```text
target distance
MFE
realized exit
```

---

# 76. Trade Duration Analysis

Certaines stratégies peuvent perdre leur edge après un certain temps.

Mesurer :

```text
expectancy by holding duration
```

---

# 77. Time-of-Day Analysis

Comparer :

```text
Asia
London
New York
```

ou des plages UTC précises.

---

# 78. Day-of-Week Analysis

Mesurer sans supposer que l'effet observé est structurel.

---

# 79. Event Context

Une version future pourra relier :

```text
macro events
funding
economic calendar
```

aux performances.

---

# 80. Data Quality Attribution

Un trade exécuté pendant une période de données dégradées doit être identifiable.

---

# 81. Incident Attribution

Relier :

```text
incident_id
```

aux trades ou décisions potentiellement affectés.

---

# 82. Strategy Reliability

Une stratégie peut avoir une bonne performance mais une mauvaise fiabilité opérationnelle.

Exemple :

```text
frequent stale signals
execution rejects
high slippage
```

Le Knowledge Engine doit mesurer les deux dimensions.

---

# 83. Knowledge Object

Structure conceptuelle :

```python
KnowledgeObject:
    knowledge_id

    title
    statement

    scope
    evidence

    sample_size
    confidence

    source_experiments

    status

    created_at
    reviewed_at

    version
```

---

# 84. Knowledge Status

Valeurs :

```text
HYPOTHESIS
OBSERVED
VALIDATED
REJECTED
DEPRECATED
```

---

# 85. HYPOTHESIS

Une idée à tester.

Exemple :

```text
Liquidity sweeps improve reversal expectancy.
```

---

# 86. OBSERVED

Un effet a été observé dans les données, mais n'est pas encore suffisamment validé.

---

# 87. VALIDATED

L'effet a survécu à un protocole de validation défini.

---

# 88. REJECTED

Les tests n'ont pas confirmé l'hypothèse.

---

# 89. DEPRECATED

Une connaissance précédemment utilisée n'est plus considérée comme applicable.

---

# 90. Evidence

Chaque KnowledgeObject doit référencer :

```text
experiments
datasets
queries
versions
metrics
```

---

# 91. No Unsupported Knowledge

Une phrase comme :

```text
Order blocks work better in London session
```

ne doit pas devenir une règle du système simplement parce qu'elle semble plausible.

Elle doit avoir des preuves.

---

# 92. Knowledge Registry

Le système doit disposer d'un registre central des conclusions.

Cela évite :

```text
same idea tested repeatedly
```

sans savoir que l'équipe l'avait déjà rejetée six mois auparavant.

---

# 93. Experiment Integration

Chaque expérience du :

```text
Experiment Registry
```

doit pouvoir produire :

```text
KnowledgeObject
```

---

# 94. Experiment Result

Structure :

```text
experiment_id
hypothesis
dataset
method
baseline
candidate
metrics
result
conclusion
```

---

# 95. Reproducibility

Une expérience doit enregistrer :

```text
code version
data version
configuration
random seed
environment
```

---

# 96. Dataset Registry

Les datasets de recherche doivent être identifiés.

Exemple :

```text
dataset_id
dataset_version
start_date
end_date
symbols
timeframes
feature_versions
```

---

# 97. Immutable Dataset References

Une expérience historique doit toujours pointer vers la version exacte du dataset utilisée.

---

# 98. Dataset Lineage

Le système doit savoir :

```text
raw data
↓
cleaned data
↓
features
↓
research dataset
```

---

# 99. Data Leakage Prevention

Les datasets doivent éviter :

```text
future information
```

dans les features.

---

# 100. Label Construction

Pour les recherches supervisées futures, les labels doivent être calculés séparément des features.

---

# 101. Point-in-Time Correctness

À timestamp `T`, seules les informations disponibles à `T` peuvent être utilisées comme feature.

---

# 102. Feature Registry

Une version future peut maintenir :

```text
feature_id
definition
version
owner
source
availability_delay
```

---

# 103. Feature Importance

Le Knowledge Engine peut analyser l'importance statistique des features.

Mais :

```text
feature importance
≠
causal importance
```

---

# 104. Correlation Analysis

Mesurer les relations entre :

```text
features
scores
outcomes
```

sans surinterpréter.

---

# 105. Conditional Analysis

Exemple :

```text
FVG expectancy
conditioned on TRENDING regime
```

peut être plus informative que l'effet global.

---

# 106. Interaction Effects

Certaines features peuvent être inutiles seules mais utiles ensemble.

Exemple :

```text
liquidity sweep
+
HTF alignment
```

---

# 107. Dimensionality Risk

Plus le nombre de dimensions augmente, plus le risque d'overfitting augmente.

---

# 108. Baseline First

Toute nouvelle hypothèse doit être comparée à une baseline simple.

---

# 109. Benchmark Strategy

Exemples :

```text
buy and hold
simple breakout
simple moving average trend
randomized entry control
```

selon l'expérience.

---

# 110. Random Baseline

Une baseline randomisée peut aider à vérifier qu'une logique complexe apporte réellement de l'information.

---

# 111. Ablation Study

Retirer une feature ou une règle et mesurer l'effet.

Exemple :

```text
full strategy
vs
strategy without Volume Profile
```

---

# 112. Feature Value

Si retirer une feature ne change rien de manière robuste, elle peut ajouter de la complexité sans valeur.

---

# 113. Strategy Complexity

Le Knowledge Engine peut suivre :

```text
number_of_rules
number_of_features
number_of_parameters
```

et comparer cette complexité à la performance.

---

# 114. Simplicity Bias

À performance comparable, QuantLab doit préférer la stratégie la plus simple.

---

# 115. Model Drift

Pour les futurs modèles ML :

```text
feature drift
prediction drift
performance drift
```

doivent être suivis.

---

# 116. Strategy Drift

Même sans ML, une stratégie peut perdre son edge.

Mesurer :

```text
rolling expectancy
rolling win rate
rolling drawdown
```

---

# 117. Rolling Windows

Exemples :

```text
last 50 trades
last 100 trades
last 30 days
```

---

# 118. Small Sample Warning

Les fenêtres trop courtes doivent afficher un avertissement.

---

# 119. Change Detection

Une version future peut utiliser :

```text
CUSUM
change-point detection
```

ou d'autres méthodes.

---

# 120. Performance Degradation

Une dégradation ne doit pas automatiquement désactiver une stratégie sauf règle de gouvernance/risk définie.

---

# 121. Research Query Layer

Le Knowledge Engine doit permettre des requêtes telles que :

```text
expectancy by strategy
```

ou :

```text
performance of bullish FVG setups
when 4H regime = TRENDING
and 15m score > 80
```

---

# 122. Query Reproducibility

Une analyse importante doit pouvoir être sauvegardée avec :

```text
query
dataset version
filters
result
```

---

# 123. Analytics API

Endpoints conceptuels :

```text
GET /knowledge/trades
GET /knowledge/performance
GET /knowledge/setups
GET /knowledge/experiments
GET /knowledge/objects
```

---

# 124. Research Notebook Integration

Les chercheurs ou agents IA pourront consommer des datasets depuis :

```text
Python notebooks
research jobs
AI agents
```

sans accéder directement aux systèmes live.

---

# 125. Production Isolation

Le Knowledge Engine doit être majoritairement :

```text
read-oriented
```

par rapport au système de trading live.

Une requête analytique lourde ne doit pas ralentir l'exécution.

---

# 126. Analytical Database

À terme, il peut être utile de séparer :

```text
operational database
```

et :

```text
analytical database
```

---

# 127. ETL / ELT

Pipeline :

```text
Operational Data
↓
Validation
↓
Transformation
↓
Analytical Store
```

---

# 128. Batch Processing

De nombreuses analyses peuvent être calculées :

```text
hourly
daily
after trade close
```

plutôt qu'en temps réel.

---

# 129. Real-Time Knowledge

Certaines métriques peuvent toutefois être actualisées en continu :

```text
rolling expectancy
strategy health
execution quality
```

---

# 130. Caching

Les analyses coûteuses fréquemment consultées peuvent être mises en cache.

---

# 131. Materialized Views

Exemples :

```text
strategy_daily_performance
setup_performance
score_bucket_performance
execution_quality
```

---

# 132. Knowledge Dashboard

Afficher :

```text
Strategy Performance
Setup Performance
Regime Performance
Score Calibration
Execution Cost
Risk Attribution
Recent Experiments
Validated Knowledge
```

---

# 133. Strategy Report

Rapport standard :

```text
trade count
net R
expectancy
win rate
profit factor
max drawdown
average holding time
fees
slippage
```

---

# 134. Setup Report

Exemple :

```text
Setup:
Bullish liquidity sweep + BOS

Sample:
482

Expectancy:
+0.31R

Win rate:
43%

Average win:
2.2R

Average loss:
1.0R
```

---

# 135. Confidence Display

Les rapports doivent afficher :

```text
sample size
uncertainty
```

pour éviter la fausse précision.

---

# 136. No Cherry Picking

Les dashboards ne doivent pas permettre de présenter uniquement les meilleures périodes sans indiquer le filtre appliqué.

---

# 137. Filter Transparency

Chaque résultat doit afficher :

```text
date range
symbols
strategy version
filters
sample size
```

---

# 138. Survivorship Bias

Si certains actifs disparaissent du dataset, l'analyse historique doit éviter de les supprimer rétrospectivement.

---

# 139. Look-Ahead Bias

Les données utilisées doivent respecter leur disponibilité réelle.

---

# 140. Selection Bias

Une stratégie développée sur les actifs où elle fonctionnait déjà peut sembler artificiellement robuste.

---

# 141. Confirmation Bias

Le Knowledge Engine doit conserver les résultats négatifs.

Un test rejeté est une connaissance utile.

---

# 142. Negative Results

Exemple :

```text
Hypothesis:
POC reclaim improves trend continuation.

Result:
No robust improvement.

Status:
REJECTED
```

Ce résultat doit rester consultable.

---

# 143. Experiment Graveyard

Un registre des idées rejetées évite de les ressusciter tous les trois mois sous un nouveau nom, activité à laquelle les équipes humaines excellent avec une constance impressionnante.

---

# 144. AI Read Access

L'AI & Learning Engine doit pouvoir rechercher :

```text
validated knowledge
rejected hypotheses
experiment results
performance reports
```

---

# 145. AI Write Boundary

L'IA peut proposer :

```text
new hypothesis
new experiment
draft knowledge object
```

mais ne doit pas déclarer seule :

```text
VALIDATED
```

une connaissance critique.

---

# 146. Human / Governance Validation

La promotion :

```text
OBSERVED
→
VALIDATED
```

doit respecter le Governance Engine.

---

# 147. Knowledge Confidence

Une note peut combiner :

```text
sample size
out-of-sample evidence
cross-asset stability
temporal stability
replication count
```

---

# 148. Confidence Levels

Exemple :

```text
LOW
MEDIUM
HIGH
```

---

# 149. No Absolute Truth

Même une connaissance `VALIDATED` reste valide dans un scope.

Exemple :

```text
BTC
15m
2022–2026
specific strategy version
```

Elle ne doit pas être généralisée sans preuve.

---

# 150. Knowledge Scope

Chaque objet doit préciser :

```text
assets
timeframes
market regimes
date range
strategy versions
```

---

# 151. Knowledge Expiration

Certaines connaissances peuvent nécessiter une revalidation périodique.

---

# 152. Revalidation

Exemple :

```text
validated knowledge
↓
new 6 months of data
↓
revalidation experiment
```

---

# 153. Deprecation

Si l'effet disparaît :

```text
VALIDATED
→
DEPRECATED
```

sans supprimer l'historique.

---

# 154. Knowledge Versioning

Chaque modification doit produire une nouvelle version.

---

# 155. Audit

Le système doit conserver :

```text
who changed status
why
evidence
timestamp
```

---

# 156. Security

Les données analytiques peuvent contenir :

```text
strategy IP
positions
performance
capital information
```

L'accès doit être contrôlé.

---

# 157. Data Access Levels

Exemples :

```text
RESEARCH_READ
KNOWLEDGE_READ
EXPERIMENT_WRITE
KNOWLEDGE_REVIEW
KNOWLEDGE_APPROVE
```

---

# 158. Data Anonymization

Si des datasets sont exportés vers des systèmes externes, retirer les informations non nécessaires.

---

# 159. AI Data Minimization

Un modèle externe ne doit recevoir que les données nécessaires à la tâche.

---

# 160. Testing

Le Knowledge Engine doit être testé pour :

- calculs de performance ;
- lineage ;
- dataset versioning ;
- point-in-time correctness ;
- filters ;
- reproducibility ;
- knowledge status transitions.

---

# 161. Metric Tests

Utiliser de petits datasets connus pour vérifier :

```text
win rate
expectancy
profit factor
drawdown
MFE
MAE
```

---

# 162. Leakage Tests

Créer des tests garantissant qu'une feature future ne peut pas entrer dans un snapshot passé.

---

# 163. Reproducibility Test

La même :

```text
query
dataset version
code version
```

doit produire le même résultat.

---

# 164. Lineage Test

À partir d'un :

```text
trade_id
```

le système doit retrouver :

```text
decision
risk
orders
fills
features
versions
```

---

# 165. Dataset Integrity

Vérifier :

```text
duplicates
missing records
timestamp consistency
version consistency
```

---

# 166. Performance

Les requêtes analytiques lourdes doivent être isolées des systèmes transactionnels.

---

# 167. Monitoring

Métriques :

```text
knowledge_queries_total
query_latency
dataset_build_time
dataset_failures
experiment_count
knowledge_objects_count
```

---

# 168. Knowledge Metrics

Suivre :

```text
hypotheses_total
observed_total
validated_total
rejected_total
deprecated_total
```

---

# 169. Experiment Velocity

Mesurer :

```text
experiments_per_month
median_time_to_conclusion
replication_rate
```

sans transformer la quantité d'expériences en objectif aveugle.

---

# 170. Research Quality

Des indicateurs plus utiles sont :

```text
reproducibility
out-of-sample validation rate
percentage of negative results preserved
```

---

# 171. Priorités V1

Implémenter :

- TradeRecord ;
- FeatureSnapshot ;
- TradeOutcome ;
- lineage complet ;
- R-multiple ;
- expectancy ;
- win rate ;
- profit factor ;
- drawdown ;
- MFE / MAE ;
- performance par stratégie ;
- performance par symbole ;
- performance par régime ;
- score calibration ;
- reason-code analytics ;
- experiment linkage ;
- Knowledge Registry ;
- dataset versioning.

---

# 172. Priorités V2

Ajouter :

- counterfactual datasets ;
- bootstrap ;
- Monte Carlo ;
- sensitivity analysis ;
- ablation studies ;
- rolling performance ;
- analytical database dédiée.

---

# 173. Priorités V3

Ajouter :

- feature registry ;
- drift detection ;
- change-point detection ;
- advanced statistical validation ;
- automated research reports.

---

# 174. Priorités V4

Ajouter :

- semantic knowledge search ;
- AI research agents ;
- automated hypothesis generation ;
- experiment proposal system ;
- knowledge graph ;
- cross-strategy meta-analysis.

---

# 175. Critères d'acceptation V1

La V1 est valide lorsque :

- chaque trade peut être reconstruit de bout en bout ;
- les features historiques sont versionnées ;
- les performances sont calculables en R ;
- l'expectancy est disponible ;
- les frais et le slippage sont attribués ;
- les résultats peuvent être segmentés par stratégie, symbole et régime ;
- les scores peuvent être calibrés contre les outcomes ;
- les reason codes peuvent être analysés ;
- les expériences sont reproductibles ;
- les résultats négatifs sont conservés ;
- les connaissances possèdent un statut ;
- aucune connaissance n'est considérée comme globale sans scope ;
- les datasets respectent le point-in-time correctness.

---

# 176. Risques principaux

## Overfitting

Trouver une règle excellente sur le passé mais inutile dans le futur.

## Data Leakage

Utiliser involontairement une information future.

## Confirmation Bias

Ne conserver que les résultats qui soutiennent l'hypothèse préférée.

## Multiple Testing

Trouver des effets aléatoires en testant trop de combinaisons.

## Small Samples

Prendre des décisions sur quelques observations.

## Backtest Illusion

Confondre performance simulée et performance exécutable.

## Knowledge Drift

Continuer d'utiliser une conclusion qui n'est plus valide.

---

# 177. Principe de recherche

QuantLab doit traiter chaque idée comme :

```text
hypothesis
```

et non comme :

```text
truth
```

jusqu'à ce que les preuves soient suffisantes.

---

# 178. Architecture cible

```text
Operational Events
       ↓
Trade Lineage Builder
       ↓
Feature Snapshots
       ↓
Outcome Attribution
       ↓
Analytical Store
       ↓
Performance Engine
       ↓
Experiment Registry
       ↓
Knowledge Registry
       ↓
Validated Knowledge
       ↓
AI & Learning Engine
```

---

# 179. Résultat attendu

Le Knowledge Engine doit permettre une requête comme :

```text
Show performance of:
bullish liquidity sweep
+
bullish BOS
+
long score >= 80
+
4H TRENDING regime
```

et produire :

```text
Sample size:
642

Expectancy:
+0.34R

Win rate:
44.1%

Average win:
2.15R

Average loss:
1.02R

Profit factor:
1.47

Max drawdown:
-8.2R

Backtest:
+0.41R expectancy

Paper:
+0.36R

Live:
+0.29R

Execution drag:
-0.07R

Confidence:
MEDIUM

Status:
OBSERVED
```

Le système doit ensuite pouvoir retrouver les expériences et versions qui justifient ces chiffres.

---

# 180. Règle fondatrice

> **QuantLab ne doit pas seulement se souvenir de ce qu'il a fait. Il doit se souvenir de ce qu'il a appris, de la qualité des preuves, et des raisons pour lesquelles il croit encore que cette connaissance est valable.**

Le Knowledge Engine transforme l'historique de QuantLab en mémoire structurée.

Cette mémoire devient ensuite la matière première de l'AI & Learning Engine.

---

# 181. Statut

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
- `13-Monitoring-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `16-Governance-Engine.md`
- `17-AI-Development-Protocol.md`
- `18-Testing-Strategy.md`
- `20-Engineering-Principles.md`
- `21-Experiment-Registry.md`
- `22-API-Specification.md`
- `23-Database-Schema.md`
- `24-Security.md`
- `25-Roadmap.md`

**Prochain document : `15-AI-and-Learning-Engine.md`**
