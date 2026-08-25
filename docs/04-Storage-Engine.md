# 04 — Storage Engine

**Projet : QuantLab**  
**Document : Storage Engine**  
**Version : 1.0**  
**Statut : Spécification technique**

## 1. Objectif

Le Storage Engine est la couche responsable de la persistance, de l'organisation, de la récupération, du versioning et de la conservation des données de QuantLab.

Son objectif principal est de garantir que les données utilisées par QuantLab soient persistantes, accessibles, cohérentes, versionnées, traçables, reproductibles, sécurisées et évolutives.

Le Storage Engine ne contient aucune logique de trading. Il ne décide ni d'acheter, ni de vendre, ni de modifier une stratégie, ni de prendre un risque, ni d'exécuter un ordre.

## 2. Principe architectural

Les moteurs métier ne doivent jamais dépendre directement du fournisseur de base de données.

```text
Application
    ↓
Storage Engine
    ↓
Storage Interface
    ↓
Database / Object Storage / Cache
```

Ainsi :

```text
Market Analysis Engine
        ↓
Storage Engine
        ↓
PostgreSQL
```

et non :

```text
Market Analysis Engine
        ↓
SQL PostgreSQL directement
```

Cette abstraction permet de changer ultérieurement de technologie sans réécrire les moteurs métier.

## 3. Architecture globale

```text
                    QUANTLAB
                       │
                       ▼
                STORAGE ENGINE
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
   PostgreSQL      Object Storage     Cache
        │              │
        │              │
        ▼              ▼
   Structured       Large Files
      Data           Datasets
```

## 4. Stack initiale

### Base relationnelle

**PostgreSQL**

Utilisation :

- métadonnées ;
- instruments ;
- bougies ;
- trades ;
- signaux ;
- stratégies ;
- expériences ;
- décisions ;
- risques ;
- ordres ;
- positions ;
- événements ;
- utilisateurs ;
- gouvernance.

### Supabase

Supabase peut être utilisé comme couche d'infrastructure autour de PostgreSQL.

Il pourra fournir notamment :

- PostgreSQL ;
- authentification ;
- API ;
- stockage objet ;
- politiques de sécurité ;
- fonctionnalités temps réel lorsque pertinentes.

**Principe important :** QuantLab doit considérer PostgreSQL comme le modèle de persistance relationnelle, et Supabase comme une infrastructure permettant de l'exploiter. Cela évite de coupler toute l'application à des fonctionnalités propriétaires.

## 5. Object Storage

Les fichiers volumineux ne doivent pas nécessairement être stockés directement dans PostgreSQL.

Exemples :

- datasets historiques massifs ;
- fichiers Parquet ;
- exports CSV ;
- snapshots ;
- fichiers de recherche ;
- modèles ML ;
- rapports ;
- artefacts d'expérimentation.

La base conserve la référence vers le fichier.

## 6. Séparation des responsabilités

Le Storage Engine gère :

- écriture ;
- lecture ;
- mise à jour ;
- suppression contrôlée ;
- versioning ;
- transactions ;
- indexation ;
- partitionnement ;
- rétention ;
- archivage ;
- backup ;
- restauration ;
- intégrité.

Il ne gère pas :

- stratégie ;
- scoring ;
- décision ;
- risk management ;
- execution.

## 7. Catégories de données

### Market Data

- candles ;
- trades ;
- quotes ;
- order books ;
- funding ;
- open interest ;
- liquidations.

### Derived Data

- indicateurs ;
- structure ;
- volume profile ;
- SMC ;
- features ;
- régimes de marché.

### Trading Data

- signals ;
- decisions ;
- risk assessments ;
- orders ;
- fills ;
- positions ;
- trades.

### Research Data

- experiments ;
- hypotheses ;
- datasets ;
- backtests ;
- results.

### Knowledge Data

- documentation ;
- observations ;
- lessons ;
- strategy versions ;
- model versions.

### Governance Data

- approvals ;
- deployments ;
- audit events ;
- configuration changes ;
- policy violations.

## 8. Source of Truth

Chaque catégorie doit avoir une source de vérité clairement définie.

Exemple :

```text
Historical Market Data
        ↓
Storage Engine

Current Position
        ↓
Execution / Trading State

Strategy Definition
        ↓
Knowledge / Strategy Registry
```

Il ne doit pas exister plusieurs sources contradictoires pour une même information critique.

## 9. Immutabilité des données historiques

Les données historiques brutes doivent être considérées comme immuables.

Si une donnée doit être corrigée :

```text
Dataset v1
   ↓
Correction
   ↓
Dataset v2
```

et non :

```text
Dataset v1
   ↓
Modification silencieuse
```

Cette règle est essentielle pour la reproductibilité des expériences.

## 10. Versioning

Chaque dataset important doit posséder une version.

Exemple :

```text
dataset_id:
btc_usdt_5m

version:
2026.08.01
```

Une expérience doit pouvoir référencer précisément :

```text
Dataset
Dataset Version
Strategy Version
Code Version
Configuration Version
```

## 11. Data Lineage

Le Storage Engine doit conserver la provenance des données.

```text
Backtest Result
      ↓
Experiment
      ↓
Dataset Version
      ↓
Normalized Dataset
      ↓
Raw Dataset
      ↓
Provider
```

Cela permet de répondre à :

- D'où vient cette donnée ?
- Quelle version de la donnée a produit ce résultat ?

## 12. Schéma logique

```text
Market
 ├── Instrument
 ├── Candle
 ├── Trade
 ├── OrderBook
 └── DerivativesData

Research
 ├── Experiment
 ├── Dataset
 ├── Backtest
 └── Result

Strategy
 ├── Strategy
 ├── StrategyVersion
 └── Configuration

Trading
 ├── Signal
 ├── Decision
 ├── RiskAssessment
 ├── Order
 ├── Fill
 ├── Position
 └── Trade

Governance
 ├── Approval
 ├── Deployment
 └── AuditEvent
```

Le détail complet sera défini dans `23-Database-Schema.md`.

## 13. Identifiants

Chaque entité importante doit disposer d'un identifiant unique.

Exemples :

```text
dataset_id
experiment_id
strategy_id
strategy_version_id
signal_id
decision_id
risk_assessment_id
order_id
position_id
trade_id
event_id
```

Les identifiants doivent être générés de manière robuste et éviter les collisions.

## 14. Timestamps

Les données doivent conserver plusieurs timestamps lorsqu'ils sont pertinents.

```text
event_timestamp
source_timestamp
received_at
processed_at
created_at
updated_at
```

Cela permet de distinguer :

- moment où l'événement s'est produit ;
- moment où QuantLab l'a reçu ;
- moment où il a été traité ;
- moment où il a été enregistré.

## 15. Transactions

Les opérations critiques doivent utiliser des transactions.

```text
Create Order
     ↓
Store Order
     ↓
Store Event
     ↓
Commit
```

Si une étape critique échoue :

```text
Rollback
```

Le système doit éviter les états partiellement enregistrés.

## 16. Idempotence

Les opérations d'écriture doivent être conçues pour éviter les doublons.

Exemple :

```text
event_id = ABC123
```

Si le même événement est reçu deux fois, il ne doit être enregistré qu'une fois lorsque la logique métier l'exige.

## 17. Contraintes d'intégrité

La base doit utiliser des contraintes lorsque cela est pertinent :

- primary keys ;
- foreign keys ;
- unique constraints ;
- check constraints ;
- not null ;
- indexes.

L'intégrité ne doit pas dépendre uniquement du code applicatif.

## 18. Indexation

Les tables fréquemment interrogées doivent être indexées.

Exemples :

```text
symbol
exchange
timestamp
timeframe
strategy_id
experiment_id
status
created_at
```

Les index doivent être ajoutés sur la base de mesures réelles de performance.

Trop d'index ralentissent les écritures.

## 19. Partitionnement

Les séries temporelles importantes pourront être partitionnées.

Exemple :

```text
candles
 ├── 2024
 ├── 2025
 └── 2026
```

ou par date, marché ou instrument.

Le choix définitif doit dépendre du volume réel.

## 20. Time-Series Data

Les données de marché sont principalement des séries temporelles.

Le stockage doit être optimisé pour les requêtes du type :

```sql
SELECT *
FROM candles
WHERE symbol = 'BTC-USDT'
AND timeframe = '5m'
AND timestamp BETWEEN ...
ORDER BY timestamp;
```

La conception doit privilégier ce type de requête.

## 21. Compression

Pour les datasets volumineux, la compression doit être envisagée.

Elle peut être appliquée :

- au stockage objet ;
- aux fichiers Parquet ;
- aux backups ;
- aux archives.

La compression ne doit pas compromettre inutilement les performances des données fréquemment utilisées.

## 22. Parquet

Le format Parquet est recommandé pour les datasets analytiques volumineux.

Exemple :

```text
data/
  market/
    BTC-USDT/
      5m/
        2025/
          data.parquet
```

Avantages :

- compression ;
- lecture colonne par colonne ;
- performance analytique ;
- compatibilité avec l'écosystème Python ;
- facilité de versioning.

## 23. PostgreSQL vs Object Storage

### PostgreSQL

Pour :

- données opérationnelles ;
- métadonnées ;
- relations ;
- événements ;
- stratégies ;
- trades ;
- résultats synthétiques.

### Object Storage

Pour :

- gros datasets ;
- Parquet ;
- snapshots ;
- fichiers ;
- modèles ;
- artefacts.

## 24. Cache

Un cache pourra être utilisé pour :

- métadonnées fréquemment consultées ;
- configuration ;
- instruments ;
- résultats coûteux ;
- données récentes.

Le cache n'est jamais la source de vérité.

En cas de divergence, la source persistante prévaut.

## 25. Repository Pattern

L'accès aux données doit passer par des repositories ou services équivalents.

```python
class CandleRepository:
    def get_range(...):
        ...

    def save(...):
        ...

    def bulk_save(...):
        ...
```

Le moteur métier ne doit pas écrire du SQL directement partout dans le projet.

## 26. Interfaces

Exemple :

```python
class StorageRepository:

    def create(self, entity):
        ...

    def get(self, entity_id):
        ...

    def update(self, entity):
        ...

    def delete(self, entity_id):
        ...
```

Les interfaces doivent rester suffisamment abstraites pour permettre l'évolution de l'infrastructure.

## 27. Bulk Operations

Les données de marché doivent être insérées par lots lorsque possible.

Mauvais modèle :

```text
1 candle
→ 1 transaction
→ 1 requête
```

Meilleur modèle :

```text
10 000 candles
→ batch
→ transaction
```

La taille optimale doit être déterminée par benchmark.

## 28. Lecture

Le Storage Engine doit supporter :

- lecture ponctuelle ;
- lecture par plage temporelle ;
- pagination ;
- agrégation ;
- filtrage ;
- lecture batch.

Les requêtes doivent être prévisibles et mesurables.

## 29. Pagination

Pour les datasets importants, la pagination doit éviter les offsets gigantesques lorsque ceux-ci deviennent coûteux.

Selon le contexte :

- cursor pagination ;
- timestamp pagination ;
- ID pagination.

## 30. Rétention

Toutes les données n'ont pas nécessairement besoin d'être conservées au même niveau de disponibilité.

```text
Hot
↓
Recent data

Warm
↓
Historical research

Cold
↓
Archive
```

Les politiques de rétention seront définies selon :

- importance ;
- coût ;
- fréquence d'utilisation ;
- exigences réglementaires éventuelles.

## 31. Archivage

Les données anciennes peuvent être déplacées vers un stockage moins coûteux.

```text
PostgreSQL
    ↓
Object Storage
    ↓
Archive
```

L'archive doit rester identifiable et récupérable.

## 32. Backups

Le système doit prévoir :

- backups automatiques ;
- backups réguliers ;
- restauration testée ;
- conservation de plusieurs versions.

Un backup qui n'a jamais été restauré n'est pas une preuve de résilience.

## 33. Disaster Recovery

Le système doit définir :

- RPO ;
- RTO ;
- procédure de restauration ;
- dépendances critiques ;
- procédure de reprise.

```text
Database Failure
      ↓
Detect
      ↓
Failover / Restore
      ↓
Verify Integrity
      ↓
Resume
```

## 34. Environnements

Chaque environnement doit posséder ses propres données.

```text
Development
Testing
Research
Paper
Production
```

Les données de production ne doivent pas être manipulées directement par les environnements de développement.

## 35. Sécurité

Les accès doivent suivre le principe du moindre privilège.

```text
Data Collector
    ↓
WRITE market data

Research
    ↓
READ historical data

Trading
    ↓
READ required data

Admin
    ↓
FULL ACCESS
```

Les permissions doivent être explicitement définies.

## 36. Row Level Security

Lorsque Supabase est utilisé, les politiques RLS peuvent contrôler l'accès aux données sensibles ou multi-utilisateurs.

La RLS ne doit pas être considérée comme l'unique couche de sécurité.

```text
Application
    ↓
API
    ↓
Database Permissions
    ↓
RLS
```

## 37. Secrets

Le Storage Engine ne doit jamais stocker :

- mots de passe en clair ;
- secrets API ;
- clés privées ;
- credentials sensibles.

Les secrets doivent être gérés par un mécanisme dédié.

## 38. Audit

Les opérations sensibles doivent produire un audit event.

Exemples :

```text
STRATEGY_CREATED
STRATEGY_UPDATED
CONFIG_CHANGED
DEPLOYMENT_APPROVED
ORDER_CREATED
ORDER_CANCELLED
RISK_POLICY_CHANGED
USER_PERMISSION_CHANGED
```

Les événements d'audit doivent être conservés suffisamment longtemps pour permettre une investigation.

## 39. Observabilité

Le Storage Engine doit exposer des métriques :

```text
query_latency
write_latency
error_rate
connection_count
pool_usage
storage_size
cache_hit_rate
backup_status
```

Les anomalies doivent être détectées par le Monitoring Engine.

## 40. Connection Pooling

Les connexions PostgreSQL doivent être gérées par un pool.

Objectifs :

- limiter le nombre de connexions ;
- réduire le coût de connexion ;
- éviter l'épuisement des ressources ;
- améliorer la stabilité.

Les paramètres doivent être configurables par environnement.

## 41. Concurrence

Le système doit gérer correctement plusieurs workers écrivant simultanément.

Selon le cas :

- transactions ;
- locks ;
- unique constraints ;
- optimistic locking ;
- version numbers.

La stratégie doit être définie entité par entité.

## 42. Event Store

Les événements importants peuvent être conservés dans un event store logique.

```text
event_id
event_type
entity_type
entity_id
timestamp
payload
version
source
```

Cela permettra de reconstruire certains états historiques.

## 43. Trade Record

Un trade historique doit conserver suffisamment d'informations pour être analysé.

```text
trade_id
strategy_id
strategy_version
symbol
side
entry_time
entry_price
exit_time
exit_price
quantity
fees
slippage
PnL
risk_parameters
decision_id
```

## 44. Decision Record

Une décision doit pouvoir être reconstruite.

```text
decision_id
timestamp
symbol
timeframe
market_context
signals
score
decision
strategy_version
risk_assessment_id
```

## 45. Experiment Record

Une expérience doit conserver :

```text
experiment_id
hypothesis
dataset_version
strategy_version
configuration
code_version
parameters
start_time
end_time
metrics
result
status
```

Cela devient une brique fondamentale du Knowledge Engine.

## 46. Strategy Version

Chaque modification importante d'une stratégie doit produire une nouvelle version.

```text
Strategy: MomentumBreakout

v1.0
v1.1
v1.2
v2.0
```

Une expérience doit toujours référencer une version précise.

## 47. Configuration Version

Les paramètres doivent également être versionnés.

Une expérience doit éviter de dépendre d'un fichier de configuration mutable.

## 48. Code Version

La version Git du code doit être enregistrée lorsqu'une expérience est exécutée.

Exemple :

```text
git_commit:
a82f91c
```

Ainsi :

```text
Experiment
=
Dataset
+
Strategy
+
Config
+
Code
```

## 49. Reproductibilité complète

Une expérience doit idéalement être reproductible avec :

```text
Dataset ID
Dataset Version
Strategy Version
Configuration Version
Git Commit
Model Version
Environment
Random Seed
```

Si un résultat ne peut pas être reproduit, il doit être marqué comme non reproductible.

## 50. Migration Database

Toute modification du schéma doit utiliser des migrations versionnées.

```text
001_initial_schema
002_add_market_data
003_add_experiments
004_add_strategy_versions
```

Les migrations doivent être :

- ordonnées ;
- testées ;
- réversibles lorsque possible ;
- documentées.

## 51. Seed Data

Les environnements de développement et de test doivent pouvoir être initialisés avec des données contrôlées.

Les données de test ne doivent jamais être confondues avec des données réelles.

## 52. Testing

Le Storage Engine doit être testé à plusieurs niveaux.

### Unit Tests

- repositories ;
- validation ;
- mapping ;
- serialization.

### Integration Tests

- PostgreSQL ;
- Supabase ;
- Object Storage ;
- transactions.

### Performance Tests

- bulk insertion ;
- range queries ;
- concurrent writes ;
- large datasets.

### Recovery Tests

- backup ;
- restore ;
- corruption ;
- migration.

## 53. Failure Handling

Le Storage Engine doit gérer :

- database unavailable ;
- timeout ;
- connection failure ;
- transaction failure ;
- constraint violation ;
- storage unavailable ;
- corrupted file ;
- network failure.

Il ne doit jamais masquer silencieusement une erreur critique.

## 54. Atomicité des opérations critiques

Une opération comme :

```text
Order Created
+
Execution Event
+
Audit Event
```

doit être conçue de manière à éviter les incohérences.

Lorsque plusieurs systèmes sont concernés, un mécanisme transactionnel ou event-driven approprié devra être utilisé.

## 55. Performance

Les performances doivent être mesurées plutôt que supposées.

Métriques principales :

- read latency ;
- write latency ;
- throughput ;
- storage growth ;
- query cost ;
- cache efficiency.

Les optimisations doivent être basées sur des données réelles.

## 56. Scalabilité

La première version doit rester simple.

```text
Application
    ↓
PostgreSQL / Supabase
    ↓
Object Storage
```

À mesure que le volume augmente :

```text
Application
      ↓
Storage API
      ↓
PostgreSQL
      +
Object Storage
      +
Cache
      +
Analytical Storage
```

Puis éventuellement une architecture distribuée, uniquement si les volumes le justifient.

## 57. Séparation OLTP / Analytics

Les opérations transactionnelles et les analyses massives peuvent avoir des besoins différents.

### OLTP

- ordres ;
- positions ;
- utilisateurs ;
- décisions ;
- état courant.

### Analytics

- gros datasets ;
- backtests ;
- statistiques ;
- recherches historiques.

L'architecture doit permettre de les séparer progressivement si nécessaire.

## 58. Data Warehouse futur

Si QuantLab atteint un volume important, une couche analytique dédiée pourra être introduite.

```text
Operational DB
      ↓
Data Pipeline
      ↓
Analytical Storage
      ↓
Research / Analytics
```

Cette évolution ne doit pas être imposée dans la V1.

## 59. Objectifs de performance initiaux

Les objectifs exacts seront établis par benchmark.

QuantLab doit viser :

- lecture rapide des séries récentes ;
- insertion batch efficace ;
- récupération fiable des historiques ;
- faible latence pour les données nécessaires à la décision ;
- absence de blocage de l'exécution par des opérations analytiques lourdes.

## 60. Principes de conception

Le Storage Engine doit respecter :

1. **Database as infrastructure, not business logic.**
2. **Source of truth explicite.**
3. **Immutabilité des données historiques.**
4. **Versioning systématique des expériences.**
5. **Traçabilité des transformations.**
6. **Transactions pour les opérations critiques.**
7. **Idempotence lorsque nécessaire.**
8. **Moindre privilège.**
9. **Backups testés.**
10. **Évolution progressive.**

## 61. Flux principal

```text
Data Provider
      ↓
Data Engine
      ↓
Storage Engine
      ↓
PostgreSQL / Object Storage
      ↓
Analysis Engines
      ↓
Research / Decision / Trading
```

## 62. Flux expérimental

```text
Historical Data
      ↓
Storage Engine
      ↓
Experiment
      ↓
Backtest
      ↓
Results
      ↓
Storage Engine
      ↓
Knowledge Engine
```

## 63. Flux trading

```text
Market Data
      ↓
Data Engine
      ↓
Storage / Cache
      ↓
Analysis
      ↓
Decision
      ↓
Risk
      ↓
Execution
      ↓
Trading Events
      ↓
Storage Engine
```

## 64. Critères d'acceptation

Le Storage Engine est considéré comme valide lorsque :

- les données peuvent être stockées et récupérées de manière fiable ;
- les données historiques sont versionnées ;
- les datasets volumineux peuvent être externalisés vers Object Storage ;
- les transactions critiques sont protégées ;
- les doublons sont contrôlés ;
- les relations sont cohérentes ;
- les accès sont sécurisés ;
- les backups sont automatisés ;
- les restaurations sont testées ;
- les expériences sont reproductibles ;
- les migrations sont versionnées ;
- les métriques de stockage sont monitorées ;
- les environnements sont séparés.

## 65. Priorités d'implémentation

### V1

- PostgreSQL ;
- Supabase ;
- migrations ;
- repositories ;
- instruments ;
- candles ;
- datasets ;
- stratégies ;
- expériences ;
- logs ;
- audit minimal ;
- backups.

### V2

- Object Storage ;
- Parquet ;
- versioning avancé ;
- data lineage ;
- cache ;
- partitionnement.

### V3

- event store ;
- analytical storage ;
- data warehouse ;
- réplication avancée.

### V4

- architecture distribuée si les volumes le justifient.

## 66. Relation avec Supabase

Supabase est explicitement prévu dans l'architecture de QuantLab comme une infrastructure potentielle de stockage et de services.

Cependant :

```text
QuantLab
   ↓
Storage Interface
   ↓
PostgreSQL abstraction
   ↓
Supabase
```

et non :

```text
QuantLab
   ↓
Supabase-specific logic everywhere
```

Cette distinction permet de bénéficier de Supabase maintenant tout en conservant la possibilité de migrer ultérieurement vers une infrastructure PostgreSQL ou cloud différente.

## 67. Résultat attendu

Le Storage Engine doit fournir une fondation durable permettant à QuantLab de conserver l'ensemble de son historique :

```text
Market Data
     +
Signals
     +
Decisions
     +
Risk
     +
Orders
     +
Trades
     +
Experiments
     +
Strategies
     +
Models
     +
Knowledge
     +
Governance
```

L'objectif final est que QuantLab puisse répondre à une question fondamentale :

> **Qu'avons-nous utilisé, qu'avons-nous décidé, pourquoi l'avons-nous décidé, et quel résultat cela a-t-il produit ?**

La réponse doit être reconstruisible à partir des données persistées.

## 68. Statut

**Version : 1.0**

Documents directement liés :

- `02-Architecture-Generale.md`
- `03-Data-Engine.md`
- `09-Scoring-Engine.md`
- `10-Decision-Engine.md`
- `12-Execution-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `16-Governance-Engine.md`
- `18-Testing-Strategy.md`
- `19-Deployment-Guide.md`
- `23-Database-Schema.md`
- `24-Security.md`
