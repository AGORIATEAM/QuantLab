# ADR-0003 — Performance de la recherche

## Statut
ACCEPTED — 2026-09-02 (plan validé avec niveau 2 d'équivalence et exigence
de déterminisme ajoutés à la revue)

## Contexte — constat chiffré
Le premier run in-sample de EXP-20260901-003 (runner `885b4c2`, boucle
chaude en Decimal, 216 configurations × 12+18 moteurs partagés sur un seul
replay) a été mesuré à **~18 événements/s** (un FETCH de 50 000 lignes du
curseur replay toutes les ~46 min), soit **~9,5 h par instrument et
> 30 h** pour l'hypothèse complète (IS + OOS × 2 instruments). Intenable
pour un protocole qui exige des voisinages de paramètres à chaque
hypothèse. Le replay lui-même n'est pas le goulot (29-51 k bougies/s
mesurés en T7) : le coût est dans la boucle chaude Decimal.

Le run BTC in-sample a été mené à terme et son CSV est la **référence
dorée** (`experiments/EXP-20260901-003…/insample_BTCUSDT_metrics.csv`,
SHA-256 `3de5d0b427ec2f403e29457bd6445d1c496c42a82b26a0ec6480f66af2ff12b5`,
commit `4ac2e2f`). ETHUSDT n'a jamais tourné sur cette implémentation.

## Décisions

1. **Parallélisation en deux phases.** Phase d'extraction : une seule
   passe de replay par (instrument, période) — verify fail-closed intact,
   payé une fois — matérialisée en tableaux numériques compacts. Phase de
   calcul : les configurations réparties en shards sur les cœurs
   disponibles (`multiprocessing`), chaque worker rejouant ses configs sur
   les tableaux en mémoire.

2. **Exception ENCADRÉE à la règle Decimal.** Le périmètre
   `quantlab/research/fast/` est autorisé à utiliser le flottant double
   (float64) dans la boucle chaude : miroirs des moteurs de structure et
   du simulateur, à sémantique identique. Frontières : Decimal → float une
   fois à l'extraction ; float → Decimal (quantisation explicite) à
   l'écriture des enregistrements. `quantlab/structure/`, execution,
   accounting, ledger et tout ce qui est persisté restent Decimal — JAMAIS
   de float dans ces couches. Justification numérique : prix à ≤ 8
   décimales sur ~6 ordres de grandeur ; float64 porte 15-16 chiffres
   significatifs, l'erreur relative accumulée sur la vie d'un trade est
   ≤ ~1e-12.

3. **Équivalence obligatoire, deux niveaux, contre la référence dorée.**
   - Niveau 1 (bloquant) : relance BTC in-sample complète sur la version
     optimisée ; les 216 lignes doivent reproduire le CSV doré — compteurs
     entiers (`trades`, `skipped_min_stop`, `ignored_in_position`,
     `capped`) **exactement égaux**, métriques monétaires/R à tolérance
     relative **1e-9**. Marge ~×1000 sur l'erreur float64 théorique : toute
     divergence de logique la dépasse de plusieurs ordres.
   - Niveau 2 (bloquant) : fenêtre de 90 jours ([2021-01-01, 2021-04-01),
     lookback 30 j — période à la fois tendancielle et volatile), rejouée
     par l'implémentation Decimal **conservée intacte** (journal de trades
     ajouté par sous-classe, sans toucher au simulateur de référence) et
     par la version optimisée : comparaison **trade par trade** (horodatages
     d'entrée/sortie exacts, prix et R à 1e-9) sur les 216 configurations.

4. **Déterminisme.** Deux exécutions de la version optimisée produisent
   des sorties **identiques au hash près**. Ordre de sommation fixe par
   simulateur (une passe séquentielle par config), écriture ordonnée par
   index de configuration, indépendante de l'ordre d'achèvement des
   workers. Testé (hash de CSV sur deux runs).

5. **Budget cible : in-sample 2 instruments < 30 minutes** sur cette
   machine. Estimation au plan : extraction ~1 min/instrument ; boucle
   chaude float ~130 µs/bougie toutes configs, ~75 s/instrument mono-cœur,
   divisée par ~8 cœurs → marge estimée > 6×. Le temps réel est mesuré et
   consigné dans le rapport d'exécution.

## Conséquences
- Hyp-1 est relancée INTÉGRALEMENT (IS 2 instruments, rapport
  diagnostique, puis OOS une seule fois) sur la version optimisée ; le
  pré-enregistrement reste inchangé.
- L'implémentation Decimal de référence (`quantlab/research/h1.py`,
  `quantlab/structure/`) est conservée : c'est l'étalon sémantique de
  toute optimisation future.
- Toute évolution des règles de trading se fait D'ABORD dans l'étalon
  Decimal, puis se propage au miroir fast sous les mêmes tests
  d'équivalence.

## Alternatives considérées
- **Tout passer en float** : écarté — la règle Decimal protège
  l'exécution et la comptabilité réelles ; l'exception est un périmètre,
  pas un précédent.
- **Cython/Numba/Rust** : écartés à ce stade — une dépendance lourde pour
  un gain que float64 + multiprocessing atteint déjà avec > 6× de marge
  sur le budget. À reconsidérer si le budget est dépassé.
- **Réduire les voisinages** : écarté — le protocole (ADR-0002) prime sur
  la commodité d'exécution.

## Addendum A (2026-09-02) — équivalence niveau 2 étendue aux deux instruments (grille H3)

Sur ordre utilisateur, la preuve trade par trade (niveau 2) a été exécutée
sur ETHUSDT en complément du passage BTCUSDT, même fenêtre 90 jours
`[2021-01-01, 2021-04-01)`, grille H3 gelée (96 configurations,
EXP-20260902-002), harnais `scripts/equivalence_h3.py <SYMBOL>` :

- **BTCUSDT** : 6 905 trades, parité trade par trade (timings/side exacts,
  prix et R à rel 1e-9), compteur `stop_atr_dominated` exact par
  configuration (6 889/6 905), déterminisme au hash `f05dbfe850d951fa…`.
- **ETHUSDT** : 5 780 trades, mêmes critères tous verts, 5 768/5 780
  stops dominés par k×ATR, déterminisme au hash `aed5f39681bb082e…`.

Le niveau 2 n'est donc plus limité à un seul instrument : les deux
instruments du périmètre (ADR-0002 décision 5) sont couverts par la même
preuve. Règle inchangée : tout écart trade par trade arrête la recherche
jusqu'à diagnostic.
