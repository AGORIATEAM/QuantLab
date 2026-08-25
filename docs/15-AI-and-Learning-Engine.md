# 15 — AI and Learning Engine

**Projet : QuantLab**  
**Document : AI and Learning Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

L'AI and Learning Engine est la couche de QuantLab chargée d'utiliser l'intelligence artificielle, l'apprentissage statistique et l'automatisation de la recherche pour améliorer progressivement le système sans abandonner le contrôle, la reproductibilité ni la gouvernance.

Sa mission n'est pas de créer une IA qui « trade toute seule ».

Sa mission est de construire une boucle structurée :

```text
OBSERVATION
↓
HYPOTHÈSE
↓
EXPÉRIENCE
↓
VALIDATION
↓
CONNAISSANCE
↓
PROPOSITION D'AMÉLIORATION
↓
GOUVERNANCE
↓
DÉPLOIEMENT CONTRÔLÉ
↓
MESURE
```

L'IA doit donc augmenter les capacités de recherche, d'analyse et d'optimisation de QuantLab, tout en restant séparée de l'autorité finale d'exécution.

---

# 2. Principe fondamental

La règle centrale est :

> **L'IA peut proposer. Elle ne peut pas s'autoriser elle-même.**

Flux autorisé :

```text
AI Proposal
↓
Experiment
↓
Validation
↓
Governance Approval
↓
Versioned Configuration
↓
Decision / Risk / Execution
```

Flux interdit :

```text
AI
↓
Exchange
```

Aucun modèle génératif, agent autonome ou modèle ML ne doit disposer d'un chemin direct permettant de créer une exposition financière non validée.

---

# 3. Position dans l'architecture

```text
Operational Engines
       ↓
Knowledge Engine
       ↓
Experiment Registry
       ↓
┌──────────────────────────────┐
│   AI AND LEARNING ENGINE     │
├──────────────────────────────┤
│ Research Assistant           │
│ Hypothesis Generator         │
│ Feature Research             │
│ Model Training               │
│ Model Evaluation             │
│ Strategy Analysis            │
│ Drift Detection              │
│ Recommendation Engine        │
│ Agent Orchestration          │
└──────────────┬───────────────┘
               ↓
        Governance Engine
               ↓
     Approved Experiments
               ↓
   Controlled Deployment
```

---

# 4. Responsabilités

L'AI and Learning Engine doit pouvoir :

1. interroger le Knowledge Engine ;
2. rechercher des patterns ;
3. générer des hypothèses ;
4. proposer des expériences ;
5. préparer des datasets ;
6. sélectionner des features ;
7. entraîner des modèles ;
8. évaluer les modèles ;
9. comparer modèles et baselines ;
10. détecter l'overfitting ;
11. analyser les erreurs ;
12. détecter les dérives ;
13. produire des recommandations ;
14. documenter les résultats ;
15. générer des rapports de recherche ;
16. proposer des modifications de paramètres ;
17. proposer de nouvelles règles ;
18. proposer des modèles de scoring ;
19. proposer des modèles de risque ou d'exécution ;
20. déclencher des workflows expérimentaux autorisés ;
21. conserver la provenance de chaque proposition ;
22. transmettre les résultats au Governance Engine.

---

# 5. Hors périmètre

L'AI and Learning Engine ne doit jamais, de sa propre autorité :

- envoyer un ordre live ;
- modifier une position ;
- déplacer un stop ;
- augmenter une limite de risque ;
- désactiver un kill switch ;
- modifier directement une configuration production ;
- remplacer une stratégie live ;
- promouvoir son propre modèle ;
- modifier ses propres permissions ;
- supprimer les traces d'une expérience ;
- déclarer une hypothèse validée sans protocole de validation.

---

# 6. Séparation des responsabilités

QuantLab doit distinguer quatre niveaux :

```text
AI RESEARCH
AI RECOMMENDATION
GOVERNANCE APPROVAL
PRODUCTION EXECUTION
```

Ces niveaux doivent rester séparés techniquement.

---

# 7. AI Research

L'IA peut librement explorer les données autorisées dans un environnement de recherche isolé.

Elle peut :

```text
analyser
comparer
segmenter
formuler des hypothèses
proposer des features
```

---

# 8. AI Recommendation

Une conclusion de recherche devient une proposition structurée.

Exemple :

```text
Increase long-score threshold
from 75
to 80
during RANGE regime
```

Cette proposition n'est pas encore une modification du système.

---

# 9. Governance Approval

Le Governance Engine décide si la proposition peut :

```text
être rejetée
être testée
être déployée en paper
être déployée en shadow
être déployée en limited live
```

---

# 10. Production Execution

Seules les configurations explicitement approuvées peuvent être consommées par les moteurs live.

---

# 11. Architecture de sécurité

```text
AI Environment
     ↓
Proposal API
     ↓
Experiment Registry
     ↓
Governance Engine
     ↓
Approved Artifact Registry
     ↓
Production Engines
```

Il ne doit pas exister de :

```text
AI Environment
→ Production Database Write
```

pour les configurations critiques.

---

# 12. Modes d'utilisation de l'IA

Le moteur peut exploiter plusieurs catégories :

```text
LLM
CLASSICAL ML
DEEP LEARNING
STATISTICAL MODELS
OPTIMIZATION
AGENTIC WORKFLOWS
```

Chaque catégorie répond à des besoins différents.

---

# 13. LLM

Les modèles de langage sont adaptés à :

- analyse documentaire ;
- synthèse d'incidents ;
- génération d'hypothèses ;
- analyse de résultats ;
- production de rapports ;
- interrogation du Knowledge Engine ;
- génération assistée de code de recherche ;
- comparaison d'expériences.

Ils ne doivent pas être traités comme des calculateurs déterministes ou des oracles de marché.

---

# 14. Classical ML

Modèles potentiels :

```text
logistic regression
linear models
decision trees
random forest
gradient boosting
```

Ils peuvent être utilisés pour :

- classification de setups ;
- estimation de probabilité ;
- ranking ;
- calibration de score ;
- estimation de slippage.

---

# 15. Deep Learning

Des architectures plus complexes pourront être étudiées si les données et le problème le justifient.

Exemples :

```text
temporal models
transformers
representation learning
```

Mais la complexité n'est pas une preuve d'edge.

---

# 16. Statistical Models

Les méthodes statistiques restent essentielles :

```text
regression
Bayesian analysis
bootstrap
Monte Carlo
change-point detection
```

L'IA ne remplace pas les statistiques. Elle peut surtout aider à les utiliser moins péniblement.

---

# 17. Optimization

Des méthodes d'optimisation peuvent rechercher :

```text
thresholds
weights
execution parameters
risk parameters
```

avec des contraintes strictes.

---

# 18. Agentic Workflows

Des agents peuvent automatiser certaines tâches de recherche :

```text
retrieve evidence
build experiment
run tests
summarize results
create proposal
```

Mais leurs permissions doivent être limitées.

---

# 19. AI Roles

Rôles conceptuels :

```text
Research Agent
Data Analyst Agent
Experiment Agent
Model Evaluation Agent
Code Review Agent
Incident Analysis Agent
Documentation Agent
```

---

# 20. Research Agent

Mission :

```text
Knowledge Engine
↓
identify unanswered questions
↓
generate hypotheses
```

---

# 21. Data Analyst Agent

Mission :

```text
dataset
↓
statistical analysis
↓
segments
↓
anomalies
↓
report
```

---

# 22. Experiment Agent

Mission :

```text
hypothesis
↓
experiment specification
↓
reproducible execution
↓
results
```

---

# 23. Model Evaluation Agent

Mission :

```text
candidate model
vs
baseline
```

avec contrôle :

```text
in-sample
validation
out-of-sample
robustness
```

---

# 24. Code Review Agent

Peut analyser :

```text
research code
tests
data leakage risks
non-deterministic behavior
```

mais ne doit pas fusionner seul du code production critique.

---

# 25. Incident Analysis Agent

Peut consommer :

```text
logs
metrics
traces
incident history
```

et proposer :

```text
probable root cause
related incidents
corrective actions
```

---

# 26. Documentation Agent

Peut maintenir :

```text
experiment reports
model cards
strategy documentation
ADRs
change summaries
```

---

# 27. Agent Permissions

Chaque agent doit avoir une permission minimale.

Exemple :

```text
Research Agent:
READ analytical data
WRITE experiment proposals
NO production writes
NO trading permissions
```

---

# 28. Principle of Least Privilege

Une IA ne doit recevoir que :

```text
les données
les outils
les actions
```

strictement nécessaires à sa tâche.

---

# 29. Tool Allowlist

Chaque agent doit disposer d'une liste explicite d'outils autorisés.

Exemple :

```text
query_knowledge
create_experiment
run_backtest
write_report
```

---

# 30. Tool Denylist

Les actions suivantes doivent être interdites par architecture :

```text
submit_live_order
change_risk_limit
disable_kill_switch
modify_production_secret
approve_own_model
```

---

# 31. Human-in-the-Loop

Les décisions critiques doivent nécessiter une validation humaine ou une règle de gouvernance pré-approuvée.

---

# 32. Machine-in-the-Loop

L'humain ne doit pas non plus devenir le seul mécanisme de sécurité.

Les contraintes critiques doivent être imposées par le système.

---

# 33. Knowledge Engine Integration

L'AI Engine doit utiliser prioritairement les données structurées du Knowledge Engine.

Il ne doit pas reconstruire arbitrairement la vérité depuis des logs bruts lorsqu'une source canonique existe.

---

# 34. Retrieval Layer

Le moteur doit fournir une couche de recherche permettant de retrouver :

```text
trades
experiments
knowledge objects
incidents
strategies
versions
research reports
```

---

# 35. Semantic Retrieval

Une recherche sémantique peut permettre :

```text
Find experiments related to
liquidity sweeps in ranging markets
```

---

# 36. Structured Retrieval

Pour les calculs :

```text
SQL / analytical query
```

doit rester préférable à une interprétation libre par LLM.

---

# 37. Hybrid Retrieval

Architecture recommandée :

```text
semantic retrieval
+
structured filters
+
versioned data
```

---

# 38. Source Grounding

Toute conclusion générée par IA doit pouvoir référencer ses sources.

Exemple :

```text
experiment IDs
dataset IDs
knowledge IDs
metric queries
```

---

# 39. No Evidence, No Promotion

Une proposition sans preuve traçable ne doit pas atteindre la phase de validation production.

---

# 40. Hypothesis Object

Structure conceptuelle :

```python
Hypothesis:
    hypothesis_id

    statement
    rationale

    source_evidence
    target_metric

    expected_effect

    scope

    proposed_by
    created_at

    status
```

---

# 41. Hypothesis Status

Valeurs :

```text
DRAFT
PROPOSED
APPROVED_FOR_TEST
TESTING
SUPPORTED
REJECTED
INCONCLUSIVE
```

---

# 42. Hypothesis Generation

L'IA peut rechercher :

```text
performance anomalies
regime differences
score calibration issues
execution cost patterns
risk inefficiencies
```

---

# 43. Example Hypothesis

```text
Hypothesis:
Bullish liquidity sweep setups
with long_score >= 80
perform better when price is below VAL
before reclaiming value.
```

---

# 44. Hypothesis Quality Gate

Une hypothèse doit être :

```text
testable
specific
measurable
scoped
```

---

# 45. Experiment Proposal

Structure :

```python
ExperimentProposal:
    experiment_id
    hypothesis_id

    baseline
    candidate

    dataset
    metrics

    validation_method
    acceptance_criteria

    risks
```

---

# 46. Experiment Registry

Toutes les expériences doivent être enregistrées dans :

```text
21-Experiment-Registry.md
```

avant qu'un résultat ne puisse devenir une connaissance officielle.

---

# 47. Automated Experimentation

L'IA peut lancer automatiquement des expériences si :

```text
environment = RESEARCH
resources within limits
experiment type approved
no production impact
```

---

# 48. Compute Budget

Chaque workflow doit respecter :

```text
CPU budget
GPU budget
memory budget
time budget
API budget
```

---

# 49. Experiment Explosion

L'IA peut générer beaucoup plus d'idées qu'une équipe humaine.

C'est utile jusqu'au moment où elle teste 80 000 variations et découvre miraculeusement une stratégie parfaite sur le passé.

Le système doit donc limiter la recherche.

---

# 50. Search Budget

Définir :

```text
max experiments per hypothesis
max parameter combinations
max compute cost
```

---

# 51. Multiple Testing Control

Le moteur doit enregistrer :

```text
number of tested variants
```

et appliquer des méthodes adaptées lorsque nécessaire.

---

# 52. Baseline Requirement

Tout modèle candidat doit être comparé à une baseline.

---

# 53. Simple Baseline First

Exemples :

```text
fixed threshold
logistic regression
simple rule
current production model
```

Un modèle complexe qui ne bat pas une baseline simple ne mérite pas une cérémonie de déploiement.

---

# 54. Dataset Contract

Chaque entraînement doit utiliser un dataset identifié par :

```text
dataset_id
dataset_version
feature_version
label_version
```

---

# 55. Point-in-Time Correctness

Les features utilisées à `T` doivent être celles disponibles à `T`.

Aucune information future ne doit contaminer le dataset.

---

# 56. Train / Validation / Test

Séparer :

```text
TRAIN
VALIDATION
TEST
```

---

# 57. Temporal Split

Pour les marchés, préférer souvent des séparations temporelles aux splits aléatoires naïfs.

---

# 58. Walk-Forward Validation

Processus :

```text
train past
↓
test future
↓
advance window
↓
repeat
```

---

# 59. Purging

Pour certains labels temporels, il peut être nécessaire d'éviter le chevauchement entre train et validation.

---

# 60. Embargo

Une période d'embargo peut être utilisée pour réduire les fuites liées aux observations proches.

---

# 61. Feature Engineering

L'IA peut proposer de nouvelles features dérivées de :

```text
market structure
volume profile
SMC
volatility
time
execution
risk
```

---

# 62. Feature Registry

Toute feature candidate doit posséder :

```text
feature_id
definition
version
source
calculation
availability_time
```

---

# 63. Feature Approval

Une feature utilisée en production doit être :

```text
documented
tested
versioned
approved
```

---

# 64. Feature Leakage Test

Chaque feature doit être testée contre les risques de look-ahead.

---

# 65. Feature Ablation

Pour vérifier sa valeur :

```text
model with feature
vs
model without feature
```

---

# 66. Feature Stability

Mesurer :

```text
distribution by period
distribution by asset
missing rate
drift
```

---

# 67. Model Types

QuantLab peut progressivement supporter :

```text
classification
regression
ranking
anomaly detection
forecasting
representation models
```

---

# 68. Classification

Exemple :

```text
probability setup reaches +2R before -1R
```

---

# 69. Regression

Exemple :

```text
expected future R
```

ou :

```text
expected slippage
```

---

# 70. Ranking

Le modèle peut classer plusieurs opportunités simultanées.

---

# 71. Anomaly Detection

Utilisable pour :

```text
data anomalies
execution anomalies
strategy drift
```

---

# 72. Forecasting

Les prévisions directes de prix doivent être traitées avec une prudence particulière.

Un modèle capable de prédire correctement un prix historique est une curiosité statistique. Un modèle capable de le faire hors échantillon est le sujet intéressant.

---

# 73. Model Artifact

Structure conceptuelle :

```python
ModelArtifact:
    model_id
    model_version

    model_type
    framework

    training_dataset_id
    feature_set_version

    hyperparameters

    training_code_version

    metrics

    created_at
    status
```

---

# 74. Model Registry

Tous les modèles doivent être enregistrés.

Statuts :

```text
EXPERIMENTAL
CANDIDATE
VALIDATED
SHADOW
PAPER
LIMITED_LIVE
PRODUCTION
RETIRED
```

---

# 75. Model Card

Chaque modèle doit avoir une fiche contenant :

```text
purpose
inputs
outputs
training data
metrics
limitations
known failure modes
approved scope
```

---

# 76. Model Versioning

Une modification de :

```text
features
hyperparameters
training data
code
```

doit produire une nouvelle version.

---

# 77. Reproducible Training

Conserver :

```text
random seed
code commit
container/environment
dependency versions
dataset version
configuration
```

---

# 78. Determinism

Lorsque possible, les entraînements doivent être reproductibles.

Lorsque ce n'est pas possible, la variance doit être mesurée.

---

# 79. Model Evaluation

L'évaluation doit inclure :

```text
predictive metrics
trading metrics
robustness metrics
operational metrics
```

---

# 80. Predictive Metrics

Selon le modèle :

```text
precision
recall
F1
AUC
log loss
Brier score
MAE
RMSE
```

---

# 81. Trading Metrics

Toujours mesurer l'effet réel sur :

```text
expectancy
profit factor
drawdown
turnover
fees
slippage
```

---

# 82. Accuracy Trap

Une accuracy élevée ne signifie pas nécessairement une stratégie rentable.

Le marché ne verse malheureusement aucune prime pour avoir correctement classé beaucoup de cas inutiles.

---

# 83. Calibration

Pour un modèle probabiliste :

```text
predicted probability
vs
observed frequency
```

doit être analysé.

---

# 84. Calibration Curve

Exemple :

```text
predicted 70%
→ observed 52%
```

signale une mauvaise calibration.

---

# 85. Ranking Metrics

Pour sélectionner les meilleurs setups :

```text
precision@k
NDCG
top-decile expectancy
```

peuvent être utiles.

---

# 86. Economic Objective

L'objectif d'entraînement ne doit pas être confondu avec l'objectif économique final.

Exemple :

```text
minimize classification loss
```

n'est qu'un proxy.

L'objectif réel peut être :

```text
maximize robust risk-adjusted expectancy after costs
```

---

# 87. Transaction Costs

Les évaluations doivent inclure :

```text
fees
spread
slippage
```

---

# 88. Capacity

Une amélioration théorique peut disparaître lorsque la taille des ordres augmente.

---

# 89. Robustness Testing

Tester :

```text
different periods
different assets
different regimes
different parameters
different cost assumptions
```

---

# 90. Stress Testing

Exemples :

```text
2x slippage
higher fees
missing data
high volatility
latency
```

---

# 91. Sensitivity Analysis

Une amélioration robuste doit survivre à de petites variations de paramètres.

---

# 92. Out-of-Sample Gate

Aucun modèle ne doit être promu uniquement sur la performance d'entraînement.

---

# 93. Shadow Mode

En `SHADOW` :

```text
model receives live inputs
↓
produces predictions
↓
predictions stored
↓
no trading authority
```

---

# 94. Shadow Evaluation

Comparer :

```text
predictions
vs
real outcomes
```

sans capital exposé.

---

# 95. Paper Mode

Le modèle peut ensuite alimenter une stratégie paper.

---

# 96. Limited Live

Après validation :

```text
small risk budget
strict limits
enhanced monitoring
```

---

# 97. Production Promotion

Flux recommandé :

```text
EXPERIMENTAL
↓
CANDIDATE
↓
VALIDATED
↓
SHADOW
↓
PAPER
↓
LIMITED_LIVE
↓
PRODUCTION
```

---

# 98. Promotion Gate

Chaque transition doit avoir des critères explicites.

---

# 99. Rollback

Tout modèle production doit pouvoir être remplacé rapidement par :

```text
previous stable version
```

---

# 100. Champion / Challenger

Architecture possible :

```text
Champion = production model
Challenger = candidate
```

Le challenger peut être évalué en shadow.

---

# 101. A/B Testing

En trading, l'A/B testing live doit être utilisé avec prudence car les observations ne sont pas indépendantes et le capital est exposé.

---

# 102. Drift Monitoring

Trois catégories :

```text
DATA DRIFT
PREDICTION DRIFT
PERFORMANCE DRIFT
```

---

# 103. Data Drift

Les distributions d'inputs changent.

---

# 104. Prediction Drift

Les sorties du modèle changent.

---

# 105. Performance Drift

La relation entre prédiction et outcome se dégrade.

---

# 106. Drift Metrics

Méthodes possibles :

```text
PSI
KS statistic
distribution distance
rolling calibration
rolling expectancy
```

---

# 107. Drift Response

Une dérive peut déclencher :

```text
alert
investigation
retraining proposal
shadow revalidation
model downgrade
```

---

# 108. No Blind Retraining

Une dérive ne doit pas automatiquement entraîner :

```text
retrain
→ deploy
```

sans validation.

---

# 109. Retraining Pipeline

Flux :

```text
new dataset
↓
training
↓
evaluation
↓
comparison
↓
experiment record
↓
governance
```

---

# 110. Retraining Frequency

Elle doit dépendre :

```text
data volume
strategy horizon
drift
model stability
```

et non d'un calendrier arbitraire uniquement.

---

# 111. Continuous Learning

QuantLab peut tendre vers un système de continuous learning.

Mais :

```text
continuous learning
≠
continuous uncontrolled deployment
```

---

# 112. Recommendation Engine

L'IA peut produire des recommandations structurées.

Types :

```text
PARAMETER_CHANGE
FEATURE_CHANGE
MODEL_CHANGE
STRATEGY_CHANGE
RISK_CHANGE
EXECUTION_CHANGE
MONITORING_CHANGE
```

---

# 113. Recommendation Object

```python
AIRecommendation:
    recommendation_id

    type
    target_component

    current_state
    proposed_state

    rationale
    evidence

    expected_benefit
    risks

    confidence

    experiment_ids

    status
```

---

# 114. Recommendation Status

```text
DRAFT
PROPOSED
UNDER_REVIEW
APPROVED_FOR_TEST
REJECTED
IMPLEMENTED
```

---

# 115. Explainability

Chaque recommandation doit fournir :

```text
what
why
evidence
scope
expected impact
uncertainty
```

---

# 116. No Fake Precision

L'IA ne doit pas présenter :

```text
87.34% confidence
```

si cette valeur n'a aucune calibration statistique réelle.

---

# 117. Uncertainty

Le moteur doit distinguer :

```text
model probability
statistical confidence
LLM confidence
evidence quality
```

Ces notions ne sont pas interchangeables.

---

# 118. Reason Codes

Les modèles utilisés dans la chaîne de décision doivent produire autant que possible des reason codes ou facteurs explicatifs.

---

# 119. Explainability Techniques

Selon le modèle :

```text
coefficients
feature importance
SHAP-like methods
partial dependence
counterfactual analysis
```

---

# 120. Explainability Limitation

Une explication post-hoc n'est pas nécessairement une description causale exacte du modèle.

---

# 121. LLM Prompt Management

Les prompts utilisés par les agents doivent être :

```text
versioned
tested
reviewed
```

---

# 122. Prompt Registry

Structure :

```text
prompt_id
version
purpose
model
template
tools
evaluation_suite
```

---

# 123. Prompt Changes

Une modification significative d'un prompt de production doit être traitée comme un changement logiciel.

---

# 124. LLM Model Version

Conserver :

```text
provider
model_name
model_version
parameters
```

---

# 125. LLM Non-Determinism

Les workflows critiques ne doivent pas dépendre d'une réponse libre impossible à valider.

---

# 126. Structured Outputs

Préférer des sorties structurées :

```json
{
  "hypothesis": "...",
  "evidence_ids": ["..."],
  "confidence": "MEDIUM"
}
```

---

# 127. Schema Validation

Toute sortie d'IA destinée à un workflow automatique doit être validée contre un schéma.

---

# 128. Hallucination Defense

Les conclusions LLM doivent être vérifiées contre :

```text
retrieved sources
structured data
allowed actions
validation rules
```

---

# 129. Citation Requirement

Pour les analyses importantes, l'agent doit citer les IDs internes ayant servi de preuve.

---

# 130. Context Isolation

Ne pas donner à un agent plus de contexte qu'il n'en a besoin.

Cela améliore :

```text
security
cost
relevance
```

---

# 131. Prompt Injection Defense

Les contenus externes doivent être considérés comme non fiables.

Une donnée de marché, un document ou un commentaire ne doit jamais pouvoir modifier les règles système d'un agent.

---

# 132. External Data Boundary

Tout contenu externe doit passer par :

```text
ingestion
validation
sanitization
classification
```

avant utilisation.

---

# 133. Secret Isolation

Les agents ne doivent jamais recevoir :

```text
exchange API secrets
database admin passwords
private keys
```

si leur tâche n'en a pas besoin.

Dans la majorité des cas, ils n'en ont jamais besoin.

---

# 134. Code Generation

L'IA peut générer du code pour :

```text
research
tests
analysis
documentation
```

---

# 135. Production Code Boundary

Le code généré pour la production doit passer par :

```text
review
tests
security checks
CI
governance
```

---

# 136. AI Development Protocol

Les règles détaillées de développement assisté par IA seront définies dans :

```text
17-AI-Development-Protocol.md
```

---

# 137. Evaluation Harness

Chaque agent ou modèle doit disposer d'une suite d'évaluation.

---

# 138. LLM Evaluation

Mesurer notamment :

```text
groundedness
schema compliance
tool correctness
citation correctness
consistency
```

---

# 139. Agent Evaluation

Tester :

```text
correct tool selection
permission boundaries
failure handling
retry behavior
```

---

# 140. Adversarial Tests

Tester :

```text
prompt injection
malformed data
false evidence
conflicting instructions
unauthorized tool requests
```

---

# 141. Model Evaluation Dataset

Conserver un dataset de cas représentatifs et difficiles.

---

# 142. Regression Tests

Une nouvelle version ne doit pas dégrader silencieusement les cas déjà résolus.

---

# 143. Golden Cases

Créer des cas de référence avec résultats attendus.

---

# 144. Red-Team Cases

Créer des cas visant à faire violer :

```text
risk boundaries
tool permissions
source requirements
```

---

# 145. AI Failure Modes

Principaux risques :

```text
hallucination
overconfidence
data leakage
overfitting
prompt injection
tool misuse
model drift
automation bias
```

---

# 146. Automation Bias

Un opérateur peut accorder trop de confiance à une recommandation parce qu'elle vient d'une IA.

L'interface doit afficher les preuves et l'incertitude.

---

# 147. Human Override

Un humain autorisé doit pouvoir rejeter une recommandation.

Mais l'override doit être audité.

---

# 148. AI Override Prohibition

L'IA ne doit jamais pouvoir contourner :

```text
Risk Engine
Governance Engine
Security controls
Kill Switch
```

---

# 149. AI Service Health

Le Monitoring Engine doit suivre :

```text
AI request latency
error rate
provider availability
token usage
cost
model version
```

---

# 150. AI Failure Policy

Si l'AI Engine est indisponible :

```text
core trading safety
```

doit continuer de fonctionner.

---

# 151. Graceful Degradation

Le système peut revenir à :

```text
deterministic production rules
```

si un service IA secondaire tombe.

---

# 152. No AI Dependency for Emergency Exit

Une sortie de sécurité ne doit jamais nécessiter l'accord ou la disponibilité d'un modèle IA.

---

# 153. Cost Monitoring

Suivre :

```text
training cost
inference cost
LLM API cost
storage cost
experiment cost
```

---

# 154. Cost per Insight

Une métrique future peut comparer :

```text
research cost
vs
validated improvement
```

---

# 155. Resource Quotas

Définir des quotas par :

```text
agent
experiment
project
environment
```

---

# 156. Caching

Les réponses ou embeddings réutilisables peuvent être mis en cache lorsque cela ne compromet pas la fraîcheur.

---

# 157. AI Data Store

Le moteur peut utiliser :

```text
model registry
feature registry
prompt registry
evaluation registry
embedding/vector store
```

---

# 158. Vector Store

Un vector store peut indexer :

```text
knowledge objects
experiment reports
ADRs
incidents
documentation
```

---

# 159. Vector Store Limitation

Le vector store n'est pas une source de vérité transactionnelle.

La base canonique reste la référence.

---

# 160. Model Serving

Les modèles production doivent être servis derrière une interface versionnée.

Exemple :

```text
POST /models/{model_id}/predict
```

---

# 161. Prediction Record

Chaque prédiction importante doit pouvoir être persistée :

```text
prediction_id
model_id
model_version
features_version
timestamp
output
```

---

# 162. Prediction Lineage

Pour une décision influencée par un modèle, il faut pouvoir reconstruire :

```text
input
model version
prediction
decision
outcome
```

---

# 163. Online vs Offline Features

Les features online et offline doivent avoir la même définition.

---

# 164. Training-Serving Skew

Le système doit détecter les différences entre :

```text
training feature calculation
```

et :

```text
production feature calculation
```

---

# 165. Feature Parity Tests

Tester les mêmes inputs dans :

```text
offline pipeline
online pipeline
```

et comparer les outputs.

---

# 166. Latency Budget

Un modèle utilisé dans la chaîne live doit respecter une latence maximale.

---

# 167. Timeout Policy

Si le modèle dépasse son timeout :

```text
fallback
NO_TRADE
or deterministic rule
```

selon le composant.

---

# 168. Fallback

Tout modèle critique doit définir son comportement de fallback.

---

# 169. Fail Closed

Pour une IA qui augmente le risque :

```text
uncertain / unavailable
→ no new exposure
```

---

# 170. Risk Model AI

L'IA peut proposer des modèles de :

```text
volatility
correlation
drawdown risk
position sizing
```

Mais les limites absolues restent déterministes.

---

# 171. Risk Hard Limits

Exemples :

```text
max leverage
max daily loss
max portfolio heat
max position size
```

ne doivent pas dépendre uniquement d'un modèle ML.

---

# 172. Scoring AI

Le Scoring Engine peut progressivement intégrer :

```text
ML probability
ranking score
calibrated confidence
```

comme composants versionnés.

---

# 173. Decision AI

Le Decision Engine peut utiliser des outputs IA approuvés, mais doit conserver des règles déterministes autour :

```text
eligibility
state
cooldown
risk handoff
```

---

# 174. Execution AI

L'IA peut optimiser :

```text
order type
timing
slippage estimate
fill probability
venue choice
```

sous contraintes explicites.

---

# 175. Monitoring AI

L'IA peut :

```text
summarize incidents
cluster alerts
suggest root cause
```

sans supprimer les alertes critiques déterministes.

---

# 176. Knowledge AI

L'IA peut :

```text
search
summarize
compare
generate hypotheses
```

sur la mémoire de QuantLab.

---

# 177. Governance AI

L'IA peut aider à vérifier :

```text
missing evidence
missing tests
policy violations
```

mais ne doit pas être l'autorité finale sur ses propres changements.

---

# 178. Self-Improvement Boundary

QuantLab peut être conçu pour s'améliorer.

Mais la boucle doit être :

```text
self-propose
not self-authorize
```

---

# 179. Recursive Modification

Un agent ne doit pas pouvoir modifier :

```text
its own system prompt
its own permissions
governance rules
security policies
```

sans workflow externe contrôlé.

---

# 180. Autonomous Research Loop

Architecture future :

```text
Knowledge Gap
↓
AI Hypothesis
↓
Experiment Proposal
↓
Automated Research Test
↓
Statistical Evaluation
↓
Knowledge Draft
↓
Governance Review
```

---

# 181. Autonomous Improvement Loop

Après validation :

```text
Approved Knowledge
↓
AI Change Proposal
↓
Code / Config Candidate
↓
Tests
↓
Shadow
↓
Paper
↓
Limited Live
↓
Governance
↓
Production
```

---

# 182. No Direct Self-Deployment

Même dans une architecture avancée :

```text
AI generated change
→ automatic unrestricted production
```

reste interdit.

---

# 183. AI Audit Trail

Chaque action doit enregistrer :

```text
agent_id
model
model_version
prompt_version
tools_used
input references
output
timestamp
```

---

# 184. Decision Audit

Pour chaque recommandation :

```text
who/what proposed
what evidence
what model
what experiment
who approved
what was deployed
```

---

# 185. Reproducible AI Analysis

Une analyse importante doit enregistrer suffisamment d'informations pour être reproduite ou réévaluée.

---

# 186. Data Retention

Les prompts et outputs sensibles doivent avoir une politique de rétention adaptée.

---

# 187. Privacy

Ne pas envoyer inutilement des données sensibles à des modèles externes.

---

# 188. Provider Abstraction

Créer une interface commune :

```python
class AIProvider:
    generate(...)
    embed(...)
    health(...)
```

afin de limiter le couplage à un fournisseur.

---

# 189. Model Routing

Une version future pourra sélectionner un modèle selon :

```text
task
cost
latency
quality
privacy
```

---

# 190. Local Models

Des modèles locaux peuvent être utilisés pour certaines tâches sensibles ou répétitives.

---

# 191. External Models

Les modèles externes peuvent être utilisés lorsqu'ils offrent une valeur suffisante et que les contraintes de données le permettent.

---

# 192. Provider Failure

Une panne fournisseur ne doit pas provoquer une panne du système de trading principal.

---

# 193. AI API

Endpoints conceptuels :

```text
POST /ai/hypotheses
POST /ai/experiments/propose
POST /ai/models/train
POST /ai/models/evaluate
GET  /ai/models
POST /ai/recommendations
GET  /ai/recommendations
```

Les permissions devront être strictes.

---

# 194. Event Model

Événements possibles :

```text
AI_HYPOTHESIS_CREATED
EXPERIMENT_PROPOSED
MODEL_TRAINING_STARTED
MODEL_TRAINING_COMPLETED
MODEL_VALIDATION_FAILED
MODEL_VALIDATED
AI_RECOMMENDATION_CREATED
MODEL_DRIFT_DETECTED
```

---

# 195. Database Entities

Entités potentielles :

```text
ai_agents
ai_runs
prompts
models
model_versions
predictions
features
feature_versions
recommendations
evaluations
```

Le détail sera défini dans `23-Database-Schema.md`.

---

# 196. Monitoring Metrics

Mesurer :

```text
ai_requests_total
ai_errors_total
ai_latency_ms
ai_cost
training_runs
training_failures
model_predictions
model_timeouts
drift_alerts
recommendations_created
```

---

# 197. Governance Metrics

Suivre :

```text
recommendations_approved
recommendations_rejected
models_promoted
models_rolled_back
```

---

# 198. Research Metrics

Suivre :

```text
hypotheses_created
experiments_completed
experiments_supported
experiments_rejected
```

---

# 199. Quality Metrics

Mesurer :

```text
reproducibility rate
out-of-sample success
shadow-to-live degradation
model rollback rate
```

---

# 200. V1 Priorities

La V1 doit rester volontairement simple.

Implémenter :

- AI provider abstraction ;
- Knowledge Engine retrieval ;
- structured research assistant ;
- hypothesis generation ;
- experiment proposal ;
- experiment result summarization ;
- recommendation objects ;
- prompt versioning ;
- AI run audit trail ;
- strict tool permissions ;
- structured outputs ;
- evidence references ;
- cost monitoring ;
- no production write access.

---

# 201. V2 Priorities

Ajouter :

- model registry ;
- feature registry ;
- classical ML training pipeline ;
- walk-forward evaluation ;
- shadow predictions ;
- calibration analysis ;
- drift monitoring ;
- champion/challenger workflow.

---

# 202. V3 Priorities

Ajouter :

- automated experiment agents ;
- semantic knowledge retrieval ;
- model serving ;
- feature parity testing ;
- retraining proposals ;
- advanced evaluation harness ;
- AI incident analysis.

---

# 203. V4 Priorities

Ajouter :

- multi-agent research ;
- autonomous hypothesis discovery ;
- automated ablation ;
- adaptive model routing ;
- controlled continuous learning ;
- AI-generated change candidates ;
- automated shadow deployment.

---

# 204. V5 Vision

Une version mature peut fonctionner comme un laboratoire quantitatif semi-autonome :

```text
observe
↓
question
↓
research
↓
test
↓
learn
↓
propose
↓
validate
↓
deploy carefully
↓
measure
```

Le système devient capable d'accélérer sa propre recherche sans disposer du droit de contourner sa gouvernance.

---

# 205. Critères d'acceptation V1

La V1 est valide lorsque :

- l'IA peut interroger la connaissance sans accès direct aux secrets ;
- chaque run IA est auditable ;
- les prompts sont versionnés ;
- les outputs automatisés sont structurés et validés ;
- les hypothèses sont enregistrées ;
- les propositions référencent leurs preuves ;
- aucune IA ne peut envoyer d'ordre ;
- aucune IA ne peut modifier les limites de risque ;
- aucune IA ne peut promouvoir son propre changement ;
- les expériences sont liées au registre ;
- les coûts sont mesurés ;
- une panne IA n'empêche pas les fonctions critiques de sécurité ;
- les recommandations peuvent être soumises au Governance Engine.

---

# 206. Risques principaux

## Hallucination

Le modèle peut inventer une explication ou une preuve.

## Overfitting

L'automatisation de la recherche peut trouver des patterns aléatoires à grande échelle.

## Automation Bias

Les humains peuvent survaloriser les recommandations de l'IA.

## Data Leakage

Une mauvaise construction du dataset peut produire des résultats irréalistes.

## Prompt Injection

Des contenus externes peuvent tenter de détourner les agents.

## Excessive Permissions

Un agent disposant de trop d'outils peut devenir un risque opérationnel.

## Model Drift

Un modèle performant aujourd'hui peut perdre son edge.

## Self-Modification Risk

Une boucle autonome mal gouvernée peut progressivement contourner les contraintes initiales.

---

# 207. Principe d'ingénierie

La sophistication de l'AI Engine doit augmenter uniquement lorsque :

```text
observability
testing
reproducibility
security
governance
```

sont déjà suffisamment solides.

Ajouter des agents autonomes sur une infrastructure mal observée ne crée pas un système intelligent. Cela crée juste des problèmes plus rapides.

---

# 208. Architecture cible

```text
Knowledge Engine
      ↓
Retrieval Layer
      ↓
AI Research Agents
      ↓
Hypothesis Registry
      ↓
Experiment Registry
      ↓
Training / Evaluation
      ↓
Model Registry
      ↓
Recommendation Engine
      ↓
Governance Engine
      ↓
Shadow / Paper / Limited Live
      ↓
Production
      ↓
Monitoring + Outcomes
      ↓
Knowledge Engine
```

Cette architecture forme une boucle d'apprentissage contrôlée.

---

# 209. Résultat attendu

Le système doit pouvoir produire un workflow tel que :

```text
Observation:
Long-score 80–90 setups
underperform in RANGE regime.

AI Hypothesis:
Increase threshold to 88
when regime = RANGE.

Evidence:
1,842 historical setups.

Experiment:
Current threshold 80
vs
candidate threshold 88.

Out-of-sample result:
Expectancy:
+0.08R → +0.19R

Trade count:
-24%

Drawdown:
-11.2R → -8.7R

Status:
SUPPORTED

AI Recommendation:
Test candidate in SHADOW.

Governance:
APPROVED_FOR_TEST

Deployment:
SHADOW ONLY
```

À aucun moment l'IA ne doit pouvoir transformer seule cette observation en changement live.

---

# 210. Règle fondatrice

> **QuantLab doit apprendre automatiquement plus vite qu'un humain, sans acquérir automatiquement plus d'autorité qu'un humain.**

L'AI and Learning Engine est donc le moteur d'amélioration du système, pas son souverain.

La boucle recherchée est :

```text
MORE DATA
→ BETTER KNOWLEDGE
→ BETTER EXPERIMENTS
→ BETTER SYSTEM
```

et non :

```text
MORE AI
→ MORE AUTONOMY
→ HOPE FOR THE BEST
```

---

# 211. Statut

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
- `14-Knowledge-Engine.md`
- `16-Governance-Engine.md`
- `17-AI-Development-Protocol.md`
- `18-Testing-Strategy.md`
- `19-Deployment-Guide.md`
- `20-Engineering-Principles.md`
- `21-Experiment-Registry.md`
- `22-API-Specification.md`
- `23-Database-Schema.md`
- `24-Security.md`
- `25-Roadmap.md`

**Prochain document : `16-Governance-Engine.md`**
