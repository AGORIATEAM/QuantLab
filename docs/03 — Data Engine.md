# 03 — Data Engine

**Projet : QuantLab**  
**Document : Data Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

---

# 1. Objectif

Le Data Engine est la couche responsable de l'acquisition, de la validation, de la normalisation, de la synchronisation et de la distribution des données utilisées par QuantLab.

Il constitue l'une des briques les plus critiques du système.

Une stratégie ne peut être correctement évaluée que si les données utilisées sont :

- fiables ;
- cohérentes ;
- suffisamment précises ;
- correctement horodatées ;
- versionnées ;
- reproductibles ;
- adaptées au marché étudié.

Le Data Engine ne prend aucune décision de trading.

Il fournit uniquement des données fiables aux autres composants.

---

# 2. Responsabilités

Le Data Engine est responsable de :

1. connecter les fournisseurs de données ;
2. récupérer les données historiques ;
3. recevoir les données temps réel ;
4. normaliser les formats ;
5. vérifier leur intégrité ;
6. détecter les doublons ;
7. détecter les trous de données ;
8. détecter les anomalies ;
9. synchroniser les timestamps ;
10. gérer les reconnexions ;
11. gérer les limites API ;
12. gérer les erreurs fournisseurs ;
13. enrichir les données ;
14. publier les événements de données ;
15. transmettre les données au Storage Engine.

Il ne doit pas :

- calculer le scoring d'une stratégie ;
- décider d'une entrée ;
- gérer une position ;
- envoyer un ordre ;
- modifier une stratégie.

---

# 3. Architecture générale

```text
                    DATA PROVIDERS
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
     CEX/API           BROKERS             DEX
        │                 │                 │
        └─────────────────┼─────────────────┘
                          ▼
                  CONNECTOR LAYER
                          │
                          ▼
                   INGESTION LAYER
                          │
                          ▼
                 VALIDATION LAYER
                          │
                          ▼
                NORMALIZATION LAYER
                          │
                          ▼
                ENRICHMENT LAYER
                          │
                          ▼
                   EVENT BUS
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
       STORAGE ENGINE          LIVE ANALYSIS
```

---

# 4. Sources de données

QuantLab doit être conçu pour intégrer plusieurs catégories de fournisseurs.

## 4.1 Exchanges centralisés

Exemples de données :

- OHLCV ;
- trades ;
- order book ;
- funding ;
- open interest ;
- liquidations ;
- mark price ;
- index price.

La première version doit privilégier des marchés très liquides.

---

# 4.2 Brokers

Pour les marchés traditionnels :

- XAU/USD ;
- Forex ;
- indices ;
- futures ;
- actions selon les futures intégrations.

Le connecteur doit isoler les spécificités du broker.

---

# 4.3 DEX

Les marchés décentralisés nécessitent une couche spécifique.

Données potentielles :

- swaps ;
- pools ;
- liquidité ;
- réserves ;
- prix ;
- volumes ;
- frais ;
- événements on-chain ;
- transactions ;
- blocs.

Le système doit conserver les informations permettant de reconstruire le contexte de liquidité.

---

# 4.4 Données on-chain

Pour les crypto-actifs :

- transactions ;
- wallets ;
- mouvements de tokens ;
- volumes ;
- TVL ;
- liquidité ;
- activité des contrats ;
- événements blockchain.

Les données on-chain doivent être séparées des données de marché classiques.

---

# 4.5 Données macroéconomiques

Le Data Engine pourra intégrer :

- taux directeurs ;
- CPI ;
- NFP ;
- PPI ;
- PIB ;
- chômage ;
- décisions de banques centrales ;
- calendrier économique.

Ces données seront notamment utilisées par le News Filter et le Decision Engine.

---

# 5. Types de données

Le système doit supporter au minimum :

## Market Data

- Tick ;
- Trade ;
- Quote ;
- OHLCV ;
- Order Book.

## Derivatives Data

- Funding Rate ;
- Open Interest ;
- Liquidations ;
- Mark Price ;
- Index Price.

## Alternative Data

- On-chain ;
- macro ;
- sentiment lorsque disponible ;
- données de liquidité.

---

# 6. Modèle OHLCV

Une bougie standard doit contenir au minimum :

```python
Candle:
    timestamp
    open
    high
    low
    close
    volume
    symbol
    exchange
    timeframe
```

Des champs supplémentaires peuvent être ajoutés :

```text
quote_volume
trade_count
vwap
taker_buy_volume
taker_sell_volume
```

---

# 7. Timestamps

Le système doit utiliser une référence temporelle unique.

Tous les timestamps internes doivent être stockés en UTC.

Format recommandé :

```text
ISO 8601 UTC
```

ou timestamp numérique UTC selon le système.

Le timezone local d'un utilisateur ne doit jamais modifier les données historiques.

---

# 8. Précision temporelle

Le système doit conserver la précision disponible auprès du fournisseur.

Selon la source :

- secondes ;
- millisecondes ;
- microsecondes lorsque disponibles.

La précision ne doit pas être artificiellement réduite avant le stockage brut.

---

# 9. Raw Data

Le Data Engine doit conserver une représentation des données brutes lorsque cela est nécessaire.

Architecture :

```text
Provider
   ↓
Raw Data
   ↓
Validation
   ↓
Normalized Data
```

La conservation du brut permet :

- audit ;
- reconstruction ;
- correction des erreurs ;
- comparaison entre versions ;
- amélioration future du pipeline.

---

# 10. Normalisation

Chaque fournisseur peut utiliser des formats différents.

Le Data Engine doit les convertir vers des modèles internes communs.

Exemple :

```text
Binance Candle
Kraken Candle
Coinbase Candle
        ↓
Normalized Candle
```

Le reste du système ne doit pas connaître le format spécifique du fournisseur.

---

# 11. Identité d'un instrument

Chaque instrument doit disposer d'un identifiant interne.

Exemple :

```text
asset_id
symbol
base_asset
quote_asset
market_type
exchange
contract_type
```

Exemple conceptuel :

```yaml
asset_id: BTC-USDT-SPOT
base_asset: BTC
quote_asset: USDT
market_type: spot
exchange: example_exchange
```

---

# 12. Market Type

Le système doit distinguer :

- spot ;
- perpetual ;
- future ;
- option ;
- CFD ;
- forex ;
- action ;
- ETF ;
- DEX pool.

Cette distinction est importante pour interpréter correctement les données.

---

# 13. Connecteurs

Chaque source doit être encapsulée par un connecteur.

Interface conceptuelle :

```python
class DataConnector:

    def connect():
        ...

    def disconnect():
        ...

    def fetch_historical():
        ...

    def subscribe():
        ...

    def unsubscribe():
        ...

    def health_check():
        ...
```

Les implémentations spécifiques ne doivent pas être exposées aux moteurs supérieurs.

---

# 14. Historique

Le système doit pouvoir télécharger des données historiques par :

- actif ;
- exchange ;
- timeframe ;
- date de début ;
- date de fin.

Exemple :

```text
BTC-USDT
5m
2024-01-01
2026-01-01
```

Le téléchargement doit être :

- reprenable ;
- idempotent ;
- vérifiable ;
- journalisé.

---

# 15. Données temps réel

Le système doit supporter les flux temps réel lorsque le fournisseur le permet.

Architecture :

```text
WebSocket / Stream
       ↓
Connector
       ↓
Parser
       ↓
Validator
       ↓
Normalizer
       ↓
Event Bus
```

Les flux temps réel ne doivent jamais être directement connectés au moteur d'exécution sans validation intermédiaire.

---

# 16. Reconnexion

Les connecteurs temps réel doivent gérer :

- déconnexion ;
- timeout ;
- erreur réseau ;
- changement de connexion ;
- limitation API.

Stratégie recommandée :

```text
Connection Lost
      ↓
Retry
      ↓
Exponential Backoff
      ↓
Reconnect
      ↓
Resynchronize
```

---

# 17. Gap Detection

Le Data Engine doit détecter les trous dans les séries.

Exemple :

```text
10:00
10:05
10:10
10:20
```

La bougie 10:15 est absente.

Le système doit générer un événement :

```text
DATA_GAP_DETECTED
```

Une stratégie ne doit pas utiliser silencieusement une série incomplète.

---

# 18. Duplicate Detection

Le système doit détecter les données dupliquées.

Identifiant logique possible :

```text
exchange
symbol
timeframe
timestamp
```

Deux enregistrements identiques ne doivent pas être considérés comme deux observations différentes.

---

# 19. Data Validation

Chaque donnée doit passer par plusieurs contrôles.

## Contrôles temporels

- timestamp valide ;
- ordre chronologique ;
- absence de timestamps futurs ;
- absence de doublons.

## Contrôles numériques

Pour une bougie :

```text
high >= max(open, close)
low <= min(open, close)
high >= low
volume >= 0
```

Une donnée violant ces contraintes doit être rejetée ou placée en quarantaine.

---

# 20. Anomaly Detection

Le Data Engine doit pouvoir détecter des anomalies évidentes.

Exemples :

- volume impossible ;
- prix négatif ;
- variation extrême ;
- timestamp incorrect ;
- changement de symbole ;
- données répétées.

Attention :

Une variation de prix extrême n'est pas nécessairement une erreur.

Elle doit donc être signalée plutôt que supprimée automatiquement.

---

# 21. Data Quality Score

Chaque dataset peut recevoir un score de qualité.

Exemple conceptuel :

```text
Completeness
Consistency
Timestamp Integrity
Duplicate Rate
Missing Data
Provider Reliability
```

Résultat :

```text
Data Quality Score = 0 → 100
```

Une stratégie pourra imposer un seuil minimal de qualité.

---

# 22. Data Quarantine

Les données suspectes ne doivent pas être détruites immédiatement.

Architecture :

```text
Incoming Data
      ↓
Validation
   ┌──┴──┐
   ↓     ↓
Valid  Suspicious
   ↓     ↓
Store  Quarantine
```

La quarantaine permet une analyse ultérieure.

---

# 23. Réconciliation

Lorsque plusieurs fournisseurs existent pour le même marché, le système pourra comparer :

```text
Provider A
Provider B
Provider C
```

Objectif :

- détecter les divergences ;
- identifier les erreurs ;
- mesurer la qualité des fournisseurs.

La divergence ne signifie pas nécessairement qu'un fournisseur est faux.

Les marchés peuvent présenter des différences de liquidité et de microstructure.

---

# 24. Données multi-exchange

QuantLab doit conserver la provenance exacte des données.

Exemple :

```text
BTC/USDT
Exchange A
Exchange B
Exchange C
```

Les données ne doivent pas être fusionnées aveuglément.

Chaque observation doit conserver :

- source ;
- timestamp ;
- marché ;
- type d'instrument.

---

# 25. Agrégation

Le système pourra créer des données agrégées.

Exemple :

```text
1m → 5m → 15m → 1H → 4H → 1D
```

L'agrégation doit être déterministe.

Exemple :

```text
Open = first
High = max
Low = min
Close = last
Volume = sum
```

---

# 26. Construction des bougies

Les bougies doivent être construites avec prudence.

Le système doit distinguer :

- bougies fournies par un exchange ;
- bougies calculées à partir des trades ;
- bougies agrégées.

La provenance doit être enregistrée.

---

# 27. Market Sessions

Le Data Engine doit pouvoir associer une session à chaque donnée lorsque cela est pertinent.

Exemples :

- Asia ;
- London ;
- New York ;
- overlap London/New York.

Pour les crypto-actifs, qui tradent 24/7, les sessions doivent être définies comme des fenêtres analytiques et non comme des périodes de fermeture.

---

# 28. Data Events

Le Data Engine doit publier des événements.

Exemples :

```text
CANDLE_RECEIVED
CANDLE_CLOSED
TRADE_RECEIVED
ORDERBOOK_UPDATED
FUNDING_UPDATED
OPEN_INTEREST_UPDATED
DATA_GAP_DETECTED
DATA_QUALITY_WARNING
PROVIDER_DISCONNECTED
PROVIDER_RECONNECTED
```

---

# 29. Event Schema

Exemple conceptuel :

```json
{
  "event_type": "CANDLE_CLOSED",
  "timestamp": "2026-01-01T10:00:00Z",
  "symbol": "BTC-USDT",
  "exchange": "example_exchange",
  "timeframe": "5m",
  "data_version": "1.0"
}
```

---

# 30. Data Versioning

Les transformations importantes doivent être versionnées.

Exemple :

```text
dataset_version = 1.0
normalization_version = 1.2
provider_version = ...
```

Une expérience doit pouvoir indiquer précisément quelles données elle a utilisées.

---

# 31. Reproductibilité

Un backtest doit pouvoir être relié à :

```text
Dataset
+
Dataset Version
+
Strategy Version
+
Configuration Version
+
Code Version
```

Cela permet de reconstruire une expérience.

---

# 32. Data Lineage

Chaque donnée transformée doit pouvoir être reliée à sa source.

Exemple :

```text
Normalized Candle
      ↓
Raw Candle
      ↓
Exchange
      ↓
Provider
```

Pour les données dérivées :

```text
Market Profile
      ↓
Normalized Trades
      ↓
Exchange
```

---

# 33. Latence

Pour les données temps réel, le système doit mesurer :

```text
Exchange Timestamp
        ↓
Reception Timestamp
        ↓
Processing Timestamp
```

Cela permet de calculer :

- network latency ;
- processing latency ;
- end-to-end latency.

---

# 34. Clock Synchronization

Les serveurs doivent utiliser une horloge synchronisée.

Le système doit détecter les dérives temporelles importantes.

Une horloge incorrecte peut provoquer :

- signaux faux ;
- mauvais ordre des événements ;
- problèmes de backtest ;
- erreurs d'exécution.

---

# 35. Rate Limits

Les connecteurs doivent connaître les limites de chaque fournisseur.

Ils doivent gérer :

- nombre de requêtes ;
- poids des requêtes ;
- quotas ;
- restrictions WebSocket.

Une abstraction commune doit être utilisée pour éviter que chaque stratégie gère directement les limites API.

---

# 36. Cache

Le Data Engine peut utiliser un cache pour :

- données fréquemment demandées ;
- métadonnées ;
- informations instrument ;
- requêtes historiques.

Le cache ne doit jamais être considéré comme la source de vérité.

---

# 37. Résilience

Le système doit continuer à fonctionner correctement lorsqu'un fournisseur devient indisponible.

Selon le contexte :

```text
Provider A unavailable
        ↓
Provider B
```

ou :

```text
Trading paused
```

Le fallback doit être défini par type de donnée.

---

# 38. Priorité des données

Toutes les données ne possèdent pas la même importance.

Exemple :

```text
Critical
Market price
Order status

High
Volume
Order book

Medium
Funding
Open interest

Optional
Sentiment
Alternative data
```

Les priorités seront définies précisément dans les modules concernés.

---

# 39. Données pour le Backtesting

Les données de backtest doivent être isolées des flux live.

Le backtest doit utiliser un dataset figé.

Il ne doit pas utiliser accidentellement :

- données futures ;
- données corrigées après coup ;
- informations indisponibles à l'époque simulée.

---

# 40. Prévention du Look-Ahead Bias

Le Data Engine doit empêcher l'utilisation accidentelle d'informations futures.

Exemple incorrect :

```text
Bougie 10:00
+
Volume final connu à 10:05
```

si la stratégie est censée prendre sa décision à 10:00.

Le timestamp de disponibilité de la donnée doit être distingué du timestamp auquel elle se rapporte.

---

# 41. Survivorship Bias

Pour les univers multi-actifs, le système doit conserver les actifs qui ont disparu du marché lorsque les données sont disponibles.

Une analyse historique ne doit pas uniquement considérer les actifs actuellement survivants.

---

# 42. Frais et données d'exécution

Le Data Engine doit pouvoir intégrer :

- trading fees ;
- funding fees ;
- gas fees ;
- commissions ;
- slippage estimé.

Ces données seront nécessaires au Backtesting Engine.

---

# 43. Données DEX

Pour les DEX, le système doit pouvoir conserver :

```text
block_number
transaction_hash
pool_address
token_in
token_out
amount_in
amount_out
timestamp
gas
fee
```

Les données doivent être liées à la blockchain et au protocole.

---

# 44. Données de liquidité

Pour les pools AMM :

```text
liquidity_before
liquidity_after
reserve_0
reserve_1
price_before
price_after
```

Ces informations pourront alimenter ultérieurement des analyses spécifiques.

---

# 45. Data Catalog

QuantLab doit maintenir un catalogue des datasets disponibles.

Pour chaque dataset :

- nom ;
- source ;
- actif ;
- période ;
- timeframe ;
- fréquence ;
- qualité ;
- version ;
- date d'import ;
- statut.

---

# 46. Data Health

Le Monitoring Engine doit recevoir des métriques du Data Engine :

```text
data_freshness
data_gap_count
duplicate_count
provider_latency
provider_status
quality_score
```

---

# 47. Sécurité

Les credentials des fournisseurs doivent être stockés hors du code.

Le Data Engine doit utiliser :

- variables d'environnement ;
- secret manager ;
- credentials séparés par environnement.

Les clés utilisées uniquement pour lire les données doivent être distinctes des clés permettant de trader.

Lorsque cela est possible, les clés de lecture seule doivent être privilégiées pour le Data Engine.

---

# 48. Tests

Le Data Engine doit posséder :

## Unit Tests

Tester :

- parsing ;
- normalisation ;
- validation ;
- détection de doublons ;
- calculs temporels.

## Integration Tests

Tester :

- connexion API ;
- WebSocket ;
- stockage ;
- reconnexion.

## Failure Tests

Tester :

- timeout ;
- API indisponible ;
- données corrompues ;
- messages incomplets ;
- doublons ;
- gaps.

---

# 49. Critères d'acceptation

Le Data Engine est considéré comme valide lorsque :

- les données sont correctement normalisées ;
- les timestamps sont cohérents ;
- les doublons sont détectés ;
- les gaps sont détectés ;
- les données invalides sont rejetées ou mises en quarantaine ;
- les erreurs fournisseurs sont gérées ;
- les connexions peuvent être rétablies ;
- les datasets sont versionnés ;
- la provenance est conservée ;
- les données historiques sont reproductibles ;
- les flux temps réel sont surveillés ;
- les secrets ne sont jamais exposés.

---

# 50. Priorités d'implémentation

## V1

- BTC ;
- ETH ;
- données OHLCV ;
- historique ;
- temps réel ;
- normalisation ;
- validation ;
- PostgreSQL/Supabase ;
- logging ;
- versioning.

## V2

- trades ;
- order book ;
- funding ;
- open interest ;
- liquidations.

## V3

- multi-exchange ;
- réconciliation ;
- données on-chain.

## V4

- DEX ;
- pools ;
- liquidité ;
- données blockchain avancées.

## V5

- données alternatives ;
- sentiment ;
- sources macro avancées.

---

# 51. Interface avec les autres moteurs

Le Data Engine fournit principalement des données au :

- Storage Engine ;
- Market Analysis Engine ;
- Market Structure Engine ;
- Volume Profile Engine ;
- Smart Money Concepts Engine ;
- Knowledge Engine ;
- Research Engine.

Il ne doit pas appeler directement le Risk Engine ou l'Execution Engine.

---

# 52. Principe fondamental

La règle fondamentale du Data Engine est :

> **Garbage in, garbage out.**

Une stratégie sophistiquée construite sur des données incorrectes reste une stratégie incorrecte.

QuantLab doit donc investir dans la qualité des données avant d'investir dans la sophistication des modèles.

---

# 53. Résultat attendu

Le Data Engine doit fournir une couche de données fiable permettant aux autres moteurs de fonctionner sans connaître les particularités de chaque fournisseur.

Le résultat attendu est :

```text
Multiple Providers
       ↓
Unified Data Model
       ↓
Validated Data
       ↓
Versioned Data
       ↓
Reproducible Research
       ↓
Reliable Analysis
```

---

# 54. Statut

**Version : 1.0**

Le Data Engine constitue la fondation de l'ensemble du système.

Toute modification importante concernant le format des données, les sources, la normalisation ou la provenance doit être documentée dans un ADR et répercutée dans les documents :

- `04-Storage-Engine.md`
- `05-Market-Analysis-Engine.md`
- `18-Testing-Strategy.md`
- `23-Database-Schema.md`
- `24-Security.md`