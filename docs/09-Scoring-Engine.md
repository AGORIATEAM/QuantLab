# 09 — Scoring Engine

**Projet : QuantLab**  
**Document : Scoring Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Scoring Engine est la couche chargée de transformer les observations produites par les moteurs analytiques de QuantLab en scores normalisés, explicables, comparables et versionnés.

Il constitue l'interface entre :

```text
Analyse du marché
```

et :

```text
Décision
```

Son rôle n'est pas d'exécuter un trade.

Son rôle est de répondre à une question plus précise :

> **À quel point les conditions actuellement observées correspondent-elles aux conditions recherchées par une stratégie donnée ?**

Le moteur doit notamment agréger :

- contexte de marché ;
- structure ;
- Volume Profile ;
- Smart Money Concepts ;
- momentum ;
- volatilité ;
- liquidité ;
- contexte multi-timeframe ;
- qualité des données ;
- qualité et fraîcheur des signaux.

La sortie principale est un objet :

```text
ScoreContext
```

destiné au Decision Engine.

---

# 2. Principe fondamental

Le scoring ne doit pas être confondu avec une probabilité.

Exemple :

```text
score = 82/100
```

ne signifie pas automatiquement :

```text
82% de probabilité de gain
```

sauf si une calibration statistique rigoureuse démontre cette relation.

Par défaut :

> **Un score mesure la conformité d'un contexte à un ensemble de critères.**

Une probabilité estimée constitue un objet différent.

---

# 3. Responsabilités

Le Scoring Engine doit :

1. recevoir les features des moteurs analytiques ;
2. vérifier leur disponibilité ;
3. normaliser les valeurs ;
4. appliquer les règles de scoring ;
5. calculer des sous-scores ;
6. calculer les scores long et short ;
7. intégrer les pénalités ;
8. intégrer la qualité des données ;
9. gérer les features manquantes ;
10. calculer un niveau de confiance ;
11. expliquer la composition du score ;
12. versionner les règles ;
13. publier les changements significatifs ;
14. conserver les scores pour la recherche ;
15. fournir une sortie stable au Decision Engine.

---

# 4. Hors périmètre

Le moteur ne doit pas :

- envoyer d'ordre ;
- déterminer le position sizing final ;
- contourner le Risk Engine ;
- décider qu'un score élevé doit obligatoirement être tradé ;
- apprendre directement en production ;
- modifier ses pondérations sans protocole expérimental ;
- transformer arbitrairement un score en probabilité.

---

# 5. Architecture

```text
Market Analysis Engine ──────┐
Market Structure Engine ─────┤
Volume Profile Engine ───────┤
SMC Engine ──────────────────┤
Data Quality ────────────────┤
                             ▼
                    Feature Normalizer
                             │
                             ▼
                      Scoring Engine
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
              Long Score           Short Score
                  │                     │
                  └──────────┬──────────┘
                             ▼
                       ScoreContext
                             │
                             ▼
                       Decision Engine
```

---

# 6. Entrées

Le moteur reçoit des features standardisées.

Exemples :

```text
market_regime
trend_score
momentum_score
volatility_state

structure_score
bos_quality
choch_state
timeframe_alignment

distance_to_poc
distance_to_vah
distance_to_val
profile_stability

liquidity_sweep
fvg_quality
order_block_quality
displacement_score

data_quality
```

Toutes les entrées doivent posséder une provenance identifiable.

---

# 7. Feature Contract

Chaque feature utilisée doit respecter un contrat.

Exemple :

```yaml
feature:
  name: bullish_structure_score
  source: market_structure_engine
  version: 1.0
  type: float
  range: [-1, 1]
  timestamp: ...
  available_at: ...
  confidence: 0.91
```

Le Scoring Engine ne doit pas consommer silencieusement des valeurs dont la version est inconnue.

---

# 8. Feature Registry

Toutes les features admissibles doivent être enregistrées.

Champs :

```text
feature_id
feature_name
source_engine
feature_version
description
data_type
expected_range
normalization_method
status
```

États possibles :

```text
EXPERIMENTAL
VALIDATED
DEPRECATED
DISABLED
```

---

# 9. ScoreContext

Structure conceptuelle :

```python
ScoreContext:
    score_id
    symbol
    timestamp
    strategy_id

    long_score
    short_score

    market_score
    structure_score
    volume_profile_score
    smc_score
    momentum_score
    liquidity_score

    penalties
    bonuses

    data_quality
    confidence

    reason_codes
    feature_contributions

    scoring_version
```

---

# 10. Scores séparés Long / Short

Le moteur doit éviter un score unique ambigu.

Il doit pouvoir produire :

```text
long_score
short_score
```

Exemple :

```text
long_score = 78
short_score = 24
```

ou :

```text
long_score = 42
short_score = 46
```

Le second cas représente une absence de conviction claire.

---

# 11. Échelle standard

Une échelle recommandée :

```text
0 → 100
```

où :

```text
0   = aucune conformité
50  = contexte moyen / ambigu
100 = conformité maximale aux critères
```

L'interprétation exacte dépend de la stratégie.

---

# 12. Sous-scores

Le score global doit être décomposable.

Exemple :

```text
Market Context Score
Structure Score
Volume Profile Score
SMC Score
Momentum Score
Liquidity Score
Timing Score
```

Cela permet de comprendre pourquoi un score est élevé ou faible.

---

# 13. Exemple

```yaml
long_score: 81

components:
  market_context: 16/20
  structure: 19/20
  volume_profile: 12/15
  smc: 14/20
  momentum: 10/10
  liquidity: 7/10
  timing: 3/5
```

Le total reste entièrement explicable.

---

# 14. Weighted Scoring

Forme générale :

```text
Score =
Σ(weight_i × feature_i)
```

avec :

```text
Σ weights = 1
```

après normalisation.

---

# 15. Exemple de pondération

Illustratif uniquement :

```text
Market Context    20%
Structure         25%
Volume Profile    15%
SMC               20%
Momentum          10%
Liquidity         10%
```

Ces poids ne doivent pas être choisis parce qu'ils « semblent logiques ».

Ils doivent être testés.

---

# 16. Normalisation

Les moteurs peuvent produire des échelles différentes.

Exemples :

```text
structure_score = [-100,100]
momentum_score = [-1,1]
confidence = [0,1]
distance = ATR multiples
```

Le Scoring Engine doit les transformer dans une représentation cohérente.

---

# 17. Normalisation Min-Max

Formule :

```text
normalized =
(x - min)
/
(max - min)
```

Cette méthode nécessite des bornes fiables.

---

# 18. Z-Score

Pour certaines features :

```text
z =
(x - mean)
/
std
```

Attention :

- distributions non stationnaires ;
- outliers ;
- dépendance à la fenêtre historique.

---

# 19. Percentile

Une approche robuste peut utiliser :

```text
historical_percentile
```

Exemple :

```text
current volume = 92nd percentile
```

Le percentile est souvent plus comparable entre actifs.

---

# 20. Clipping

Les valeurs extrêmes doivent pouvoir être limitées.

Exemple :

```text
z-score clipped to [-3,3]
```

Cela évite qu'un outlier domine entièrement le score.

---

# 21. Directionnalité des features

Chaque feature doit préciser son impact.

Exemple :

```text
bullish_structure_score
→ positive for LONG
→ negative for SHORT
```

Mais certaines features ne sont pas symétriques.

Le système ne doit pas supposer automatiquement :

```text
short_score = 100 - long_score
```

---

# 22. Features non directionnelles

Exemple :

```text
data_quality
liquidity_quality
execution_conditions
```

peuvent améliorer ou dégrader les deux directions simultanément.

---

# 23. Positive Contributions

Exemple long :

```text
bullish HTF alignment
+15
```

```text
sell-side liquidity sweep
+8
```

```text
bullish BOS
+12
```

---

# 24. Penalties

Exemples :

```text
high timeframe conflict
-15
```

```text
low data quality
-25
```

```text
extreme volatility
-10
```

```text
poor liquidity
-20
```

---

# 25. Hard Filters vs Penalties

Distinction essentielle.

### Penalty

Le score est réduit.

### Hard Filter

Le setup devient inéligible.

Exemple :

```text
data_quality < minimum
→ HARD REJECT
```

Les hard filters doivent rester rares et explicites.

---

# 26. Scoring vs Decision

Le Scoring Engine peut produire :

```text
long_score = 92
```

mais le Decision Engine peut répondre :

```text
NO_TRADE
```

pour une raison telle que :

```text
risk limit reached
```

ou :

```text
strategy disabled
```

La séparation doit être stricte.

---

# 27. Missing Features

Une feature peut être absente.

Exemple :

```text
order book unavailable
```

Le moteur ne doit pas automatiquement transformer cela en :

```text
score = 0
```

si l'absence n'indique pas une condition négative.

---

# 28. Missing Data Policy

Trois stratégies :

```text
IGNORE_AND_RENORMALIZE
NEUTRAL_VALUE
REJECT_SCORE
```

La politique doit être définie par feature.

---

# 29. Re-normalisation

Si une composante facultative manque :

```text
available weights
```

peuvent être renormalisés.

Exemple :

```text
total configured weight = 1.0
available = 0.9

effective weights =
weights / 0.9
```

La confiance doit toutefois être réduite.

---

# 30. Confidence Score

Le score doit être accompagné de :

```text
score_confidence ∈ [0,1]
```

Ce score peut dépendre de :

- qualité des données ;
- nombre de features disponibles ;
- confiance des moteurs sources ;
- cohérence multi-timeframe ;
- stabilité du modèle.

---

# 31. Confidence n'est pas Edge

Un score peut être calculé avec forte confiance et rester sans valeur prédictive.

Exemple :

```text
confidence = 0.95
```

signifie :

```text
nous sommes très sûrs du calcul
```

et non :

```text
nous sommes très sûrs que le trade gagnera
```

---

# 32. Score Thresholds

Le Decision Engine peut utiliser des seuils.

Exemple :

```text
score < 60
→ reject

60–74
→ weak candidate

75–84
→ candidate

85+
→ strong candidate
```

Ces seuils doivent être validés expérimentalement.

---

# 33. Pas de seuil magique

Un seuil de :

```text
80
```

n'est pas meilleur parce qu'il semble propre.

QuantLab doit étudier :

```text
expectancy by score bucket
```

---

# 34. Score Buckets

Exemple :

```text
0–49
50–59
60–69
70–79
80–89
90–100
```

Pour chaque bucket :

```text
trade_count
win_rate
expectancy
profit_factor
MFE
MAE
```

---

# 35. Calibration

Si les scores élevés ne produisent pas de meilleurs résultats que les scores faibles, le scoring est mauvais.

Le système doit vérifier la monotonie.

Idéalement :

```text
score ↑
→
expected edge ↑
```

Cette relation doit être mesurée hors échantillon.

---

# 36. Calibration Probabiliste future

Une couche distincte pourra transformer des features en :

```text
P(target before stop | context)
```

via :

- logistic regression ;
- isotonic regression ;
- Platt scaling ;
- modèles ML calibrés.

Cette probabilité ne doit pas être confondue avec le score heuristique initial.

---

# 37. Rule-Based Baseline

La V1 doit commencer par un scoring déterministe simple.

Pourquoi ?

Parce qu'il est :

- interprétable ;
- testable ;
- auditable ;
- facile à comparer.

Le ML ne doit arriver qu'après une baseline solide.

---

# 38. Strategy-Specific Scoring

Le score doit dépendre de la stratégie.

Exemple :

```text
Trend Following Strategy
```

peut valoriser :

```text
trend alignment
BOS
momentum
```

alors que :

```text
Mean Reversion Strategy
```

peut valoriser :

```text
range regime
extreme deviation
return toward value
```

Il ne doit donc pas exister un unique score universel pour toutes les stratégies.

---

# 39. Strategy Score Profile

Exemple :

```yaml
strategy_id: trend_following_v1

weights:
  market_regime: 0.20
  structure: 0.30
  momentum: 0.20
  volume_profile: 0.10
  smc: 0.10
  liquidity: 0.10
```

---

# 40. Score Versioning

Chaque configuration doit posséder :

```text
scoring_version
```

Exemple :

```text
trend_following_score_v1.2.0
```

Un backtest doit toujours enregistrer cette version.

---

# 41. Immutable Historical Scores

Un score historique ne doit pas changer silencieusement lorsqu'une nouvelle version est déployée.

Il faut distinguer :

```text
score calculated with v1
```

et :

```text
recomputed score with v2
```

---

# 42. Feature Contributions

Chaque score doit enregistrer la contribution individuelle.

Exemple :

```yaml
contributions:
  bullish_structure: +18
  htf_alignment: +12
  bullish_fvg: +6
  sell_side_sweep: +8
  low_liquidity: -10
```

---

# 43. Reason Codes

Exemples :

```text
SCORE_BULLISH_STRUCTURE
SCORE_BEARISH_STRUCTURE
SCORE_HTF_ALIGNMENT
SCORE_HTF_CONFLICT
SCORE_FVG_CONFLUENCE
SCORE_LIQUIDITY_SWEEP
SCORE_LOW_DATA_QUALITY
SCORE_HIGH_VOLATILITY
SCORE_LOW_LIQUIDITY
```

---

# 44. Explainability

Le moteur doit pouvoir produire :

```text
LONG SCORE = 84
```

avec explication :

```text
+ Strong bullish structure
+ Higher timeframe alignment
+ Sell-side sweep
+ Bullish displacement
- High volatility
- Moderate liquidity
```

Pas seulement un nombre sorti d'une boîte noire, cette grande tradition humaine consistant à ajouter un chiffre à quelque chose pour lui donner l'air scientifique.

---

# 45. Feature Freshness

Les features vieillissent.

Exemple :

```text
BOS 2 minutes ago
```

n'est pas forcément équivalent à :

```text
BOS 12 hours ago
```

Le moteur doit pouvoir intégrer :

```text
feature_age
```

---

# 46. Time Decay

Forme possible :

```text
effective_weight =
base_weight × decay(age)
```

Exemple exponentiel :

```text
decay(age) = exp(-lambda × age)
```

Le decay doit être testé.

---

# 47. Event Persistence

Certaines features persistent jusqu'à invalidation.

Exemple :

```text
4H bullish structure
```

D'autres sont transitoires :

```text
recent liquidity sweep
```

Chaque feature doit définir sa politique de fraîcheur.

---

# 48. Multi-Timeframe Scoring

Exemple :

```text
4H structure
1H regime
15m setup
5m trigger
```

Le score peut intégrer plusieurs horizons.

---

# 49. Timeframe Weights

Exemple configurable :

```text
4H = 35%
1H = 30%
15m = 20%
5m = 15%
```

Ces poids doivent dépendre de la stratégie.

---

# 50. Timeframe Conflict Penalty

Exemple :

```text
4H bearish
15m bullish setup
```

Le moteur peut appliquer :

```text
HTF_CONFLICT_PENALTY
```

si la stratégie concernée exige l'alignement.

---

# 51. Pullback Context

Un conflit apparent peut être cohérent.

Exemple :

```text
4H bullish
1H bullish
15m bearish
```

peut représenter :

```text
bullish HTF + bearish pullback
```

Le scoring doit pouvoir distinguer cette situation d'un véritable conflit structurel.

---

# 52. Market Regime Gating

Certaines stratégies peuvent recevoir une pénalité forte dans certains régimes.

Exemple :

```text
trend strategy
+
RANGING regime
→ score penalty
```

Cela doit être validé par les performances historiques.

---

# 53. Volatility Adjustment

La volatilité peut affecter le score.

Exemple :

```text
EXTREME_VOLATILITY
```

peut réduire la qualité d'un setup si la stratégie souffre historiquement dans ce contexte.

Mais ce comportement doit être strategy-specific.

---

# 54. Liquidity Adjustment

Une faible liquidité peut :

- réduire le score ;
- réduire la confiance ;
- déclencher un hard filter.

La politique dépend de l'instrument et de la stratégie.

---

# 55. Data Quality Penalty

Exemple :

```text
effective_score =
raw_score × data_quality
```

Une autre approche consiste à garder le score brut mais réduire :

```text
confidence
```

Les deux doivent être distingués.

---

# 56. Recommandation V1

Pour éviter de mélanger les concepts :

```text
raw_signal_score
```

doit mesurer le setup.

```text
confidence
```

doit mesurer la fiabilité des informations.

Puis le Decision Engine décide comment les combiner.

---

# 57. Raw Score

Exemple :

```text
raw_long_score = 87
```

---

# 58. Confidence

Exemple :

```text
confidence = 0.72
```

---

# 59. Adjusted Score

Une sortie facultative :

```text
adjusted_score =
raw_score × confidence
```

Exemple :

```text
87 × 0.72 = 62.64
```

Mais le système doit conserver les valeurs originales séparément.

---

# 60. Symmetry Testing

Le scoring long et short doit être testé pour détecter des biais involontaires.

Exemple :

si le score produit beaucoup plus de longs que de shorts, il faut déterminer si cela vient :

- du marché ;
- de la stratégie ;
- d'un bug ;
- d'une asymétrie des règles.

---

# 61. Score Distribution

Monitoring :

```text
mean_score
median_score
score_std
score_percentiles
```

par :

- actif ;
- stratégie ;
- direction ;
- timeframe.

---

# 62. Score Saturation

Si presque tous les contextes produisent :

```text
80–100
```

le score est mal calibré.

Même problème si presque tout est :

```text
0–20
```

La distribution doit rester informative.

---

# 63. Feature Correlation

Plusieurs features peuvent mesurer la même chose.

Exemple :

```text
trend score
EMA alignment
market structure
momentum
```

peuvent être fortement corrélés.

Les additionner naïvement peut compter plusieurs fois la même information.

---

# 64. Double Counting

Le moteur doit documenter les dépendances entre features.

Exemple :

```text
Order Block quality
```

peut déjà intégrer :

```text
BOS quality
```

Si le scoring ajoute ensuite BOS une seconde fois, le même phénomène peut être surpondéré.

---

# 65. Correlation Matrix

Le Knowledge Engine doit pouvoir calculer une matrice de corrélation des features.

Les features très redondantes doivent être étudiées.

---

# 66. Ablation Testing

Exemple :

```text
Full Score
```

vs :

```text
Score without SMC
```

vs :

```text
Score without Volume Profile
```

vs :

```text
Score without Momentum
```

Cela permet de mesurer la contribution réelle de chaque famille.

---

# 67. Marginal Contribution

Question centrale :

> Cette feature améliore-t-elle la capacité du score à distinguer les bons et mauvais contextes ?

Une feature séduisante mais sans contribution marginale doit pouvoir être supprimée.

---

# 68. Overfitting Risk

Le Scoring Engine est une zone majeure de risque d'overfitting.

Exemple :

```text
25 features
×
10 poids possibles
×
10 seuils
```

produit un espace de recherche énorme.

Une optimisation naïve trouvera presque forcément une configuration magnifique sur le passé et inutile ensuite.

---

# 69. Weight Optimization

Les poids peuvent être optimisés plus tard, mais avec :

- train set ;
- validation set ;
- test set ;
- walk-forward ;
- contraintes de complexité ;
- stabilité des paramètres.

---

# 70. Simplicity Penalty

Le processus de recherche doit favoriser les modèles simples lorsque leurs performances sont comparables.

Exemple :

```text
5-feature model
Sharpe 1.4
```

contre :

```text
38-feature model
Sharpe 1.43
```

Le premier peut être préférable.

Trois centièmes de Sharpe ne justifient pas forcément trente-trois nouvelles façons de casser le système.

---

# 71. Monotonicity Test

Le score doit être évalué par déciles.

Exemple :

```text
Score Decile 1 → expectancy -0.2R
Score Decile 5 → expectancy +0.05R
Score Decile 10 → expectancy +0.35R
```

Une progression stable serait encourageante.

---

# 72. Statistical Significance

Chaque bucket doit disposer d'un nombre suffisant d'observations.

Un score de 95 ayant produit trois trades gagnants ne constitue pas une preuve.

Le moteur de recherche doit conserver :

```text
sample_size
confidence_interval
```

---

# 73. Expected Value Mapping

À terme, le Knowledge Engine peut construire :

```text
E[R | score, regime, strategy]
```

Exemple :

```text
Score 80–90
Trending regime
Strategy A
→ historical expectancy = +0.24R
```

---

# 74. Strategy-Specific Calibration

Un score de 80 pour :

```text
Trend Strategy
```

n'a aucune raison d'avoir la même signification qu'un score de 80 pour :

```text
Mean Reversion Strategy
```

Les calibrations doivent rester séparées.

---

# 75. Asset-Specific Analysis

Le scoring peut être commun, mais les performances doivent être étudiées par actif.

Exemple :

```text
BTC
ETH
XAU/USD
```

Si une feature ne fonctionne que sur un actif, cette dépendance doit être visible.

---

# 76. Cross-Asset Robustness

Une feature particulièrement intéressante est celle qui reste informative sur plusieurs actifs et périodes.

Cela ne signifie pas qu'un modèle doit être identique partout, mais une robustesse transversale augmente la crédibilité d'un signal.

---

# 77. Score Event

Lorsque le score est calculé :

```text
SCORE_UPDATED
```

Exemple :

```json
{
  "symbol": "BTC-USDT",
  "strategy_id": "trend_v1",
  "long_score": 82,
  "short_score": 21,
  "confidence": 0.88,
  "scoring_version": "1.0.0"
}
```

---

# 78. Threshold Cross Event

Le moteur peut publier :

```text
SCORE_THRESHOLD_CROSSED
```

Exemple :

```text
long score:
74 → 81
```

Le Decision Engine décide ensuite si cela mérite une action.

---

# 79. Score Persistence

Chaque score important doit pouvoir être stocké.

Champs :

```text
score_id
timestamp
symbol
strategy_id
long_score
short_score
confidence
scoring_version
feature_snapshot_id
```

---

# 80. Feature Snapshot

Il est recommandé de conserver la référence exacte des features ayant produit un score.

Cela permet de reconstruire :

```text
Pourquoi score = 84 ?
```

plusieurs mois après.

---

# 81. Snapshot Hash

Un hash peut identifier l'ensemble des inputs.

Exemple :

```text
feature_snapshot_hash
```

Il facilite l'audit et la reproductibilité.

---

# 82. Determinism

Avec :

```text
same feature snapshot
same scoring configuration
same scoring version
```

le score doit être strictement identique.

---

# 83. Configuration

Exemple :

```yaml
scoring:

  strategy_id: trend_following_v1
  version: 1.0.0

  scale:
    min: 0
    max: 100

  components:
    market_context:
      weight: 0.20

    structure:
      weight: 0.25

    volume_profile:
      weight: 0.15

    smc:
      weight: 0.20

    momentum:
      weight: 0.10

    liquidity:
      weight: 0.10

  missing_feature_policy:
    optional: renormalize
    required: reject

  confidence:
    enabled: true
```

---

# 84. Validation de configuration

Le moteur doit vérifier :

```text
weights sum
valid ranges
known feature IDs
compatible versions
duplicate features
```

Une configuration invalide doit empêcher le moteur de démarrer.

---

# 85. Schema Validation

Les fichiers de scoring doivent respecter un schéma formel.

Exemple :

```text
JSON Schema
```

ou validation Pydantic.

Les erreurs de configuration doivent être détectées avant production.

---

# 86. Hot Reload

En production, le changement dynamique des poids doit être évité en V1.

Une nouvelle configuration doit suivre :

```text
experiment
↓
validation
↓
approval
↓
version
↓
deployment
```

---

# 87. Testing unitaire

Tester :

- normalisation ;
- pondération ;
- score long ;
- score short ;
- penalties ;
- hard filters ;
- missing features ;
- confidence ;
- clipping ;
- reason codes.

---

# 88. Synthetic Tests

Exemple :

```text
all bullish features = maximum
```

Résultat attendu :

```text
long_score proche de 100
```

Autre :

```text
all bearish features = maximum
```

Résultat :

```text
short_score proche de 100
```

---

# 89. Neutral Test

Inputs neutres :

```text
no trend
range
no SMC event
neutral momentum
```

Le score doit produire un résultat cohérent avec la stratégie, pas un extrême artificiel.

---

# 90. Missing Feature Test

Retirer :

```text
Volume Profile
```

et vérifier que :

- la politique configurée est respectée ;
- la confiance baisse ;
- aucune erreur silencieuse ne survient.

---

# 91. Regression Tests

Une configuration donnée doit produire les mêmes scores sur un dataset de référence après toute modification logicielle non liée.

Toute différence doit être expliquée.

---

# 92. Replay Testing

Le scoring doit être recalculé événement par événement.

Il ne doit utiliser que les features dont :

```text
available_at <= decision_time
```

---

# 93. Look-Ahead Protection

Le moteur doit refuser une feature dont :

```text
available_at > score_timestamp
```

Ce contrôle doit idéalement être centralisé et automatique.

---

# 94. Integration Tests

Pipeline :

```text
Data Engine
↓
Market Analysis
↓
Market Structure
↓
Volume Profile
↓
SMC
↓
Scoring
```

Le résultat doit être déterministe.

---

# 95. Backtest Integration

Le backtest doit stocker :

```text
score at decision time
```

et non recalculer après coup avec des informations futures.

---

# 96. Performance Metrics

Pour chaque version de scoring :

```text
signal_count
score_distribution
expectancy_by_bucket
win_rate_by_bucket
profit_factor_by_bucket
MFE_by_bucket
MAE_by_bucket
```

---

# 97. Stability Metrics

Comparer les performances :

```text
by year
by quarter
by asset
by regime
by volatility
by session
```

Un score utile doit montrer une stabilité raisonnable.

---

# 98. Drift Detection

Le Monitoring Engine peut surveiller :

```text
score distribution drift
feature distribution drift
bucket performance drift
```

Exemple :

si le score moyen passe brutalement :

```text
55 → 82
```

sans raison connue, une anomalie peut exister.

---

# 99. Feature Drift

Exemple :

```text
FVG frequency
```

peut changer après :

- changement de volatilité ;
- changement de marché ;
- bug de données ;
- nouvelle version de calcul.

Le scoring doit être surveillé en conséquence.

---

# 100. Interaction avec Decision Engine

Le Scoring Engine fournit :

```text
ScoreContext
```

Le Decision Engine applique ensuite :

- seuils ;
- règles de stratégie ;
- restrictions ;
- cooldowns ;
- état du portefeuille ;
- validation du Risk Engine.

Le scoring ne doit jamais contourner cette couche.

---

# 101. Interaction avec Risk Engine

Le Risk Engine peut recevoir :

```text
score
confidence
```

pour éventuellement adapter le risque.

Exemple futur :

```text
high confidence
→ risk multiplier
```

Mais une telle relation doit être validée avec une prudence extrême.

Un score élevé ne doit jamais permettre de dépasser les limites absolues de risque.

---

# 102. Interaction avec Execution Engine

Le Scoring Engine ne communique idéalement pas directement avec l'Execution Engine.

Flux recommandé :

```text
Scoring
↓
Decision
↓
Risk
↓
Execution
```

---

# 103. Interaction avec Knowledge Engine

Le Knowledge Engine doit conserver :

```text
feature snapshot
score
decision
trade result
market regime
```

Cela permettra de mesurer l'efficacité réelle du scoring.

---

# 104. Interaction avec AI & Learning Engine

L'AI & Learning Engine pourra :

- proposer de nouvelles features ;
- détecter des interactions ;
- optimiser des pondérations ;
- identifier des features redondantes ;
- proposer des modèles alternatifs.

Toute proposition doit être traitée comme une expérience.

---

# 105. ML Scoring futur

Une version future pourra remplacer ou compléter :

```text
weighted rule score
```

par un modèle :

```text
features
↓
ML model
↓
predicted edge
```

Mais la baseline déterministe doit rester disponible.

---

# 106. Champion / Challenger

Architecture recommandée :

```text
Champion Model
= version actuellement validée

Challenger Model
= nouvelle version testée
```

Le challenger ne remplace le champion qu'après validation.

---

# 107. Shadow Mode

Un nouveau scoring peut tourner en :

```text
SHADOW
```

Il produit des scores mais n'influence aucune décision réelle.

Cela permet de comparer :

```text
Champion
vs
Challenger
```

en conditions réelles.

---

# 108. Governance

Toute nouvelle version doit enregistrer :

```text
author
reason
experiment_id
validation_results
approval
deployment_date
```

Le détail sera défini dans `16-Governance-Engine.md`.

---

# 109. Monitoring

Métriques opérationnelles :

```text
scores_generated
score_latency
missing_feature_rate
rejected_scores
confidence_distribution
long_score_distribution
short_score_distribution
threshold_cross_count
error_rate
```

---

# 110. Alertes

Alertes potentielles :

```text
SCORING_ENGINE_DOWN
FEATURE_SOURCE_MISSING
SCORE_DISTRIBUTION_ANOMALY
CONFIGURATION_INVALID
UNKNOWN_FEATURE_VERSION
LATENCY_TOO_HIGH
```

---

# 111. Latence

Le scoring doit être suffisamment rapide pour ne pas devenir un goulot d'étranglement.

Mesurer :

```text
p50 latency
p95 latency
p99 latency
```

par stratégie et actif.

---

# 112. Audit

Pour toute décision, QuantLab doit pouvoir reconstruire :

```text
Market Data
↓
Features
↓
Feature Versions
↓
Scoring Configuration
↓
Feature Contributions
↓
Final Score
```

C'est indispensable pour comprendre les erreurs.

---

# 113. Priorités V1

Implémenter :

- Feature Registry ;
- normalisation ;
- scoring pondéré ;
- long / short séparés ;
- sous-scores ;
- penalties ;
- hard filters ;
- missing feature policies ;
- confidence ;
- reason codes ;
- feature contributions ;
- persistence ;
- deterministic replay.

---

# 114. Priorités V2

Ajouter :

- feature decay ;
- multi-timeframe scoring avancé ;
- score calibration ;
- score bucket analytics ;
- drift monitoring ;
- advanced confluence.

---

# 115. Priorités V3

Ajouter :

- weight optimization contrôlée ;
- automated ablation ;
- feature selection ;
- probabilistic calibration ;
- champion/challenger.

---

# 116. Priorités V4

Ajouter :

- ML scoring ;
- adaptive models ;
- contextual weighting ;
- online monitoring avancé ;
- learning proposals sous gouvernance.

---

# 117. Critères d'acceptation V1

La V1 est valide lorsque :

- les features ont des contrats explicites ;
- les scores sont déterministes ;
- long et short sont séparés ;
- les sous-scores sont visibles ;
- chaque contribution est explicable ;
- les données manquantes sont gérées explicitement ;
- la confiance est distincte du score ;
- aucun look-ahead n'est possible ;
- les configurations sont versionnées ;
- les scores peuvent être reconstruits ;
- les tests unitaires passent ;
- les tests de replay passent ;
- les scores sont persistables.

---

# 118. Risques principaux

## Double Counting

Plusieurs features peuvent représenter la même information.

## Overfitting

Trop de poids et de seuils permettent de fabriquer artificiellement de bons backtests.

## Score Inflation

Trop de bonus peuvent produire des scores systématiquement élevés.

## False Precision

Un score comme :

```text
83.742
```

peut donner une illusion de précision inexistante.

## Calibration Confusion

Un score ne doit pas être présenté comme une probabilité sans preuve.

---

# 119. Principe de simplicité

La première version doit privilégier :

```text
few features
clear rules
explicit weights
strong logging
```

plutôt que :

```text
hundreds of indicators
complex optimization
opaque interactions
```

Le moteur doit devenir plus complexe uniquement si les données justifient cette complexité.

---

# 120. Architecture finale

```text
Market Context ───────────┐
Market Structure ─────────┤
Volume Profile ───────────┤
SMC Context ──────────────┤
Momentum ─────────────────┤
Liquidity ────────────────┤
Data Quality ─────────────┤
                          ▼
                 Feature Normalization
                          ↓
                   Component Scores
                          ↓
              Bonuses / Penalties / Gates
                          ↓
                  LONG / SHORT SCORE
                          ↓
                      Confidence
                          ↓
                    ScoreContext
                          ↓
                    Decision Engine
```

---

# 121. Résultat attendu

Le Scoring Engine doit permettre à QuantLab de passer de :

```text
« plusieurs éléments semblent intéressants »
```

à :

```text
« voici exactement les facteurs observés,
leur poids,
leur contribution,
leur fraîcheur,
leur confiance,
et le score résultant »
```

Chaque score doit être traçable et reproductible.

---

# 122. Règle fondatrice

> **Le Scoring Engine ne doit pas fabriquer de conviction. Il doit mesurer, de manière transparente, la force des éléments réellement observés.**

Un score complexe qui ne produit pas une meilleure séparation statistique des opportunités qu'une baseline simple doit être rejeté.

Le but n'est pas de créer le score le plus sophistiqué.

Le but est de créer le score le plus utile hors échantillon.

---

# 123. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `03-Data-Engine.md`
- `05-Market-Analysis-Engine.md`
- `06-Market-Structure-Engine.md`
- `07-Volume-Profile-Engine.md`
- `08-Smart-Money-Concepts-Engine.md`
- `10-Decision-Engine.md`
- `11-Risk-Engine.md`
- `13-Monitoring-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `16-Governance-Engine.md`
- `18-Testing-Strategy.md`
- `21-Experiment-Registry.md`
- `23-Database-Schema.md`

**Prochain document : `10-Decision-Engine.md`**
