# 21 --- Experiment Registry

**Projet : QuantLab**\
**Document : Experiment Registry**\
**Version : 1.0**\
**Statut : Standard de recherche quantitative et de traçabilité
expérimentale**

------------------------------------------------------------------------

# 1. Objectif

L'Experiment Registry est le système de référence utilisé par QuantLab
pour enregistrer, reproduire, comparer, valider et gouverner toutes les
expériences quantitatives.

Il doit empêcher un problème classique de recherche :

``` text
tester
→ modifier
→ retester
→ obtenir un meilleur résultat
→ oublier exactement ce qui a changé
```

Toute expérience significative doit pouvoir répondre à :

``` text
WHY was it run?
WHAT was tested?
WHICH data was used?
WHICH code was used?
WHICH configuration was used?
WHAT happened?
IS the result reproducible?
WAS it approved?
WHAT decision followed?
```

La règle centrale est :

> **Un résultat qui ne peut pas être reproduit et relié à ses données,
> son code et sa configuration n'est pas une preuve exploitable par
> QuantLab.**

------------------------------------------------------------------------

# 2. Périmètre

Le registre couvre notamment :

-   stratégies ;
-   signaux ;
-   indicateurs ;
-   Market Structure ;
-   Volume Profile ;
-   Smart Money Concepts ;
-   scoring ;
-   Decision Engine ;
-   Risk Engine ;
-   règles d'exécution ;
-   paramètres ;
-   features ;
-   modèles ML ;
-   prompts et workflows IA ;
-   univers d'actifs ;
-   coûts d'exécution ;
-   filtres de marché ;
-   analyses de robustesse ;
-   simulations ;
-   comparaisons champion/challenger.

------------------------------------------------------------------------

# 3. Principe scientifique

Le workflow cible est :

``` text
OBSERVATION
↓
HYPOTHESIS
↓
EXPERIMENT DESIGN
↓
PREDEFINED METRICS
↓
EXECUTION
↓
RESULT
↓
ROBUSTNESS TESTS
↓
INTERPRETATION
↓
DECISION
↓
PROMOTION / REJECTION / ITERATION
```

------------------------------------------------------------------------

# 4. Hypothesis First

Toute expérience importante doit commencer par une hypothèse explicite.

Exemple :

``` text
Adding a liquidity-sweep confirmation to the existing setup
will improve out-of-sample risk-adjusted performance
without materially reducing trade frequency.
```

------------------------------------------------------------------------

# 5. Hypothèse falsifiable

Une bonne hypothèse doit pouvoir être invalidée.

Éviter :

``` text
"This concept seems useful."
```

Préférer :

``` text
"The filter improves OOS expectancy after fees by at least X
without increasing maximum drawdown above Y."
```

Les valeurs exactes doivent être définies avant analyse lorsque
pertinent.

------------------------------------------------------------------------

# 6. Experiment ID

Chaque expérience reçoit un identifiant unique.

Format recommandé :

``` text
EXP-YYYYMMDD-NNN
```

Exemple :

``` text
EXP-20260824-001
```

------------------------------------------------------------------------

# 7. Experiment Record

Structure conceptuelle :

``` yaml
experiment_id:
title:
status:
owner:
created_at:
hypothesis:
experiment_type:
strategy_version:
code_commit:
dataset_version:
config_version:
feature_version:
model_version:
prompt_version:
parent_experiment_id:
baseline_experiment_id:
metrics:
acceptance_criteria:
results:
decision:
artifacts:
notes:
```

------------------------------------------------------------------------

# 8. Statuts

``` text
DRAFT
READY
RUNNING
COMPLETED
INVALID
REJECTED
ACCEPTED
PROMOTED
ARCHIVED
```

------------------------------------------------------------------------

# 9. DRAFT

Hypothèse en préparation.

------------------------------------------------------------------------

# 10. READY

Design suffisamment défini pour exécution.

------------------------------------------------------------------------

# 11. RUNNING

Expérience en cours.

------------------------------------------------------------------------

# 12. COMPLETED

Exécution terminée, résultat disponible.

------------------------------------------------------------------------

# 13. INVALID

Résultat inutilisable à cause d'un problème méthodologique ou technique.

Exemples :

``` text
corrupted dataset
look-ahead bias
incorrect fee model
execution bug
```

------------------------------------------------------------------------

# 14. REJECTED

Expérience valide mais hypothèse non soutenue.

Un résultat négatif reste utile.

------------------------------------------------------------------------

# 15. ACCEPTED

Les critères expérimentaux définis ont été satisfaits.

------------------------------------------------------------------------

# 16. PROMOTED

Le résultat a été accepté dans un workflow supérieur :

``` text
paper
shadow
limited live
production candidate
```

------------------------------------------------------------------------

# 17. ARCHIVED

Expérience conservée pour historique mais inactive.

------------------------------------------------------------------------

# 18. Experiment Types

Types recommandés :

``` text
SIGNAL
FEATURE
PARAMETER
STRATEGY
RISK
EXECUTION
MODEL
AI
DATA
INFRASTRUCTURE
ROBUSTNESS
ABLATION
```

------------------------------------------------------------------------

# 19. Parent Experiment

Une expérience dérivée doit référencer son parent.

Cela permet de reconstruire l'arbre de recherche.

------------------------------------------------------------------------

# 20. Baseline

Toute amélioration doit être comparée à une baseline explicite.

------------------------------------------------------------------------

# 21. Baseline Types

Exemples :

``` text
current production strategy
previous experiment
simple rule
buy-and-hold benchmark
random baseline
no-filter version
```

selon le contexte.

------------------------------------------------------------------------

# 22. No Baseline, No Improvement Claim

Sans comparaison appropriée, le mot « amélioration » n'a pas de sens
quantitatif.

------------------------------------------------------------------------

# 23. Code Version

Toute expérience doit enregistrer le commit Git exact :

``` text
commit_sha
```

------------------------------------------------------------------------

# 24. Dirty Working Tree

Une expérience officielle ne devrait pas être exécutée depuis un état
Git non enregistré.

Si cela arrive :

``` text
dirty_state = true
```

doit être explicitement marqué.

------------------------------------------------------------------------

# 25. Strategy Version

Toute stratégie testée doit avoir une version identifiable.

------------------------------------------------------------------------

# 26. Configuration Version

Les paramètres doivent être enregistrés intégralement ou via un artefact
versionné.

------------------------------------------------------------------------

# 27. Dataset Version

Toute expérience doit identifier précisément son dataset.

------------------------------------------------------------------------

# 28. Dataset Metadata

Inclure :

``` text
source
symbols
start
end
frequency
timezone
adjustments
quality status
hash/version
```

------------------------------------------------------------------------

# 29. Data Snapshot

Lorsque nécessaire, créer un snapshot immutable des données utilisées.

------------------------------------------------------------------------

# 30. Data Lineage

Le registre doit permettre de remonter :

``` text
experiment
→ dataset
→ raw source
```

------------------------------------------------------------------------

# 31. Feature Version

Pour les expériences ML ou quantitatives complexes :

``` text
feature_set_version
```

doit être enregistré.

------------------------------------------------------------------------

# 32. Model Version

Pour les expériences ML :

``` text
model_type
model_version
hyperparameters
training_seed
```

------------------------------------------------------------------------

# 33. Prompt Version

Pour les expériences IA :

``` text
prompt_version
model_provider
model_name
temperature/config
tool configuration
```

------------------------------------------------------------------------

# 34. Environment

Enregistrer :

``` text
local
research
backtest
paper
shadow
```

------------------------------------------------------------------------

# 35. Runtime Environment

Lorsque nécessaire :

``` text
Python version
dependency lock hash
container image
hardware
```

------------------------------------------------------------------------

# 36. Random Seed

Toute expérience stochastique doit enregistrer ses seeds.

------------------------------------------------------------------------

# 37. Deterministic Replay

Lorsque possible :

``` text
same experiment spec
→ same result
```

------------------------------------------------------------------------

# 38. Experiment Specification

Avant exécution, enregistrer :

``` text
hypothesis
baseline
variables
metrics
acceptance criteria
dataset split
```

------------------------------------------------------------------------

# 39. Independent Variable

Définir ce qui change réellement.

------------------------------------------------------------------------

# 40. Controlled Variables

Maintenir le reste constant autant que possible.

------------------------------------------------------------------------

# 41. One Major Question Per Experiment

Éviter de modifier simultanément :

``` text
entry
stop
risk
session filter
scoring
```

puis d'attribuer le résultat à un seul changement.

------------------------------------------------------------------------

# 42. Factorial Experiments

Les interactions multiples peuvent être testées explicitement avec une
méthodologie adaptée.

------------------------------------------------------------------------

# 43. Acceptance Criteria

Les critères doivent être définis avant observation des résultats
lorsque possible.

------------------------------------------------------------------------

# 44. Primary Metric

Chaque expérience doit avoir une métrique principale.

------------------------------------------------------------------------

# 45. Secondary Metrics

Les métriques secondaires apportent le contexte.

------------------------------------------------------------------------

# 46. Guardrail Metrics

Certaines métriques empêchent une « amélioration » qui détruit une autre
dimension.

Exemple :

``` text
Primary:
Sharpe improvement

Guardrail:
Max drawdown must not exceed limit
```

------------------------------------------------------------------------

# 47. Trading Metrics

Selon la stratégie :

``` text
net return
CAGR
expectancy
profit factor
Sharpe
Sortino
Calmar
max drawdown
volatility
win rate
average win
average loss
payoff ratio
trade count
exposure
turnover
```

------------------------------------------------------------------------

# 48. Risk Metrics

``` text
max drawdown
VaR / ES where appropriate
portfolio heat
tail loss
worst trade
loss streak
```

------------------------------------------------------------------------

# 49. Execution Metrics

``` text
slippage
fees
fill ratio
rejection rate
latency
market impact estimate
```

------------------------------------------------------------------------

# 50. Stability Metrics

``` text
performance by year
performance by regime
performance by asset
parameter sensitivity
```

------------------------------------------------------------------------

# 51. ML Metrics

Selon le problème :

``` text
precision
recall
F1
AUC
log loss
Brier score
calibration
```

Une bonne métrique ML ne garantit pas une bonne stratégie de trading.

------------------------------------------------------------------------

# 52. Economic Metrics

Toujours vérifier l'impact économique réel après coûts.

------------------------------------------------------------------------

# 53. Gross vs Net

Enregistrer séparément :

``` text
gross performance
net performance
```

------------------------------------------------------------------------

# 54. Fees

Le modèle de frais doit être versionné.

------------------------------------------------------------------------

# 55. Slippage

Le modèle de slippage doit être explicite.

------------------------------------------------------------------------

# 56. Multiple Slippage Scenarios

Tester lorsque pertinent :

``` text
optimistic
base
adverse
stress
```

------------------------------------------------------------------------

# 57. Liquidity Assumptions

Documenter les hypothèses de liquidité.

------------------------------------------------------------------------

# 58. Capacity

Pour les stratégies sensibles à la taille, tester plusieurs niveaux de
capital ou notionnel.

------------------------------------------------------------------------

# 59. Market Impact

À mesure que QuantLab augmente en taille, intégrer des hypothèses de
market impact.

------------------------------------------------------------------------

# 60. Data Splits

Structure recommandée :

``` text
TRAIN
VALIDATION
TEST
```

ou pour stratégie non ML :

``` text
DEVELOPMENT
OUT_OF_SAMPLE
```

------------------------------------------------------------------------

# 61. Holdout

Une partie des données doit rester réellement hors optimisation.

------------------------------------------------------------------------

# 62. Holdout Discipline

Ne pas consulter répétitivement le holdout puis continuer à optimiser.

Sinon il cesse progressivement d'être hors échantillon, phénomène
mystérieusement redécouvert par chaque génération de quants.

------------------------------------------------------------------------

# 63. Walk-Forward

Utiliser lorsque pertinent :

``` text
train window
→ validation future
→ roll forward
```

------------------------------------------------------------------------

# 64. Anchored Walk-Forward

Option :

``` text
growing training window
```

------------------------------------------------------------------------

# 65. Rolling Walk-Forward

Option :

``` text
fixed training window
```

------------------------------------------------------------------------

# 66. Time-Series Split

Les splits doivent respecter la causalité temporelle.

------------------------------------------------------------------------

# 67. No Random Leakage

Un split aléatoire classique peut être invalide pour certaines séries
temporelles.

------------------------------------------------------------------------

# 68. Purging / Embargo

Pour certains labels financiers chevauchants, utiliser des méthodes de
séparation adaptées lorsque nécessaire.

------------------------------------------------------------------------

# 69. Look-Ahead Detection

Toute expérience doit vérifier explicitement l'absence de données
futures.

------------------------------------------------------------------------

# 70. Survivorship Bias

Documenter si l'univers historique peut contenir un biais de survivants.

------------------------------------------------------------------------

# 71. Selection Bias

Documenter comment les actifs ont été sélectionnés.

------------------------------------------------------------------------

# 72. Regime Coverage

Le dataset doit idéalement contenir plusieurs régimes.

------------------------------------------------------------------------

# 73. Regime Segmentation

Analyser séparément :

``` text
trend
range
high volatility
low volatility
bull
bear
```

selon la taxonomie QuantLab.

------------------------------------------------------------------------

# 74. Session Segmentation

Lorsque pertinent :

``` text
Asia
London
New York
```

ou autres sessions.

------------------------------------------------------------------------

# 75. Asset Segmentation

Analyser par :

``` text
symbol
asset class
liquidity bucket
```

------------------------------------------------------------------------

# 76. Time Segmentation

Analyser :

``` text
year
quarter
month
```

selon l'horizon.

------------------------------------------------------------------------

# 77. Sample Size

Toujours enregistrer :

``` text
number of observations
number of trades
```

------------------------------------------------------------------------

# 78. Small Sample Warning

Un résultat basé sur peu de trades doit être marqué comme incertain.

------------------------------------------------------------------------

# 79. Confidence Intervals

Lorsque pertinent, calculer des intervalles d'incertitude.

------------------------------------------------------------------------

# 80. Bootstrap

Peut être utilisé pour estimer l'incertitude des métriques.

------------------------------------------------------------------------

# 81. Monte Carlo

Peut être utilisé pour étudier :

``` text
trade ordering
drawdown distribution
path dependency
```

------------------------------------------------------------------------

# 82. Parameter Search

Toute optimisation doit enregistrer :

``` text
search space
method
number of trials
objective
```

------------------------------------------------------------------------

# 83. Search Methods

Exemples :

``` text
grid
random
Bayesian
manual
```

------------------------------------------------------------------------

# 84. Parameter Count

Plus le nombre de paramètres augmente, plus le risque d'overfitting
augmente.

------------------------------------------------------------------------

# 85. Multiple Testing

Enregistrer le nombre de variantes testées.

------------------------------------------------------------------------

# 86. Best-of-N Bias

Le meilleur résultat parmi 1 000 essais n'a pas la même valeur
statistique que le résultat d'une hypothèse testée une seule fois.

------------------------------------------------------------------------

# 87. Parameter Stability

Analyser les valeurs voisines du paramètre optimal.

------------------------------------------------------------------------

# 88. Robust Plateau

Préférer :

``` text
broad stable region
```

à :

``` text
isolated optimum
```

------------------------------------------------------------------------

# 89. Sensitivity Analysis

Modifier les paramètres clés autour de leur valeur retenue.

------------------------------------------------------------------------

# 90. Ablation Study

Supprimer un composant pour mesurer sa contribution.

Exemple :

``` text
full strategy
vs
without volume profile
```

------------------------------------------------------------------------

# 91. Feature Ablation

Pour les modèles :

``` text
remove feature
→ retrain
→ compare
```

------------------------------------------------------------------------

# 92. Rule Ablation

Pour les stratégies :

``` text
remove filter
→ compare
```

------------------------------------------------------------------------

# 93. Complexity Penalty

Une amélioration marginale peut être refusée si elle ajoute trop de
complexité.

------------------------------------------------------------------------

# 94. Simpler Model Preference

À performance robuste équivalente :

``` text
simpler model wins
```

------------------------------------------------------------------------

# 95. Statistical Significance

Utiliser lorsque pertinente, mais ne pas la confondre avec l'importance
économique.

------------------------------------------------------------------------

# 96. Economic Significance

Une amélioration statistiquement détectable mais économiquement
insignifiante peut ne pas justifier un déploiement.

------------------------------------------------------------------------

# 97. Practical Significance

Le registre doit permettre de conclure :

``` text
Does this matter operationally?
```

------------------------------------------------------------------------

# 98. Robustness Suite

Toute stratégie candidate sérieuse doit passer une suite de robustesse.

------------------------------------------------------------------------

# 99. Robustness Dimensions

Tester :

``` text
time
assets
regimes
parameters
fees
slippage
latency
missing data
```

------------------------------------------------------------------------

# 100. Stress Scenarios

Exemples :

``` text
2x fees
2x slippage
execution delay
lower liquidity
missing signals
```

------------------------------------------------------------------------

# 101. Perturbation Tests

Modifier légèrement :

``` text
entry price
exit price
indicator period
threshold
```

et mesurer la stabilité.

------------------------------------------------------------------------

# 102. Noise Injection

Ajouter un bruit raisonnable pour tester la fragilité.

------------------------------------------------------------------------

# 103. Delayed Signal Test

Simuler une entrée retardée.

------------------------------------------------------------------------

# 104. Missed Trade Test

Supprimer aléatoirement une fraction des trades.

------------------------------------------------------------------------

# 105. Adverse Fill Test

Dégrader systématiquement les fills.

------------------------------------------------------------------------

# 106. Worst-Case Analysis

Analyser les scénarios défavorables plausibles.

------------------------------------------------------------------------

# 107. Experiment Artifacts

Une expérience peut produire :

``` text
metrics.json
equity_curve.csv
trades.parquet
config.yaml
report.md
plots/
logs/
model artifact
```

------------------------------------------------------------------------

# 108. Artifact Directory

Structure recommandée :

``` text
experiments/
  EXP-20260824-001/
    experiment.yaml
    metrics.json
    report.md
    artifacts/
```

------------------------------------------------------------------------

# 109. Experiment YAML

Exemple :

``` yaml
experiment_id: EXP-20260824-001
title: liquidity_sweep_confirmation
status: completed

hypothesis:
  statement: >
    Liquidity sweep confirmation improves
    out-of-sample expectancy after costs.

baseline:
  experiment_id: EXP-20260820-004

code:
  commit_sha: abc123

data:
  dataset_version: market-v12
  start: 2022-01-01
  end: 2026-07-31

metrics:
  primary: expectancy
  guardrails:
    - max_drawdown
    - trade_count
```

------------------------------------------------------------------------

# 110. Machine-Readable First

Les métadonnées principales doivent être structurées.

------------------------------------------------------------------------

# 111. Human Report

Chaque expérience importante doit aussi produire un résumé lisible.

------------------------------------------------------------------------

# 112. Report Structure

Format recommandé :

``` text
Hypothesis
Method
Data
Baseline
Results
Robustness
Limitations
Conclusion
Decision
```

------------------------------------------------------------------------

# 113. Results Must Include Failures

Ne pas supprimer les scénarios où la stratégie fonctionne mal.

------------------------------------------------------------------------

# 114. Charts

Les graphiques servent à comprendre le résultat, pas à le rendre plus
impressionnant.

------------------------------------------------------------------------

# 115. Equity Curve

Toujours accompagner l'equity curve de métriques quantitatives.

------------------------------------------------------------------------

# 116. Drawdown Curve

Afficher le drawdown pour les stratégies significatives.

------------------------------------------------------------------------

# 117. Distribution Analysis

Analyser :

``` text
trade returns
holding time
MAE
MFE
```

lorsque pertinent.

------------------------------------------------------------------------

# 118. Trade-Level Storage

Les trades simulés doivent être conservés pour inspection.

------------------------------------------------------------------------

# 119. Decision-Level Storage

Pour QuantLab, conserver idéalement aussi :

``` text
market context
score
decision
risk result
```

------------------------------------------------------------------------

# 120. Explainability

Une performance doit pouvoir être reliée aux décisions qui l'ont
produite.

------------------------------------------------------------------------

# 121. Experiment Comparison

Le registre doit permettre :

``` text
experiment A
vs
experiment B
```

------------------------------------------------------------------------

# 122. Comparison Rules

Comparer avec :

``` text
same dataset
same cost assumptions
same evaluation window
```

lorsque possible.

------------------------------------------------------------------------

# 123. Apples-to-Apples

Le système doit avertir lorsque deux expériences ne sont pas directement
comparables.

------------------------------------------------------------------------

# 124. Ranking

Le registre peut classer les expériences, mais pas uniquement par
rendement.

------------------------------------------------------------------------

# 125. Multi-Metric Ranking

Exemple :

``` text
return
risk
stability
complexity
execution feasibility
```

------------------------------------------------------------------------

# 126. Pareto Analysis

Identifier les expériences non dominées sur plusieurs objectifs.

------------------------------------------------------------------------

# 127. Champion

Le champion est la version de référence actuelle.

------------------------------------------------------------------------

# 128. Challenger

Un challenger tente de remplacer le champion.

------------------------------------------------------------------------

# 129. Champion/Challenger Record

Enregistrer :

``` text
champion_id
challenger_id
comparison_period
decision
```

------------------------------------------------------------------------

# 130. Promotion Ladder

Une expérience acceptée ne va pas directement en production.

``` text
BACKTEST
↓
ROBUSTNESS
↓
PAPER
↓
SHADOW
↓
LIMITED LIVE
↓
PRODUCTION
```

------------------------------------------------------------------------

# 131. Promotion Criteria

Chaque niveau doit avoir ses critères propres.

------------------------------------------------------------------------

# 132. Backtest → Paper

Exiger :

``` text
valid methodology
OOS evidence
cost-adjusted performance
robustness
```

------------------------------------------------------------------------

# 133. Paper → Shadow

Exiger :

``` text
stable live data behavior
correct decision generation
operational stability
```

------------------------------------------------------------------------

# 134. Shadow → Limited Live

Exiger :

``` text
acceptable comparison
execution readiness
risk approval
```

------------------------------------------------------------------------

# 135. Limited Live → Production

Exiger :

``` text
real execution evidence
slippage acceptable
no critical incidents
risk behavior valid
```

------------------------------------------------------------------------

# 136. Governance Integration

Les promotions importantes doivent passer par :

``` text
16-Governance-Engine.md
```

------------------------------------------------------------------------

# 137. Promotion Proposal

Le registre fournit les preuves au Governance Engine.

------------------------------------------------------------------------

# 138. Evidence Bundle

Exemple :

``` text
experiment spec
results
robustness report
test report
artifact hashes
```

------------------------------------------------------------------------

# 139. Rejection Record

Une hypothèse rejetée doit être conservée.

------------------------------------------------------------------------

# 140. Why Keep Failures

Cela évite :

``` text
repeat failed research
publication bias
memory loss
```

------------------------------------------------------------------------

# 141. Negative Results

Un résultat négatif bien conçu peut être plus utile qu'un résultat
positif fragile.

------------------------------------------------------------------------

# 142. Invalid vs Rejected

Distinction essentielle :

``` text
INVALID
=
experiment cannot answer question

REJECTED
=
experiment answered question negatively
```

------------------------------------------------------------------------

# 143. Experiment Review

Les expériences importantes doivent être revues.

------------------------------------------------------------------------

# 144. Review Questions

``` text
Was hypothesis defined first?
Is dataset valid?
Any leakage?
Is baseline fair?
Are costs realistic?
Is sample sufficient?
Was search space disclosed?
Are results robust?
```

------------------------------------------------------------------------

# 145. Research Review

Un reviewer doit chercher activement les raisons pour lesquelles le
résultat pourrait être faux.

------------------------------------------------------------------------

# 146. Confirmation Bias Defense

Inclure une section obligatoire :

``` text
Evidence Against Hypothesis
```

------------------------------------------------------------------------

# 147. Limitations

Toute expérience doit documenter ses limitations.

------------------------------------------------------------------------

# 148. Unknowns

Le rapport peut explicitement déclarer :

``` text
UNKNOWN
```

------------------------------------------------------------------------

# 149. No Forced Conclusion

Un résultat ambigu peut produire :

``` text
INCONCLUSIVE
```

------------------------------------------------------------------------

# 150. Experiment Decision

Valeurs possibles :

``` text
REJECT
ITERATE
ACCEPT
PROMOTE
INCONCLUSIVE
```

------------------------------------------------------------------------

# 151. Decision Rationale

La décision doit être justifiée séparément du résultat brut.

------------------------------------------------------------------------

# 152. Researcher vs Approver

Pour les promotions à fort impact, le chercheur ne doit pas être seul
décideur.

------------------------------------------------------------------------

# 153. AI-Generated Experiments

Les agents IA peuvent proposer et exécuter des expériences dans leurs
permissions.

------------------------------------------------------------------------

# 154. AI Experiment Record

Enregistrer :

``` text
agent_id
model_version
prompt_version
tools_used
```

------------------------------------------------------------------------

# 155. AI Hypothesis Generation

Une hypothèse proposée par IA reste une hypothèse.

Elle n'acquiert pas un statut scientifique parce qu'un modèle l'a
formulée avec une prose convaincante.

------------------------------------------------------------------------

# 156. AI Experiment Limits

Les agents doivent respecter :

``` text
compute budget
data permissions
experiment count
production restrictions
```

------------------------------------------------------------------------

# 157. Autonomous Search Risk

Un agent testant des milliers de variantes augmente fortement le risque
de data mining.

------------------------------------------------------------------------

# 158. Search Budget

Définir :

``` text
max_trials
compute_budget
time_budget
```

------------------------------------------------------------------------

# 159. AI Multiple-Testing Record

Tout search automatisé doit enregistrer le nombre total de candidats
évalués.

------------------------------------------------------------------------

# 160. AI Promotion Restriction

Un agent ne peut pas promouvoir seul une stratégie vers production.

------------------------------------------------------------------------

# 161. Experiment Lineage Graph

Architecture cible :

``` text
EXP-A
├── EXP-B
│   ├── EXP-D
│   └── EXP-E
└── EXP-C
```

------------------------------------------------------------------------

# 162. Knowledge Integration

Les résultats validés peuvent alimenter :

``` text
14-Knowledge-Engine.md
```

------------------------------------------------------------------------

# 163. Knowledge Promotion

Seuls les résultats suffisamment validés deviennent des connaissances
actives.

------------------------------------------------------------------------

# 164. Superseded Knowledge

Une nouvelle expérience peut invalider une connaissance précédente.

------------------------------------------------------------------------

# 165. Research Memory

Le registre constitue la mémoire scientifique de QuantLab.

------------------------------------------------------------------------

# 166. Search

Le système doit permettre de rechercher par :

``` text
strategy
symbol
concept
status
owner
date
metric
tag
```

------------------------------------------------------------------------

# 167. Tags

Exemples :

``` text
SMC
volume-profile
BTC
intraday
risk
execution
ML
```

------------------------------------------------------------------------

# 168. Experiment Collections

Les expériences peuvent être regroupées par programme de recherche.

------------------------------------------------------------------------

# 169. Research Program

Exemple :

``` text
RP-001
Market Structure Confirmation
```

------------------------------------------------------------------------

# 170. Program Objective

Un programme peut contenir plusieurs hypothèses liées.

------------------------------------------------------------------------

# 171. Experiment Dependencies

Une expérience peut dépendre d'une autre.

------------------------------------------------------------------------

# 172. Reproduction Run

Un run peut avoir :

``` text
run_type = REPRODUCTION
```

------------------------------------------------------------------------

# 173. Independent Reproduction

Les expériences critiques devraient pouvoir être reproduites
indépendamment.

------------------------------------------------------------------------

# 174. Reproduction Failure

Si un résultat ne peut pas être reproduit :

``` text
status review required
```

------------------------------------------------------------------------

# 175. Artifact Integrity

Les artefacts importants doivent avoir un hash.

------------------------------------------------------------------------

# 176. Immutable Results

Une fois finalisé, un résultat officiel ne doit pas être modifié
silencieusement.

------------------------------------------------------------------------

# 177. Correction

Une correction doit créer :

``` text
new version
or
new experiment
```

avec référence à l'original.

------------------------------------------------------------------------

# 178. Experiment Versioning

La spécification elle-même peut avoir une version.

------------------------------------------------------------------------

# 179. Audit Trail

Enregistrer :

``` text
created
modified
executed
reviewed
approved
promoted
```

------------------------------------------------------------------------

# 180. Database Model

Tables conceptuelles :

``` text
experiments
experiment_runs
experiment_metrics
experiment_artifacts
experiment_parameters
experiment_reviews
experiment_relationships
```

------------------------------------------------------------------------

# 181. Experiments Table

``` text
experiment_id
title
type
status
owner
hypothesis
created_at
```

------------------------------------------------------------------------

# 182. Experiment Runs

Une expérience peut être exécutée plusieurs fois.

``` text
run_id
experiment_id
started_at
completed_at
environment
seed
status
```

------------------------------------------------------------------------

# 183. Metrics Table

``` text
run_id
metric_name
metric_value
segment
```

------------------------------------------------------------------------

# 184. Parameters Table

``` text
run_id
parameter_name
parameter_value
```

------------------------------------------------------------------------

# 185. Artifacts Table

``` text
artifact_id
run_id
type
location
hash
```

------------------------------------------------------------------------

# 186. Relationships Table

Relations :

``` text
PARENT_OF
BASELINE_OF
REPRODUCES
SUPERSEDES
CHALLENGES
```

------------------------------------------------------------------------

# 187. Reviews Table

``` text
review_id
experiment_id
reviewer
decision
comments
created_at
```

------------------------------------------------------------------------

# 188. API Concept

Endpoints futurs :

``` text
POST /experiments
GET /experiments/{id}
POST /experiments/{id}/runs
POST /experiments/{id}/complete
POST /experiments/{id}/review
POST /experiments/{id}/promote
```

------------------------------------------------------------------------

# 189. CLI Concept

Exemple :

``` bash
quantlab experiment create experiment.yaml
quantlab experiment run EXP-20260824-001
quantlab experiment compare EXP-A EXP-B
quantlab experiment reproduce EXP-A
```

------------------------------------------------------------------------

# 190. Automated Metadata Capture

Le runner doit capturer automatiquement autant que possible :

``` text
commit SHA
environment
dependency version
dataset hash
timestamp
```

------------------------------------------------------------------------

# 191. Avoid Manual Metadata

Plus une information peut être capturée automatiquement, moins elle doit
dépendre de la mémoire humaine.

------------------------------------------------------------------------

# 192. Experiment Runner

Architecture cible :

``` text
Experiment Spec
↓
Validation
↓
Environment Build
↓
Dataset Resolution
↓
Execution
↓
Metrics
↓
Artifacts
↓
Registry
↓
Report
```

------------------------------------------------------------------------

# 193. Spec Validation

Une expérience ne démarre pas si les champs obligatoires manquent.

------------------------------------------------------------------------

# 194. Dataset Resolution

Le runner doit résoudre une version exacte.

------------------------------------------------------------------------

# 195. Code Resolution

Le runner doit enregistrer la version exacte du code.

------------------------------------------------------------------------

# 196. Execution Isolation

Les expériences lourdes doivent être isolées du système production.

------------------------------------------------------------------------

# 197. Resource Limits

Définir :

``` text
CPU
memory
GPU
runtime
```

selon le type.

------------------------------------------------------------------------

# 198. Experiment Timeout

Une expérience doit pouvoir être interrompue proprement.

------------------------------------------------------------------------

# 199. Failure Record

Un run échoué doit conserver :

``` text
error
logs
partial metadata
```

------------------------------------------------------------------------

# 200. Re-run

Un nouveau run ne doit pas écraser l'ancien.

------------------------------------------------------------------------

# 201. Metric Computation

Les métriques doivent utiliser des implémentations versionnées.

------------------------------------------------------------------------

# 202. Metric Definition Registry

Les métriques importantes doivent avoir une définition standard.

------------------------------------------------------------------------

# 203. Sharpe Definition

Documenter :

``` text
return frequency
annualization
risk-free assumption
```

------------------------------------------------------------------------

# 204. Drawdown Definition

Documenter précisément le calcul.

------------------------------------------------------------------------

# 205. Trade Definition

Définir ce qu'est un trade lorsque plusieurs fills existent.

------------------------------------------------------------------------

# 206. Consistent Metrics

Deux expériences comparées doivent utiliser les mêmes définitions.

------------------------------------------------------------------------

# 207. Report Generation

Le rapport doit idéalement être généré automatiquement depuis les
artefacts structurés.

------------------------------------------------------------------------

# 208. Human Commentary

Une section humaine peut expliquer :

``` text
interpretation
limitations
decision rationale
```

------------------------------------------------------------------------

# 209. No Manual Metric Copying

Éviter de recopier manuellement des chiffres dans les rapports lorsque
le système peut les injecter.

------------------------------------------------------------------------

# 210. Dashboard

Un dashboard futur peut afficher :

``` text
recent experiments
champions
challengers
accepted hypotheses
rejected hypotheses
promotion pipeline
```

------------------------------------------------------------------------

# 211. Research Funnel

Visualiser :

``` text
DRAFT
→ COMPLETED
→ ACCEPTED
→ PAPER
→ SHADOW
→ LIVE
```

------------------------------------------------------------------------

# 212. Experiment Velocity

Mesurer le nombre d'expériences utiles, pas seulement le nombre total.

------------------------------------------------------------------------

# 213. Quality Over Quantity

Cent expériences mal contrôlées peuvent apporter moins d'information que
cinq expériences bien conçues.

------------------------------------------------------------------------

# 214. Research Metrics

Suivre :

``` text
reproduction rate
acceptance rate
promotion rate
live survival rate
```

------------------------------------------------------------------------

# 215. Live Survival

Mesurer combien de stratégies promues restent valides après passage
live.

------------------------------------------------------------------------

# 216. Backtest-to-Live Degradation

Comparer :

``` text
backtest
paper
shadow
live
```

------------------------------------------------------------------------

# 217. Degradation Analysis

Une dégradation importante doit générer une nouvelle investigation.

------------------------------------------------------------------------

# 218. Experiment Retention

Les métadonnées doivent être conservées durablement.

------------------------------------------------------------------------

# 219. Large Artifacts

Les artefacts volumineux peuvent être stockés hors base avec référence.

------------------------------------------------------------------------

# 220. Storage Separation

Exemple :

``` text
metadata → PostgreSQL
large datasets/artifacts → object storage
```

------------------------------------------------------------------------

# 221. Security

Les expériences doivent respecter les permissions de données.

------------------------------------------------------------------------

# 222. Sensitive Datasets

Certains datasets peuvent avoir un accès restreint.

------------------------------------------------------------------------

# 223. Secrets

Aucun secret ne doit être stocké dans :

``` text
experiment.yaml
reports
artifacts
logs
```

------------------------------------------------------------------------

# 224. External Research

Les sources externes utilisées doivent être référencées.

------------------------------------------------------------------------

# 225. Licensing

Les datasets externes doivent respecter leurs licences.

------------------------------------------------------------------------

# 226. Governance of Compute

Les expériences coûteuses peuvent nécessiter un budget ou une
approbation.

------------------------------------------------------------------------

# 227. Compute Cost Tracking

Enregistrer lorsque pertinent :

``` text
runtime
CPU/GPU hours
AI token cost
```

------------------------------------------------------------------------

# 228. Research ROI

À maturité, QuantLab peut mesurer le coût de recherche par amélioration
réellement promue.

------------------------------------------------------------------------

# 229. Experiment Templates

Créer des templates par type.

------------------------------------------------------------------------

# 230. Strategy Template

Contient :

``` text
hypothesis
baseline
dataset
cost assumptions
metrics
robustness
```

------------------------------------------------------------------------

# 231. ML Template

Contient :

``` text
target
features
splits
model
hyperparameters
calibration
metrics
```

------------------------------------------------------------------------

# 232. AI Template

Contient :

``` text
task
prompt
model
evaluation dataset
baseline
quality metrics
cost
latency
```

------------------------------------------------------------------------

# 233. Risk Template

Contient :

``` text
risk rule
baseline
scenario set
tail behavior
capital impact
```

------------------------------------------------------------------------

# 234. Execution Template

Contient :

``` text
order logic
fill assumptions
latency
slippage
failure scenarios
```

------------------------------------------------------------------------

# 235. Experiment Checklist

Avant run :

``` text
[ ] hypothesis defined
[ ] baseline defined
[ ] dataset versioned
[ ] no leakage identified
[ ] metrics defined
[ ] acceptance criteria defined
[ ] costs defined
[ ] code version recorded
```

------------------------------------------------------------------------

# 236. Post-Run Checklist

``` text
[ ] results stored
[ ] robustness completed
[ ] limitations documented
[ ] contrary evidence reviewed
[ ] decision recorded
[ ] artifacts hashed
```

------------------------------------------------------------------------

# 237. Promotion Checklist

``` text
[ ] methodology valid
[ ] OOS passed
[ ] robustness passed
[ ] execution feasible
[ ] risk acceptable
[ ] tests passed
[ ] governance evidence attached
```

------------------------------------------------------------------------

# 238. Invalid Experiment Checklist

Marquer INVALID si :

``` text
data corrupted
leakage found
wrong implementation
incorrect costs
wrong split
missing critical artifact
```

------------------------------------------------------------------------

# 239. Experiment Naming

Format recommandé :

``` text
<domain>-<concept>-<change>
```

Exemple :

``` text
smc-liquidity-sweep-confirmation
```

------------------------------------------------------------------------

# 240. Tags vs Names

Le nom doit rester lisible.

Les détails supplémentaires vont dans les tags et métadonnées.

------------------------------------------------------------------------

# 241. Documentation Link

Chaque expérience peut référencer :

``` text
ADR
strategy spec
research note
issue
pull request
```

------------------------------------------------------------------------

# 242. PR Integration

Une modification de stratégie peut référencer l'Experiment ID dans la
Pull Request.

------------------------------------------------------------------------

# 243. Commit Integration

Format possible :

``` text
Experiment: EXP-20260824-001
```

dans les métadonnées ou messages appropriés.

------------------------------------------------------------------------

# 244. Deployment Integration

Un déploiement de stratégie doit référencer l'expérience ayant justifié
la promotion.

------------------------------------------------------------------------

# 245. Monitoring Integration

Une stratégie live doit rester liée à son expérience champion.

------------------------------------------------------------------------

# 246. Incident Integration

Un incident live peut créer une expérience destinée à comprendre ou
corriger le comportement.

------------------------------------------------------------------------

# 247. Knowledge Loop

Boucle cible :

``` text
Experiment
↓
Evidence
↓
Knowledge
↓
Production
↓
Monitoring
↓
New Observation
↓
New Experiment
```

------------------------------------------------------------------------

# 248. V1 Implementation

La V1 peut être simple :

``` text
Git-based experiment specs
+
structured YAML
+
artifact directories
+
automated runner
+
summary reports
```

Une plateforme entière n'est pas nécessaire dès le premier jour. Le
monde survivra probablement à l'absence d'un dashboard animé pendant
quelques semaines.

------------------------------------------------------------------------

# 249. V1 Repository Structure

``` text
experiments/
├── README.md
├── templates/
│   ├── strategy.yaml
│   ├── model.yaml
│   └── ai.yaml
├── registry/
│   └── experiments.jsonl
└── runs/
    └── EXP-YYYYMMDD-NNN/
```

------------------------------------------------------------------------

# 250. V1 Required Fields

Obligatoires :

``` text
experiment_id
title
owner
hypothesis
type
baseline
code_commit
dataset_version
configuration
metrics
acceptance_criteria
status
result
decision
```

------------------------------------------------------------------------

# 251. V1 Automation

Automatiser :

``` text
ID generation
Git SHA capture
timestamp
config snapshot
metric export
report skeleton
```

------------------------------------------------------------------------

# 252. V1 Validation

Refuser un run officiel si :

``` text
hypothesis missing
dataset unknown
code version unknown
metrics missing
```

------------------------------------------------------------------------

# 253. V2

Ajouter :

-   PostgreSQL registry ;
-   API ;
-   dashboard ;
-   automatic experiment comparison ;
-   model registry integration ;
-   richer lineage.

------------------------------------------------------------------------

# 254. V3

Ajouter :

-   distributed experiment runner ;
-   automated robustness suites ;
-   champion/challenger automation ;
-   compute budget management ;
-   automated reproducibility checks.

------------------------------------------------------------------------

# 255. V4

Ajouter :

-   AI-generated experiment proposals ;
-   controlled autonomous experiment execution ;
-   automated meta-analysis ;
-   continuous hypothesis generation ;
-   governance-aware research agents.

------------------------------------------------------------------------

# 256. Critères d'acceptation V1

L'Experiment Registry V1 est valide lorsque :

-   chaque expérience possède un ID unique ;
-   l'hypothèse est enregistrée avant résultat ;
-   la baseline est connue ;
-   le commit Git est enregistré ;
-   le dataset est versionné ;
-   la configuration est sauvegardée ;
-   les coûts d'exécution sont documentés ;
-   les métriques sont définies ;
-   les résultats sont conservés ;
-   les résultats négatifs ne sont pas supprimés ;
-   les expériences invalides sont distinguées des hypothèses rejetées ;
-   les runs multiples restent séparés ;
-   les expériences peuvent être reproduites ;
-   les relations parent/baseline sont enregistrées ;
-   les expériences peuvent être comparées ;
-   les promotions vers paper/shadow/live sont traçables ;
-   les expériences importantes alimentent le Knowledge Engine ;
-   les changements critiques peuvent référencer leurs preuves
    expérimentales.

------------------------------------------------------------------------

# 257. Risques principaux

## Overfitting

Trop d'itérations sur les mêmes données produisent une stratégie adaptée
au passé.

## Data Leakage

Des informations futures contaminent l'expérience.

## Multiple Testing

Un grand nombre d'essais augmente la probabilité de faux positifs.

## Survivorship Bias

L'univers historique ne représente pas la réalité passée.

## Unrealistic Costs

Les résultats disparaissent une fois frais et slippage ajoutés.

## Research Memory Loss

Les expériences anciennes sont oubliées et répétées.

## Cherry Picking

Seuls les bons résultats sont conservés.

## AI Search Explosion

Des agents peuvent tester des milliers de variantes et fabriquer
involontairement des découvertes statistiques.

------------------------------------------------------------------------

# 258. Principe de décision

Une expérience ne doit pas répondre uniquement :

``` text
Did it make money?
```

Elle doit répondre :

``` text
Was the hypothesis supported?
Was the test valid?
Is the result robust?
Is the effect economically meaningful?
Can it survive execution?
Can it survive risk constraints?
Can it be reproduced?
```

------------------------------------------------------------------------

# 259. Architecture cible

``` text
Research Question
      ↓
Hypothesis
      ↓
Experiment Specification
      ↓
Experiment Registry
      ↓
Versioned Dataset + Code + Config
      ↓
Experiment Runner
      ↓
Metrics + Artifacts
      ↓
Robustness Engine
      ↓
Experiment Report
      ↓
Review
      ↓
Knowledge Engine
      ↓
Governance Engine
      ↓
Paper / Shadow / Limited Live
      ↓
Production Monitoring
      ↓
New Evidence
      ↓
Experiment Registry
```

------------------------------------------------------------------------

# 260. Règle fondatrice

> **QuantLab ne doit pas devenir une machine à produire de beaux
> backtests. Il doit devenir une machine à éliminer méthodiquement les
> mauvaises hypothèses et à augmenter le niveau de preuve des bonnes.**

Le registre transforme la recherche de :

``` text
"I tried something and it looked good."
```

vers :

``` text
"We tested a defined hypothesis,
under known conditions,
against a known baseline,
with reproducible evidence,
and this is what survived."
```

C'est cette discipline qui permet de transformer la recherche
quantitative en connaissance exploitable.

------------------------------------------------------------------------

# 261. Statut

**Version : 1.0**

Documents directement liés :

-   `01-Vision-du-Projet.md`
-   `05-Market-Analysis-Engine.md`
-   `06-Market-Structure-Engine.md`
-   `07-Volume-Profile-Engine.md`
-   `08-Smart-Money-Concepts-Engine.md`
-   `09-Scoring-Engine.md`
-   `10-Decision-Engine.md`
-   `11-Risk-Engine.md`
-   `12-Execution-Engine.md`
-   `14-Knowledge-Engine.md`
-   `15-AI-and-Learning-Engine.md`
-   `16-Governance-Engine.md`
-   `17-AI-Development-Protocol.md`
-   `18-Testing-Strategy.md`
-   `19-Deployment-Guide.md`
-   `20-Engineering-Principles.md`
-   `22-API-Specification.md`
-   `23-Database-Schema.md`
-   `24-Security.md`
-   `25-Roadmap.md`

**Prochain document : `22-API-Specification.md`**
