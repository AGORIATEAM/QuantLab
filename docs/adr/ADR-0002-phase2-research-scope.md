# ADR-0002 — Périmètre de recherche de la Phase 2

## Statut
ACCEPTED — 2026-09-01 (décisions dictées à l'ouverture de la Phase 2,
avant toute ligne de code des moteurs docs/05+)

## Contexte
La Phase 1 a livré la plateforme de données (rapport :
`docs/phase-reports/PHASE-1-CLOSURE.md`) : dataset officiel
`btc-eth-spot-binance@v1` (12 séries, hash `178e7403…`), replay
déterministe fail-closed, baselines enregistrées (EXP-20260901-001
buy-and-hold, EXP-20260901-002 breakout24). La Phase 2 (Research &
Analysis, docs/25 §35+) démarre. Ce qui suit fige le périmètre de
recherche AVANT les premiers moteurs, pour que chaque hypothèse soit
testée dans un cadre non négocié après coup.

## Décisions

1. **Horizon : intraday.** Trades de quelques minutes à quelques heures.

2. **Timeframes.** Décision sur 5m et 15m ; contexte sur 1h (4h en
   extension). Le 1m sert à la construction (indicateurs, simulation
   fine), jamais à la décision. **Le scalping à la seconde est HORS
   PÉRIMÈTRE** : les données 1m sont insuffisantes pour le simuler
   honnêtement, et le plancher de coûts mesuré par EXP-20260901-002 est
   d'environ **0,22 % par aller-retour** (taker 0,10 % + demi-spread
   1 bp, par côté) — insurmontable à cette échelle. **Condition de
   révision :** données tick + frais maker.

3. **Adaptation mécanique uniquement.** Tout « ça dépend du marché »
   doit devenir un **régime mesuré** (structure higher-timeframe,
   volatilité ATR) avec des **règles fixes par régime**. Aucune
   discrétion, aucun paramètre ajusté après coup.

4. **Modèle de fill de référence.** Celui d'EXP-20260901-001/002
   (signal au close, exécution à l'open suivant, taker 0,10 %,
   demi-spread fixe 1 bp par côté, courbe mark-to-market, liquidation
   finale dans le net), enregistré verbatim dans chaque expérience —
   jusqu'au modèle de fill commun suivi dans `BACKLOG.md`. Le sizing
   est un paramètre d'expérience, pas du modèle de fill.

5. **Protocole expérimental (docs/21).**
   - **Pré-enregistrement obligatoire** de chaque hypothèse (statut
     PLANNED, avec règles, voisinages, métriques ET critères de
     réfutation) AVANT toute exécution.
   - **In-sample : 2017-08 → 2022-12** (bornes [2017-08-17,
     2023-01-01)). **Out-of-sample : 2023-01 → 2026-08-30** (bornes
     [2023-01-01, 2026-08-30)). Jamais inversé, jamais re-découpé.
   - **Sensibilité par voisinages de paramètres** pré-déclarés — jamais
     d'optimisation (pas de recherche du meilleur paramètre ; un
     résultat qui ne tient que sur un point du voisinage est réfuté).
   - **BTC et ETH tous deux requis** : une hypothèse qui ne tient que
     sur un instrument est réfutée.

## Conséquences
- Aucun moteur ne consomme le 1m pour décider ; les moteurs produisent
  des événements horodatés `available_at` compatibles replay (docs/06
  §55-§56).
- Les expériences sans pré-enregistrement commité sont invalides par
  construction (docs/21 §22 s'applique aussi aux comparaisons).
- Le breakout EXP-002 et le buy-and-hold EXP-001 restent les baselines
  de comparaison par défaut.

## Alternatives considérées
- **Scalping seconde** : écarté (décision 2) — données et coûts.
- **Optimisation walk-forward** : écartée — la Phase 2 teste des
  hypothèses à paramètres fixes dans des voisinages déclarés ; toute
  optimisation exigerait un cadre anti-surapprentissage qui n'existe
  pas encore.
- **Timeframes de décision 1h/4h (swing multi-jours)** : écarté de
  l'horizon Phase 2 — l'horizon intraday est la décision 1 ; le 4h
  reste disponible comme contexte en extension.

---

## Addendum B — Préservation de l'out-of-sample

**Statut : ACCEPTED — 2026-09-02**

L'out-of-sample est une **ressource épuisable**. Il n'est exécuté que si
l'in-sample franchit les critères nécessaires ; un IS uniformément non
viable clôt l'hypothèse **REJECTED sur l'IS seul**. Précédent :
EXP-20260902-001 (0/288 configurations à espérance positive sur les deux
instruments, sans inversion de voisinage — OOS non consommé).

---

## Addendum C — Révision de périmètre sur preuves : plancher 15m

**Statut : ACCEPTED — 2026-09-02**

Les **entrées sur structure 5m sont retirées du périmètre de recherche en
frais taker** : EXP-20260901-003 et EXP-20260902-001 établissent que les
stops naturels du 5m (0,27-0,33 % médian) rendent le coût par trade
(1,3-1,6 R au modèle de fill de référence, plancher 0,22 %/aller-retour)
structurellement supérieur à tout edge plausible. **La frontière basse des
entrées devient le 15m.** Le 5m et le 1m restent disponibles pour la
construction (indicateurs, simulation fine), jamais pour la décision.

**Conditions de révision :** modèle de fill maker (ADR dédié) ou données
tick.
