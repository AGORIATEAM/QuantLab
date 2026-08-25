# 08 — Smart Money Concepts Engine

**Projet : QuantLab**  
**Document : Smart Money Concepts Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Smart Money Concepts Engine, ou SMC Engine, est responsable de transformer certains concepts couramment utilisés dans l'analyse dite « Smart Money Concepts » en objets algorithmiques précis, reproductibles, testables et versionnés.

Le moteur doit notamment pouvoir identifier et qualifier :

- zones de liquidité ;
- Equal Highs / Equal Lows contextualisés ;
- liquidity sweeps ;
- liquidity grabs ;
- displacement ;
- Fair Value Gaps ;
- imbalances ;
- Order Blocks ;
- Breaker Blocks ;
- mitigation events ;
- premium / discount ;
- confluences entre structure, liquidité et inefficiences.

Le moteur ne doit jamais considérer ces concepts comme intrinsèquement prédictifs.

Sa fonction est :

```text
Détection
↓
Formalisation
↓
Mesure
↓
Transmission aux moteurs de scoring et de recherche
```

et non :

```text
Pattern SMC détecté
↓
Trade automatique
```

---

# 2. Principe scientifique

Les concepts SMC sont largement utilisés de manière discrétionnaire.

Deux traders peuvent observer le même graphique et identifier :

```text
deux Order Blocks différents
trois Fair Value Gaps différents
plusieurs niveaux de liquidité
```

QuantLab doit éliminer cette ambiguïté.

Chaque concept utilisé doit disposer de :

- définition formelle ;
- paramètres ;
- conditions de validation ;
- conditions d'invalidation ;
- timestamp de disponibilité ;
- version d'algorithme ;
- score de qualité ;
- tests statistiques.

---

# 3. Règle fondamentale

Dans QuantLab :

> **Un concept SMC n'existe que s'il peut être défini de manière suffisamment précise pour qu'un ordinateur le détecte deux fois de la même façon sur les mêmes données.**

Si une notion ne peut pas satisfaire cette règle, elle reste une hypothèse de recherche et ne doit pas entrer dans la logique de production.

---

# 4. Responsabilités

Le SMC Engine doit :

1. recevoir les données de marché validées ;
2. recevoir la structure de marché ;
3. recevoir éventuellement le contexte de marché ;
4. détecter les zones de liquidité ;
5. détecter les sweeps ;
6. détecter les Fair Value Gaps ;
7. détecter les displacements ;
8. détecter les Order Blocks selon une définition versionnée ;
9. détecter les Breaker Blocks ;
10. suivre les mitigations ;
11. calculer premium / discount ;
12. produire des scores de qualité ;
13. publier des événements ;
14. stocker les objets détectés ;
15. alimenter le Scoring Engine ;
16. alimenter le Knowledge Engine pour validation statistique.

---

# 5. Hors périmètre

Le moteur ne doit pas :

- exécuter un ordre ;
- dimensionner une position ;
- fixer le risque global ;
- décider qu'un Order Block est une entrée ;
- supposer qu'un sweep implique un retournement ;
- considérer un FVG comme devant obligatoirement être comblé ;
- modifier automatiquement les règles SMC en production.

---

# 6. Dépendances principales

Le moteur dépend principalement de :

```text
Data Engine
↓
Market Analysis Engine
↓
Market Structure Engine
↓
SMC Engine
```

Il peut également utiliser les sorties du Volume Profile Engine.

---

# 7. Entrées

Entrées minimales :

```text
OHLCV
confirmed swings
market structure
BOS events
CHOCH events
```

Entrées facultatives :

```text
volume
trades
order book
volume profile
volatility
market regime
sessions
open interest
liquidations
```

---

# 8. Sortie principale

Objet conceptuel :

```python
SMCContext:
    symbol
    timeframe
    timestamp

    liquidity_zones
    liquidity_sweeps

    fair_value_gaps
    active_fvgs

    order_blocks
    active_order_blocks

    breaker_blocks

    premium_discount_state

    displacement_state

    smc_score
    confidence

    algorithm_version
```

---

# 9. Liquidity Concept

Le moteur ne peut pas observer directement « l'intention institutionnelle ».

Il peut uniquement identifier des structures où des ordres sont plausiblement concentrés.

Le terme :

```text
liquidity zone
```

doit donc signifier :

> Zone de prix définie algorithmiquement présentant des caractéristiques associées à une concentration potentielle d'ordres.

Cette distinction évite de transformer une interprétation narrative en fait.

---

# 10. Sources potentielles de liquidité

Le moteur peut considérer comme candidats :

- Equal Highs ;
- Equal Lows ;
- swing highs ;
- swing lows ;
- previous day high ;
- previous day low ;
- previous week high ;
- previous week low ;
- session highs ;
- session lows ;
- range highs ;
- range lows ;
- niveaux structurels significatifs.

---

# 11. Buy-Side Liquidity

Zone potentielle située au-dessus d'un niveau structurel.

Exemples :

```text
equal highs
swing high
previous day high
range high
```

Classification :

```text
BUY_SIDE_LIQUIDITY
```

Cela ne signifie pas que des stops sont réellement observés.

Il s'agit d'une hypothèse structurelle.

---

# 12. Sell-Side Liquidity

Zone potentielle située sous :

```text
equal lows
swing low
previous day low
range low
```

Classification :

```text
SELL_SIDE_LIQUIDITY
```

---

# 13. Liquidity Zone

Structure possible :

```python
LiquidityZone:
    zone_id
    symbol
    timeframe

    side
    source_type

    price_low
    price_high
    reference_price

    created_at
    available_at

    touch_count
    swept

    significance
    confidence
```

---

# 14. Tolérance des Equal Highs / Lows

Les niveaux ne doivent pas être exactement identiques.

Exemple :

```text
abs(high_a - high_b)
<= ATR × tolerance
```

ou :

```text
relative_distance <= threshold
```

Le paramètre doit être configurable.

---

# 15. Liquidity Significance Score

Une zone peut recevoir :

```text
liquidity_significance ∈ [0,1]
```

Features possibles :

- nombre de touches ;
- timeframe ;
- ancienneté ;
- swing significance ;
- volume ;
- confluence structurelle ;
- distance entre niveaux ;
- réaction historique.

---

# 16. Liquidity Sweep

Définition initiale d'un sweep buy-side :

```text
price trades above liquidity zone
AND
returns below zone
```

Exemple :

```text
liquidity_high = 100

high = 102
close = 99
```

Résultat potentiel :

```text
BUY_SIDE_LIQUIDITY_SWEEP
```

---

# 17. Sell-Side Sweep

Inverse :

```text
price trades below liquidity zone
AND
returns above zone
```

Résultat :

```text
SELL_SIDE_LIQUIDITY_SWEEP
```

---

# 18. Sweep vs Breakout

Le moteur doit distinguer :

```text
SWEEP
```

de :

```text
BREAKOUT
```

Exemple :

```text
wick beyond level
close back inside
→ sweep candidate
```

alors que :

```text
close beyond level
follow-through
→ breakout candidate
```

Les critères exacts doivent être testés.

---

# 19. Sweep Confirmation

Une confirmation peut nécessiter :

```text
penetration
+
close back through level
+
minimum wick ratio
```

Version plus stricte :

```text
sweep
+
opposite displacement
```

Les variantes doivent être enregistrées séparément dans l'Experiment Registry.

---

# 20. Sweep Depth

Feature :

```text
sweep_depth =
maximum_penetration / ATR
```

Cela permet de distinguer une micro-excursion d'une rupture importante.

---

# 21. Sweep Duration

Mesure :

```text
time_outside_zone
```

ou :

```text
bars_outside_zone
```

Cette information peut aider à distinguer sweep et breakout.

---

# 22. Liquidity Consumed

Après une rupture confirmée et acceptation au-delà d'une zone :

```text
liquidity_status = CONSUMED
```

Une zone consommée ne doit pas rester éternellement active.

---

# 23. Liquidity Zone Lifecycle

États possibles :

```text
CREATED
ACTIVE
TESTED
SWEPT
CONSUMED
INVALIDATED
EXPIRED
```

Chaque transition doit être enregistrée.

---

# 24. Fair Value Gap — FVG

Le FVG doit être défini algorithmiquement.

Version classique haussière sur trois bougies :

```text
high[candle_1] < low[candle_3]
```

avec une bougie intermédiaire créant un déplacement.

Zone :

```text
high[candle_1]
→
low[candle_3]
```

---

# 25. Bearish FVG

Définition :

```text
low[candle_1] > high[candle_3]
```

Zone :

```text
high[candle_3]
→
low[candle_1]
```

---

# 26. FVG Minimum Size

Les gaps minuscules peuvent être du bruit.

Condition possible :

```text
fvg_size >= ATR × minimum_fvg_size
```

ou :

```text
fvg_size / price >= threshold
```

---

# 27. FVG Structure

```python
FairValueGap:
    fvg_id
    symbol
    timeframe

    direction

    price_low
    price_high
    midpoint

    size
    normalized_size

    created_at
    available_at

    status
    fill_percentage

    quality_score
    confidence
```

---

# 28. FVG Lifecycle

États :

```text
CREATED
ACTIVE
PARTIALLY_FILLED
MITIGATED
FILLED
INVALIDATED
EXPIRED
```

---

# 29. FVG Fill Percentage

Exemple :

```text
fill_percentage =
penetration_into_gap
/
gap_size
```

Valeur :

```text
0 → untouched
0.5 → moitié remplie
1 → complètement rempli
```

---

# 30. Consequent Encroachment

Le midpoint d'un FVG peut être calculé :

```text
CE =
(fvg_high + fvg_low) / 2
```

Le moteur peut exposer cette feature.

Il ne doit pas supposer que le prix doit réagir à ce niveau.

---

# 31. FVG Quality Score

Features potentielles :

- taille normalisée ;
- displacement associé ;
- volume ;
- structure ;
- timeframe ;
- rapidité de création ;
- absence de chevauchement ;
- contexte de régime.

Exemple :

```text
fvg_quality ∈ [0,1]
```

---

# 32. FVG Overlap

Plusieurs FVG peuvent se chevaucher.

Le moteur doit pouvoir :

- les conserver séparément ;
- calculer une zone d'intersection ;
- éventuellement produire un cluster.

---

# 33. FVG Expiration

Un FVG ne doit pas nécessairement rester actif indéfiniment.

Méthodes possibles :

```text
expire after N bars
expire after full fill
expire after structural invalidation
never expire
```

Cette règle doit être configurable.

---

# 34. Imbalance

Le terme imbalance peut être utilisé comme catégorie plus générale.

Exemples :

```text
FVG
large directional candle
thin traded zone
order-flow imbalance
```

QuantLab doit éviter de mélanger ces concepts.

Chaque type doit posséder son propre identifiant.

---

# 35. Displacement

Définition algorithmique possible :

```text
large directional body
+
range > ATR × threshold
+
body_ratio > threshold
```

Exemple :

```text
DISPLACEMENT_UP
DISPLACEMENT_DOWN
```

---

# 36. Displacement Score

Features :

```text
range / ATR
body / range
volume / average_volume
close_location
follow_through
```

Score :

```text
displacement_score ∈ [0,1]
```

---

# 37. Order Block — problème de définition

Le terme Order Block est particulièrement ambigu.

QuantLab ne doit pas utiliser une définition vague comme :

> « dernière bougie opposée avant un mouvement institutionnel ».

Le mot « institutionnel » n'est pas directement observable.

Il faut donc remplacer cette formulation par une définition algorithmique.

---

# 38. Order Block — définition V1

Définition expérimentale haussière :

```text
Last bearish candle
before a bullish displacement
that produces a confirmed bullish BOS
```

Définition baissière :

```text
Last bullish candle
before a bearish displacement
that produces a confirmed bearish BOS
```

Cette définition doit être considérée comme :

```text
OB_ALGORITHM_V1
```

et non comme une vérité universelle.

---

# 39. Bullish Order Block

Conditions possibles :

```text
candle direction = bearish
followed by bullish displacement
displacement produces BOS
```

Zone possible :

```text
full candle range
```

ou :

```text
open → low
```

ou :

```text
body only
```

Ces variantes doivent être testées séparément.

---

# 40. Bearish Order Block

Inverse :

```text
bullish candle
↓
bearish displacement
↓
bearish BOS
```

---

# 41. Order Block Structure

```python
OrderBlock:
    ob_id
    symbol
    timeframe

    direction

    price_low
    price_high
    midpoint

    source_candle_timestamp
    confirmation_timestamp

    associated_bos
    associated_displacement

    status
    mitigation_count

    quality_score
    confidence

    algorithm_version
```

---

# 42. Order Block Availability

Un Order Block ne peut être considéré confirmé qu'après confirmation de ses conditions.

Exemple :

```text
source candle:
10:00

displacement:
10:05

BOS confirmed:
10:15
```

L'Order Block devient disponible au plus tôt :

```text
10:15
```

Le backtest ne doit jamais l'utiliser à 10:05 comme s'il était déjà connu.

---

# 43. Order Block Mitigation

Lorsqu'un prix revient dans la zone :

```text
ORDER_BLOCK_TOUCHED
```

ou :

```text
ORDER_BLOCK_MITIGATED
```

selon la définition choisie.

---

# 44. Mitigation Percentage

Mesure :

```text
mitigation_percentage =
penetration_into_order_block
/
order_block_size
```

---

# 45. Order Block Invalidation

Exemple haussier :

```text
close below order_block_low
```

peut invalider l'OB.

Version alternative :

```text
wick below low
```

Les deux doivent être testées.

---

# 46. Order Block Lifecycle

États :

```text
CANDIDATE
CONFIRMED
ACTIVE
TOUCHED
PARTIALLY_MITIGATED
MITIGATED
INVALIDATED
EXPIRED
```

---

# 47. Order Block Quality

Features possibles :

- displacement strength ;
- BOS quality ;
- FVG association ;
- volume ;
- timeframe ;
- first retest ;
- distance travelled after creation ;
- market regime ;
- structure alignment.

Score :

```text
ob_quality ∈ [0,1]
```

---

# 48. Fresh Order Block

Une zone jamais revisitée après confirmation peut être marquée :

```text
FRESH
```

Après premier test :

```text
TESTED
```

Cette distinction peut être étudiée statistiquement.

---

# 49. Breaker Block

Définition expérimentale :

Un Order Block invalidé puis traversé peut devenir une zone structurelle opposée.

Exemple :

```text
Bullish OB
↓
invalidated downward
↓
price retests zone from below
↓
Bearish Breaker candidate
```

Le concept doit être versionné et testé séparément.

---

# 50. Breaker Structure

```python
BreakerBlock:
    breaker_id
    source_order_block_id
    direction
    zone
    created_at
    available_at
    status
    quality_score
```

---

# 51. Mitigation Block

Si QuantLab expérimente ce concept, il doit disposer d'une définition distincte.

Il ne faut pas mélanger :

```text
Order Block
Breaker
Mitigation Block
```

simplement parce que certaines communautés utilisent les termes de manière interchangeable.

---

# 52. Premium / Discount

Le moteur peut calculer la position du prix à l'intérieur d'un dealing range.

Exemple :

```text
range_low
range_high
```

Midpoint :

```text
equilibrium =
(range_high + range_low) / 2
```

---

# 53. Premium

```text
price > equilibrium
```

Classification :

```text
PREMIUM
```

---

# 54. Discount

```text
price < equilibrium
```

Classification :

```text
DISCOUNT
```

---

# 55. Equilibrium

Autour du midpoint :

```text
EQUILIBRIUM
```

avec une tolérance configurable.

---

# 56. Dealing Range

Le point difficile est la définition du range utilisé.

Possibilités :

- dernier external swing high/low ;
- impulsion structurelle ;
- range confirmé ;
- période fixe.

La méthode doit être explicitement versionnée.

---

# 57. Premium/Discount n'est pas un signal

Règle :

```text
DISCOUNT
≠
BUY
```

et :

```text
PREMIUM
≠
SELL
```

Ces informations sont uniquement contextuelles.

---

# 58. Previous Highs / Lows

Le moteur peut recevoir ou calculer :

```text
PDH = Previous Day High
PDL = Previous Day Low

PWH = Previous Week High
PWL = Previous Week Low
```

Ces niveaux peuvent devenir des candidats de liquidité.

---

# 59. Session Liquidity

Niveaux possibles :

```text
Asia High
Asia Low
London High
London Low
New York High
New York Low
```

Les conventions horaires doivent être définies précisément.

---

# 60. Timezone

La référence interne doit être :

```text
UTC
```

Les sessions sont ensuite calculées selon des règles explicites.

Les changements d'heure doivent être gérés correctement pour les marchés concernés.

---

# 61. Liquidity Sweep Event

Exemple :

```text
LIQUIDITY_SWEEP_DETECTED
```

Payload :

```json
{
  "symbol": "BTC-USDT",
  "timeframe": "15m",
  "side": "BUY_SIDE",
  "zone_id": "liq_123",
  "penetration_atr": 0.18,
  "close_back_inside": true,
  "confidence": 0.77
}
```

---

# 62. FVG Event

```text
FVG_CREATED
FVG_PARTIALLY_FILLED
FVG_FILLED
FVG_INVALIDATED
```

---

# 63. Order Block Events

```text
ORDER_BLOCK_CONFIRMED
ORDER_BLOCK_TOUCHED
ORDER_BLOCK_MITIGATED
ORDER_BLOCK_INVALIDATED
```

---

# 64. Breaker Events

```text
BREAKER_CREATED
BREAKER_TESTED
BREAKER_INVALIDATED
```

---

# 65. Confluence Objects

Le moteur peut produire des confluences descriptives.

Exemple :

```text
Bullish Order Block
+
Bullish FVG
+
Sell-Side Liquidity Sweep
```

Résultat :

```text
SMC_CONFLUENCE
```

Mais le score final appartient au Scoring Engine.

---

# 66. SMC Feature Vector

Exemple :

```text
nearest_bullish_ob_distance
nearest_bearish_ob_distance

nearest_bullish_fvg_distance
nearest_bearish_fvg_distance

buy_side_liquidity_distance
sell_side_liquidity_distance

recent_buy_side_sweep
recent_sell_side_sweep

premium_discount_position

displacement_score
smc_confidence
```

---

# 67. Distance Normalization

Les distances doivent être normalisées.

Exemple :

```text
distance_to_ob / ATR
distance_to_fvg / ATR
distance_to_liquidity / ATR
```

Cela facilite le multi-actifs.

---

# 68. Zone Overlap

Le moteur doit pouvoir mesurer les intersections.

Exemple :

```text
Order Block
∩
FVG
```

ou :

```text
Order Block
∩
Volume Profile HVN
```

Le second nécessite une interaction avec le Volume Profile Engine.

---

# 69. Confluence Score

Le SMC Engine peut produire un score interne descriptif :

```text
smc_confluence_score
```

mais celui-ci ne doit pas être assimilé à la probabilité d'un trade gagnant.

Le Scoring Engine doit conserver la décision finale de pondération.

---

# 70. Multi-Timeframe SMC

Les objets doivent rester liés à leur timeframe.

Exemple :

```text
4H bullish Order Block
1H bullish FVG
15m sell-side sweep
```

Le moteur doit permettre de construire cette hiérarchie.

---

# 71. Higher-Timeframe Zones

Un objet HTF peut être projeté sur un timeframe inférieur.

Exemple :

```text
4H Order Block
↓
visible sur 15m
```

Mais l'objet conserve :

```text
origin_timeframe = 4H
```

---

# 72. Zone Priority

Le moteur peut fournir des informations de priorité basées sur :

- timeframe ;
- freshness ;
- quality ;
- significance.

Le Scoring Engine décidera de leur importance réelle.

---

# 73. Nested Zones

Exemple :

```text
4H Order Block
contains
1H FVG
contains
15m Order Block
```

Le moteur doit pouvoir représenter ces relations.

---

# 74. Causal Detection

Tous les objets utilisés en live doivent être détectables sans données futures.

Chaque objet doit avoir :

```text
origin_timestamp
confirmation_timestamp
available_at
```

---

# 75. Look-Ahead Risk

Le SMC est particulièrement vulnérable au biais rétrospectif.

Un graphique historique rend les structures évidentes après coup.

QuantLab doit donc tester chaque algorithme en replay événementiel.

---

# 76. Replay Requirement

Le moteur doit fonctionner :

```text
candle 1
↓
candle 2
↓
candle 3
...
```

sans accès aux bougies suivantes.

Cette règle est obligatoire.

---

# 77. Object Lifecycle

Tous les objets SMC doivent avoir un cycle de vie.

Exemple générique :

```text
CANDIDATE
↓
CONFIRMED
↓
ACTIVE
↓
TESTED
↓
MITIGATED / CONSUMED / INVALIDATED / EXPIRED
```

---

# 78. Persistence

Objets à stocker :

```text
liquidity_zones
liquidity_events
fair_value_gaps
order_blocks
breaker_blocks
smc_events
```

Le schéma détaillé sera défini dans `23-Database-Schema.md`.

---

# 79. Auditability

Pour chaque objet, QuantLab doit pouvoir répondre :

```text
Pourquoi cet objet a-t-il été créé ?
```

Exemple :

```text
Order Block OB-123

Reason:
last bearish candle
before displacement D-55
which caused BOS B-92
```

---

# 80. Reason Codes

Exemples :

```text
LIQ_EQUAL_HIGHS
LIQ_EQUAL_LOWS
LIQ_PREVIOUS_DAY_HIGH
LIQ_PREVIOUS_DAY_LOW

SWEEP_WICK_REJECTION
SWEEP_CLOSE_RECLAIM

FVG_THREE_CANDLE_BULLISH
FVG_THREE_CANDLE_BEARISH

OB_BEARISH_CANDLE_BEFORE_BULLISH_BOS
OB_BULLISH_CANDLE_BEFORE_BEARISH_BOS

BREAKER_INVALIDATED_OB
```

---

# 81. Algorithm Versioning

Exemple :

```text
smc_engine_version = 1.0.0
```

Sous-versions :

```text
fvg_algorithm = 1.0
order_block_algorithm = 1.0
liquidity_algorithm = 1.0
```

Une modification d'une définition doit produire une nouvelle version.

---

# 82. Configuration

Exemple :

```yaml
smc:

  liquidity:
    equal_level_atr_tolerance: 0.10
    minimum_touches: 2

  sweeps:
    require_close_reclaim: true
    minimum_penetration_atr: 0.02

  fvg:
    enabled: true
    minimum_size_atr: 0.05
    expiration_bars: 500

  displacement:
    minimum_range_atr: 1.5
    minimum_body_ratio: 0.65

  order_blocks:
    enabled: true
    require_bos: true
    zone_definition: full_candle

  premium_discount:
    enabled: true
```

Tous les paramètres doivent être versionnés.

---

# 83. Data Quality

Si les données sont insuffisantes :

```text
SMCContext.confidence ↓
```

ou :

```text
status = DEGRADED
```

Exemples :

- gap de données ;
- swings non fiables ;
- volume manquant ;
- historique insuffisant.

---

# 84. Testing unitaire

Tester séparément :

- equal highs ;
- equal lows ;
- buy-side sweep ;
- sell-side sweep ;
- bullish FVG ;
- bearish FVG ;
- partial FVG fill ;
- full FVG fill ;
- displacement ;
- bullish OB ;
- bearish OB ;
- mitigation ;
- invalidation ;
- breaker ;
- premium ;
- discount.

---

# 85. Synthetic Tests

Créer des séries de prix artificielles où les résultats sont connus.

Exemple FVG haussier :

```text
Candle 1 high = 100
Candle 2 strong bullish displacement
Candle 3 low = 102
```

Résultat :

```text
Bullish FVG
100 → 102
```

---

# 86. Sweep Test

Exemple :

```text
Equal High = 100

Next candle:
high = 101
close = 99.5
```

Résultat attendu :

```text
BUY_SIDE_LIQUIDITY_SWEEP
```

si les paramètres sont satisfaits.

---

# 87. Order Block Test

Séquence synthétique :

```text
bearish candle
↓
bullish displacement
↓
confirmed bullish BOS
```

Résultat :

```text
BULLISH_ORDER_BLOCK
```

La date de disponibilité doit correspondre à la confirmation du BOS.

---

# 88. Anti Look-Ahead Tests

Tests obligatoires :

- FVG non visible avant la troisième bougie requise ;
- OB non confirmé avant le BOS ;
- liquidity zone non confirmée avant les touches nécessaires ;
- swing-based liquidity non disponible avant confirmation du swing.

---

# 89. Historical Validation

Chaque concept doit être évalué séparément.

Exemple :

```text
Bullish FVG
```

Mesurer :

```text
fill_probability
time_to_fill
future_return
MFE
MAE
```

---

# 90. Order Block Validation

Mesurer :

```text
first_touch_reaction
break_probability
MFE after touch
MAE after touch
```

segmenté par :

- timeframe ;
- market regime ;
- volatility ;
- quality score ;
- freshness.

---

# 91. Sweep Validation

Mesurer après un sweep :

```text
reversal_probability
continuation_probability
MFE
MAE
```

Il est possible que certains sweeps ne possèdent aucun edge exploitable.

Le système doit accepter ce résultat.

---

# 92. FVG Validation

Tester notamment :

```text
P(fill within N bars)
```

et :

```text
return after first touch
```

Une forte probabilité de remplissage ne signifie pas nécessairement qu'une stratégie basée sur ce phénomène est rentable.

---

# 93. Ablation Testing

Tester :

```text
Strategy
```

puis :

```text
Strategy + FVG
```

puis :

```text
Strategy + FVG + Sweep
```

puis :

```text
Strategy + FVG + Sweep + OB
```

L'objectif est de mesurer la contribution marginale de chaque concept.

---

# 94. Multiple Testing Risk

Le nombre élevé de concepts et paramètres SMC crée un risque majeur de data mining.

Si QuantLab teste :

```text
1000 variantes
```

certaines sembleront performantes par hasard.

Le Testing Strategy doit appliquer des contrôles contre :

- overfitting ;
- p-hacking ;
- multiple hypothesis testing ;
- selection bias.

---

# 95. Baseline

Avant le SMC Engine, une stratégie baseline sans SMC doit exister.

Exemple :

```text
Market Structure
+
Trend
+
Risk Management
```

Puis comparer :

```text
Baseline
vs
Baseline + SMC
```

Si SMC n'améliore pas robustement la performance hors échantillon, il ne doit pas être conservé pour des raisons esthétiques.

Les graphiques colorés ne constituent malheureusement pas une métrique financière.

---

# 96. Experiment Registry

Exemples :

```text
EXP-SMC-001
FVG fill probability

EXP-SMC-002
First-touch Order Block reaction

EXP-SMC-003
Liquidity sweep reversal

EXP-SMC-004
FVG + BOS confluence

EXP-SMC-005
OB + sell-side sweep

EXP-SMC-006
Premium/discount contribution
```

---

# 97. Interaction avec Market Analysis Engine

Le moteur reçoit :

```text
regime
volatility
momentum
activity
```

Exemple :

un FVG créé pendant :

```text
HIGH_VOLATILITY
```

peut avoir des propriétés différentes d'un FVG créé pendant :

```text
LOW_VOLATILITY
```

Cette différence doit être mesurée.

---

# 98. Interaction avec Market Structure Engine

Le Market Structure Engine fournit :

```text
swings
BOS
CHOCH
protected levels
ranges
```

Ces informations constituent la base de nombreux objets SMC.

Le SMC Engine ne doit pas recalculer une structure concurrente.

---

# 99. Interaction avec Volume Profile Engine

Confluences potentielles :

```text
Order Block + HVN
FVG + LVN
Liquidity Zone + VAH
Sweep + Previous POC
```

Ces combinaisons doivent être testées expérimentalement.

---

# 100. Interaction avec Scoring Engine

Features possibles :

```text
smc_score
liquidity_score
sweep_score
fvg_score
order_block_score
displacement_score
premium_discount_score
smc_confidence
```

Le Scoring Engine détermine la pondération.

---

# 101. Interaction avec Decision Engine

Le Decision Engine peut utiliser des règles validées comme :

```text
candidate LONG
only after sell-side sweep
+
bullish structure confirmation
```

Mais cette logique n'appartient pas au SMC Engine.

---

# 102. Interaction avec Risk Engine

Le SMC Engine peut fournir :

```text
zone_invalidation_level
```

Exemple :

```text
bullish OB low
```

Le Risk Engine peut utiliser ce niveau comme candidat de stop structurel.

Il reste responsable du stop final et du position sizing.

---

# 103. Interaction avec Knowledge Engine

Le Knowledge Engine doit relier :

```text
SMC Object
+
Market Context
+
Decision
+
Trade Result
```

Cela permettra de répondre à des questions comme :

> Quels types d'Order Blocks ont réellement produit une expectancy positive ?

---

# 104. Interaction avec AI & Learning Engine

L'IA pourra :

- analyser les variantes de définition ;
- rechercher des interactions ;
- proposer des clusters de zones ;
- identifier des patterns non évidents ;
- suggérer la suppression de features inutiles.

Elle ne doit pas inventer silencieusement de nouvelles définitions en production.

---

# 105. Monitoring

Métriques :

```text
liquidity_zones_created
sweeps_detected
fvgs_created
fvgs_filled
order_blocks_created
order_blocks_mitigated
breaker_blocks_created
smc_processing_latency
smc_unknown_rate
smc_errors
```

---

# 106. Performance

Le moteur doit fonctionner de manière incrémentale.

Exemple :

```text
new candle
↓
update active liquidity zones
↓
check sweeps
↓
check FVG
↓
check displacement
↓
update OB lifecycle
↓
publish events
```

Il ne doit pas recalculer l'intégralité de l'historique à chaque observation.

---

# 107. Object Limits

Les anciens objets doivent pouvoir être :

```text
EXPIRED
ARCHIVED
```

afin d'éviter de conserver des milliers de zones actives inutiles.

Les règles d'expiration doivent être explicites.

---

# 108. Determinism

Avec :

```text
same market data
same market structure
same parameters
same algorithm version
```

le moteur doit produire exactement les mêmes objets.

---

# 109. Critères d'acceptation V1

La V1 est considérée valide lorsque :

- Equal Highs/Lows sont exploitables ;
- les zones de liquidité sont créées causalement ;
- les sweeps sont distingués des breakouts ;
- les FVG sont détectés sans look-ahead ;
- les FVG possèdent un lifecycle ;
- les displacements sont quantifiés ;
- les Order Blocks utilisent une définition explicite ;
- les OB ne sont disponibles qu'après confirmation ;
- premium/discount est calculable ;
- tous les objets sont versionnés ;
- tous les événements sont persistables ;
- les tests unitaires passent ;
- les tests synthétiques passent ;
- le replay historique est déterministe.

---

# 110. Priorités V1

Implémenter :

- liquidity zones ;
- Equal Highs / Lows ;
- previous day/week levels ;
- liquidity sweeps ;
- FVG ;
- FVG lifecycle ;
- displacement ;
- Order Block V1 ;
- Order Block lifecycle ;
- premium / discount ;
- reason codes ;
- persistence ;
- tests.

---

# 111. Priorités V2

Ajouter :

- session liquidity ;
- sweep quality ;
- FVG quality ;
- OB quality ;
- first-touch tracking ;
- breaker blocks ;
- nested zones ;
- multi-timeframe projection.

---

# 112. Priorités V3

Ajouter :

- mitigation blocks ;
- advanced liquidity clustering ;
- volume-profile confluence ;
- order-flow confirmation ;
- statistical adaptive scoring.

---

# 113. Priorités V4

Ajouter :

- ML pattern classification ;
- automated feature discovery ;
- cross-market SMC analysis ;
- adaptive definitions sous gouvernance stricte.

---

# 114. Risques conceptuels

Le SMC Engine est l'un des moteurs présentant le plus grand risque de biais narratif.

Principaux risques :

### Subjectivité

Définitions différentes selon les traders.

### Look-Ahead

Les structures semblent évidentes après coup.

### Overfitting

Beaucoup de concepts et paramètres peuvent être combinés.

### Confirmation Bias

Il est facile de sélectionner uniquement les exemples où les concepts semblent fonctionner.

### Terminologie

Les mêmes termes peuvent désigner des choses différentes selon les sources.

QuantLab doit donc être particulièrement strict sur ce moteur.

---

# 115. Principe de falsification

Pour chaque concept :

```text
Hypothèse
↓
Définition algorithmique
↓
Test
↓
Out-of-sample
↓
Accept / Reject
```

Un concept populaire doit pouvoir être rejeté.

Le but de QuantLab n'est pas de prouver que SMC fonctionne.

Le but est de déterminer **quelles parties, dans quelles conditions et avec quelle robustesse, apportent réellement de l'information**.

---

# 116. Architecture finale

```text
Validated Market Data
        ↓
Market Analysis Engine
        ↓
Market Structure Engine
        ↓
┌────────────────────────┐
│       SMC ENGINE       │
├────────────────────────┤
│ Liquidity Detection    │
│ Sweep Detection        │
│ FVG Detection          │
│ Displacement           │
│ Order Blocks           │
│ Breakers               │
│ Premium / Discount     │
└───────────┬────────────┘
            ↓
        SMCContext
            ↓
    Scoring Engine
            ↓
    Decision Engine

            +
            ↓
    Knowledge Engine
            ↓
    Statistical Validation
```

---

# 117. Résultat attendu

Le moteur doit transformer des concepts graphiques souvent subjectifs en objets structurés tels que :

```text
LiquidityZone
LiquiditySweep
FairValueGap
OrderBlock
BreakerBlock
Displacement
PremiumDiscountState
```

Chaque objet doit posséder :

```text
definition
parameters
origin
confirmation
available_at
status
quality
confidence
version
```

---

# 118. Règle fondatrice

> **QuantLab ne doit jamais coder une histoire de marché. Il doit coder une définition, puis vérifier si les données lui donnent raison.**

Le Smart Money Concepts Engine est donc un moteur d'hypothèses quantifiées, pas une collection de croyances de trading transformées en code.

---

# 119. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `03-Data-Engine.md`
- `05-Market-Analysis-Engine.md`
- `06-Market-Structure-Engine.md`
- `07-Volume-Profile-Engine.md`
- `09-Scoring-Engine.md`
- `10-Decision-Engine.md`
- `11-Risk-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `16-Governance-Engine.md`
- `18-Testing-Strategy.md`
- `21-Experiment-Registry.md`
- `23-Database-Schema.md`

**Prochain document : `09-Scoring-Engine.md`**
