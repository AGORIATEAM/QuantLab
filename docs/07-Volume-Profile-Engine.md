# 07 — Volume Profile Engine

**Projet : QuantLab**  
**Document : Volume Profile Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Volume Profile Engine est responsable de l'analyse de la distribution de l'activité de marché par niveau de prix.

Contrairement au volume classique, qui répond principalement à :

> Combien de volume a été échangé pendant une période donnée ?

le Volume Profile cherche à répondre à :

> À quels niveaux de prix l'activité s'est-elle concentrée ?

Le moteur doit transformer les données de marché en une représentation quantitative permettant d'identifier :

- Point of Control (POC) ;
- Value Area High (VAH) ;
- Value Area Low (VAL) ;
- High Volume Nodes (HVN) ;
- Low Volume Nodes (LVN) ;
- zones d'acceptation ;
- zones de faible acceptation ;
- distribution du volume ;
- évolution du profil dans le temps ;
- relation entre prix actuel et zones de volume.

Le Volume Profile Engine ne prend aucune décision de trading.

Il produit des observations et des features destinées aux moteurs suivants.

---

# 2. Principe fondamental

Le moteur doit distinguer :

```text
Volume by Time
```

et :

```text
Volume by Price
```

Exemple :

```text
Volume classique

10:00 → 500 BTC
10:05 → 800 BTC
10:10 → 400 BTC
```

Volume Profile :

```text
100000 → 120 BTC
100100 → 350 BTC
100200 → 900 BTC
100300 → 280 BTC
```

Cette seconde représentation permet d'étudier les zones où le marché a réellement concentré son activité.

---

# 3. Responsabilités

Le moteur doit :

1. recevoir des données validées ;
2. définir une plage d'analyse ;
3. construire les price bins ;
4. distribuer le volume par prix ;
5. calculer le POC ;
6. calculer la Value Area ;
7. déterminer VAH et VAL ;
8. détecter HVN et LVN ;
9. produire des profils de session ;
10. produire des profils fixes ;
11. produire des profils roulants ;
12. comparer plusieurs profils ;
13. générer des features normalisées ;
14. publier des événements ;
15. conserver les résultats ;
16. garantir la reproductibilité des calculs.

---

# 4. Hors périmètre

Le moteur ne doit pas :

- envoyer des ordres ;
- déterminer la taille d'une position ;
- décider qu'un POC est automatiquement un support ;
- décider qu'un LVN constitue automatiquement une entrée ;
- interpréter seul un liquidity sweep ;
- créer un signal final ;
- modifier une stratégie en production.

Le Scoring Engine et le Decision Engine restent responsables de l'utilisation des informations produites.

---

# 5. Sources de données

Le moteur peut fonctionner avec plusieurs niveaux de précision.

## Niveau 1 — OHLCV

Disponible presque partout.

```text
open
high
low
close
volume
```

Le volume doit être approximativement réparti sur la plage de prix de chaque bougie.

Cette méthode est une approximation.

## Niveau 2 — Trade Data

Chaque trade contient :

```text
timestamp
price
quantity
```

Le volume peut alors être attribué précisément au prix exécuté.

## Niveau 3 — Tick / AggTrades

Permet une construction plus précise du profil.

## Niveau 4 — Order Flow enrichi

Peut inclure :

- aggressor side ;
- bid volume ;
- ask volume ;
- delta.

Cette couche pourra alimenter des extensions futures.

---

# 6. Hiérarchie de qualité

Le moteur doit enregistrer la qualité de la source utilisée.

Exemple :

```text
TICK_EXACT
TRADE_EXACT
CANDLE_ESTIMATED
DEGRADED
```

Un profil calculé depuis OHLCV ne doit pas être présenté comme équivalent à un profil construit à partir de trades réels.

---

# 7. Structure de sortie

Exemple conceptuel :

```python
VolumeProfile:
    profile_id
    symbol
    timeframe

    start_timestamp
    end_timestamp

    profile_type

    poc
    vah
    val

    value_area_percentage

    hvn_levels
    lvn_levels

    total_volume
    price_bins

    current_price_location
    profile_shape

    confidence
    data_quality

    algorithm_version
```

---

# 8. Price Bins

Le profil doit diviser la plage de prix en intervalles.

Exemple :

```text
100000 - 100100
100100 - 100200
100200 - 100300
```

Chaque intervalle reçoit une quantité de volume.

---

# 9. Taille des bins

La taille des bins doit être configurable.

Méthodes possibles :

### Fixed Tick

```text
bin_size = 10 USD
```

### Percentage

```text
bin_size = price × 0.0005
```

### ATR-Based

```text
bin_size = ATR × coefficient
```

### Fixed Number of Rows

Exemple :

```text
100 bins sur toute la plage
```

Aucune méthode ne doit être considérée comme universellement optimale sans validation.

---

# 10. Normalisation multi-actifs

Un bin fixe en dollars fonctionne mal sur plusieurs actifs.

Exemple :

```text
BTC = 100000
ETH = 4000
XAU/USD = 3000
```

Le moteur doit donc supporter des méthodes adaptatives.

Une approche relative ou basée sur la volatilité est recommandée pour les comparaisons multi-actifs.

---

# 11. Distribution OHLCV approximative

Lorsque seules les bougies sont disponibles, plusieurs méthodes sont possibles.

### Méthode uniforme

```text
volume réparti uniformément entre low et high
```

### Méthode pondérée

Une plus grande part du volume peut être attribuée autour :

```text
open
close
typical price
```

### Méthode intrabar

Si des données de timeframe inférieur existent :

```text
1H profile
↓
construit avec données 1m
```

Cette méthode est préférable lorsque disponible.

---

# 12. Principe de précision

Pour un profil 4H :

```text
4H OHLCV
```

est moins précis que :

```text
1m trades / candles agrégés dans la fenêtre 4H
```

Le moteur doit donc utiliser la granularité la plus fine disponible, dans des limites raisonnables de coût.

---

# 13. Point of Control — POC

Le POC correspond au niveau ou bin ayant reçu le plus grand volume.

Formellement :

```text
POC =
argmax(volume_by_price)
```

Exemple :

```text
100000 → 200
100100 → 450
100200 → 900 ← POC
100300 → 300
```

Résultat :

```text
POC = 100200
```

---

# 14. POC Tie

Si plusieurs bins possèdent exactement le même volume maximal, la règle de résolution doit être déterministe.

Méthodes possibles :

- bin le plus proche du prix moyen ;
- bin le plus proche du midpoint du profil ;
- premier bin ;
- moyenne des bins concernés.

La méthode retenue doit être versionnée.

---

# 15. Value Area

La Value Area représente la zone contenant une proportion définie du volume total.

Convention courante :

```text
70%
```

Mais QuantLab doit rendre ce paramètre configurable.

Exemple :

```text
value_area_percentage = 0.70
```

---

# 16. Calcul de la Value Area

Algorithme possible :

1. commencer au POC ;
2. comparer le volume des bins voisins ;
3. ajouter le côté ayant le plus de volume ;
4. continuer jusqu'à atteindre le pourcentage cible.

Résultat :

```text
VAL
↓
Value Area
↓
POC
↓
Value Area
↓
VAH
```

---

# 17. VAH

```text
VAH = Value Area High
```

Il représente la limite supérieure de la zone de valeur calculée.

---

# 18. VAL

```text
VAL = Value Area Low
```

Il représente la limite inférieure de la zone de valeur.

---

# 19. Position du prix par rapport à la Value Area

Le moteur doit produire :

```text
ABOVE_VALUE
INSIDE_VALUE
BELOW_VALUE
AT_VAH
AT_VAL
```

avec une tolérance configurable.

---

# 20. Distance normalisée

Exemple :

```text
distance_to_poc
distance_to_vah
distance_to_val
```

Ces distances doivent être normalisées.

Possibilités :

```text
distance / ATR
```

ou :

```text
distance / price
```

---

# 21. High Volume Node — HVN

Un HVN représente une zone locale de concentration élevée du volume.

Une définition algorithmique doit être utilisée.

Exemple :

```text
volume_bin >
local_percentile_threshold
```

ou détection de maxima locaux sur une distribution lissée.

---

# 22. Low Volume Node — LVN

Un LVN représente une zone de faible concentration relative.

Définition possible :

```text
volume_bin <
local_percentile_threshold
```

ou minima locaux entre deux zones de forte activité.

---

# 23. HVN/LVN et interprétation

QuantLab ne doit pas coder comme vérité :

```text
HVN = support
LVN = breakout
```

Ce sont des hypothèses de marché.

Le moteur produit uniquement :

```text
HVN detected
LVN detected
```

La valeur prédictive doit être étudiée expérimentalement.

---

# 24. Lissage

Les distributions peuvent être bruitées.

Le moteur pourra appliquer :

- moving average ;
- Gaussian smoothing ;
- kernel smoothing.

Le niveau de lissage doit être configurable et versionné.

Un lissage excessif peut supprimer des informations utiles.

---

# 25. Profile Types

Le moteur doit supporter plusieurs types de profils.

```text
SESSION_PROFILE
FIXED_RANGE_PROFILE
ROLLING_PROFILE
ANCHORED_PROFILE
COMPOSITE_PROFILE
```

---

# 26. Session Profile

Profil calculé sur une session définie.

Exemples :

```text
ASIA
LONDON
NEW_YORK
DAILY
```

Pour crypto, les frontières de session sont analytiques et doivent être définies explicitement.

---

# 27. Daily Profile

Convention recommandée :

```text
00:00 UTC
→
23:59:59 UTC
```

pour la crypto.

Cette convention doit rester configurable selon le marché.

---

# 28. Fixed Range Profile

Profil calculé entre :

```text
start_timestamp
end_timestamp
```

Exemple :

```text
2026-08-01 00:00
→
2026-08-05 00:00
```

Très utile pour la recherche et le backtesting.

---

# 29. Rolling Profile

Exemple :

```text
last 24h
last 100 candles
last 7 days
```

À chaque nouvelle observation, le profil est recalculé ou mis à jour incrémentalement.

---

# 30. Anchored Profile

Le profil peut être ancré à un événement.

Exemples :

```text
major swing
BOS
session open
weekly open
high-impact event
```

L'ancrage doit provenir d'un événement explicite, jamais d'une sélection rétrospective cachée.

---

# 31. Composite Profile

Un profil composite combine une période longue.

Exemple :

```text
30 days
90 days
year-to-date
```

Il peut être utilisé pour identifier des zones historiques importantes.

---

# 32. Developing POC

Le moteur doit pouvoir suivre le POC pendant la construction du profil.

```text
developing_poc
```

Exemple :

```text
09:00 → 100100
10:00 → 100200
11:00 → 100200
12:00 → 100350
```

---

# 33. POC Migration

Le déplacement du POC peut être mesuré.

```text
POC_MIGRATING_UP
POC_STABLE
POC_MIGRATING_DOWN
```

Cette information peut devenir une feature.

Elle ne doit pas être interprétée automatiquement comme direction future.

---

# 34. Value Area Migration

De même :

```text
VAH migration
VAL migration
Value Area midpoint migration
```

peuvent être suivis dans le temps.

---

# 35. Previous Session Levels

Le moteur doit pouvoir exposer :

```text
previous_session_poc
previous_session_vah
previous_session_val
```

ainsi que leurs distances au prix courant.

---

# 36. Naked POC

Un ancien POC non revisité peut être marqué :

```text
UNTESTED_POC
```

ou :

```text
NAKED_POC
```

Mais cette notion doit être définie précisément.

Exemple :

```text
price has not traded inside POC tolerance zone since profile close
```

---

# 37. Tested Levels

Chaque niveau historique peut conserver :

```text
first_test_timestamp
test_count
last_test_timestamp
```

Cela permettra d'étudier si la réaction statistique évolue avec le nombre de tests.

---

# 38. Profile Shape

Le moteur pourra classifier la forme du profil.

Exemples :

```text
D_SHAPE
P_SHAPE
B_SHAPE
DOUBLE_DISTRIBUTION
THIN_PROFILE
UNKNOWN
```

Ces catégories sont utiles uniquement si elles possèdent des définitions algorithmiques.

---

# 39. D-Shape

Profil relativement équilibré autour du centre.

Caractéristiques possibles :

- POC proche du midpoint ;
- distribution approximativement symétrique ;
- concentration centrale.

La définition exacte doit être testée.

---

# 40. P-Shape et b-Shape

Ces formes sont souvent interprétées discrétionnairement.

QuantLab doit éviter d'intégrer leur signification traditionnelle comme vérité.

Le moteur pourra classifier la géométrie, puis l'Experiment Registry déterminera si cette classification possède une utilité réelle.

---

# 41. Double Distribution

Détection possible :

```text
HVN
↓
LVN significatif
↓
HVN
```

Résultat :

```text
DOUBLE_DISTRIBUTION
```

Les seuils doivent être explicites.

---

# 42. Acceptance

Le moteur peut mesurer l'acceptation autour d'un niveau.

Features possibles :

- temps passé ;
- volume échangé ;
- nombre de traversées ;
- stabilité du POC.

Exemple :

```text
acceptance_score ∈ [0,1]
```

---

# 43. Rejection

La faible activité suivie d'un éloignement rapide peut être étudiée comme rejet.

Mais :

```text
rejection
```

doit être défini quantitativement.

Exemple :

```text
short residence time
+
low volume
+
rapid directional move
```

---

# 44. Time at Price

Si les données le permettent :

```text
time_at_price
```

peut compléter :

```text
volume_at_price
```

Les deux concepts ne doivent pas être confondus.

---

# 45. Volume Density

Exemple :

```text
volume_density =
volume_bin / bin_width
```

Cette mesure peut être utile lorsque les tailles de bins ne sont pas identiques.

---

# 46. Relative Volume Density

Normalisation possible :

```text
volume_bin
/
mean_profile_bin_volume
```

Cela permet de comparer différents profils.

---

# 47. HVN Score

Chaque HVN peut recevoir :

```text
hvn_score
```

selon :

- volume relatif ;
- largeur ;
- persistance ;
- nombre de profils où la zone apparaît ;
- distance au POC.

---

# 48. LVN Score

De même :

```text
lvn_score
```

peut mesurer la profondeur du creux de volume.

---

# 49. Zone plutôt que point

POC, HVN et LVN ne doivent pas toujours être traités comme un prix exact.

Une zone peut être plus robuste.

Exemple :

```text
POC zone:
100190 → 100210
```

La largeur peut dépendre :

- du bin size ;
- de l'ATR ;
- de la liquidité.

---

# 50. Profile Overlap

Le moteur peut comparer deux Value Areas.

Exemple :

```text
overlap_ratio =
intersection(previous_value_area, current_value_area)
/
union(...)
```

Cela permet de quantifier la stabilité du marché.

---

# 51. Value Migration

Exemple :

```text
current_poc > previous_poc
current_vah > previous_vah
current_val > previous_val
```

Résultat potentiel :

```text
VALUE_MIGRATION_UP
```

L'interprétation directionnelle reste à tester.

---

# 52. Balance / Imbalance

Une distribution stable et fortement chevauchante peut être classifiée :

```text
BALANCED_PROFILE
```

Une migration rapide avec faible overlap :

```text
IMBALANCED_PROFILE
```

Ces concepts doivent être définis statistiquement.

---

# 53. Profile Stability Score

Exemple :

```text
profile_stability ∈ [0,1]
```

Features :

- POC movement ;
- Value Area overlap ;
- distribution similarity ;
- HVN persistence.

---

# 54. Distribution Similarity

Deux profils peuvent être comparés par :

- correlation ;
- cosine similarity ;
- Jensen-Shannon divergence ;
- Wasserstein distance.

Ces méthodes sont particulièrement intéressantes pour la recherche future.

---

# 55. Current Price Context

Le moteur doit produire un résumé exploitable.

Exemple :

```yaml
price_context:
  location: ABOVE_VALUE
  distance_to_poc_atr: 1.4
  distance_to_vah_atr: 0.3
  nearest_hvn_distance_atr: 0.8
  nearest_lvn_distance_atr: 0.2
```

---

# 56. Nearest Level

Le moteur doit pouvoir retourner :

```text
nearest_poc
nearest_hvn
nearest_lvn
nearest_vah
nearest_val
```

ainsi que :

```text
distance
direction
profile_age
```

---

# 57. Confluence

Le Volume Profile Engine ne calcule pas le score final de confluence.

Il expose simplement ses niveaux.

Le Scoring Engine pourra détecter :

```text
Market Structure Swing
+
Previous VAH
+
HVN
```

comme confluence potentielle.

---

# 58. Multi-Timeframe Volume Profile

Plusieurs profils peuvent coexister.

Exemple :

```text
Daily Profile
Weekly Profile
Monthly Composite
Rolling 24h
```

Le moteur doit conserver leurs identités séparément.

---

# 59. Higher-Timeframe Levels

Exemple :

```text
Weekly POC
Daily POC
Current Session POC
```

Ces niveaux peuvent avoir des poids différents dans le Scoring Engine.

Le Volume Profile Engine ne fixe pas ces poids.

---

# 60. Futures / CEX Volume

Pour certains marchés centralisés, le volume observé représente l'activité de la plateforme concernée.

Il ne représente pas nécessairement le marché mondial.

Le moteur doit conserver :

```text
venue
```

dans les métadonnées.

---

# 61. Crypto Fragmentation

Exemple :

```text
BTC-USDT Binance
BTC-USDT OKX
BTC-USDT Bybit
```

peuvent produire des profils légèrement différents.

QuantLab doit pouvoir :

- conserver les profils par venue ;
- construire éventuellement un profil consolidé.

---

# 62. Consolidated Profile

Une version future pourra agréger plusieurs venues.

Problèmes à traiter :

- symbol mapping ;
- quote currency ;
- volume normalization ;
- timestamps ;
- doublons ;
- différences de liquidité.

Le profil consolidé doit être explicitement marqué comme tel.

---

# 63. Spot vs Perpetual

Les profils :

```text
BTC spot
```

et :

```text
BTC perpetual
```

ne doivent pas être mélangés automatiquement.

Ils représentent des marchés différents.

---

# 64. XAU/USD

Pour l'or, le volume disponible dépend du fournisseur et du type de marché.

Le moteur doit distinguer :

- futures volume ;
- CFD tick volume ;
- spot proxy.

La qualité et la signification des données doivent être documentées.

---

# 65. DEX Volume Profile

Pour un DEX, le volume peut être construit à partir :

```text
swaps
price
quantity
block_timestamp
```

Des contraintes spécifiques existent :

- AMM pricing ;
- concentrated liquidity ;
- gas ;
- MEV ;
- pool fragmentation.

Une implémentation DEX devra être séparée de la V1 CEX.

---

# 66. Incremental Calculation

Le moteur ne doit pas recalculer l'intégralité d'un profil à chaque nouveau trade lorsque cela peut être évité.

Exemple :

```text
new trade
↓
identify bin
↓
add volume
↓
update POC if necessary
↓
update profile state
```

---

# 67. Rolling Window Expiration

Pour un profil roulant :

```text
new data enters
old data exits
```

Le moteur doit pouvoir soustraire le volume expiré.

Cela nécessite une structure de données adaptée.

---

# 68. Determinism

Avec :

```text
same data
same binning
same parameters
same algorithm version
```

le profil doit être identique.

---

# 69. Anti Look-Ahead

Un profil en développement à 10:00 ne doit utiliser que les données disponibles jusqu'à 10:00.

Un backtest ne doit jamais utiliser le POC final d'une session avant la clôture de cette session.

Cette erreur est particulièrement dangereuse.

---

# 70. Developing vs Final Profile

Le système doit distinguer :

```text
DEVELOPING
```

et :

```text
FINAL
```

Exemple :

```text
Daily POC at 12:00
```

n'est pas le même objet conceptuel que :

```text
Final Daily POC at 23:59
```

---

# 71. Availability Timestamp

Chaque niveau doit contenir :

```text
calculated_at
available_at
```

Le backtest doit respecter `available_at`.

---

# 72. Versioning

Le profil doit conserver :

```text
algorithm_version
binning_method
bin_size
value_area_percentage
smoothing_method
source_granularity
```

Sans cela, une expérience n'est pas reproductible.

---

# 73. Storage

Tables logiques potentielles :

```text
volume_profiles
volume_profile_bins
volume_profile_levels
volume_profile_events
```

Le schéma définitif sera détaillé dans `23-Database-Schema.md`.

---

# 74. Volume Profile Record

Exemple :

```text
profile_id
symbol
venue
profile_type
start_timestamp
end_timestamp
status
poc
vah
val
total_volume
data_quality
algorithm_version
created_at
```

---

# 75. Bin Record

Exemple :

```text
profile_id
price_low
price_high
price_mid
volume
buy_volume
sell_volume
trade_count
```

Les champs buy/sell peuvent être nuls si la source ne permet pas leur calcul.

---

# 76. Events

Événements possibles :

```text
VOLUME_PROFILE_UPDATED
VOLUME_PROFILE_FINALIZED
POC_CHANGED
PRICE_ENTERED_VALUE
PRICE_LEFT_VALUE
VAH_TESTED
VAL_TESTED
HVN_TESTED
LVN_TESTED
```

Ces événements doivent rester descriptifs.

---

# 77. Reason Codes

Exemples :

```text
PRICE_ABOVE_VALUE
PRICE_INSIDE_VALUE
PRICE_BELOW_VALUE
POC_MIGRATING_UP
POC_MIGRATING_DOWN
HVN_NEAR_PRICE
LVN_NEAR_PRICE
PROFILE_LOW_QUALITY
PROFILE_INCOMPLETE
```

---

# 78. Confidence

Un score de confiance peut dépendre :

```text
data_quality
sample_size
profile_duration
source_granularity
bin_stability
```

Exemple :

```text
confidence ∈ [0,1]
```

---

# 79. Minimum Sample

Un profil ne doit pas être considéré fiable avec trop peu de données.

Paramètres possibles :

```text
minimum_trades
minimum_candles
minimum_volume
minimum_duration
```

Si le seuil n'est pas atteint :

```text
profile_status = INSUFFICIENT_DATA
```

---

# 80. Data Quality Integration

Le moteur doit recevoir les informations du Data Engine.

Si :

```text
missing trades
large data gap
duplicate data
```

alors :

```text
confidence ↓
```

ou le profil doit être rejeté.

---

# 81. Testing unitaire

Tester :

- bin assignment ;
- volume aggregation ;
- POC ;
- Value Area ;
- VAH ;
- VAL ;
- HVN ;
- LVN ;
- distance calculations ;
- profile overlap ;
- POC migration.

---

# 82. Synthetic Profile Tests

Exemple :

```text
100 → 10
101 → 20
102 → 100
103 → 20
104 → 10
```

Résultat attendu :

```text
POC = 102
```

La Value Area doit être calculable exactement.

---

# 83. Edge Cases

Tester :

- volume nul ;
- un seul bin ;
- égalité de POC ;
- très faible plage ;
- énorme gap ;
- prix négatif impossible pour les actifs concernés ;
- données manquantes ;
- profil vide.

---

# 84. Replay Testing

Le profil doit être reconstruit progressivement :

```text
trade 1
trade 2
trade 3
...
```

Le POC en développement doit être identique à celui obtenu en environnement live avec les mêmes données.

---

# 85. Performance Tests

Tester :

```text
1 million trades
10 million trades
multiple symbols
multiple profiles
```

Mesures :

```text
processing_latency
memory_usage
update_rate
storage_size
```

---

# 86. Statistical Validation

Les niveaux doivent être étudiés objectivement.

Exemple :

```text
price reaches previous VAH
```

Mesurer ensuite :

```text
future_return
MFE
MAE
rejection_probability
break_probability
```

sur différents horizons.

---

# 87. No Assumed Edge

Règle :

```text
POC
≠
support garanti
```

```text
VAH
≠
short automatique
```

```text
VAL
≠
long automatique
```

```text
LVN
≠
accélération garantie
```

Le moteur décrit une distribution. Le Testing Strategy détermine ce qui possède réellement une valeur prédictive.

---

# 88. Experiment Registry

Les expériences devront pouvoir tester :

```text
EXP-VP-001
Previous VAH reaction

EXP-VP-002
Previous VAL reaction

EXP-VP-003
POC migration

EXP-VP-004
LVN breakout

EXP-VP-005
HVN mean reversion
```

Chaque hypothèse doit être séparée.

---

# 89. Interaction avec Market Analysis Engine

Le Market Analysis Engine fournit :

```text
regime
volatility
activity
```

Le Volume Profile Engine peut utiliser la volatilité pour adapter certains paramètres comme la taille des bins.

---

# 90. Interaction avec Market Structure Engine

Le moteur reçoit potentiellement :

```text
swings
BOS
ranges
```

pour créer des profils ancrés.

Exemple :

```text
Anchored Profile
from confirmed swing low
```

L'ancrage doit être disponible causalement.

---

# 91. Interaction avec SMC Engine

Le SMC Engine pourra combiner :

```text
liquidity zone
+
LVN/HVN
+
Value Area
```

Mais les responsabilités doivent rester séparées.

---

# 92. Interaction avec Scoring Engine

Features possibles :

```text
distance_to_poc
distance_to_vah
distance_to_val
nearest_hvn_distance
nearest_lvn_distance
inside_value
profile_migration_score
profile_stability
volume_profile_confidence
```

Le Scoring Engine décide des pondérations.

---

# 93. Interaction avec Decision Engine

Le Decision Engine peut utiliser des règles comme :

```text
avoid breakout strategy
if price is deep inside balanced value
```

si cette règle est validée expérimentalement.

Elle n'appartient pas au Volume Profile Engine.

---

# 94. Interaction avec Risk Engine

Les zones de volume peuvent aider à estimer :

- proximité de zones actives ;
- contexte de liquidité ;
- potentiel de slippage indirect.

Le Risk Engine conserve la responsabilité du risque final.

---

# 95. Interaction avec Knowledge Engine

Le Knowledge Engine doit pouvoir répondre à des questions comme :

> Les breakouts de LVN fonctionnent-ils mieux lorsque le marché est déjà en expansion ?

ou :

> Les retours vers le POC ont-ils une expectancy positive en régime de range ?

Le stockage doit permettre ce type d'analyse.

---

# 96. Interaction avec AI & Learning Engine

L'IA pourra ultérieurement :

- classifier les formes de profil ;
- identifier des distributions récurrentes ;
- proposer de nouveaux descriptors ;
- comparer des méthodes de binning ;
- rechercher des interactions entre structure et volume.

Toute proposition doit être validée hors échantillon.

---

# 97. Monitoring

Métriques :

```text
profiles_generated
profiles_finalized
profile_update_latency
poc_changes
invalid_profiles
low_quality_profiles
bin_count
memory_usage
processing_errors
```

---

# 98. Configuration

Exemple :

```yaml
volume_profile:

  enabled: true

  source:
    preferred: trades
    fallback: ohlcv

  binning:
    method: atr
    atr_multiplier: 0.05

  value_area:
    percentage: 0.70

  hvn:
    enabled: true

  lvn:
    enabled: true

  profiles:
    session: true
    rolling: true
    anchored: true

  rolling:
    window: 24h
```

Tous les paramètres doivent être versionnés.

---

# 99. Priorités V1

Implémenter :

- trade-based profile lorsque disponible ;
- OHLCV fallback ;
- deterministic binning ;
- POC ;
- VAH ;
- VAL ;
- Value Area ;
- basic HVN/LVN ;
- session profile ;
- fixed range profile ;
- rolling profile ;
- distance features ;
- storage ;
- tests.

---

# 100. Priorités V2

Ajouter :

- anchored profiles ;
- developing POC ;
- POC migration ;
- Value Area migration ;
- profile overlap ;
- tested/untested levels ;
- profile stability.

---

# 101. Priorités V3

Ajouter :

- profile shape classification ;
- composite profiles ;
- consolidated exchange profiles ;
- advanced HVN/LVN detection ;
- distribution similarity.

---

# 102. Priorités V4

Ajouter :

- order-flow enriched profiles ;
- buy/sell volume ;
- delta profile ;
- DEX profiles ;
- ML profile classification.

---

# 103. Critères d'acceptation

Le moteur V1 est considéré valide lorsque :

- le profil est reproductible ;
- le POC est calculé correctement ;
- VAH et VAL sont déterministes ;
- le pourcentage de Value Area est configurable ;
- les profils finalisés et en développement sont séparés ;
- aucun look-ahead n'est possible ;
- les profils possèdent une indication de qualité ;
- les niveaux peuvent être persistés ;
- les calculs sont versionnés ;
- les tests unitaires passent ;
- les tests synthétiques passent ;
- le replay produit les mêmes résultats que le calcul live.

---

# 104. Risques techniques

Principaux risques :

### Mauvaise granularité

Un profil OHLCV peut donner une illusion de précision.

### Binning arbitraire

Un changement de taille de bin peut modifier fortement HVN/LVN.

### Look-Ahead

Utiliser un profil final avant la fin de la période invalide un backtest.

### Surinterprétation

Des concepts populaires peuvent sembler intuitifs sans posséder d'edge statistique.

### Fragmentation

Le volume crypto dépend de la venue observée.

Ces risques doivent être explicitement contrôlés.

---

# 105. Principe de recherche

Pour chaque concept Volume Profile :

```text
POC
VAH
VAL
HVN
LVN
profile migration
```

QuantLab doit demander :

```text
Quelle information nouvelle cette feature apporte-t-elle ?
```

Puis :

```text
Cette information améliore-t-elle réellement
la performance hors échantillon ?
```

Si la réponse est non, la feature ne doit pas être conservée uniquement parce qu'elle est populaire chez les traders.

---

# 106. Résultat attendu

Pipeline :

```text
Market Data
    ↓
Trade / Intrabar Aggregation
    ↓
Price Binning
    ↓
Volume Distribution
    ↓
POC
VAH
VAL
HVN
LVN
    ↓
Profile Context
    ↓
VolumeProfile
    ↓
Scoring Engine
Decision Engine
Knowledge Engine
AI & Learning Engine
```

---

# 107. Règle fondatrice

> **Le Volume Profile Engine mesure où l'activité s'est produite. Il ne suppose pas pourquoi elle s'est produite ni ce que le prix fera ensuite.**

Cette séparation est indispensable pour éviter de transformer des conventions de trading en pseudo-vérités algorithmiques.

---

# 108. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `03-Data-Engine.md`
- `04-Storage-Engine.md`
- `05-Market-Analysis-Engine.md`
- `06-Market-Structure-Engine.md`
- `08-Smart-Money-Concepts-Engine.md`
- `09-Scoring-Engine.md`
- `10-Decision-Engine.md`
- `11-Risk-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `18-Testing-Strategy.md`
- `21-Experiment-Registry.md`
- `23-Database-Schema.md`

**Prochain document : `08-Smart-Money-Concepts-Engine.md`**
