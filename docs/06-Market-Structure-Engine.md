# 06 — Market Structure Engine

**Projet : QuantLab**  
**Document : Market Structure Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Market Structure Engine est responsable de transformer l'évolution du prix en une représentation structurée, objective et exploitable de la dynamique de marché.

Son rôle principal est d'identifier :

- les swings significatifs ;
- les séquences de sommets et creux ;
- les structures haussières ;
- les structures baissières ;
- les ranges ;
- les ruptures de structure ;
- les changements de structure ;
- les phases d'expansion ;
- les phases de contraction ;
- les transitions entre régimes structurels.

Le moteur doit fournir une lecture du marché suffisamment précise pour alimenter les autres composants de QuantLab sans dépendre d'une interprétation discrétionnaire.

Il ne doit pas envoyer d'ordre.

Il ne doit pas décider seul qu'un trade doit être exécuté.

Il fournit une représentation structurée du prix.

---

# 2. Principe fondamental

Les concepts de structure doivent être définis de manière algorithmique.

Des formulations telles que :

```text
"le marché est haussier"
```

ou :

```text
"la structure vient de casser"
```

ne sont pas suffisamment précises pour être implémentées.

QuantLab doit transformer ces concepts en définitions mesurables.

Exemple :

```text
Un Break of Structure haussier est détecté lorsqu'un swing high
précédemment confirmé est dépassé selon une règle de validation
définie et que la clôture satisfait les critères de confirmation.
```

Chaque définition devra être :

- paramétrable ;
- versionnée ;
- testable ;
- documentée ;
- falsifiable.

---

# 3. Responsabilités

Le Market Structure Engine doit :

1. recevoir des données OHLCV validées ;
2. détecter les swings ;
3. classifier les highs et lows ;
4. construire une séquence structurelle ;
5. déterminer un biais structurel ;
6. détecter les ruptures ;
7. détecter les changements potentiels de structure ;
8. identifier les ranges ;
9. identifier les expansions et contractions ;
10. produire des événements structurels ;
11. gérer plusieurs timeframes ;
12. attribuer un niveau de confiance ;
13. conserver l'historique structurel ;
14. fournir une sortie standardisée au Scoring Engine.

---

# 4. Ce que le moteur ne doit pas faire

Le Market Structure Engine ne doit pas :

- déterminer le risque final ;
- calculer la taille d'une position ;
- exécuter des ordres ;
- décider seul d'entrer long ou short ;
- valider automatiquement un Order Block ;
- valider automatiquement un Fair Value Gap ;
- décider qu'une rupture est rentable ;
- ajuster ses paramètres en production sans pipeline de validation.

---

# 5. Entrées

Le moteur doit fonctionner au minimum avec :

```text
timestamp
open
high
low
close
volume
symbol
timeframe
```

Données complémentaires possibles :

- volume relatif ;
- volatilité ;
- MarketContext ;
- session ;
- spread ;
- données de trades ;
- données order book.

La détection structurelle de base ne doit pas dépendre obligatoirement de données complexes.

---

# 6. Sortie principale

Le moteur doit produire un objet standardisé.

Exemple conceptuel :

```python
MarketStructure:
    instrument
    timeframe
    timestamp

    trend_state
    structure_state

    last_confirmed_swing_high
    last_confirmed_swing_low

    previous_swing_high
    previous_swing_low

    last_break_type
    last_break_timestamp

    bos_direction
    choch_direction

    range_state
    expansion_state

    structure_score
    confidence

    algorithm_version
```

---

# 7. Concepts structurels principaux

La première version doit reconnaître :

```text
HIGHER_HIGH
HIGHER_LOW
LOWER_HIGH
LOWER_LOW
EQUAL_HIGH
EQUAL_LOW
```

ainsi que :

```text
BULLISH_STRUCTURE
BEARISH_STRUCTURE
RANGE
TRANSITION
UNKNOWN
```

---

# 8. Swing High

Un Swing High est un sommet local significatif.

Une définition simple :

```text
high[i] > high[i-n:i]
AND
high[i] >= high[i+1:i+n]
```

où :

```text
n = swing_window
```

Exemple avec `n = 2` :

```text
bar -2
bar -1
bar 0 ← potentiel swing high
bar +1
bar +2
```

Le high central doit être supérieur aux highs environnants.

---

# 9. Swing Low

Définition symétrique :

```text
low[i] < low[i-n:i]
AND
low[i] <= low[i+1:i+n]
```

Le point central devient un Swing Low potentiel.

---

# 10. Confirmation différée des swings

Un swing ne doit pas être confirmé immédiatement s'il dépend de futures bougies.

Exemple :

avec :

```text
swing_window = 2
```

le swing au temps :

```text
t
```

ne peut être confirmé qu'au temps :

```text
t + 2 bougies
```

Cette distinction est essentielle pour éviter le look-ahead bias.

Le système doit enregistrer :

```text
pivot_timestamp
confirmation_timestamp
```

---

# 11. Swings adaptatifs

Une fenêtre fixe n'est pas toujours adaptée.

Le moteur pourra ultérieurement utiliser une sensibilité dépendante de la volatilité.

Exemple :

```text
minimum_swing_distance =
ATR × multiplier
```

Ainsi, dans un marché très volatile, les micro-mouvements ne seront pas automatiquement considérés comme des swings significatifs.

---

# 12. Swing Significance Score

Chaque swing peut recevoir un score.

Critères possibles :

- distance au swing précédent ;
- amplitude en ATR ;
- volume ;
- nombre de bougies depuis le dernier swing ;
- réaction du prix ;
- contexte multi-timeframe.

Exemple :

```text
swing_significance ∈ [0,1]
```

---

# 13. Classification des highs et lows

Une fois les swings confirmés :

```text
current_high > previous_high
→ HIGHER_HIGH
```

```text
current_high < previous_high
→ LOWER_HIGH
```

```text
current_low > previous_low
→ HIGHER_LOW
```

```text
current_low < previous_low
→ LOWER_LOW
```

Les égalités doivent utiliser une tolérance.

---

# 14. Equal High / Equal Low

Deux niveaux ne sont presque jamais exactement identiques.

Une tolérance doit donc être utilisée.

Exemple :

```text
abs(price_a - price_b)
<=
ATR × equal_level_tolerance
```

ou :

```text
percentage_distance <= threshold
```

Exemple de classification :

```text
EQUAL_HIGH
EQUAL_LOW
```

---

# 15. Structure haussière

Une structure haussière classique peut être représentée par :

```text
HH
HL
HH
HL
```

Mais QuantLab ne doit pas supposer qu'une séquence parfaite est nécessaire à chaque instant.

Le moteur doit utiliser un état structurel.

Exemple :

```text
BULLISH_CONFIRMED
BULLISH_WEAKENING
TRANSITION
BEARISH_CONFIRMED
```

---

# 16. Structure baissière

Séquence classique :

```text
LL
LH
LL
LH
```

Comme pour la structure haussière, le moteur doit considérer la continuité et non uniquement une paire isolée de pivots.

---

# 17. Structure State Machine

Une machine d'état est recommandée.

Exemple :

```text
UNKNOWN
   ↓
BULLISH
   ↓
BULLISH_WEAKENING
   ↓
TRANSITION
   ↓
BEARISH
```

et inversement.

Les transitions doivent être explicites.

---

# 18. Break of Structure — BOS

Le BOS représente une rupture cohérente avec la structure dominante.

Exemple haussier :

```text
Structure = BULLISH

Previous Swing High = 100

Price closes > 100
→ Potential Bullish BOS
```

Exemple baissier :

```text
Structure = BEARISH

Previous Swing Low = 100

Price closes < 100
→ Potential Bearish BOS
```

---

# 19. Validation d'un BOS

Une rupture ne doit pas être validée uniquement parce qu'une mèche dépasse un niveau.

Plusieurs méthodes doivent pouvoir être testées.

### Méthode A — Close Confirmation

```text
close > swing_high
```

### Méthode B — Buffer

```text
close >
swing_high + ATR × breakout_buffer
```

### Méthode C — Percentage Buffer

```text
close >
swing_high × (1 + threshold)
```

### Méthode D — Multi-bar Confirmation

La rupture doit rester valide pendant plusieurs bougies.

Ces méthodes doivent être comparées statistiquement.

---

# 20. Wick Break

Une rupture par mèche doit être enregistrée séparément.

Exemple :

```text
high > swing_high
AND
close <= swing_high
```

Résultat :

```text
WICK_BREAK
```

Cela peut être utile pour le Smart Money Concepts Engine, notamment pour les liquidity sweeps.

---

# 21. BOS Event

Exemple :

```text
STRUCTURE_BOS_CONFIRMED
```

Payload conceptuel :

```json
{
  "symbol": "BTC-USDT",
  "timeframe": "15m",
  "direction": "BULLISH",
  "level": 100000,
  "break_price": 100250,
  "confidence": 0.81
}
```

---

# 22. Change of Character — CHOCH

Le terme CHOCH est souvent utilisé de manière floue.

QuantLab doit le traiter comme une hypothèse algorithmique.

Définition initiale possible :

> Une rupture significative dans la direction opposée à la structure structurelle dominante.

Exemple :

```text
Structure haussière
HH
HL
HH

Puis rupture confirmée du dernier HL significatif
→ Potential Bearish CHOCH
```

---

# 23. CHOCH n'est pas automatiquement un retournement

Important :

```text
CHOCH
≠
Trend Reversal garanti
```

Il peut représenter :

- correction ;
- transition ;
- fausse rupture ;
- retournement réel.

Le moteur doit donc produire :

```text
POTENTIAL_CHOCH
```

puis éventuellement :

```text
CONFIRMED_STRUCTURE_REVERSAL
```

si des critères supplémentaires sont satisfaits.

---

# 24. Confirmation de retournement

Une confirmation plus robuste peut nécessiter :

```text
CHOCH
+
opposite swing formation
+
new structural break
```

Exemple :

```text
Bullish structure
↓
Bearish CHOCH
↓
Lower High
↓
Bearish BOS
↓
Bearish Structure Confirmed
```

Cette logique doit être configurable.

---

# 25. External Structure vs Internal Structure

Le moteur doit pouvoir distinguer :

### External Structure

Swings majeurs.

### Internal Structure

Micro-structure à l'intérieur du mouvement principal.

Exemple :

```text
External:
4H bullish

Internal:
15m bearish correction
```

Cette distinction est importante pour éviter d'interpréter chaque correction comme un retournement macro.

---

# 26. Paramètres multi-échelles

Une solution possible :

```text
external_swing_window = large
internal_swing_window = small
```

Exemple :

```text
internal = 3 bars
external = 10 bars
```

Les valeurs ne doivent pas être universelles.

---

# 27. Structure hiérarchique

Exemple :

```text
4H:
External bullish structure

1H:
Bullish

15m:
Bearish internal correction

5m:
Bullish micro reversal
```

Cette information pourra alimenter le Scoring Engine.

---

# 28. Protected High / Protected Low

Le moteur peut utiliser les concepts :

```text
PROTECTED_HIGH
PROTECTED_LOW
```

Exemple en tendance haussière :

le dernier Higher Low à l'origine d'un nouveau Higher High peut être considéré comme :

```text
protected_low
```

Une rupture de ce niveau peut signaler une dégradation structurelle.

---

# 29. Structure Invalidation

Chaque structure doit avoir un niveau logique d'invalidation.

Exemple :

```text
BULLISH_STRUCTURE

invalidation_level =
last_protected_low
```

Si le prix casse ce niveau selon les règles de confirmation :

```text
structure_status = INVALIDATED
```

---

# 30. Range Detection

Le moteur doit identifier les ranges.

Une approche peut combiner :

- absence de nouveaux HH/LL significatifs ;
- faible pente ;
- prix contenu dans une zone ;
- oscillation répétée entre deux limites ;
- volatilité relative stable.

Résultat :

```text
RANGE
```

---

# 31. Range Boundaries

Un range doit contenir :

```text
range_high
range_low
range_mid
range_width
range_duration
```

Exemple :

```text
range_mid =
(range_high + range_low) / 2
```

---

# 32. Range Confirmation

Un range ne doit pas être déclaré après deux bougies.

Critères potentiels :

```text
minimum_duration
minimum_touches
maximum_trend_slope
```

Chaque méthode devra être testée.

---

# 33. Range Breakout

Lorsqu'une limite est cassée :

```text
RANGE_BREAKOUT_UP
RANGE_BREAKOUT_DOWN
```

Le breakout doit être distingué d'une simple excursion temporaire.

---

# 34. Failed Breakout

Exemple :

```text
price breaks range high
then closes back inside range
```

Résultat :

```text
FAILED_BREAKOUT_UP
```

Ce type d'événement pourra être utilisé par le SMC Engine.

---

# 35. Expansion

Une expansion représente une phase de déplacement directionnel important.

Critères possibles :

- range de bougie élevé ;
- plusieurs bougies directionnelles ;
- ATR élevé ;
- peu de retracement ;
- volume supérieur à la moyenne.

Résultat :

```text
EXPANSION_UP
EXPANSION_DOWN
```

---

# 36. Compression

Une compression peut être définie par :

- diminution du range ;
- diminution ATR ;
- contraction des swings ;
- réduction de volatilité.

Résultat :

```text
COMPRESSION
```

---

# 37. Displacement

Le concept de displacement peut être traité à l'interface entre structure et SMC.

Définition initiale possible :

```text
Directional move
+
range > ATR × threshold
+
body ratio élevé
```

Le Market Structure Engine peut produire :

```text
STRUCTURAL_DISPLACEMENT
```

Le SMC Engine pourra ensuite l'interpréter.

---

# 38. Body Ratio

Feature :

```text
body_ratio =
abs(close - open)
/
(high - low)
```

Valeur proche de 1 :

```text
forte bougie directionnelle
```

Valeur faible :

```text
fortes mèches / faible conviction directionnelle
```

---

# 39. Structural Impulse

Une impulsion peut être définie comme une séquence produisant :

```text
new swing extreme
+
confirmed BOS
```

Un mouvement intermédiaire contre cette direction peut être considéré comme :

```text
retracement
```

---

# 40. Impulse / Retracement Model

Exemple haussier :

```text
Impulse Up
↓
Retracement
↓
Impulse Up
```

Le moteur peut fournir :

```text
current_leg_type:
IMPULSE
RETRACEMENT
UNKNOWN
```

---

# 41. Structural Leg

Chaque mouvement entre deux pivots confirmés peut être enregistré.

```text
leg_id
start_pivot
end_pivot
direction
duration
price_change
atr_multiple
volume
```

Cela permettra une analyse statistique des jambes de marché.

---

# 42. Leg Statistics

Le Knowledge Engine pourra mesurer :

```text
average_impulse_size
average_retracement_size
retracement_ratio
average_duration
```

par :

- actif ;
- timeframe ;
- régime.

---

# 43. Retracement Ratio

Exemple :

```text
retracement_ratio =
retracement_size / previous_impulse_size
```

Cette métrique peut être utilisée comme feature sans imposer de niveaux Fibonacci arbitraires.

---

# 44. Structural Strength Score

Le moteur peut produire :

```text
structure_strength ∈ [0,1]
```

Features potentielles :

- séquence HH/HL ou LL/LH ;
- taille des impulsions ;
- faible profondeur des retracements ;
- fréquence des BOS ;
- cohérence multi-timeframe ;
- momentum ;
- volume.

Le score doit être validé statistiquement.

---

# 45. Structure Confidence

Le moteur doit séparer :

```text
structure_state
```

de :

```text
structure_confidence
```

Exemple :

```text
state = BULLISH
confidence = 0.91
```

ou :

```text
state = BULLISH
confidence = 0.54
```

---

# 46. Structure Score

Une sortie normalisée peut être :

```text
structure_score ∈ [-100, +100]
```

où :

```text
+100 = structure haussière forte
0 = neutre / range / incertain
-100 = structure baissière forte
```

Ce score sera utilisé par le Scoring Engine.

---

# 47. Exemple de scoring structurel

Illustratif :

```text
HH sequence                    +20
HL sequence                    +20
Bullish BOS                    +20
Protected low intact           +15
Strong impulse                 +10
Higher timeframe alignment     +15
```

Les poids doivent être testés.

---

# 48. Multi-Timeframe Structure

Le moteur doit produire une structure pour chaque timeframe indépendamment.

Exemple :

```yaml
BTC-USDT:

  4H:
    structure: BULLISH

  1H:
    structure: BULLISH

  15m:
    structure: BEARISH_INTERNAL

  5m:
    structure: TRANSITION
```

---

# 49. Structure Alignment

Le moteur peut produire :

```text
FULL_BULLISH_ALIGNMENT
BULLISH_WITH_PULLBACK
MIXED
BEARISH_WITH_PULLBACK
FULL_BEARISH_ALIGNMENT
```

Cette information devra être utilisée par le Scoring Engine, pas interprétée directement comme une entrée.

---

# 50. Higher-Timeframe Dominance

Une règle configurable peut donner davantage d'importance aux horizons supérieurs.

Exemple :

```text
4H weight = 0.4
1H weight = 0.3
15m weight = 0.2
5m weight = 0.1
```

Ces valeurs sont des paramètres expérimentaux.

---

# 51. Structural Conflict

Exemple :

```text
4H bullish
1H bearish
15m bearish
```

Le moteur doit pouvoir retourner :

```text
STRUCTURAL_CONFLICT
```

et une confiance réduite.

---

# 52. Swing Storage

Chaque pivot doit pouvoir être enregistré.

Exemple :

```text
swing_id
symbol
timeframe
pivot_type
pivot_price
pivot_timestamp
confirmation_timestamp
significance
algorithm_version
```

---

# 53. Structure Event Storage

Événements :

```text
SWING_HIGH_CONFIRMED
SWING_LOW_CONFIRMED
BOS_CONFIRMED
CHOCH_DETECTED
STRUCTURE_REVERSAL
RANGE_STARTED
RANGE_BROKEN
STRUCTURE_INVALIDATED
```

Chaque événement doit être traçable.

---

# 54. Reason Codes

Exemples :

```text
BOS_CLOSE_CONFIRMATION
BOS_WICK_ONLY
CHOCH_PROTECTED_LOW_BREAK
CHOCH_PROTECTED_HIGH_BREAK
STRUCTURE_HH_HL
STRUCTURE_LL_LH
STRUCTURE_RANGE
STRUCTURE_CONFLICT
INSUFFICIENT_DATA
```

---

# 55. Anti Look-Ahead

La détection structurelle est particulièrement exposée au look-ahead bias.

Un pivot futur ne doit jamais être utilisé avant sa confirmation.

Exemple :

```text
pivot timestamp = 10:00
confirmation = 10:10
```

Une stratégie exécutée à :

```text
10:05
```

ne doit pas connaître ce pivot comme confirmé.

---

# 56. Event Availability Timestamp

Chaque événement doit donc contenir :

```text
event_timestamp
available_at
```

Exemple :

```text
Swing formed:
10:00

Swing confirmed:
10:10
```

Le backtesting doit utiliser :

```text
available_at = 10:10
```

---

# 57. Data Quality

Le moteur doit refuser ou dégrader la confiance lorsque :

- bougies manquantes ;
- timestamps incohérents ;
- données anormales ;
- historique insuffisant.

Exemple :

```text
structure_state = UNKNOWN
reason = DATA_QUALITY_LOW
```

---

# 58. Warm-Up

Le moteur doit disposer d'un minimum d'historique avant de produire une structure fiable.

État :

```text
WARMING_UP
```

puis :

```text
READY
```

Le nombre minimal de swings requis doit être configurable.

---

# 59. Equal Levels et liquidité

Le moteur peut identifier des zones :

```text
EQUAL_HIGHS
EQUAL_LOWS
```

mais l'interprétation comme pool de liquidité appartient au SMC Engine.

Séparation :

```text
Market Structure:
Equal highs detected

SMC:
Potential liquidity pool
```

---

# 60. Structural Zones

Le moteur peut produire certaines zones purement structurelles :

- swing zones ;
- range boundaries ;
- broken structure levels ;
- protected highs/lows.

Il ne doit pas les qualifier automatiquement d'Order Blocks.

---

# 61. Reclaim

Un niveau structurel cassé puis repris peut produire :

```text
LEVEL_RECLAIMED
```

Exemple :

```text
support broken
↓
price returns above
↓
reclaim
```

Cette feature peut être testée ultérieurement.

---

# 62. Retest

Après BOS :

```text
break
↓
return toward broken level
```

le moteur peut identifier :

```text
STRUCTURAL_RETEST
```

Il ne doit pas supposer que le retest est automatiquement tradable.

---

# 63. BOS Quality Score

Une rupture peut recevoir un score selon :

- distance de clôture au niveau ;
- taille de la bougie ;
- volume ;
- volatility regime ;
- absence de rejet immédiat ;
- suivi directionnel.

Exemple :

```text
bos_quality ∈ [0,1]
```

---

# 64. False Break Analysis

Le système doit mesurer statistiquement :

```text
confirmed_break
then reversal within N bars
```

Cela permettra d'identifier les conditions associées aux faux breakouts.

---

# 65. Structural Follow-Through

Après une rupture :

```text
follow_through =
max_directional_extension
within N bars
```

Cette métrique permet d'évaluer objectivement la qualité historique des BOS.

---

# 66. Maximum Favorable / Adverse Excursion

Pour chaque événement structurel, la recherche peut calculer :

```text
MFE
MAE
```

sur plusieurs horizons.

Exemple :

```text
BOS event
→ MFE after 5 bars
→ MFE after 10 bars
→ MAE after 5 bars
```

Cela permet de tester la valeur prédictive réelle de l'événement.

---

# 67. Statistical Validation

Chaque concept doit être mesuré séparément.

Exemple :

```text
Bullish BOS
```

doit être analysé selon :

- asset ;
- timeframe ;
- regime ;
- session ;
- volatility ;
- volume ;
- trend alignment.

---

# 68. Baseline

Une baseline structurelle simple doit être implémentée avant des variantes complexes.

V1 :

```text
confirmed swing highs/lows
+
HH/HL/LL/LH
+
close-confirmed BOS
+
basic CHOCH
```

Cette baseline servira de référence.

---

# 69. Variantes expérimentales

Versions futures :

### Variant A

Fractal pivots fixes.

### Variant B

ATR-adaptive pivots.

### Variant C

ZigZag volatility-based.

### Variant D

Machine-learning swing segmentation.

Chaque variante doit être comparée à la baseline.

---

# 70. ZigZag

Une méthode basée sur variation minimale peut être étudiée.

Exemple :

```text
new pivot only if move >= ATR × threshold
```

Avantage :

réduit le bruit.

Risque :

retard important et choix arbitraire du seuil.

---

# 71. Causal Pivot Detection

Les méthodes utilisées en live doivent être causales.

Toute méthode utilisant implicitement des informations futures doit être réservée à l'analyse descriptive et marquée comme telle.

---

# 72. Performance

Le moteur doit pouvoir traiter efficacement plusieurs actifs et timeframes.

Complexité à surveiller :

- recalcul intégral des pivots ;
- recalcul multi-timeframe ;
- historique volumineux.

Une architecture incrémentale est recommandée.

---

# 73. Incremental Update

Au lieu de recalculer tout l'historique à chaque bougie :

```text
new candle
↓
update candidate pivot
↓
confirm/invalidate
↓
update structure
```

Cette approche réduit les coûts.

---

# 74. État interne

Le moteur peut maintenir :

```text
candidate_high
candidate_low
last_confirmed_high
last_confirmed_low
protected_high
protected_low
current_structure
```

Cet état doit pouvoir être reconstruit à partir de données persistées si nécessaire.

---

# 75. Déterminisme

Avec :

```text
same data
same parameters
same engine version
```

le résultat doit être identique.

Cette propriété est indispensable pour :

- backtesting ;
- debugging ;
- audit.

---

# 76. Configuration

Exemple :

```yaml
market_structure:

  swing_detection:
    method: fractal
    window: 3

  equal_levels:
    atr_tolerance: 0.10

  breakout:
    confirmation: close
    atr_buffer: 0.05

  choch:
    enabled: true
    require_confirmed_protected_level: true

  multi_timeframe:
    enabled: true

  scoring:
    enabled: true
```

Tous les paramètres doivent être versionnés.

---

# 77. Engine Version

Exemple :

```text
market_structure_engine_version = 1.0.0
```

Toute modification importante des définitions doit changer cette version.

---

# 78. Tests unitaires

Tester :

- swing high ;
- swing low ;
- equal high ;
- equal low ;
- HH ;
- HL ;
- LH ;
- LL ;
- BOS haussier ;
- BOS baissier ;
- wick break ;
- CHOCH ;
- range ;
- invalidation.

---

# 79. Tests synthétiques

Construire des séries déterministes.

### Série haussière

```text
100
105
102
110
106
115
```

Résultat attendu :

```text
HH
HL
HH
HL
HH
```

### Série baissière

```text
115
110
113
105
109
100
```

Résultat :

```text
LL
LH
LL
LH
LL
```

---

# 80. Tests de range

Créer une série oscillant entre :

```text
100
110
```

sans breakout confirmé.

Résultat :

```text
RANGE
```

---

# 81. Tests de fausse rupture

Exemple :

```text
range high = 110

high = 112
close = 108
```

Résultat :

```text
WICK_BREAK
FAILED_BREAKOUT
```

et non BOS confirmé.

---

# 82. Tests anti look-ahead

Le moteur doit être testé bougie par bougie.

Un swing ne doit apparaître dans la sortie qu'à sa date de confirmation.

C'est un test bloquant.

---

# 83. Integration Tests

Tester :

```text
Data Engine
↓
Market Analysis Engine
↓
Market Structure Engine
↓
Storage Engine
```

Le résultat doit rester cohérent entre backtest et live.

---

# 84. Historical Replay Tests

Le moteur doit pouvoir fonctionner en replay :

```text
bar 1
bar 2
bar 3
...
```

comme si les données arrivaient en temps réel.

Le résultat final doit être comparé aux événements enregistrés.

---

# 85. Backtest Validation

Pour chaque événement :

```text
BOS
CHOCH
range break
```

mesurer :

- future returns ;
- MFE ;
- MAE ;
- continuation probability ;
- false break rate.

---

# 86. No Assumed Edge

Règle essentielle :

```text
BOS détecté
≠
edge démontré
```

Le Market Structure Engine produit un événement.

Le Testing Strategy doit déterminer si cet événement contient réellement une information exploitable.

---

# 87. Interaction avec Market Analysis Engine

Entrée :

```text
MarketContext
```

Exemple :

```text
regime = TRENDING
volatility = HIGH
```

Le Market Structure Engine peut utiliser ce contexte pour adapter certains seuils, mais la logique de structure doit rester explicitement versionnée.

---

# 88. Interaction avec SMC Engine

Sorties importantes :

```text
confirmed swings
equal highs/lows
BOS
CHOCH
protected levels
wick breaks
```

Ces données alimenteront :

- liquidity sweeps ;
- Order Blocks ;
- Fair Value Gaps contextualisés ;
- Breakers.

---

# 89. Interaction avec Volume Profile

Le Scoring Engine pourra combiner :

```text
structural level
+
VAH/VAL/POC
```

Le Market Structure Engine ne doit cependant pas intégrer directement la logique du Volume Profile.

---

# 90. Interaction avec Scoring Engine

Sorties possibles :

```text
structure_score
structure_direction
bos_quality
choch_state
timeframe_alignment
structure_confidence
```

Ces features pourront recevoir des pondérations.

---

# 91. Interaction avec Decision Engine

Le Decision Engine peut appliquer des politiques comme :

```text
LONG candidate only if
higher timeframe structure != BEARISH
```

Mais cette règle appartient au Decision Engine, pas au Market Structure Engine.

---

# 92. Interaction avec Risk Engine

La structure peut fournir des niveaux potentiels :

```text
structural_invalidation_level
```

Le Risk Engine peut les utiliser comme information pour calculer :

- stop distance ;
- position size.

Le Risk Engine conserve la décision finale.

---

# 93. Interaction avec Knowledge Engine

Chaque événement doit pouvoir être étudié historiquement.

Question type :

> Les BOS haussiers avec volume élevé et alignement 4H/1H ont-ils une meilleure expectancy que les BOS isolés ?

C'est précisément le genre de question que QuantLab doit rendre mesurable.

---

# 94. Interaction avec AI & Learning Engine

L'IA pourra ultérieurement :

- comparer les algorithmes de swing ;
- identifier des patterns structurels ;
- proposer de nouveaux seuils ;
- classifier des séquences.

Mais aucune définition produite par IA ne doit entrer directement en production.

---

# 95. Monitoring

Métriques :

```text
swings_detected
bos_detected
choch_detected
range_count
structure_unknown_rate
processing_latency
conflict_rate
error_rate
```

Des variations inhabituelles peuvent signaler :

- changement de marché ;
- problème de données ;
- régression logicielle.

---

# 96. Critères d'acceptation V1

Le moteur est valide lorsque :

- les swings sont détectés sans look-ahead ;
- HH/HL/LH/LL sont correctement classifiés ;
- BOS et wick breaks sont séparés ;
- CHOCH possède une définition explicite ;
- les ranges sont identifiables ;
- les événements sont versionnés ;
- la structure multi-timeframe est supportée ;
- un score de confiance est produit ;
- tous les événements peuvent être persistés ;
- les tests unitaires passent ;
- les tests synthétiques passent ;
- le replay historique est déterministe.

---

# 97. Priorités d'implémentation

## V1

- causal swing detection ;
- HH/HL/LH/LL ;
- equal highs/lows ;
- BOS ;
- wick breaks ;
- CHOCH basique ;
- protected levels ;
- range basique ;
- structure score ;
- multi-timeframe ;
- logging.

## V2

- swings adaptatifs ATR ;
- BOS quality ;
- structural legs ;
- impulse/retracement ;
- range quality ;
- failed breakouts.

## V3

- external/internal structure ;
- adaptive state machine ;
- advanced multi-timeframe alignment ;
- statistical quality scores.

## V4

- ML structure segmentation ;
- regime-adaptive swing detection ;
- advanced sequence analysis.

---

# 98. Principe de simplicité

La V1 doit rester volontairement simple.

Une définition simple et reproductible vaut mieux qu'une définition SMC très sophistiquée impossible à reproduire exactement.

QuantLab doit commencer par une baseline structurelle robuste, puis mesurer l'intérêt de chaque couche supplémentaire.

---

# 99. Résultat attendu

Pipeline final :

```text
OHLCV
  ↓
Causal Swing Detection
  ↓
Confirmed Pivots
  ↓
HH / HL / LH / LL
  ↓
Structural State
  ↓
BOS / CHOCH / Range Events
  ↓
Structure Score
  ↓
MarketStructure
  ↓
SMC Engine
Scoring Engine
Decision Engine
Knowledge Engine
```

Le Market Structure Engine doit transformer la géométrie brute du prix en un langage structurel précis, testable et versionné.

---

# 100. Règle fondatrice

> **Une structure de marché n'est pas ce qu'un trader croit voir sur un graphique. Dans QuantLab, c'est le résultat reproductible d'un algorithme documenté.**

Toute interprétation utilisée par le système doit pouvoir être reconstruite à partir :

```text
data
+
parameters
+
algorithm version
```

---

# 101. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `03-Data-Engine.md`
- `05-Market-Analysis-Engine.md`
- `07-Volume-Profile-Engine.md`
- `08-Smart-Money-Concepts-Engine.md`
- `09-Scoring-Engine.md`
- `10-Decision-Engine.md`
- `11-Risk-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `18-Testing-Strategy.md`
- `21-Experiment-Registry.md`

**Prochain document : `07-Volume-Profile-Engine.md`**
