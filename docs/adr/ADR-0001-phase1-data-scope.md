# ADR-0001 — Périmètre data de la Phase 1 (Data Platform)

## Statut
ACCEPTED — 2026-08-26 (plan Phase 1 validé, incluant les modifications demandées à la revue)

## Contexte
La Phase 1 construit la plateforme de données pour BTC/USDT et ETH/USDT spot, avec
Binance comme source publique (aucun compte, aucune clé API). Les docs 03/04/23/25
définissent le système cible complet ; plusieurs éléments doivent être explicitement
inclus, différés ou adaptés pour cette phase. Ce qui suit fige ces choix.

## Décision

1. **OHLCV uniquement, timeframes natifs Binance** (1m, 5m, 15m, 1h, 4h, 1d,
   configurables). Pas de trades, ni d'order book, ni d'agrégation locale de bougies :
   les bougies sont celles fournies par la venue (provenance « venue-provided »,
   docs/03 §26). Conséquence : aucun dataset dérivé n'existe en Phase 1, la table
   `dataset_lineage` (docs/23 §151) est différée jusqu'au premier dataset dérivé
   (agrégation ou correction — attendu en Phase 2).

2. **Dataset versionné = snapshot logique hash-vérifié.** Un dataset publié référence
   une sélection immuable de `candles` (instrument, timeframe, source, plage) et un
   `content_hash` SHA-256 calculé sur une sérialisation canonique versionnée des
   lignes. `storage_uri` est une URI logique PostgreSQL. Pas de Parquet ni d'object
   storage en Phase 1 (roadmap §29 : « selon volume » ; ~12 M lignes tiennent
   largement en PostgreSQL). **Condition de révision :** export Parquet + object
   storage dès que le volume dégrade les requêtes de recherche ou que des données
   V2 (trades, order book) arrivent.

3. **Non-persistance du brut REST en Phase 1.** Les payloads klines REST ne sont pas
   archivés : la venue est re-téléchargeable à l'identique et le magasin canonique
   (`candles`) est protégé par hash de dataset ; le mode `--verify` du downloader
   permet de re-comparer à la source à tout moment. **Condition de révision :** si
   une divergence `CANDLE_MISMATCH` est observée entre re-téléchargements (la venue
   réécrit son historique), ou si une source non re-téléchargeable est ajoutée, la
   conservation du brut correspondant devient obligatoire avant tout nouvel import.

4. **Exception : les messages WebSocket bruts sont conservés** (chemin live, T8).
   Un flux WS est éphémère — non re-téléchargeable par nature. Les messages reçus
   sont archivés en append-only avant normalisation, pour audit et rejeu du pipeline
   d'ingestion (docs/03 §9). Le périmètre exact (tous les messages des streams
   souscrits vs uniquement les klines fermées) et le support (fichiers JSONL
   compressés vs table) seront tranchés à la conception de T8, dans un addendum au
   présent ADR.

5. **Provenance par source distincte :** `source='binance'` pour l'historique REST,
   `source='binance_ws'` pour le live. L'unicité des candles porte sur
   (instrument, timeframe, open_time, source) : les deux coexistent et leur
   comparaison servira de contrôle qualité croisé.

6. **Replay fail-closed :** `replay_candles(dataset_id)` exécute `verify_dataset`
   au démarrage et échoue si le hash diverge du hash publié. Un replay ne consomme
   jamais silencieusement des données qui ne sont plus celles du dataset figé.

## Conséquences
- Reproductibilité garantie par la chaîne : candles INSERT-only → dataset publié
  immuable → hash re-vérifiable → replay refusant toute divergence.
- Dette acceptée et suivie : `dataset_lineage` absente (migration future), pas
  d'archive brute REST (condition de révision ci-dessus), pas de Parquet.
- Le chemin live est plus lourd que le chemin historique (archive brute en plus) —
  assumé, car c'est le seul chemin où la donnée source est irrécupérable.
- T8 devra dimensionner l'archive WS (rotation/compression) et documenter son choix.

## Alternatives considérées
- **Archiver le brut REST dès la Phase 1** : écarté — duplication d'une source
  re-téléchargeable, coût de stockage et de code sans consommateur identifié ;
  la condition de révision couvre le risque résiduel (réécriture d'historique venue).
- **Datasets matérialisés en fichiers Parquet dès la Phase 1** : écarté — ajoute
  pyarrow et une seconde vérité des données pour un volume qui ne le justifie pas.
- **Agréger localement 1m → TF supérieurs** : écarté en Phase 1 — les TF natifs
  préservent la provenance venue et évitent un moteur d'agrégation sans besoin actuel.
- **Dumps publics `data.binance.vision` pour l'historique** : écarté — évite le rate
  limit mais ajoute un second parseur pour un gain unique (~30 min de téléchargement).

---

## Addendum A — Chemin live WebSocket (T8)

**Statut : ACCEPTED — 2026-09-01** (tranche les points laissés ouverts par la
décision 4 ; arbitrage de provenance amendé à la revue du plan T8)

### A.1 Périmètre de l'archive brute

Seuls les **messages kline fermés** (`k.x == true`) des streams souscrits
sont archivés. Les updates intra-bougie ne produisent aucune bougie
canonique, n'ont aucun consommateur en Phase 1 et multiplieraient le volume
par ~60 ; seul le message fermé constitue la preuve irrécupérable de ce que
la venue a poussé.

### A.2 Support : table PostgreSQL `raw_ws_messages`

Table append-only (trigger `forbid_mutation`), et non JSONL : même infra de
migration, de sauvegarde (`make backup`), d'immutabilité et d'audit que le
reste ; requêtable pour rejouer le pipeline d'ingestion (docs/03 §9).
Volume attendu ≈ 20 k messages/jour pour 12 streams (quelques Mo/jour).
**Condition de révision :** rotation/compression si le volume dégrade les
sauvegardes ou les requêtes.

**L'archive ne déduplique pas.** C'est un journal brut de ce que la venue a
poussé, pas une table métier : un kline fermé reçu deux fois (re-livraison
après reconnexion, replays du serveur) est archivé deux fois, horodaté à
chaque réception. La déduplication appartient au chemin candles
(ON CONFLICT sur l'unicité métier), pas au journal.

### A.3 Provenance : jamais de source mensongère

- Le flux WS écrit `source='binance_ws'`, exclusivement à partir de
  messages WS.
- Après une coupure, les bougies manquées sont récupérées par REST et
  insérées avec **leur vraie provenance : `source='binance'`**.
  `data_version` garde son sens documenté (révision de données venue) et
  n'est pas détourné en marqueur de réconciliation.
- La série `binance_ws` **conserve son trou**, enregistré comme
  DataQualityEvent **`WS_OUTAGE`** (début, fin, bougies manquées par
  série) — mesure opérationnelle de la fiabilité du flux.
- La continuité de lecture est fournie par la vue **`candles_canonical`** :
  une bougie par (instrument, timeframe, open_time), précédence
  `'binance'` puis `'binance_ws'`.

### A.4 Partage des rôles de lecture

```text
recherche / datasets / replay  →  candles WHERE source='binance' (REST pur)
consommateurs live             →  candles_canonical (continuité, précédence REST)
contrôle qualité croisé (§5)   →  binance vs binance_ws, purs tous les deux,
                                  sans liste d'exclusions à connaître
```

Le contrôle croisé de la décision 5 compare ainsi naturellement du pur WS à
du pur REST : les patchs de réconciliation vivent dans la série REST, où
est leur place.
