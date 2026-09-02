# ADR-0004 — Modèle de fill maker (révision du plancher de coût, addendum C d'ADR-0002)

**Date** : 2026-09-02
**Statut** : Accepté (plan validé et arbitré par l'utilisateur le 2026-09-02)

## Contexte

Quatre hypothèses (EXP-20260901-003, EXP-20260902-001/-002/-003) ont été
réfutées proprement sous le modèle de fill taker gelé (0,1 % + 1 bp de
demi-spread par côté, plancher **22 bp/aller-retour**). Le fil diagnostique
est constant depuis Hyp-3 : il existe un petit signal de timing **brut**
(+0,01 à +0,03 R médian selon le découpage, positif sur les deux
instruments), qu'aucune localisation testée ne concentre (Hyp-4 a même
inversé sa prédiction secondaire), et qui reste un ordre de grandeur sous
le coût taker. L'addendum C d'ADR-0002 prévoyait explicitement la voie de
révision : « ADR fill maker ou données tick ». Cet ADR ouvre la première.
On change la **contrainte**, pas le signal.

## Décision 1 — Frais de référence : venue MiCA, sensibilité hors grille

- **Venue de référence : OKX EU** (licence MiCA via Malte, janvier 2025 ;
  carnets BTC/ETH profonds). Barème spot au palier de base (Regular Lv1),
  revérifié le 2026-09-02 : **maker 0,08 % / taker 0,10 %** ; paliers VIP
  descendant vers ~0,015-0,035 % (mise à jour 2026 : seuils d'entrée VIP
  abaissés). Sources : bitdegree.org/crypto/tutorials/okx-fees,
  tradersunion.com/brokers/crypto/view/okex/fees (consultées 2026-09-02).
- **Alternative documentée : Bitvavo** (MiCA CASP délivrée par l'AFM le
  27 juin 2025, passeport EEE). Base 0,15 %/0,25 % ; **0 % maker /
  0,02 % taker au-delà de 25 M€ de volume 30 j** ; ~0/0,01 % au sommet.
  Sources : bitvavo.com/en/fees, bitvavo.com/en/news/new-maker-taker-fees
  (consultées 2026-09-02).
- **Sensibilité maker : {0, 2, 5} bp par côté** — trois lectures complètes
  rapportées. 0 bp = borne Bitvavo ≥ 25 M€ ; 2 bp = paliers VIP
  intermédiaires plausibles ; 5 bp = palier VIP bas. **Les critères de
  réfutation gelés sont évalués UNIQUEMENT au point central 2 bp** ; 0 et
  5 bp sont informatifs. La sensibilité n'est PAS un axe de grille : pas
  d'optimisation sur les frais.
- **Menace documentée** : nos prix sont Binance spot USDT ; le barème
  vient d'un autre venue. Le modèle emprunte le **barème**, pas le carnet
  ni la microstructure. Approximation assumée, au même titre que le
  demi-spread forfaitaire du modèle taker.

## Décision 2 — Sorties inchangées ; cibles maker = raffinement futur

Toutes les sorties restent **taker 0,10 % + demi-spread 1 bp** : le stop
est agressif par nature (traverser le marché quand le niveau casse), la
sortie CHoCH est un ordre au marché à l'open suivant, et la cible pourrait
en principe reposer en maker — **ce raffinement est documenté ici et NON
modélisé** : le choix pessimiste est maintenu (une cible maker créditerait
frais réduits et absence de spread sur la jambe gagnante ; l'exclure borne
le biais dans le sens défavorable).

## Décision 3 — Règle de fill conservatrice, anti-sélection adverse

- **Anti-look-ahead** : la limite est posée au close de la bougie de
  signal et n'est **active qu'à partir de la bougie suivante** — aucun
  fill dans la bougie du signal, quelles que soient ses mèches.
- **Traversée stricte** : une limite BUY à P est remplie sur une bougie
  active ssi `low < P` **strictement** (SELL : `high > P`). « Touché »
  n'est jamais « rempli » : au toucher, la position dans la file d'attente
  est inconnaissable ; exclure ces fills borne le biais par pessimisme.
- **Fill à P exactement, jamais d'amélioration** : même si la bougie
  ouvre ou gap au-delà de la limite, le prix d'entrée est P.
- **Ordre non servi = signal perdu** : expiration après K bougies 15m
  actives (K : décision 4) sans traversée ; aucun repli en market, aucune
  poursuite. Les signaux non remplis sont disproportionnellement les
  gagnants immédiats (partis sans retest) : les perdre sous-estime la
  stratégie. Les fills, eux, surviennent précisément quand le prix
  traverse contre l'ordre : la sélection adverse est DANS le modèle.
- **Nouveau signal pendant qu'une limite repose : ignoré** (compté), pas
  de remplacement — cohérent avec l'absence de pyramidage.
- **Ambiguïtés intrabar, pessimistes** (héritées d'EXP-20260901-003
  amendé et étendues) : bougie qui traverse la limite ET le stop →
  entré-puis-stoppé dans la même bougie ; stop et target après entrée →
  stop d'abord ; gap au-delà du stop → fill au niveau atteint (open).

## Décision 4 — Placement et durée de vie

- **Placement : axe de grille à deux points**, non tranché d'avance —
  limite au **niveau balayé** (`BreakEvent.level`, retour sur la
  liquidité prise) OU au **close de reprise** (le prix de référence du
  signal). Les deux sont causalement connus au close du signal et du côté
  favorable du prix (retest requis).
- **Durée de vie K : NON TRANCHÉE ici.** L'étape 0 (décision 7) mesure
  K ∈ {1, 2, 4} bougies ; le gel du pré-enregistrement Hyp-5 fixera, sur
  cette table, soit un axe soit un point unique.

## Décision 5 — Stop : prix gelé au signal

Le stop garde le **prix absolu** défini au signal par la règle H3 gelée
(`close_signal − side × max(mèche, k × ATR_15m)`) : l'invalidation
appartient au marché, pas à l'ordre. La cible est recalculée depuis
l'entrée réelle : `target = entrée ± R × (entrée − stop)`. L'amélioration
d'entrée (limite sous l'open H3 pour un long) se traduit mécaniquement en
risque plus court à stop constant — c'est le cœur économique du chantier,
mesuré par la métrique `entry_improvement`.

## Décision 6 — Simulateur et équivalence

- Référence **Decimal** `H5Simulator` : machinerie H3 avec l'étape
  d'entrée remplacée (limite au repos évaluée intrabar, expiration,
  frais paramétrés maker entrée / taker sorties, pas de demi-spread à
  l'entrée). Miroir float64 dans le périmètre ADR-0003 ; **extraction
  inchangée** (les lignes H3 suffisent — pas de profil de volume).
- **Équivalence à l'échelle ADR-0003 complète** : mini-équivalence
  synthétique en CI exerçant les quatre chemins critiques (fill par
  traversée, expiration sans fill, entrée+stop même bougie, frontière
  d'expiration exacte) ; **90 jours Decimal trade par trade sur LES DEUX
  instruments** (standard depuis l'addendum A d'ADR-0003) avec compteurs
  `filled`/`expired` exacts ; déterminisme au hash ; écritures ordonnées.
- **Métriques nouvelles** : `fill_rate` (remplis/signaux), `expired_signals`,
  `entry_improvement` (open H3 → limite, en fraction du risque signal).

## Décision 7 — Premier test : Hyp-5 = H3 sous fill maker

- **Étape 0, avant tout brouillon** : table descriptive 2024 (aucune
  rentabilité) — par placement × K ∈ {1, 2, 4} : taux de fill, délai
  médian jusqu'au fill, **amélioration d'entrée médiane** (open H3 →
  prix limite, en fraction du risque signal, normalisation k=4 point
  central du gel H3). Calibrage utilisateur sur cette table, puis
  brouillon.
- Pré-enregistrement complet (docs/21) : hypothèse « le signal de timing
  H3 devient monétisable quand la contrainte de coût est levée par
  l'exécution maker sous fill conservateur » ; parent EXP-20260902-002 ;
  **mêmes critères gelés** (OOS espérance ≤ 0 OU PF < 1,15 sur l'un des
  deux instruments OU inversion intra-famille ; addendum B) ; **garde-fou
  100 trades par configuration + décision NON TESTABLE** hérités du
  précédent EXP-20260902-003 — d'autant plus nécessaires que le taux de
  fill réduit les populations. Critères évalués au point central 2 bp
  (décision 1).
- Séquence habituelle : équivalence → IS → rapport (dont fill_rate
  réalisé vs table descriptive) → arrêt — OOS sur ordre utilisateur.

## Conséquences

- Le plancher de coût passe de 22 bp à **11-16 bp/aller-retour** selon le
  point de sensibilité (maker 0-5 + taker 10 + demi-spread sortie 1),
  plus la suppression du demi-spread d'entrée — face à un signal brut
  mesuré de l'ordre de +1 à +3 bp-R par trade, le test devient
  discriminant au lieu d'être condamné d'avance.
- Le modèle taker gelé (EXP-20260901-001/002) reste l'étalon des
  expériences closes ; rien n'est réécrit rétroactivement.
- Toute évolution des règles de fill se fait D'ABORD dans l'étalon
  Decimal, puis se propage au miroir fast sous les mêmes preuves.

## Alternatives considérées

- **Données tick / carnet** : la voie la plus fidèle, différée — coût
  d'acquisition et de stockage disproportionné pour un premier test de
  viabilité ; reste la voie de révision si Hyp-5 est prometteuse mais
  contestable sur la granularité bougie.
- **« Touché = rempli »** : écarté — suppose une priorité de file
  inconnaissable ; optimiste par construction.
- **Modèles de file d'attente probabilistes** : écartés — paramètres
  invérifiables sans données de carnet ; la traversée stricte est la
  borne inférieure honnête.
- **Tout-maker (sorties comprises)** : écarté — optimiste sur les jambes
  gagnantes ; noté en décision 2 comme raffinement futur documenté.
