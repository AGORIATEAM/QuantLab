# 02 — Architecture générale

**Projet : QuantLab**  
**Document : Architecture générale**  
**Version : 1.0**  
**Statut : Spécification fondatrice**

---

# 1. Objectif du document

Ce document définit l'architecture technique et fonctionnelle globale de QuantLab.

L'objectif est de fournir une structure suffisamment précise pour permettre à plusieurs développeurs ou agents IA de travailler sur le projet sans créer d'incohérences entre les composants.

L'architecture doit permettre :

- l'analyse multi-actifs ;
- l'intégration de plusieurs fournisseurs de données ;
- l'analyse multi-timeframe ;
- le backtesting ;
- la recherche quantitative ;
- l'expérimentation de stratégies ;
- l'utilisation progressive de modèles IA ;
- l'exécution simulée ;
- l'exécution réelle ;
- le monitoring ;
- la traçabilité complète ;
- l'évolution progressive de l'infrastructure.

Le principe architectural central est la **séparation des responsabilités**.

Aucun composant ne doit cumuler inutilement plusieurs responsabilités critiques.

---

# 2. Principes architecturaux

## 2.1 Modularité

Chaque moteur doit être indépendant autant que possible.

Un changement dans le Volume Profile Engine ne doit pas nécessiter une réécriture du Risk Engine.

---

## 2.2 Faible couplage

Les modules communiquent par des interfaces et des structures de données clairement définies.

Exemple :

```text
Market Structure Engine
        ↓
MarketStructureSignal
        ↓
Scoring Engine
```

Le Scoring Engine ne doit pas connaître les détails internes de calcul de la structure.

---

## 2.3 Forte cohésion

Chaque module doit avoir une responsabilité clairement définie.

Exemple :

Le Risk Engine ne doit pas déterminer si un Fair Value Gap est valide.

Il reçoit une opportunité et détermine si cette opportunité peut être tradée compte tenu du risque.

---

## 2.4 Immutabilité des données historiques

Les données historiques utilisées pour les recherches doivent être conservées de manière reproductible.

Une expérience passée ne doit pas changer simplement parce que les données ont été retraitées ultérieurement.

Les versions des datasets doivent être identifiables.

---

## 2.5 Séparation Research / Paper / Production

Architecture logique :

```text
RESEARCH
    ↓
VALIDATION
    ↓
PAPER
    ↓
PRODUCTION
```

Les environnements doivent être isolés.

Une stratégie expérimentale ne doit jamais pouvoir envoyer accidentellement un ordre réel.

---

# 3. Architecture globale

Architecture logique :

```text
                         DATA SOURCES
                              │
             ┌────────────────┼────────────────┐
             │                │                │
          CEX/API           Broker            DEX
             │                │                │
             └────────────────┼────────────────┘
                              ↓
                       ┌─────────────┐
                       │ DATA ENGINE │
                       └──────┬──────┘
                              ↓
                     ┌─────────────────┐
                     │ STORAGE ENGINE  │
                     └────────┬────────┘
                              ↓
                 ┌─────────────────────────┐
                 │   MARKET ANALYSIS       │
                 │        ENGINE           │
                 └────────────┬────────────┘
                              │
             ┌────────────────┼─────────────────┐
             ↓                ↓                 ↓
       MARKET STRUCTURE   VOLUME PROFILE   SMC ENGINE
             │                │                 │
             └────────────────┼─────────────────┘
                              ↓
                      ┌───────────────┐
                      │ SCORING ENGINE│
                      └───────┬───────┘
                              ↓
                     ┌────────────────┐
                     │ DECISION ENGINE│
                     └───────┬────────┘
                             ↓
                       ┌────────────┐
                       │ RISK ENGINE│
                       └──────┬─────┘
                              ↓
                    ┌──────────────────┐
                    │ EXECUTION ENGINE │
                    └────────┬─────────┘
                             ↓
                     EXCHANGES / BROKERS
                             │
                             ↓
                    ┌──────────────────┐
                    │ MONITORING ENGINE│
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ KNOWLEDGE ENGINE │
                    └────────┬─────────┘
                             ↓
                   ┌─────────────────────┐
                   │ AI & LEARNING ENGINE│
                   └─────────────────────┘
```

---

# 4. Les principaux moteurs

QuantLab doit comporter les composants suivants :

1. Data Engine
2. Storage Engine
3. Market Analysis Engine
4. Market Structure Engine
5. Volume Profile Engine
6. Smart Money Concepts Engine
7. Scoring Engine
8. Decision Engine
9. Risk Engine
10. Execution Engine
11. Monitoring Engine
12. Knowledge Engine
13. AI & Learning Engine
14. Governance Engine

À cela s'ajoutent des couches transversales :

- configuration ;
- logging ;
- sécurité ;
- observabilité ;
- API ;
- tests ;
- versioning ;
- gestion des expérimentations.

---

# 5. Data Engine

## Responsabilité

Le Data Engine est responsable de l'acquisition et de la normalisation des données.

Il ne doit pas prendre de décision de trading.

Il doit gérer :

- données OHLCV ;
- trades ;
- order books lorsque disponibles ;
- funding rates ;
- open interest ;
- données de marché ;
- données on-chain ;
- données macroéconomiques ;
- calendrier économique ;
- données provenant de brokers ;
- données provenant d'exchanges ;
- données provenant de DEX.

Flux :

```text
Provider
   ↓
Connector
   ↓
Validation
   ↓
Normalization
   ↓
Data Event
   ↓
Storage
```

---

# 6. Storage Engine

Le Storage Engine fournit une abstraction entre les moteurs applicatifs et les systèmes de stockage.

Infrastructure initiale envisagée :

- PostgreSQL ;
- Supabase ;
- stockage objet pour les datasets volumineux.

Le moteur doit permettre ultérieurement l'utilisation de :

- data lake ;
- Parquet ;
- object storage ;
- bases spécialisées ;
- systèmes distribués.

Les moteurs métier ne doivent jamais dépendre directement des détails internes de Supabase.

---

# 7. Market Analysis Engine

Ce moteur fournit une analyse générale du marché.

Il peut produire :

- tendance ;
- volatilité ;
- momentum ;
- régime ;
- liquidité ;
- volume ;
- contexte multi-timeframe.

Il sert de couche d'information commune aux moteurs spécialisés.

---

# 8. Market Structure Engine

Ce moteur transforme les mouvements de prix en structure algorithmique.

Il doit notamment pouvoir détecter :

- swing highs ;
- swing lows ;
- BOS ;
- CHOCH ;
- structure haussière ;
- structure baissière ;
- range ;
- expansion ;
- compression.

Une définition précise doit être utilisée pour chaque concept.

Aucun terme subjectif ne doit être utilisé directement par le code.

---

# 9. Volume Profile Engine

Ce moteur calcule les distributions de volume.

Concepts principaux :

- POC ;
- VAH ;
- VAL ;
- Value Area ;
- HVN ;
- LVN ;
- volume nodes ;
- Initial Balance ;
- profils par session ;
- profils par période.

Le moteur doit permettre plusieurs méthodes de calcul.

Les résultats doivent être reproductibles.

---

# 10. Smart Money Concepts Engine

Ce moteur implémente des définitions algorithmiques de concepts issus des Smart Money Concepts.

Concepts potentiels :

- liquidity pool ;
- liquidity sweep ;
- stop run ;
- Fair Value Gap ;
- Order Block ;
- Breaker Block ;
- mitigation ;
- displacement ;
- imbalance ;
- premium/discount zones.

Chaque concept doit posséder :

1. une définition ;
2. des données nécessaires ;
3. des paramètres ;
4. un algorithme ;
5. des tests ;
6. une métrique de performance ;
7. une définition de son niveau de confiance.

---

# 11. Scoring Engine

Le Scoring Engine combine les informations provenant des moteurs d'analyse.

Exemple conceptuel :

```text
Market Structure       +25
Volume Profile         +20
Liquidity Sweep        +15
Fair Value Gap         +10
Volume Confirmation    +10
Volatility Regime      +10
Session Context        +10
--------------------------------
Total                  100
```

Cette formule est uniquement illustrative.

Les pondérations doivent être testées statistiquement.

Le Scoring Engine ne doit pas exécuter d'ordres.

---

# 12. Decision Engine

Le Decision Engine transforme le contexte et le score en décision.

Décisions possibles :

```text
NO_ACTION
WATCH
LONG_CANDIDATE
SHORT_CANDIDATE
ENTER_LONG
ENTER_SHORT
REDUCE
EXIT
PAUSE
HALT
```

Le Decision Engine doit prendre en compte :

- score ;
- régime ;
- risque ;
- exposition existante ;
- contraintes de stratégie ;
- événements ;
- conditions de marché ;
- disponibilité de l'exécution.

Il doit toujours pouvoir retourner :

```text
NO TRADE
```

---

# 13. Risk Engine

Le Risk Engine est prioritaire sur la décision de trading.

Il doit contrôler :

- risque par trade ;
- exposition totale ;
- exposition par actif ;
- exposition par stratégie ;
- drawdown ;
- perte quotidienne ;
- perte hebdomadaire ;
- corrélation ;
- nombre de positions ;
- taille maximale ;
- levier ;
- stop loss ;
- distance du stop ;
- liquidité disponible.

Architecture :

```text
Decision
   ↓
Risk Validation
   ↓
Approved / Rejected
```

Une décision valide peut donc être refusée par le Risk Engine.

---

# 14. Execution Engine

Le moteur d'exécution transforme une décision approuvée en ordre.

Il doit gérer :

- market orders ;
- limit orders ;
- stop orders ;
- stop loss ;
- take profit ;
- position sizing ;
- annulation ;
- modification ;
- partial fills ;
- slippage ;
- erreurs API ;
- reconnexion ;
- idempotence.

Il doit garantir qu'une même instruction ne provoque pas plusieurs ordres accidentels.

---

# 15. Monitoring Engine

Le Monitoring Engine surveille :

### Infrastructure

- CPU ;
- mémoire ;
- réseau ;
- latence ;
- disponibilité.

### Données

- fraîcheur ;
- trous ;
- duplications ;
- incohérences.

### Trading

- positions ;
- ordres ;
- erreurs ;
- PnL ;
- drawdown.

### Stratégies

- performance ;
- dérive ;
- changement de régime ;
- anomalies.

---

# 16. Knowledge Engine

Le Knowledge Engine constitue la mémoire de QuantLab.

Il conserve :

- stratégies ;
- versions ;
- expériences ;
- datasets ;
- résultats ;
- paramètres ;
- signaux ;
- décisions ;
- trades ;
- performances ;
- anomalies ;
- observations ;
- hypothèses ;
- conclusions.

Il doit être possible de répondre à :

> Pourquoi cette stratégie a-t-elle été activée ?

ou :

> Quelle expérimentation a conduit à cette configuration ?

---

# 17. AI & Learning Engine

Ce moteur permet l'utilisation progressive de l'intelligence artificielle.

Fonctions possibles :

- classification ;
- génération d'hypothèses ;
- recherche de paramètres ;
- détection de régimes ;
- détection d'anomalies ;
- analyse de performance ;
- génération de rapports ;
- recherche automatisée.

Architecture :

```text
Knowledge
    ↓
AI Analysis
    ↓
Hypothesis
    ↓
Experiment
    ↓
Validation
    ↓
Candidate Strategy
```

Le moteur ne doit pas pouvoir modifier directement la production.

---

# 18. Governance Engine

Le Governance Engine contrôle le passage entre les environnements.

Il doit notamment vérifier :

- tests ;
- validation ;
- version ;
- performance ;
- risques ;
- approbations ;
- changements.

Exemple :

```text
Research
   ↓
Test
   ↓
Backtest
   ↓
OOS
   ↓
Walk Forward
   ↓
Paper
   ↓
Governance Approval
   ↓
Production
```

---

# 19. Communication entre modules

Les modules doivent communiquer via des objets structurés.

Exemple :

```python
MarketContext
MarketStructureSignal
VolumeProfileContext
SMCSignal
TradeCandidate
RiskAssessment
ExecutionInstruction
ExecutionResult
```

Chaque objet doit être :

- typé ;
- versionné ;
- documenté ;
- testable.

---

# 20. Event-driven architecture

QuantLab doit être capable d'utiliser une architecture événementielle.

Exemples :

```text
MARKET_DATA_RECEIVED
CANDLE_CLOSED
STRUCTURE_CHANGED
SIGNAL_GENERATED
DECISION_CREATED
RISK_APPROVED
ORDER_SUBMITTED
ORDER_FILLED
POSITION_UPDATED
TRADE_CLOSED
STRATEGY_UPDATED
BACKTEST_COMPLETED
```

Cela permettra d'évoluer vers une architecture distribuée.

---

# 21. Configuration

Les paramètres ne doivent pas être codés en dur.

Ils doivent pouvoir être définis dans des configurations versionnées.

Exemple :

```yaml
strategy:
  timeframe: 5m
  minimum_score: 75

risk:
  max_risk_per_trade: 0.005
  max_daily_loss: 0.02

execution:
  max_slippage: 0.001
```

Les valeurs exactes seront définies dans les documents spécifiques.

---

# 22. Logging

Chaque module doit produire des logs structurés.

Un log doit pouvoir contenir :

- timestamp ;
- module ;
- event ;
- strategy_id ;
- asset ;
- timeframe ;
- correlation_id ;
- parameters ;
- result ;
- error ;
- execution context.

Les logs critiques doivent être conservés.

---

# 23. Gestion des erreurs

Chaque module doit définir :

- erreurs récupérables ;
- erreurs non récupérables ;
- retry policy ;
- timeout ;
- fallback ;
- circuit breaker ;
- comportement de sécurité.

Principe :

> En cas d'incertitude critique, le système doit préférer l'absence de trading.

---

# 24. Idempotence

Les opérations critiques doivent être idempotentes.

Exemple :

Si le système reçoit deux fois :

```text
EXECUTE_ORDER_123
```

il ne doit pas envoyer deux ordres.

Chaque opération critique doit posséder un identifiant unique.

---

# 25. Sécurité architecturale

Les clés API doivent être séparées des données applicatives.

Le code ne doit jamais contenir :

```text
API_KEY
SECRET
PRIVATE_KEY
PASSWORD
```

en clair.

Les environnements Research, Paper et Production doivent utiliser des credentials distincts.

---

# 26. Environnements

## Development

Développement local.

## Testing

Tests automatisés.

## Research

Backtests et expérimentations.

## Paper

Exécution simulée en temps réel.

## Production

Trading réel.

Les accès doivent être strictement séparés.

---

# 27. Infrastructure initiale

Stack de référence :

### Backend

Python.

### Conteneurisation

Docker.

### Base de données

PostgreSQL / Supabase.

### Versioning

Git.

### CI/CD

GitHub Actions ou équivalent.

### Analyse

Python scientific stack.

### API

FastAPI ou architecture équivalente.

### Monitoring

Solution compatible avec métriques et logs structurés.

Les choix définitifs doivent être confirmés dans les documents d'architecture correspondants.

---

# 28. Architecture de déploiement initiale

```text
                 INTERNET
                    │
                    ▼
              DATA PROVIDERS
                    │
                    ▼
             DATA CONNECTORS
                    │
                    ▼
              DATA ENGINE
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
     PostgreSQL            Object Storage
      /Supabase              /Parquet
          │
          ▼
       QUANTLAB
          │
    ┌─────┴─────┐
    ▼           ▼
Research      Trading
    │           │
    │           ▼
    │       Risk Engine
    │           │
    │           ▼
    │      Execution Engine
    │           │
    │           ▼
    │      Broker / Exchange
    │
    ▼
Knowledge Engine
    │
    ▼
AI & Learning
```

---

# 29. Scalabilité future

L'architecture doit permettre ultérieurement :

- workers distribués ;
- queues ;
- calcul parallèle ;
- cloud computing ;
- data lake ;
- GPU ;
- modèles ML ;
- plusieurs exchanges ;
- plusieurs brokers ;
- plusieurs stratégies simultanées ;
- plusieurs utilisateurs.

Mais aucune complexité ne doit être ajoutée avant qu'elle soit nécessaire.

---

# 30. Règle d'architecture fondamentale

Chaque composant doit répondre à une question simple :

> Quelle est exactement sa responsabilité ?

Si la réponse est ambiguë, le composant doit être redéfini.

Une architecture saine doit permettre de supprimer ou remplacer un module sans détruire l'ensemble du système.

---

# 31. Dépendances

Le système doit respecter globalement :

```text
Data
 ↓
Analysis
 ↓
Scoring
 ↓
Decision
 ↓
Risk
 ↓
Execution
```

Le Knowledge Engine et le Monitoring Engine sont transversaux.

Le AI & Learning Engine doit principalement consommer les données et résultats issus des autres moteurs et produire des hypothèses ou recommandations.

Il ne doit pas contourner :

- Decision Engine ;
- Risk Engine ;
- Governance Engine.

---

# 32. Architecture de sécurité décisionnelle

La chaîne critique doit être :

```text
SIGNAL
   ↓
SCORING
   ↓
DECISION
   ↓
RISK
   ↓
GOVERNANCE / POLICY
   ↓
EXECUTION
```

Aucun module IA ne doit pouvoir contourner cette chaîne.

---

# 33. Architecture de recherche

La recherche doit être séparée du trading live.

```text
Historical Data
      ↓
Research Engine
      ↓
Experiment
      ↓
Backtest
      ↓
Validation
      ↓
Knowledge Engine
```

Une stratégie validée peut ensuite devenir un candidat au paper trading.

---

# 34. Architecture de décision finale

La décision finale doit être le résultat de plusieurs couches indépendantes :

```text
Market Context
      +
Market Structure
      +
Volume Profile
      +
SMC
      +
Volatility
      +
Session
      +
External Events
      ↓
Scoring
      ↓
Decision
      ↓
Risk
      ↓
Execution
```

Cette architecture permet de réduire la dépendance à un seul signal.

---

# 35. Règle "No Single Point of Truth"

Aucun indicateur individuel ne doit pouvoir imposer une décision de trading.

Par exemple :

```text
FVG détecté
≠
Trade automatique
```

De même :

```text
BOS détecté
≠
Trade automatique
```

Chaque signal doit être contextualisé.

---

# 36. Règle "No Magic AI"

Une décision ne doit jamais être justifiée uniquement par :

```text
"Le modèle IA pense que le marché va monter."
```

Une décision doit être traçable vers :

- données ;
- features ;
- signaux ;
- modèle ;
- version ;
- paramètres ;
- score ;
- contraintes de risque.

---

# 37. Critères d'acceptation architecturaux

L'architecture est considérée comme acceptable si :

- chaque moteur possède une responsabilité claire ;
- les dépendances sont documentées ;
- les interfaces sont définies ;
- les environnements sont séparés ;
- les données sont traçables ;
- les stratégies sont versionnées ;
- les décisions sont journalisées ;
- le Risk Engine peut bloquer une décision ;
- l'IA ne peut pas contourner les contrôles ;
- l'exécution est isolée ;
- les expériences sont reproductibles ;
- les composants critiques sont testables ;
- les secrets sont isolés ;
- les erreurs critiques déclenchent un comportement fail-safe.

---

# 38. Résultat attendu

L'architecture de QuantLab doit permettre de passer progressivement de :

```text
Research Platform
```

à :

```text
Multi-Asset Quantitative Trading Platform
```

puis éventuellement à :

```text
Adaptive Quantitative Research System
```

sans devoir réécrire complètement le projet.

La priorité absolue reste toutefois la robustesse de la fondation.

Une architecture trop complexe dès le départ est aussi une forme de dette technique. Le système doit donc commencer suffisamment simple pour être maîtrisable, tout en conservant des interfaces permettant son évolution.

---

# 39. Statut

**Version : 1.0**

Ce document constitue la spécification architecturale de haut niveau.

Les documents suivants doivent détailler chaque composant :

- `03-Data-Engine.md`
- `04-Storage-Engine.md`
- `05-Market-Analysis-Engine.md`
- `06-Market-Structure-Engine.md`
- `07-Volume-Profile-Engine.md`
- `08-Smart-Money-Concepts-Engine.md`
- `09-Scoring-Engine.md`
- `10-Decision-Engine.md`
- `11-Risk-Engine.md`
- `12-Execution-Engine.md`
- `13-Monitoring-Engine.md`
- `14-Knowledge-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `16-Governance-Engine.md`

Toute modification majeure de cette architecture doit être documentée dans un ADR.