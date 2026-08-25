# 05 — Market Analysis Engine

**Projet : QuantLab**  
**Document : Market Analysis Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Market Analysis Engine est la couche chargée de transformer les données de marché normalisées en un **contexte de marché structuré, quantifiable et exploitable par les autres moteurs de QuantLab**.

Son rôle n'est pas de décider d'acheter ou de vendre.

Il doit répondre à une question plus fondamentale :

> **Dans quel environnement de marché sommes-nous actuellement ?**

Il doit notamment déterminer :

- direction générale ;
- régime de marché ;
- volatilité ;
- momentum ;
- liquidité ;
- activité ;
- contexte temporel ;
- contexte multi-timeframe ;
- anomalies éventuelles.

Le résultat principal du moteur est un objet standardisé :

```text
MarketContext
```

qui sera utilisé par :

- Market Structure Engine ;
- Volume Profile Engine ;
- Smart Money Concepts Engine ;
- Scoring Engine ;
- Decision Engine ;
- Risk Engine ;
- AI & Learning Engine.

---

# 2. Philosophie

Le Market Analysis Engine ne doit pas chercher à prédire directement :

```text
BTC va monter.
```

Il doit produire une description probabiliste du contexte :

```text
BTC-USDT
4H regime = TRENDING
direction = BULLISH
volatility = HIGH
momentum = POSITIVE
liquidity = NORMAL
confidence = 0.78
```

La distinction est fondamentale.

Une description du contexte peut être testée objectivement.

Une prédiction vague beaucoup moins.

---

# 3. Responsabilités

Le moteur est responsable de :

1. recevoir les données validées ;
2. construire les features nécessaires ;
3. identifier le régime de marché ;
4. mesurer la volatilité ;
5. mesurer le momentum ;
6. analyser l'activité ;
7. analyser la liquidité disponible lorsque les données existent ;
8. analyser plusieurs timeframes ;
9. identifier les sessions ;
10. produire un MarketContext ;
11. attribuer un niveau de confiance ;
12. conserver l'historique des contextes ;
13. détecter les changements significatifs de régime.

---

# 4. Ce que le moteur ne doit pas faire

Le Market Analysis Engine ne doit pas :

- envoyer d'ordre ;
- définir la taille d'une position ;
- calculer le risque final ;
- déterminer seul une entrée ;
- interpréter un Order Block ;
- décider qu'un FVG doit être tradé ;
- modifier une stratégie ;
- optimiser automatiquement ses paramètres en production.

---

# 5. Architecture

```text
Normalized Market Data
          │
          ▼
   Feature Builder
          │
          ▼
 ┌───────────────────────┐
 │ Market Analysis Engine│
 └───────────┬───────────┘
             │
    ┌────────┼────────┐
    ▼        ▼        ▼
 Regime   Volatility Momentum
    │        │        │
    ├────────┼────────┤
    ▼        ▼        ▼
Liquidity Activity  Session
             │
             ▼
       Multi-Timeframe
             │
             ▼
        MarketContext
```

---

# 6. Entrées

Le moteur peut recevoir :

## Données obligatoires

- OHLCV ;
- instrument ;
- timeframe ;
- timestamp.

## Données facultatives

- trades ;
- bid/ask ;
- order book ;
- funding ;
- open interest ;
- liquidations ;
- volume delta ;
- données on-chain ;
- données macro ;
- données de session.

Le moteur doit continuer à fonctionner avec un ensemble minimal de données.

Les fonctionnalités nécessitant des données indisponibles doivent être désactivées proprement.

---

# 7. Sortie principale

Structure conceptuelle :

```python
MarketContext:
    instrument
    timestamp

    primary_timeframe

    regime
    direction

    volatility_state
    momentum_state
    liquidity_state
    activity_state

    session

    higher_timeframe_context
    lower_timeframe_context

    regime_confidence
    direction_confidence
    overall_confidence

    feature_version
    model_version
```

---

# 8. Régimes de marché

La première version doit reconnaître au minimum :

```text
TRENDING_UP
TRENDING_DOWN
RANGING
HIGH_VOLATILITY
LOW_VOLATILITY
TRANSITION
UNKNOWN
```

Ces catégories peuvent se combiner.

Exemple :

```text
direction = BULLISH
structure = TRENDING
volatility = HIGH
```

---

# 9. Pourquoi identifier le régime

Une stratégie peut être excellente dans un environnement et catastrophique dans un autre.

Exemple :

```text
Trend Following
→ efficace en tendance
→ potentiellement mauvais en range
```

Inversement :

```text
Mean Reversion
→ efficace dans certains ranges
→ dangereuse pendant une expansion directionnelle
```

QuantLab doit donc mesurer la performance :

```text
Strategy × Market Regime
```

et pas uniquement :

```text
Strategy × Asset
```

---

# 10. Détection de tendance

La tendance ne doit pas dépendre d'un indicateur unique.

Plusieurs familles de features peuvent être utilisées.

Exemples :

- structure des highs/lows ;
- pente des prix ;
- moving averages ;
- regression slope ;
- ADX ;
- momentum ;
- distance au VWAP ;
- expansion directionnelle.

Une première approche simple est préférable.

---

# 11. Trend Score

Un score directionnel peut être construit.

Exemple conceptuel :

```text
Higher highs            +20
Higher lows             +20
Positive regression     +20
Price above reference   +15
Positive momentum       +15
Volume confirmation     +10
```

Résultat :

```text
Trend Score = -100 → +100
```

Exemple :

```text
+100 = forte tendance haussière
0    = absence de direction
-100 = forte tendance baissière
```

Les pondérations doivent être validées statistiquement.

---

# 12. Régression

Une régression linéaire peut être utilisée comme feature de direction.

Exemple :

```text
price = a × time + b
```

Le coefficient :

```text
a
```

fournit une estimation de pente.

La pente doit être normalisée par la volatilité ou le niveau du prix pour permettre des comparaisons.

---

# 13. Moving Averages

Les moyennes mobiles peuvent servir de features, pas de vérité absolue.

Exemples :

```text
EMA20
EMA50
EMA200
```

Features possibles :

```text
price > EMA50
EMA20 > EMA50
EMA50 slope > 0
distance(price, EMA50)
```

Ces paramètres doivent rester configurables.

---

# 14. ADX

L'ADX peut être utilisé comme mesure auxiliaire de force directionnelle.

Il ne doit pas déterminer seul le régime.

Exemple :

```text
ADX élevé
+
structure directionnelle
+
slope cohérente
=
probabilité plus élevée de régime trending
```

---

# 15. Momentum

Le momentum mesure la vitesse et la persistance du mouvement.

Features potentielles :

- Rate of Change ;
- returns ;
- rolling returns ;
- RSI ;
- MACD dérivé ;
- acceleration ;
- normalized momentum.

Le moteur doit privilégier les features interprétables dans les premières versions.

---

# 16. Momentum Score

Exemple :

```text
momentum_score ∈ [-1, +1]
```

avec :

```text
-1 = momentum baissier fort
0 = neutre
+1 = momentum haussier fort
```

Le score doit être accompagné d'une confiance.

---

# 17. Volatilité

La volatilité constitue un élément central.

Elle influence :

- distance des stops ;
- position sizing ;
- seuils de structure ;
- qualité des breakouts ;
- slippage ;
- risque d'exécution.

Le Market Analysis Engine doit produire un état de volatilité normalisé.

---

# 18. Mesures de volatilité

Features possibles :

- ATR ;
- True Range ;
- realized volatility ;
- standard deviation des returns ;
- Parkinson volatility ;
- range normalisé.

La V1 peut commencer par :

```text
ATR
+
rolling standard deviation
```

avant d'introduire des modèles plus sophistiqués.

---

# 19. Normalisation de l'ATR

L'ATR brut n'est pas directement comparable entre actifs.

On peut utiliser :

```text
Normalized ATR = ATR / Price
```

Exemple :

```text
BTC ATR = 1 000
BTC Price = 100 000

Normalized ATR = 1%
```

---

# 20. Volatility Regime

Classification possible :

```text
VERY_LOW
LOW
NORMAL
HIGH
EXTREME
```

La classification doit être relative à l'historique récent de l'actif.

---

# 21. Percentile de volatilité

Approche recommandée :

```text
current_volatility_percentile
```

Exemple :

```text
10th percentile → très faible
50th percentile → normale
90th percentile → élevée
99th percentile → extrême
```

Cela est généralement plus robuste qu'un seuil absolu identique pour tous les actifs.

---

# 22. Expansion et compression

Le moteur doit pouvoir détecter :

```text
VOLATILITY_COMPRESSION
VOLATILITY_EXPANSION
```

Une compression peut précéder un mouvement important, mais cette relation doit être testée.

Elle ne doit jamais être supposée automatiquement rentable.

---

# 23. Volume

Le Market Analysis Engine peut produire une analyse générale du volume.

Les analyses détaillées par niveau de prix appartiennent au Volume Profile Engine.

Features générales :

- volume relatif ;
- volume moyen ;
- volume percentile ;
- volume spike ;
- volume contraction ;
- volume trend.

---

# 24. Relative Volume

Exemple :

```text
RVOL =
Current Volume
/
Average Volume
```

Interprétation possible :

```text
RVOL < 0.5 → activité faible
RVOL ≈ 1 → activité normale
RVOL > 2 → activité élevée
```

Ces seuils ne doivent pas être universels sans validation.

---

# 25. Activity State

Le moteur peut produire :

```text
VERY_LOW_ACTIVITY
LOW_ACTIVITY
NORMAL_ACTIVITY
HIGH_ACTIVITY
EXTREME_ACTIVITY
```

L'activité peut être calculée à partir de :

- volume ;
- nombre de trades ;
- range ;
- order book updates.

---

# 26. Liquidité

Lorsque les données nécessaires existent, le moteur doit mesurer :

- spread ;
- profondeur ;
- slippage estimé ;
- volume disponible ;
- order book imbalance.

La liquidité est particulièrement importante pour l'Execution Engine et le Risk Engine.

---

# 27. Spread

Mesure :

```text
spread = ask - bid
```

Normalisation :

```text
relative_spread =
(ask - bid) / mid_price
```

Le spread peut être classifié par percentile.

---

# 28. Depth

Lorsque l'order book est disponible :

```text
Depth ±0.1%
Depth ±0.5%
Depth ±1%
```

peut être calculée.

Cela permet d'estimer la liquidité disponible autour du prix.

---

# 29. Order Book Imbalance

Feature potentielle :

```text
OBI =
Bid Volume - Ask Volume
-----------------------
Bid Volume + Ask Volume
```

Valeur :

```text
-1 → dominance ask
0 → équilibré
+1 → dominance bid
```

Cette métrique doit être traitée avec prudence en raison :

- spoofing ;
- annulations rapides ;
- différences entre exchanges.

---

# 30. Sessions

Le moteur doit identifier le contexte temporel.

Exemples :

```text
ASIA
LONDON
NEW_YORK
LONDON_NEW_YORK_OVERLAP
OFF_HOURS
```

Pour crypto, ces sessions sont analytiques.

Le marché reste ouvert 24/7.

---

# 31. Session Statistics

Le système doit pouvoir mesurer :

```text
volatility_by_session
volume_by_session
strategy_performance_by_session
signal_frequency_by_session
```

Cela permettra de vérifier objectivement les affirmations concernant certaines heures de marché.

---

# 32. Day of Week

Feature possible :

```text
MONDAY
TUESDAY
WEDNESDAY
THURSDAY
FRIDAY
SATURDAY
SUNDAY
```

Pour crypto, les weekends doivent être explicitement analysés.

---

# 33. Multi-Timeframe Analysis

Le Market Analysis Engine doit supporter plusieurs horizons simultanément.

Exemple :

```text
1D → macro
4H → primary regime
1H → intermediate
15m → setup
5m → execution context
```

---

# 34. Hiérarchie temporelle

Un exemple configurable :

```text
Macro:
1D

Higher Timeframe:
4H

Context:
1H

Setup:
15m

Execution:
5m
```

Le système ne doit pas imposer définitivement cette hiérarchie.

---

# 35. Timeframe Alignment

Le moteur peut produire :

```text
FULL_BULLISH_ALIGNMENT
PARTIAL_BULLISH_ALIGNMENT
MIXED
PARTIAL_BEARISH_ALIGNMENT
FULL_BEARISH_ALIGNMENT
```

Exemple :

```text
1D bullish
4H bullish
1H bullish
15m bullish
```

→ alignement haussier fort.

---

# 36. Conflits multi-timeframe

Exemple :

```text
1D = bullish
4H = bullish
1H = bearish
15m = bearish
```

Cela peut représenter :

```text
Higher Timeframe Uptrend
+
Lower Timeframe Pullback
```

Le système ne doit pas considérer automatiquement cette situation comme contradictoire.

---

# 37. MarketContext multi-timeframe

Exemple :

```yaml
BTC-USDT:

  1D:
    regime: TRENDING
    direction: BULLISH

  4H:
    regime: TRENDING
    direction: BULLISH

  1H:
    regime: PULLBACK
    direction: BEARISH

  15M:
    regime: RANGING
```

Cette structure peut être utilisée par le Decision Engine.

---

# 38. Market Regime State Machine

Les régimes peuvent être modélisés comme une machine d'état.

```text
RANGE
  ↓
BREAKOUT
  ↓
TREND
  ↓
EXHAUSTION
  ↓
TRANSITION
  ↓
RANGE
```

Cette représentation est une hypothèse de recherche.

Elle ne doit pas être considérée comme une loi universelle du marché.

---

# 39. Transition Regime

`TRANSITION` doit être un état explicite.

Le moteur ne doit pas forcer chaque marché dans :

```text
TREND
```

ou :

```text
RANGE
```

Certaines périodes sont réellement ambiguës.

---

# 40. UNKNOWN

`UNKNOWN` est également un état valide.

Il peut être utilisé lorsque :

- données insuffisantes ;
- qualité faible ;
- conflit de signaux ;
- comportement inhabituel ;
- modèle incapable de classifier correctement.

Ne pas savoir est préférable à inventer une certitude.

---

# 41. Confidence Score

Chaque classification doit disposer d'un niveau de confiance.

Exemple :

```text
regime = TRENDING_UP
confidence = 0.82
```

ou :

```text
regime = UNKNOWN
confidence = 0.31
```

---

# 42. Overall Market Confidence

Un score global peut combiner :

```text
data_quality
regime_confidence
trend_confidence
volatility_confidence
liquidity_confidence
multi_timeframe_consistency
```

Exemple :

```text
overall_confidence ∈ [0,1]
```

---

# 43. Data Quality Integration

Le Market Analysis Engine doit recevoir le score de qualité du Data Engine.

Exemple :

```text
Market Analysis Confidence
×
Data Quality
```

Une analyse parfaite sur des données douteuses reste douteuse.

---

# 44. Feature Registry

Toutes les features doivent être enregistrées dans un registre.

Exemple :

```text
feature_id
feature_name
version
parameters
description
input_data
output_type
```

Cela évite les indicateurs fantômes dont personne ne sait six mois plus tard comment ils ont été calculés.

---

# 45. Feature Versioning

Une modification de calcul doit produire une nouvelle version.

Exemple :

```text
normalized_atr_v1
normalized_atr_v2
```

Une expérience doit toujours savoir quelle version elle utilise.

---

# 46. Pas de Look-Ahead

Chaque feature doit utiliser uniquement les informations disponibles au moment de la décision simulée.

Exemple interdit :

```text
classification à 10:00
utilisant la clôture de 10:05
```

Le moteur doit être compatible avec une simulation événementielle réaliste.

---

# 47. Warm-Up Period

Certains calculs nécessitent un historique minimal.

Exemple :

```text
EMA200
```

nécessite une période d'initialisation.

Le moteur doit déclarer :

```text
READY
```

ou :

```text
WARMING_UP
```

---

# 48. État du moteur

États possibles :

```text
INITIALIZING
WARMING_UP
READY
DEGRADED
PAUSED
ERROR
```

Le Decision Engine doit pouvoir connaître cet état.

---

# 49. Market Context Event

Lorsqu'un contexte est produit :

```text
MARKET_CONTEXT_UPDATED
```

peut être publié.

Exemple :

```json
{
  "symbol": "BTC-USDT",
  "timeframe": "1H",
  "regime": "TRENDING",
  "direction": "BULLISH",
  "volatility": "HIGH",
  "confidence": 0.82
}
```

---

# 50. Regime Change Event

Lorsqu'un changement significatif est détecté :

```text
MARKET_REGIME_CHANGED
```

Exemple :

```text
RANGING
→
TRENDING_UP
```

Cet événement peut être utilisé par :

- Decision Engine ;
- Risk Engine ;
- Monitoring Engine ;
- Knowledge Engine.

---

# 51. Hysteresis

Pour éviter que le régime change à chaque bougie :

```text
TREND
RANGE
TREND
RANGE
TREND
```

le moteur doit pouvoir utiliser une hystérésis.

Exemple :

un nouveau régime doit persister pendant :

```text
N observations
```

ou dépasser un seuil de confiance avant validation.

---

# 52. Régime de volatilité adaptatif

Les seuils doivent idéalement être relatifs à l'historique.

Exemple :

```text
volatility_percentile
```

plutôt que :

```text
ATR > valeur fixe
```

Cela facilite le fonctionnement multi-actifs.

---

# 53. Normalisation multi-actifs

Les features doivent être normalisées autant que possible.

Exemples :

```text
ATR / Price

Volume / Average Volume

Return / Volatility

Spread / Mid Price
```

Cela permet de comparer :

```text
BTC
ETH
XAU/USD
```

sans supposer qu'ils ont les mêmes unités.

---

# 54. Crypto 24/7

Le moteur doit gérer explicitement l'absence de clôture quotidienne naturelle des cryptos.

Les conventions doivent être définies pour :

- début de journée ;
- sessions ;
- bougies quotidiennes ;
- semaine ;
- weekend.

UTC doit être utilisé comme référence technique.

---

# 55. XAU/USD

Lors de l'intégration de l'or, le moteur devra tenir compte :

- horaires de trading ;
- sessions ;
- spreads variables ;
- événements macro ;
- fermeture hebdomadaire ;
- rollover ;
- caractéristiques propres au fournisseur.

Les règles crypto ne doivent pas être appliquées aveuglément à XAU/USD.

---

# 56. DEX

Pour les marchés décentralisés, l'analyse devra éventuellement intégrer :

- profondeur du pool ;
- TVL ;
- impact du prix ;
- volume des swaps ;
- concentration de liquidité ;
- frais ;
- gas ;
- activité on-chain.

Un régime DEX peut donc différer d'un régime CEX.

---

# 57. Macro Context

Le moteur peut recevoir un contexte macro externe.

Exemple :

```text
NORMAL
HIGH_IMPACT_EVENT_APPROACHING
POST_EVENT_VOLATILITY
```

Le Market Analysis Engine décrit ce contexte.

Le Decision Engine décidera de son impact sur le trading.

---

# 58. News

Le moteur ne doit pas interpréter naïvement les nouvelles en :

```text
bonne nouvelle = achat
```

Il doit éventuellement transmettre :

```text
event_risk = HIGH
```

ou des features spécialisées validées ultérieurement.

---

# 59. Analyse statistique

Chaque classification doit pouvoir être évaluée historiquement.

Exemple :

```text
Quand regime = TRENDING_UP :

future_return_5m
future_return_15m
future_return_1h
future_return_4h
```

Cela permet de vérifier si la classification possède une information utile.

---

# 60. Matrice de transition

Le système doit pouvoir mesurer :

```text
P(next regime | current regime)
```

Exemple :

```text
RANGE → RANGE
RANGE → TREND
TREND → TREND
TREND → TRANSITION
```

Ces probabilités doivent être observées, pas supposées.

---

# 61. Durée des régimes

Le système doit mesurer :

```text
average_regime_duration
median_regime_duration
distribution
```

par :

- actif ;
- timeframe ;
- session.

---

# 62. Performance des stratégies par régime

Le Knowledge Engine doit pouvoir produire :

```text
Strategy A

TREND:
Sharpe 1.8

RANGE:
Sharpe -0.4

HIGH VOL:
Sharpe 0.9
```

Cela permettra éventuellement au Decision Engine de sélectionner les stratégies adaptées.

---

# 63. Feature Importance

Lorsque suffisamment de données seront disponibles, QuantLab pourra mesurer l'utilité réelle de chaque feature.

Méthodes possibles :

- ablation tests ;
- permutation importance ;
- information coefficient ;
- modèles statistiques ;
- ML explainability.

Une feature qui n'ajoute aucune information doit pouvoir être supprimée.

---

# 64. Ablation Testing

Exemple :

```text
Model complet
vs
Model sans ADX
```

Si les performances restent identiques :

```text
ADX peut être inutile.
```

La simplicité doit être récompensée.

---

# 65. Baseline

Avant toute sophistication, une baseline doit être construite.

Exemple V1 :

```text
Trend:
EMA slope + market structure

Volatility:
Normalized ATR percentile

Momentum:
rolling return

Volume:
RVOL
```

Puis seulement comparer les méthodes plus complexes.

---

# 66. Machine Learning futur

Des modèles ML pourront ultérieurement classifier les régimes.

Exemples :

- clustering ;
- Hidden Markov Models ;
- gradient boosting ;
- neural networks.

Mais ils devront battre une baseline simple hors échantillon.

Complexité supplémentaire sans amélioration robuste = complexité inutile.

---

# 67. Regime Clustering

Une approche expérimentale pourra utiliser :

```text
volatility
returns
volume
trend strength
liquidity
```

pour identifier automatiquement des clusters.

Ces clusters devront ensuite être interprétés.

---

# 68. Explainability

Une classification doit idéalement pouvoir expliquer ses principaux facteurs.

Exemple :

```text
TRENDING_UP — confidence 0.84

Reasons:
+ positive regression slope
+ higher highs
+ higher lows
+ strong momentum
+ above-average volume
```

Cette information doit être enregistrée.

---

# 69. Reason Codes

Le moteur doit produire des codes standardisés.

Exemple :

```text
TREND_HH_HL
TREND_POSITIVE_SLOPE
VOLATILITY_HIGH
RVOL_HIGH
LIQUIDITY_LOW
TIMEFRAME_CONFLICT
DATA_QUALITY_LOW
```

Ils faciliteront :

- logs ;
- debugging ;
- analyse ;
- IA ;
- dashboards.

---

# 70. Storage

Chaque MarketContext important doit pouvoir être persisté.

Champs principaux :

```text
context_id
timestamp
instrument
timeframe
regime
direction
volatility_state
momentum_state
activity_state
liquidity_state
confidence
feature_version
```

---

# 71. Snapshot vs Event

Le système doit distinguer :

### Snapshot

État du marché à un instant.

### Event

Changement significatif.

Exemple :

```text
Snapshot:
BTC trending bullish

Event:
BTC changed RANGE → TREND
```

---

# 72. Monitoring

Métriques du moteur :

```text
analysis_latency
contexts_generated
regime_changes
unknown_rate
confidence_distribution
errors
feature_calculation_time
```

Une hausse anormale de :

```text
UNKNOWN
```

peut indiquer un problème de données ou de modèle.

---

# 73. Latence

Pour l'intraday, le calcul doit rester suffisamment rapide.

Pipeline :

```text
CANDLE_CLOSED
    ↓
Feature Calculation
    ↓
MarketContext
```

La latence doit être mesurée et enregistrée.

---

# 74. Déterminisme

Avec :

```text
same data
same configuration
same version
```

le moteur déterministe doit produire :

```text
same MarketContext
```

Cette propriété est indispensable pour les backtests reproductibles.

---

# 75. Configuration

Exemple conceptuel :

```yaml
market_analysis:

  regime:
    enabled: true

  volatility:
    atr_period: 14
    percentile_window: 500

  trend:
    regression_window: 50

  volume:
    rvol_window: 20

  multi_timeframe:
    enabled: true
    timeframes:
      - 1D
      - 4H
      - 1H
      - 15m
      - 5m
```

Toutes les valeurs doivent être configurables et versionnées.

---

# 76. Testing

## Unit Tests

Tester :

- ATR ;
- returns ;
- slopes ;
- RVOL ;
- percentiles ;
- classification.

## Scenario Tests

Exemples :

```text
Strong uptrend
Strong downtrend
Flat range
Volatility spike
Low volume
Data gap
```

## Integration Tests

Tester :

```text
Data Engine
→
Market Analysis Engine
→
Storage
```

---

# 77. Synthetic Tests

Des données synthétiques peuvent être utilisées.

Exemple :

```text
price = linear upward trend
```

Résultat attendu :

```text
TRENDING_UP
```

Autre :

```text
price oscillates around constant mean
```

Résultat attendu :

```text
RANGING
```

---

# 78. Historical Validation

Le moteur doit être évalué sur plusieurs périodes.

Minimum recommandé :

- bull market ;
- bear market ;
- range ;
- crise ;
- volatilité élevée ;
- faible volatilité.

Il ne doit pas être calibré uniquement sur un marché favorable.

---

# 79. Multi-Asset Validation

Validation progressive :

```text
BTC
ETH
XAU/USD
```

Une méthode robuste doit pouvoir fonctionner sans réglages totalement différents pour chaque actif, sauf justification économique claire.

---

# 80. Out-of-Sample

Les paramètres de classification doivent être évalués sur des périodes non utilisées pour leur conception.

La performance in-sample seule ne constitue pas une validation.

---

# 81. Critères d'acceptation

Le Market Analysis Engine V1 est valide lorsque :

- il produit un MarketContext standardisé ;
- les calculs sont reproductibles ;
- aucun look-ahead n'existe ;
- les régimes sont explicitement définis ;
- la volatilité est normalisée ;
- le contexte multi-timeframe fonctionne ;
- `UNKNOWN` est supporté ;
- les scores de confiance sont disponibles ;
- les features sont versionnées ;
- les changements de régime sont journalisés ;
- les tests unitaires passent ;
- les tests synthétiques passent ;
- les résultats peuvent être persistés.

---

# 82. Priorités d'implémentation

## V1

Implémenter :

- OHLCV ;
- trend ;
- momentum ;
- ATR ;
- volatility percentile ;
- RVOL ;
- sessions ;
- multi-timeframe ;
- MarketContext ;
- confidence ;
- logging.

## V2

Ajouter :

- spread ;
- liquidity ;
- order book ;
- open interest ;
- funding ;
- liquidations.

## V3

Ajouter :

- regime state machine ;
- statistical regime analysis ;
- clustering expérimental.

## V4

Ajouter :

- machine learning ;
- adaptive regime classification ;
- advanced explainability.

---

# 83. Interaction avec Market Structure Engine

Le Market Analysis Engine fournit :

```text
MarketContext
```

Le Market Structure Engine fournit :

```text
MarketStructure
```

Les deux doivent rester séparés.

Exemple :

```text
MarketContext:
high volatility bullish regime

MarketStructure:
HH / HL structure intact
```

Le Scoring Engine pourra ensuite combiner les informations.

---

# 84. Interaction avec Volume Profile Engine

Le Market Analysis Engine fournit le contexte global.

Le Volume Profile Engine fournit :

- POC ;
- VAH ;
- VAL ;
- HVN ;
- LVN ;
- distributions de volume.

Les deux moteurs ne doivent pas dupliquer leurs responsabilités.

---

# 85. Interaction avec Smart Money Concepts Engine

Le SMC Engine peut recevoir :

```text
MarketContext
+
MarketStructure
```

pour contextualiser :

- liquidity sweeps ;
- FVG ;
- order blocks ;
- displacement.

Un FVG dans un régime très différent peut ne pas avoir la même signification statistique.

---

# 86. Interaction avec Scoring Engine

Le Market Analysis Engine doit produire des features utilisables directement par le scoring.

Exemple :

```text
trend_alignment_score
volatility_score
momentum_score
activity_score
liquidity_score
context_confidence
```

Le Scoring Engine décide de leurs pondérations.

---

# 87. Interaction avec Risk Engine

Le Risk Engine peut utiliser :

```text
volatility_state
liquidity_state
market_regime
```

pour adapter :

- position sizing ;
- stop distance ;
- exposition maximale.

Le Market Analysis Engine ne doit cependant pas calculer lui-même la taille finale.

---

# 88. Interaction avec Knowledge Engine

Tous les contextes significatifs doivent pouvoir alimenter le Knowledge Engine.

Objectif :

```text
Market Context
+
Strategy
+
Decision
+
Result
```

Cela permettra d'étudier :

> Dans quels environnements cette stratégie fonctionne-t-elle réellement ?

---

# 89. Interaction avec AI & Learning Engine

L'AI & Learning Engine pourra utiliser l'historique des MarketContext pour :

- détecter de nouveaux régimes ;
- rechercher des anomalies ;
- proposer de nouvelles features ;
- analyser les transitions ;
- améliorer les classifications.

Toute modification devra repasser par le Testing Strategy et le Governance Engine.

---

# 90. Principe fondamental

Le Market Analysis Engine doit appliquer la règle suivante :

> **Décrire avant de prédire.**

La première mission de QuantLab n'est pas de deviner chaque mouvement.

Elle est de construire une représentation suffisamment fiable de l'environnement pour déterminer **quelles stratégies ont une raison statistique d'être actives dans ce contexte**.

---

# 91. Résultat attendu

Le pipeline final doit être :

```text
Raw Market Data
       ↓
Validated Data
       ↓
Features
       ↓
Market Regime
       +
Volatility
       +
Momentum
       +
Activity
       +
Liquidity
       +
Sessions
       +
Multi-Timeframe Context
       ↓
MarketContext
       ↓
Market Structure
Volume Profile
SMC
Scoring
Decision
Risk
```

Le moteur transforme donc une masse de données brutes en une description standardisée et mesurable du marché.

---

# 92. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `03-Data-Engine.md`
- `04-Storage-Engine.md`
- `06-Market-Structure-Engine.md`
- `07-Volume-Profile-Engine.md`
- `08-Smart-Money-Concepts-Engine.md`
- `09-Scoring-Engine.md`
- `10-Decision-Engine.md`
- `11-Risk-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `18-Testing-Strategy.md`
- `21-Experiment-Registry.md`

**Prochain document : `06-Market-Structure-Engine.md`**
