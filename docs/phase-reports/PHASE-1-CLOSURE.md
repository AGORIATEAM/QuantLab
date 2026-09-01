# Phase 1 — Data Platform : rapport de clôture

**Date : 2026-09-01** · Périmètre : BTC/USDT + ETH/USDT spot Binance,
6 timeframes (1m, 5m, 15m, 1h, 4h, 1d), REST public + WebSocket, sans clé
API. Cadrage : `docs/adr/ADR-0001-phase1-data-scope.md` (+ addendum A).

## Definition of Done (docs/25 §34)

### [x] historical data reproducible
- Téléchargement reprenable, idempotent, checkpoint dérivé des données
  (T4, `67adc41`) ; relance sur plage couverte = 0 insertion (validé
  utilisateur, 2026-08-30).
- **Certificat de complétude** (2026-08-30) : 12 séries, 2017-08-17 →
  2026-08-30, zéro trou inexpliqué — chaque trou est comblé ou classifié
  `KNOWN_VENUE_GAP` (326, ouverts par design), scan+backfill `44ecb61`.
- Chaîne d'immutabilité en base : `candles` INSERT-only (migration 0004,
  test `test_candles_table_is_append_only`), CHECK OHLC exercés
  (`test_candle_integrity_checks_enforced_at_database_level`).

### [x] live data normalized
- Ingestion WS klines fermées → **même chemin normalize→validate que le
  REST** → `source='binance_ws'` (T8, `7a5ad67` ; addendum ADR A).
- Journal brut append-only `raw_ws_messages` (sans déduplication) ;
  réconciliation REST à provenance vraie (`source='binance'`), trous WS
  documentés `WS_OUTAGE`, continuité par la vue `candles_canonical`.
- Run réel 2026-09-01 : 12 streams, 1 207 frames, 8+4 klines ingérées,
  coupure de 90 s détectée (2 `WS_OUTAGE`) et réconciliée (4 bougies),
  vue canonique continue sur la fenêtre.

### [x] quality checks active
- Quarantaine `INVALID_CANDLE` à la validation (T3, `57ac9ac`) ; scan de
  gaps + backfill + classification (T5) ; `CANDLE_MISMATCH` au verify de
  dataset (T6) ; `WS_OUTAGE` (T8).
- Ledger au 2026-09-01 : GAP 305/0 ouverts, INVALID_CANDLE 330/0 (résolus
  avec note), KNOWN_VENUE_GAP 326 (ouverts par design), WS_OUTAGE 2
  (mesure opérationnelle). Chaque événement est résolu ou ouvert pour une
  raison documentée.

### [x] datasets versioned
- Registry immuable hash-vérifié (T6, `bc6b3a7`) : sérialisation
  canonique versionnée `qlds-v1` (spec complète dans
  `quantlab/data/datasets.py`, verrouillée octet par octet par golden
  test), sous-hash par série, insertion tardive ⇒ verify échoue (testé).
- **Dataset officiel** : `btc-eth-spot-binance@v1`, 12 séries,
  12 220 098 bougies, [2017-08-17 → 2026-08-30),
  `content_hash 178e7403a3d60e4a…cfbb9b46` — verify OK en 2 min 16
  (run réel 2026-09-01).

### [x] replay deterministic
- Fail-closed : `verify_series` par série consommée avant toute émission
  (ADR décision 6 ; T7, `bf77ad8`) — refus testé contre PostgreSQL réel.
- Zéro look-ahead : émission ordonnée par close_time (départage durée
  croissante), horloge simulée, test explicite ; déterminisme prouvé par
  hash de flux ; snapshot REPEATABLE READ unique verify+stream.
- Débit mesuré (2026-09-01) : 1m seul 51 098 bougies/s ; 12 séries
  fusionnées 29 138 bougies/s. Premier consommateur réel : baselines
  T7bis (`EXP-20260901-001/002`, enregistrées docs/21 dans
  `experiments/`).

### [x] monitoring operational
- `make health` (T9, `f8438ab`) : fraîcheur REST/WS par série,
  complétude en mode rapport, événements ouverts par code, `WS_OUTAGE`
  agrégés, latence WS avg/p95/max depuis le journal brut ; exit 0/1 ;
  audité `HEALTH_CHECK`.
- `make sync` : téléchargement incrémental → scan/backfill → health.
- Run réel 2026-09-01 : health pré-sync a détecté 10 séries REST rassises
  et l'îlot de réconciliation (2 705 bougies/symbole) ; sync a tout
  rattrapé ; **health final : HEALTHY, exit 0** (latence WS avg 283 ms,
  p95 675 ms).

## Reste ouvert (justifié, avec point de reprise)

| Sujet | Justification | Reprise |
|---|---|---|
| Modèle de fill commun (convention de comptage des trades incluse) | Un seul consommateur (baselines T7bis) ; mutualiser sans second usage serait spéculatif | Phase 2, premier moteur (BACKLOG.md) |
| Optimisation du verify au démarrage du replay | Règle Phase 1 = verify complet ; ~2 min sur 12 séries, benchmarks enregistrés | Phase 2, si le coût gêne (BACKLOG.md) |
| Live non démonisé ; fraîcheur WS informative | Le live n'alimente que les données et tourne à la demande ; `--require-ws` prêt | Quand le live devient un service (Phase 2+) |
| `dataset_lineage`, export Parquet, archive brute REST | Conditions de révision explicites de l'ADR-0001 | Déclencheurs documentés (ADR + BACKLOG.md) |
| Page entière de klines quarantinées au backfill → classée `KNOWN_VENUE_GAP` par défaut | Cas jamais observé sur 9 ans ; plafond documenté en commentaire | Si le cas apparaît (gaps.py) |
| Monitoring Engine complet (dashboards, alerting) | Hors périmètre Phase 1 par décision | docs/13, phase dédiée |

## Références d'exécution

Commits jalons : ADR `27ae988`+`6933bd2` · T1 `faa5319` · T2 `9086e26` ·
T3 `57ac9ac` · T4 `67adc41` · T5 `44ecb61` · T6 `bc6b3a7` · T7 `bf77ad8` ·
T7bis `645df26` · T7c `76dd012` · T8 `7a5ad67` · T9 `f8438ab` · T10 `425f021`.
Suite : 166 tests (unit + intégration PostgreSQL), CI 6 jobs. Sauvegardes :
`make backup` (pg_dump vérifié) + `make restore-check`.
