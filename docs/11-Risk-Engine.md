# 11 — Risk Engine

**Projet : QuantLab**  
**Document : Risk Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Risk Engine est la couche de protection financière centrale de QuantLab.

Il reçoit les intentions produites par le Decision Engine et détermine si QuantLab est autorisé à engager, conserver, réduire ou supprimer une exposition.

Sa mission n'est pas de maximiser les gains.

Sa mission est d'empêcher qu'une stratégie, une erreur logicielle, une anomalie de marché ou une accumulation d'expositions puisse mettre le système en danger.

Le Risk Engine doit répondre à quatre questions :

```text
Ce trade est-il autorisé ?
↓
Combien pouvons-nous risquer ?
↓
Quelle exposition pouvons-nous accepter ?
↓
Le portefeuille reste-t-il dans ses limites après cette opération ?
```

Sorties principales :

```text
APPROVED
MODIFIED
REJECTED
FORCE_REDUCE
FORCE_EXIT
```

---

# 2. Principe fondamental

Dans QuantLab :

> **Aucune stratégie ne possède le droit de risquer du capital. Elle peut uniquement demander l'autorisation au Risk Engine.**

Le flux obligatoire est :

```text
Analysis
↓
Scoring
↓
Decision
↓
TradeIntent
↓
RISK ENGINE
↓
ApprovedIntent
↓
Execution Engine
```

Aucun moteur analytique ne doit pouvoir contourner cette chaîne.

---

# 3. Priorité absolue

Le Risk Engine doit disposer d'une priorité supérieure :

```text
Risk Engine
>
Decision Engine
>
Strategy
>
Signal
```

Si :

```text
Decision Engine = ENTER_LONG
```

et :

```text
Risk Engine = REJECTED
```

le résultat final est :

```text
NO EXECUTION
```

sans exception automatique.

---

# 4. Responsabilités

Le Risk Engine doit :

1. valider chaque nouvelle intention ;
2. calculer le risque monétaire ;
3. calculer la taille de position ;
4. contrôler le stop ;
5. contrôler le levier ;
6. contrôler l'exposition par actif ;
7. contrôler l'exposition globale ;
8. contrôler les positions corrélées ;
9. contrôler les pertes journalières ;
10. contrôler le drawdown ;
11. contrôler le nombre de positions ;
12. contrôler les ordres en attente ;
13. gérer les limites par stratégie ;
14. gérer les limites par portefeuille ;
15. gérer les états de réduction ;
16. imposer des sorties de sécurité ;
17. gérer les kill switches ;
18. enregistrer chaque décision de risque ;
19. publier les événements de risque ;
20. fournir un état de risque global.

---

# 5. Hors périmètre

Le Risk Engine ne doit pas :

- détecter les setups ;
- calculer le score de marché ;
- décider qu'un Order Block est valide ;
- choisir une stratégie ;
- envoyer directement les ordres à l'exchange ;
- optimiser ses limites en live sans gouvernance ;
- augmenter arbitrairement le risque parce qu'une stratégie vient de gagner plusieurs trades.

---

# 6. Architecture

```text
Decision Engine
      ↓
  TradeIntent
      ↓
┌──────────────────────────┐
│       RISK ENGINE        │
├──────────────────────────┤
│ Trade Risk               │
│ Position Sizing          │
│ Portfolio Risk           │
│ Exposure Limits          │
│ Drawdown Controls        │
│ Correlation Controls     │
│ Kill Switches            │
└────────────┬─────────────┘
             ↓
      RiskDecision
             ↓
APPROVED / MODIFIED / REJECTED
             ↓
      Execution Engine
```

---

# 7. Entrées principales

Le moteur peut recevoir :

```text
TradeIntent
PortfolioState
PositionState
AccountState
MarketState
ExecutionState
RiskConfiguration
```

Il peut également utiliser :

```text
volatility
liquidity
spread
estimated slippage
correlations
```

---

# 8. RiskDecision

Structure conceptuelle :

```python
RiskDecision:
    risk_decision_id
    intent_id

    timestamp
    strategy_id
    symbol
    direction

    status

    requested_entry
    approved_entry

    requested_risk
    approved_risk

    position_size
    notional_exposure

    stop_price
    stop_distance

    leverage

    portfolio_risk_before
    portfolio_risk_after

    reason_codes

    risk_version
```

---

# 9. États

Le moteur doit pouvoir retourner :

```text
APPROVED
MODIFIED
REJECTED
FORCE_REDUCE
FORCE_EXIT
```

---

# 10. APPROVED

L'intention respecte toutes les contraintes.

Exemple :

```text
requested risk = 0.50%
approved risk = 0.50%
```

---

# 11. MODIFIED

L'intention peut être acceptée mais avec une exposition réduite.

Exemple :

```text
requested position = 1 BTC
approved position = 0.6 BTC
```

Reason :

```text
PORTFOLIO_EXPOSURE_LIMIT
```

---

# 12. REJECTED

L'intention est refusée.

Exemples :

```text
DAILY_LOSS_LIMIT
MAX_DRAWDOWN_LIMIT
MAX_SYMBOL_EXPOSURE
INVALID_STOP
INSUFFICIENT_LIQUIDITY
RISK_ENGINE_DEGRADED
```

---

# 13. FORCE_REDUCE

Le moteur peut demander une réduction d'une exposition existante.

Exemple :

```text
portfolio exposure exceeds emergency threshold
```

---

# 14. FORCE_EXIT

Le moteur peut demander la fermeture complète d'une position.

Exemples :

```text
kill switch
critical reconciliation failure
risk state corrupted
emergency drawdown threshold
```

---

# 15. Risk Hierarchy

Les contrôles doivent être hiérarchisés.

```text
Global Risk
↓
Portfolio Risk
↓
Strategy Risk
↓
Asset Risk
↓
Trade Risk
```

Une limite supérieure ne peut jamais être contournée par une limite inférieure.

---

# 16. Capital de référence

Le moteur doit définir précisément le capital utilisé pour les calculs.

Possibilités :

```text
account_equity
available_equity
net_liquidation_value
allocated_strategy_capital
```

La convention doit être explicite.

---

# 17. Equity

Définition recommandée :

```text
equity =
cash
+
realized PnL
+
unrealized PnL
```

selon le modèle de compte utilisé.

---

# 18. Available Capital

Le capital disponible doit prendre en compte :

```text
margin used
reserved margin
pending orders
risk reservations
```

---

# 19. Risk Per Trade

Forme classique :

```text
risk_amount =
account_equity × risk_fraction
```

Exemple :

```text
equity = 100000
risk_fraction = 0.005
```

Résultat :

```text
risk_amount = 500
```

---

# 20. Position Sizing

Pour un instrument linéaire simple :

```text
position_size =
risk_amount
/
abs(entry_price - stop_price)
```

avant prise en compte des multiplicateurs contractuels, frais, slippage et contraintes de marché.

---

# 21. Exemple

```text
equity = 100000
risk = 0.5%
risk_amount = 500

entry = 100
stop = 98

risk_per_unit = 2
```

Alors :

```text
position_size = 250 units
```

avant ajustements.

---

# 22. Fees

Le risque réel doit pouvoir intégrer :

```text
entry_fee
exit_fee
```

Le calcul simplifié du stop seul peut sous-estimer la perte.

---

# 23. Slippage

Le moteur doit intégrer une estimation de slippage.

Exemple :

```text
effective_stop_loss =
price_loss
+
fees
+
estimated_slippage
```

---

# 24. Risk Buffer

Une marge de sécurité peut être ajoutée.

Exemple :

```text
risk_buffer = 5%
```

Le risque théorique de 500 devient une allocation légèrement inférieure afin de conserver une marge pour les coûts.

---

# 25. Stop Requirement

Une nouvelle position risquée doit normalement disposer d'une invalidation définie.

Si :

```text
stop_price = null
```

le Risk Engine doit refuser l'intention sauf stratégie explicitement conçue et approuvée pour fonctionner autrement.

---

# 26. Stop Validation

Le moteur doit vérifier :

```text
LONG:
stop < entry

SHORT:
stop > entry
```

Sinon :

```text
INVALID_STOP
```

---

# 27. Minimum Stop Distance

Un stop trop proche peut être incompatible avec :

- tick size ;
- spread ;
- volatilité ;
- bruit de marché.

Exemple :

```text
stop_distance >= minimum_stop_atr
```

---

# 28. Maximum Stop Distance

Un stop extrêmement éloigné peut produire :

- position minuscule ;
- mauvais R/R ;
- exposition incohérente.

Une stratégie peut définir :

```text
maximum_stop_atr
```

---

# 29. Stop Adjustment

Le Risk Engine ne doit pas déplacer arbitrairement le stop vers un niveau qui invalide la logique stratégique.

Si un stop proposé viole les contraintes :

```text
REJECT
```

peut être préférable à une modification conceptuellement incorrecte.

---

# 30. Tick Size

Tous les prix doivent être normalisés selon :

```text
tick_size
```

---

# 31. Quantity Step

La taille doit respecter :

```text
quantity_step
```

Exemple :

```text
0.001 BTC
```

---

# 32. Minimum Quantity

Si :

```text
calculated_size < exchange_minimum
```

le trade doit être rejeté plutôt que surdimensionné.

---

# 33. Minimum Notional

Le moteur doit vérifier :

```text
minimum_notional
```

imposé par la venue.

---

# 34. Maximum Order Size

Des limites internes peuvent être plus strictes que celles de l'exchange.

Exemple :

```text
max_order_notional
```

---

# 35. Leverage

Le levier ne doit pas être utilisé comme substitut au contrôle du risque.

Le moteur doit distinguer :

```text
position risk
```

et :

```text
margin requirement
```

---

# 36. Maximum Leverage

Limites possibles :

```text
global_max_leverage
strategy_max_leverage
asset_max_leverage
```

La plus restrictive s'applique.

---

# 37. Effective Leverage

Mesure :

```text
effective_leverage =
gross_notional_exposure
/
equity
```

---

# 38. Liquidation Distance

Pour les produits à levier, le moteur doit contrôler que le prix de liquidation estimé ne soit pas dangereusement proche du stop ou du prix courant.

---

# 39. Margin Mode

Le système doit distinguer :

```text
ISOLATED
CROSS
```

Les risques ne sont pas identiques.

La V1 devrait privilégier un modèle simple et explicitement supporté.

---

# 40. Trade Risk Limit

Exemple :

```text
max_risk_per_trade = 0.50%
```

Toute demande supérieure doit être :

```text
MODIFIED
```

ou :

```text
REJECTED
```

selon la configuration.

---

# 41. Strategy Risk Limit

Une stratégie peut disposer d'un budget :

```text
max_strategy_open_risk = 2%
```

---

# 42. Symbol Risk Limit

Exemple :

```text
max_BTC_open_risk = 1.5%
```

---

# 43. Portfolio Open Risk

Définition approximative :

```text
portfolio_open_risk =
Σ maximum_expected_loss_to_stop
```

sur les positions ouvertes.

---

# 44. Maximum Portfolio Open Risk

Exemple :

```text
max_portfolio_open_risk = 4%
```

Une nouvelle intention ne doit pas dépasser cette limite.

---

# 45. Gross Exposure

```text
gross_exposure =
Σ abs(position_notional)
```

---

# 46. Net Exposure

```text
net_exposure =
long_notional
-
short_notional
```

---

# 47. Exposure Limits

Le moteur peut contrôler :

```text
max_gross_exposure
max_net_exposure
max_asset_exposure
max_strategy_exposure
```

---

# 48. Concentration Risk

Exemple :

```text
80% du portefeuille exposé à BTC
```

peut être interdit même si le risque par trade semble acceptable.

---

# 49. Correlation Risk

Deux positions distinctes peuvent représenter le même pari économique.

Exemple :

```text
BTC LONG
ETH LONG
SOL LONG
```

Une simple addition du risque individuel sous-estime potentiellement le risque commun.

---

# 50. Correlation Matrix

Le moteur peut recevoir une matrice :

```text
corr(asset_i, asset_j)
```

calculée sur une fenêtre versionnée.

---

# 51. Correlation Groups

Une V1 plus simple peut utiliser des groupes :

```text
CRYPTO_MAJOR
CRYPTO_ALT
GOLD
FX_USD
```

et limiter l'exposition cumulée par groupe.

---

# 52. Recommended V1

Pour éviter une fausse sophistication :

```text
explicit correlation groups
+
simple concentration limits
```

sont préférables à un modèle de covariance complexe mal calibré.

---

# 53. Portfolio Heat

Concept :

```text
portfolio_heat =
total open risk / equity
```

Exemple :

```text
portfolio_heat = 3.2%
```

---

# 54. Maximum Heat

Exemple :

```text
max_portfolio_heat = 4%
```

Au-delà :

```text
NEW_ENTRIES_REJECTED
```

---

# 55. Daily Loss

Le moteur doit suivre :

```text
realized_daily_pnl
```

et éventuellement :

```text
realized + unrealized
```

selon la politique.

---

# 56. Daily Loss Limit

Exemple :

```text
daily_loss_limit = -2%
```

Lorsque le seuil est atteint :

```text
NEW_ENTRIES_DISABLED
```

---

# 57. Hard Daily Stop

Une limite absolue peut déclencher :

```text
REDUCE_ONLY
```

ou :

```text
TRADING_PAUSED
```

---

# 58. Daily Reset

La définition de la journée doit être explicite.

Pour crypto :

```text
00:00 UTC
```

peut être utilisée.

Pour d'autres marchés, la convention peut différer.

---

# 59. Weekly Loss Limit

Exemple :

```text
weekly_loss_limit = -5%
```

Le système peut réduire progressivement le risque avant le seuil absolu.

---

# 60. Drawdown

Définition :

```text
drawdown =
(current_equity - equity_peak)
/
equity_peak
```

Valeur négative.

---

# 61. Maximum Drawdown

Exemple :

```text
max_drawdown = -10%
```

À ce niveau :

```text
GLOBAL_TRADING_DISABLED
```

peut être déclenché.

---

# 62. Drawdown Tiers

Approche graduelle :

```text
DD < 3%
→ normal

3–5%
→ risk multiplier 0.75

5–7%
→ risk multiplier 0.50

7–10%
→ reduce only

>10%
→ kill switch
```

Les seuils sont illustratifs et doivent être validés.

---

# 63. Risk Multiplier

Forme :

```text
effective_trade_risk =
base_trade_risk × risk_multiplier
```

Le multiplicateur ne doit jamais dépasser une limite maximale autorisée.

---

# 64. No Martingale

Le système ne doit pas augmenter automatiquement le risque après une perte pour « récupérer ».

Interdiction recommandée :

```text
loss
→ larger position
```

sans stratégie explicitement étudiée, gouvernée et plafonnée.

---

# 65. No Revenge Logic

Le système ne doit contenir aucune logique équivalente à :

```text
lost previous trade
→ trade faster
```

Les machines sont parfaitement capables de reproduire les mauvaises habitudes humaines sans qu'on les programme exprès.

---

# 66. Consecutive Loss Control

Une règle possible :

```text
N consecutive losses
→ reduce risk
```

Mais elle doit être testée.

Une série de pertes ne signifie pas nécessairement que le prochain trade a une probabilité plus faible.

---

# 67. Strategy Drawdown

Chaque stratégie doit disposer de son propre suivi :

```text
strategy_equity_curve
strategy_drawdown
```

---

# 68. Strategy Kill Switch

Exemple :

```text
strategy_drawdown > threshold
```

peut désactiver uniquement cette stratégie sans arrêter tout QuantLab.

---

# 69. Asset Kill Switch

Une anomalie sur un actif peut produire :

```text
BTC_TRADING_DISABLED
```

sans affecter les autres actifs.

---

# 70. Venue Kill Switch

Exemple :

```text
exchange API unstable
order reconciliation failing
```

Résultat :

```text
VENUE_NEW_ENTRIES_DISABLED
```

---

# 71. Global Kill Switch

Le système doit disposer d'un état :

```text
GLOBAL_KILL_SWITCH
```

Effet :

```text
no new positions
cancel pending risk-increasing orders
allow/force risk-reducing actions
```

---

# 72. Kill Switch Priority

Le kill switch doit être vérifié avant toute autre logique.

Il ne doit pas dépendre d'un score ou d'une stratégie.

---

# 73. Risk States

États globaux possibles :

```text
NORMAL
CAUTION
REDUCED
REDUCE_ONLY
PAUSED
EMERGENCY
```

---

# 74. NORMAL

Fonctionnement standard.

---

# 75. CAUTION

Le moteur peut réduire légèrement les budgets ou renforcer certains contrôles.

---

# 76. REDUCED

Les nouvelles positions restent autorisées avec un risque réduit.

---

# 77. REDUCE_ONLY

Aucune nouvelle exposition nette.

Seules les actions réduisant le risque sont autorisées.

---

# 78. PAUSED

Aucune nouvelle entrée.

Les sorties restent possibles.

---

# 79. EMERGENCY

Le système peut déclencher :

```text
cancel orders
reduce positions
close positions
```

selon le protocole configuré.

---

# 80. Risk State Transitions

Exemple :

```text
NORMAL
↓
CAUTION
↓
REDUCED
↓
REDUCE_ONLY
↓
PAUSED
↓
EMERGENCY
```

Le retour vers un état moins restrictif doit également être contrôlé.

---

# 81. Hysteresis

Pour éviter des oscillations constantes autour d'un seuil :

```text
enter CAUTION at DD = 3%
exit CAUTION only below DD = 2%
```

Cette différence constitue une hystérésis.

---

# 82. Pending Orders Risk

Les ordres non exécutés peuvent créer du risque futur.

Ils doivent être inclus dans :

```text
reserved_risk
```

---

# 83. Risk Reservation

Avant envoi d'un ordre :

```text
risk budget
```

doit pouvoir être réservé.

Sinon deux décisions simultanées peuvent chacune croire que le même capital est disponible.

---

# 84. Reservation Lifecycle

États :

```text
RESERVED
PARTIALLY_CONSUMED
CONSUMED
RELEASED
EXPIRED
```

---

# 85. Concurrency

Deux TradeIntents simultanés doivent être évalués de manière transactionnelle ou sérialisée.

Exemple dangereux :

```text
available risk = 1%

Intent A requests 1%
Intent B requests 1%
```

Les deux ne doivent pas être approuvés indépendamment.

---

# 86. Atomic Risk Check

Le processus recommandé :

```text
load risk state
↓
calculate proposed exposure
↓
validate limits
↓
reserve risk
↓
persist decision
```

dans une transaction logique.

---

# 87. Partial Fill

Si un ordre n'est rempli qu'à 40% :

```text
risk reservation
```

doit être ajustée.

---

# 88. Cancelled Order

Une annulation confirmée doit libérer le risque réservé.

---

# 89. Rejected Exchange Order

Un ordre rejeté par la venue doit également libérer la réservation.

---

# 90. Position Reconciliation

Le Risk Engine doit comparer régulièrement :

```text
internal positions
vs
exchange positions
```

Une divergence critique doit empêcher les nouvelles entrées.

---

# 91. Balance Reconciliation

Même principe pour :

```text
cash
equity
margin
```

---

# 92. Unknown State

Si le système ne sait pas avec certitude :

```text
quelle exposition existe réellement
```

alors :

```text
NEW_RISK = DISABLED
```

---

# 93. Fail Closed

Pour les nouvelles expositions :

```text
uncertainty
→ reject
```

C'est la politique recommandée.

---

# 94. Fail Safe for Exits

Les mécanismes de sécurité ne doivent pas bloquer une sortie nécessaire.

Les actions réduisant le risque doivent disposer d'un chemin opérationnel prioritaire.

---

# 95. Market Liquidity Risk

Le moteur peut vérifier :

```text
spread
order book depth
estimated slippage
volume
```

avant d'approuver une taille.

---

# 96. Liquidity-Based Size Cap

Exemple :

```text
max_order_size =
fraction_of_visible_depth
```

ou :

```text
fraction_of_average_volume
```

---

# 97. Slippage Limit

Exemple :

```text
estimated_slippage_bps <= maximum
```

Sinon :

```text
MODIFIED
```

ou :

```text
REJECTED
```

---

# 98. Volatility Risk

Une volatilité extrême peut nécessiter :

```text
smaller size
wider minimum stop
new entries disabled
```

selon la stratégie.

---

# 99. Volatility Multiplier

Exemple :

```text
HIGH_VOL
→ risk multiplier = 0.75
```

Mais le mécanisme doit être testé historiquement.

---

# 100. Gap Risk

Pour les marchés pouvant ouvrir avec des gaps, le stop ne garantit pas la perte maximale.

Le Risk Engine doit intégrer une marge spécifique.

---

# 101. Crypto 24/7 Risk

Le marché crypto réduit le risque de gap de session classique mais introduit :

- liquidations rapides ;
- outages d'exchange ;
- fragmentation ;
- mouvements 24/7 ;
- risque opérationnel nocturne.

---

# 102. Venue Risk

Le moteur peut maintenir :

```text
venue_risk_state
```

selon :

- API health ;
- withdrawal status ;
- order rejection rate ;
- latency ;
- reconciliation quality.

---

# 103. Stablecoin / Quote Risk

Une exposition :

```text
BTC/USDT
```

inclut potentiellement un risque lié à la quote currency.

Une version avancée du portefeuille devra considérer cette dimension.

---

# 104. Counterparty Risk

Pour les CEX, une part du capital est exposée à la venue.

Le système peut définir :

```text
max_capital_per_venue
```

---

# 105. DEX Risk

Pour les DEX, les risques supplémentaires peuvent inclure :

- smart contract ;
- MEV ;
- gas ;
- RPC failure ;
- bridge risk ;
- pool liquidity.

Cette couche pourra être développée séparément.

---

# 106. Risk Profiles

Chaque stratégie peut référencer un profil.

Exemple :

```yaml
risk_profile: conservative_v1
```

---

# 107. Risk Profile Example

```yaml
risk:
  version: 1.0.0

  trade:
    max_risk_pct: 0.50

  strategy:
    max_open_risk_pct: 2.0

  portfolio:
    max_open_risk_pct: 4.0
    max_gross_exposure_pct: 200

  daily:
    max_loss_pct: 2.0

  drawdown:
    caution_pct: 3.0
    reduced_pct: 5.0
    pause_pct: 7.0
    emergency_pct: 10.0
```

Les valeurs sont illustratives, pas des recommandations financières.

---

# 108. Risk Configuration Versioning

Chaque décision doit enregistrer :

```text
risk_configuration_version
```

---

# 109. Immutable Risk Decisions

Une décision historique doit conserver :

```text
inputs
limits
calculations
result
version
```

même si les limites futures changent.

---

# 110. Risk Reason Codes

Exemples :

```text
RISK_APPROVED
RISK_SIZE_REDUCED
MAX_TRADE_RISK
MAX_STRATEGY_RISK
MAX_SYMBOL_RISK
MAX_PORTFOLIO_RISK
MAX_GROSS_EXPOSURE
MAX_NET_EXPOSURE
CORRELATION_LIMIT
CONCENTRATION_LIMIT
DAILY_LOSS_LIMIT
DRAWDOWN_LIMIT
INVALID_STOP
MIN_ORDER_SIZE
MAX_LEVERAGE
INSUFFICIENT_LIQUIDITY
EXCESSIVE_SLIPPAGE
RISK_STATE_REDUCE_ONLY
GLOBAL_KILL_SWITCH
POSITION_STATE_UNKNOWN
```

---

# 111. Explainability

Exemple :

```yaml
status: MODIFIED

requested_size: 1.0 BTC
approved_size: 0.62 BTC

reasons:
  - PORTFOLIO_OPEN_RISK_LIMIT

portfolio_open_risk_before: 3.4%
portfolio_open_risk_requested: 4.7%
portfolio_open_risk_limit: 4.0%
```

---

# 112. Calculation Trace

Le moteur doit pouvoir reconstruire :

```text
equity
↓
risk fraction
↓
risk amount
↓
stop distance
↓
fees/slippage
↓
raw size
↓
market constraints
↓
portfolio constraints
↓
approved size
```

---

# 113. Risk Snapshot

Chaque évaluation doit utiliser un snapshot cohérent de :

```text
equity
positions
pending orders
reserved risk
market prices
risk limits
```

---

# 114. Snapshot Timestamp

Le snapshot doit contenir :

```text
timestamp
```

et idéalement :

```text
source timestamps
```

---

# 115. Stale Risk State

Si les données critiques sont trop anciennes :

```text
RISK_STATE_STALE
```

et les nouvelles entrées doivent être bloquées.

---

# 116. Price Freshness

Un calcul de taille basé sur un prix obsolète peut être dangereux.

Le moteur doit contrôler :

```text
price_age <= maximum_price_age
```

---

# 117. Determinism

Avec :

```text
same TradeIntent
same RiskSnapshot
same configuration
same risk version
```

le résultat doit être identique.

---

# 118. Unit Tests

Tester :

- risk amount ;
- position sizing ;
- long stop ;
- short stop ;
- fees ;
- slippage ;
- tick rounding ;
- quantity rounding ;
- leverage ;
- exposure limits ;
- daily loss ;
- drawdown ;
- reservations.

---

# 119. Boundary Tests

Tester exactement :

```text
risk = limit
risk just below limit
risk just above limit
```

Les opérateurs `<`, `<=`, `>` doivent être explicites.

---

# 120. Synthetic Portfolio Tests

Exemple :

```text
portfolio open risk = 3.8%
max = 4.0%

new trade risk = 0.5%
```

Résultat attendu :

```text
MODIFIED to 0.2%
```

ou `REJECTED`, selon la policy.

---

# 121. Correlation Test

Exemple :

```text
BTC long risk = 1%
ETH long requested risk = 1%
crypto group max = 1.5%
```

Le second trade doit être réduit ou rejeté.

---

# 122. Daily Loss Test

```text
daily loss = -2%
limit = -2%
```

Résultat attendu :

```text
new entries disabled
```

si le seuil est inclusif.

---

# 123. Drawdown Test

Tester chaque transition :

```text
NORMAL → CAUTION
CAUTION → REDUCED
REDUCED → REDUCE_ONLY
```

---

# 124. Kill Switch Test

Lorsque le kill switch est actif :

```text
ENTER_LONG
```

doit être rejeté.

Une intention :

```text
EXIT_LONG
```

doit rester autorisée.

---

# 125. Concurrency Test

Simuler plusieurs intentions simultanées et vérifier que le budget n'est jamais doublement alloué.

---

# 126. Replay Testing

Le moteur doit reproduire les décisions de risque historiques à partir des snapshots enregistrés.

---

# 127. Integration Tests

Tester :

```text
Decision
↓
Risk
↓
Execution
```

avec :

```text
APPROVED
MODIFIED
REJECTED
```

---

# 128. Failure Tests

Simuler :

- database unavailable ;
- stale prices ;
- unknown positions ;
- exchange reconciliation failure ;
- malformed intent ;
- invalid configuration.

La réponse par défaut pour une nouvelle exposition doit être restrictive.

---

# 129. Stress Tests

Simuler :

```text
market crash
volatility spike
multiple simultaneous signals
exchange latency
partial fills
API outage
```

---

# 130. Flash Move Scenario

Exemple :

```text
price moves 10%
within seconds
```

Le système doit vérifier :

- stale intents ;
- stop assumptions ;
- slippage ;
- portfolio exposure ;
- emergency state.

---

# 131. Monitoring

Métriques :

```text
risk_checks_total
approved_total
modified_total
rejected_total
force_reduce_total
force_exit_total

portfolio_heat
gross_exposure
net_exposure
daily_pnl
drawdown
reserved_risk

risk_check_latency
risk_errors
```

---

# 132. Alertes

Exemples :

```text
DAILY_LOSS_LIMIT_REACHED
DRAWDOWN_THRESHOLD_REACHED
PORTFOLIO_HEAT_HIGH
POSITION_RECONCILIATION_FAILED
BALANCE_RECONCILIATION_FAILED
RISK_STATE_STALE
GLOBAL_KILL_SWITCH_ACTIVE
RISK_ENGINE_UNAVAILABLE
```

---

# 133. Dashboard

Le Monitoring Engine doit pouvoir afficher :

```text
Equity
Daily PnL
Current Drawdown
Portfolio Heat
Gross Exposure
Net Exposure
Open Risk
Risk State
Open Positions
Pending Risk
```

---

# 134. Audit

Pour chaque trade, QuantLab doit pouvoir répondre :

> Pourquoi cette taille de position a-t-elle été autorisée ?

et reconstruire précisément le calcul.

---

# 135. Interaction avec Decision Engine

Le Decision Engine propose :

```text
TradeIntent
```

Le Risk Engine répond :

```text
RiskDecision
```

Le Decision Engine ne peut pas modifier cette réponse pour augmenter le risque.

---

# 136. Interaction avec Execution Engine

Seuls les objets :

```text
APPROVED
```

ou :

```text
MODIFIED
```

peuvent être transmis pour une nouvelle exposition.

---

# 137. Execution Feedback

L'Execution Engine doit renvoyer :

```text
submitted
partial fill
fill
cancel
reject
```

afin que le Risk Engine mette à jour les réservations.

---

# 138. Interaction avec Monitoring Engine

Le Monitoring Engine doit surveiller l'état de risque en priorité élevée.

Les alertes critiques doivent être traitées indépendamment des stratégies.

---

# 139. Interaction avec Knowledge Engine

Le Knowledge Engine peut analyser :

```text
risk used
vs
risk requested
vs
trade outcome
```

mais ne doit pas conclure automatiquement qu'un trade gagnant aurait dû être plus gros.

---

# 140. Interaction avec AI & Learning Engine

L'IA pourra proposer :

- nouveaux risk tiers ;
- meilleure estimation du slippage ;
- modèles de corrélation ;
- limites adaptatives ;
- stress scenarios.

Mais aucune modification live ne doit être automatique.

---

# 141. AI Boundary

L'AI & Learning Engine ne doit jamais pouvoir écrire directement :

```text
max_risk_per_trade
max_drawdown
kill_switch
```

en production sans gouvernance.

---

# 142. Governance

Toute modification de limite doit enregistrer :

```text
author
reason
experiment
approval
effective_date
previous_value
new_value
```

---

# 143. Manual Controls

Un opérateur autorisé peut :

```text
pause new entries
set reduce only
activate kill switch
disable strategy
disable asset
disable venue
```

Les actions doivent être auditées.

---

# 144. Four-Eyes Principle

Pour certaines modifications critiques en production, une version future peut exiger une double approbation.

Exemples :

```text
increase max trade risk
increase leverage
raise drawdown limit
disable kill switch
```

---

# 145. Security

Les endpoints de risque doivent disposer de permissions strictes.

Lire le risque et modifier les limites sont deux privilèges différents.

---

# 146. No Silent Failure

Si le Risk Engine est indisponible :

```text
new entries = blocked
```

Le système ne doit jamais interpréter l'absence de réponse comme une approbation.

---

# 147. Risk Engine Availability

L'Execution Engine doit exiger une autorisation valide et non expirée.

Une vieille approbation ne doit pas rester utilisable indéfiniment.

---

# 148. Approval Expiration

Chaque `RiskDecision` peut contenir :

```text
valid_until
```

Après cette date :

```text
new risk check required
```

---

# 149. Price Deviation Check

Avant exécution, si :

```text
current_price
```

s'est trop éloigné du prix utilisé pour le sizing :

```text
risk approval invalidated
```

et un nouveau calcul est requis.

---

# 150. Maximum Entry Deviation

Exemple :

```text
abs(current_price - approved_reference_price)
>
max_entry_deviation
```

→ nouvelle validation.

---

# 151. Risk Budget Allocation

À terme, QuantLab peut répartir un budget entre :

```text
strategies
assets
venues
```

Exemple :

```text
Trend Strategy 40%
Mean Reversion 30%
Experimental 10%
Reserve 20%
```

---

# 152. Experimental Risk

Les stratégies expérimentales doivent disposer de limites plus strictes.

Exemple :

```text
SHADOW = 0 real capital
PAPER = 0 real capital
LIVE_EXPERIMENTAL = small capped budget
```

---

# 153. Risk Scaling by Evidence

Une stratégie nouvellement validée ne doit pas recevoir immédiatement le même capital qu'une stratégie éprouvée.

Le capital peut être augmenté progressivement sous gouvernance.

---

# 154. Capital Ramp

Exemple conceptuel :

```text
0%
↓
paper
↓
0.1%
↓
0.25%
↓
0.5%
```

avec critères de promotion.

---

# 155. Risk of Ruin

Le Knowledge Engine pourra calculer des approximations de :

```text
risk_of_ruin
```

à partir de :

- expectancy ;
- variance ;
- win/loss distribution ;
- risk fraction.

Ce calcul doit être utilisé comme outil d'analyse, pas comme garantie.

---

# 156. Monte Carlo

Les stratégies validées doivent pouvoir subir des simulations :

```text
trade sequence resampling
```

pour étudier :

```text
drawdown distribution
loss streaks
equity dispersion
```

---

# 157. Tail Risk

Les métriques moyennes sont insuffisantes.

Le système doit étudier :

```text
worst trades
worst days
worst weeks
gap scenarios
slippage tails
```

---

# 158. Expected Shortfall

Une version avancée pourra mesurer :

```text
Expected Shortfall
```

plutôt que dépendre uniquement de la VaR.

---

# 159. Scenario Stress Testing

Scénarios :

```text
BTC -20%
ETH -25%
XAU +8%
exchange unavailable
stablecoin depeg
slippage × 5
```

Le portefeuille doit être évalué sous ces hypothèses.

---

# 160. Model Risk

Le Risk Engine lui-même possède un risque de modèle.

Exemple :

```text
slippage model underestimates actual slippage
```

Il faut donc comparer :

```text
estimated risk
vs
realized risk
```

---

# 161. Realized Loss Attribution

Pour chaque trade :

```text
planned loss at stop
actual realized loss
difference
```

La différence doit être expliquée par :

```text
fees
slippage
gap
partial fills
execution errors
```

---

# 162. Risk Model Calibration

Les estimations doivent être recalibrées à partir des données réelles.

Exemple :

```text
estimated slippage = 3 bps
actual median = 7 bps
```

Le modèle doit être réévalué.

---

# 163. Priorités V1

Implémenter :

- risk per trade ;
- position sizing ;
- stop validation ;
- fees/slippage buffer ;
- symbol limits ;
- strategy limits ;
- portfolio open risk ;
- gross exposure ;
- daily loss limit ;
- drawdown tiers ;
- risk states ;
- risk reservations ;
- kill switch ;
- reason codes ;
- persistence ;
- deterministic replay.

---

# 164. Priorités V2

Ajouter :

- correlation groups ;
- volatility scaling ;
- liquidity-based size caps ;
- venue risk ;
- advanced reconciliation ;
- capital ramping.

---

# 165. Priorités V3

Ajouter :

- dynamic correlation ;
- scenario stress engine ;
- Monte Carlo ;
- Expected Shortfall ;
- advanced tail-risk monitoring.

---

# 166. Priorités V4

Ajouter :

- ML-assisted slippage estimation ;
- adaptive risk proposals ;
- portfolio optimization ;
- cross-venue capital allocation sous gouvernance stricte.

---

# 167. Critères d'acceptation V1

La V1 est valide lorsque :

- aucune nouvelle exposition ne contourne le Risk Engine ;
- le position sizing est déterministe ;
- les stops invalides sont rejetés ;
- les contraintes exchange sont respectées ;
- les risques en attente sont réservés ;
- les limites trade/strategy/symbol/portfolio fonctionnent ;
- le daily loss limit fonctionne ;
- les drawdown tiers fonctionnent ;
- le kill switch bloque les nouvelles expositions ;
- les sorties restent possibles en mode restrictif ;
- les états inconnus bloquent les nouvelles entrées ;
- chaque décision est explicable ;
- les décisions sont persistées ;
- le replay reproduit les résultats ;
- les tests de concurrence passent.

---

# 168. Risques principaux

## Sous-estimation du risque

Le stop théorique ne garantit pas la perte réelle.

## Double allocation

Deux ordres simultanés peuvent utiliser le même budget si les réservations sont mal conçues.

## Corrélation cachée

Plusieurs positions peuvent représenter le même risque économique.

## State Drift

L'état interne peut diverger de l'exchange.

## Leverage Illusion

Une faible marge immobilisée ne signifie pas un faible risque.

## False Precision

Un modèle sophistiqué peut donner des chiffres précis mais faux.

---

# 169. Principe de prudence

Lorsque deux estimations raisonnables de risque diffèrent, QuantLab doit privilégier la plus conservatrice tant qu'aucune validation ne justifie l'autre.

---

# 170. Architecture cible

```text
TradeIntent
     ↓
Global Safety Check
     ↓
Risk State Check
     ↓
Stop Validation
     ↓
Trade Risk Calculation
     ↓
Position Sizing
     ↓
Market Constraints
     ↓
Asset / Strategy Limits
     ↓
Portfolio Limits
     ↓
Risk Reservation
     ↓
RiskDecision
     ↓
APPROVED / MODIFIED / REJECTED
     ↓
Execution Engine
```

---

# 171. Résultat attendu

Le Risk Engine doit permettre de transformer :

```text
« La stratégie veut acheter BTC »
```

en :

```text
RiskDecision:
APPROVED

Equity:
100000

Maximum trade risk:
0.50%

Approved monetary risk:
500

Entry reference:
100000

Stop:
99000

Raw size:
0.50 BTC

Adjusted for fees/slippage:
0.47 BTC

Portfolio heat before:
2.1%

Portfolio heat after:
2.6%

All limits:
PASS
```

ou, lorsque nécessaire :

```text
REJECTED

Reason:
DAILY_LOSS_LIMIT
```

---

# 172. Règle fondatrice

> **Le Risk Engine n'a pas pour mission de savoir si le trade est bon. Il a pour mission de garantir qu'un mauvais trade, une mauvaise série ou une mauvaise journée ne puisse pas détruire le système.**

La performance de QuantLab dépendra des stratégies.

Sa survie dépendra du Risk Engine.

Et, contrairement aux backtests héroïques, la survie a cette propriété assez pratique : sans elle, tout le reste cesse d'avoir beaucoup d'intérêt.

---

# 173. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `04-Storage-Engine.md`
- `05-Market-Analysis-Engine.md`
- `09-Scoring-Engine.md`
- `10-Decision-Engine.md`
- `12-Execution-Engine.md`
- `13-Monitoring-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `16-Governance-Engine.md`
- `18-Testing-Strategy.md`
- `19-Deployment-Guide.md`
- `21-Experiment-Registry.md`
- `22-API-Specification.md`
- `23-Database-Schema.md`
- `24-Security.md`

**Prochain document : `12-Execution-Engine.md`**
