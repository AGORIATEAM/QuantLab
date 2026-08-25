# Annexes --- QuantLab

**Projet : QuantLab**\
**Document : Annexes techniques et opérationnelles**\
**Version : 1.0**\
**Statut : Référence transversale**

------------------------------------------------------------------------

# 1. Objectif

Ces annexes complètent les documents `01` à `25` de QuantLab.

Elles regroupent les conventions et références qui doivent rester
communes à l'ensemble du projet :

``` text
A — Glossaire
B — Architecture Decision Records (ADR)
C — Conventions Git
D — Standards Markdown
E — Diagrammes d’architecture
F — Checklists opérationnelles
```

L'objectif est d'éviter que chaque moteur invente ses propres
définitions, conventions ou procédures. C'est une activité étonnamment
populaire dans les projets logiciels, et rarement une bonne idée.

------------------------------------------------------------------------

# ANNEXE A --- GLOSSAIRE

## A.1 Analysis Run

Exécution versionnée d'un moteur analytique sur un ensemble déterminé de
données.

## A.2 Artifact

Objet produit par un processus QuantLab :

``` text
dataset
rapport
modèle
configuration
build
backtest
graphique
```

Un artefact critique doit être identifiable et, lorsque pertinent,
associé à un hash.

## A.3 Backtest

Simulation historique d'une stratégie sur des données antérieures.

Un backtest n'est pas une preuve de performance future.

## A.4 Baseline

Référence simple utilisée pour déterminer si une nouvelle stratégie,
règle ou méthode apporte réellement une amélioration.

## A.5 BOS

**Break of Structure.**

Rupture algorithmique d'un niveau structurel défini par le Market
Structure Engine.

## A.6 CHoCH

**Change of Character.**

Événement indiquant un changement potentiel de structure ou de régime
selon les règles formelles de QuantLab.

## A.7 Decision

Sortie explicite du Decision Engine.

Exemples :

``` text
ENTER_LONG
ENTER_SHORT
EXIT
REDUCE
HOLD
NO_TRADE
```

## A.8 Drawdown

Baisse d'un capital ou d'une equity depuis un précédent sommet.

## A.9 Experiment

Test formalisé possédant :

``` text
hypothesis
dataset
configuration
code version
metrics
acceptance criteria
result
```

## A.10 Fill

Exécution réelle ou simulée de tout ou partie d'un ordre.

## A.11 FVG

**Fair Value Gap.**

Zone d'inefficience définie selon les règles du Smart Money Concepts
Engine.

## A.12 Governance Proposal

Objet formel demandant l'autorisation d'un changement contrôlé.

## A.13 HVN

**High Volume Node.**

Zone de forte concentration de volume dans un Volume Profile.

## A.14 Idempotency

Propriété garantissant que la répétition d'une même opération ne produit
pas plusieurs effets métier non désirés.

## A.15 Kill Switch

Mécanisme permettant de bloquer rapidement tout ou partie de l'activité
de trading.

## A.16 Limited Live

Phase de trading réel utilisant une exposition volontairement réduite.

## A.17 LVN

**Low Volume Node.**

Zone de faible concentration de volume.

## A.18 Market Context

Objet normalisé regroupant l'état analytique nécessaire aux stratégies
et moteurs de décision.

## A.19 Market Structure

Représentation algorithmique des swings, tendances et ruptures de
structure.

## A.20 Order Block

Zone identifiée par le SMC Engine selon une définition algorithmique
versionnée.

## A.21 Out-of-Sample

Période ou dataset non utilisé pour concevoir ou optimiser la stratégie
testée.

## A.22 Paper Trading

Simulation en temps réel sans capital réel.

## A.23 POC

**Point of Control.**

Niveau de prix ayant concentré le volume maximal dans le profil
considéré.

## A.24 Position

Exposition nette détenue sur un instrument et un compte.

## A.25 Reconciliation

Comparaison entre l'état interne QuantLab et une source externe
d'autorité, notamment une venue.

## A.26 Replay

Relecture déterministe d'événements historiques.

## A.27 Risk Evaluation

Décision du Risk Engine appliquée à une décision stratégique.

Résultat :

``` text
APPROVED
MODIFIED
REJECTED
```

## A.28 Shadow Trading

Mode dans lequel QuantLab produit les décisions et ordres théoriques
sans les envoyer réellement à la venue.

## A.29 Slippage

Différence entre le prix théorique ou attendu et le prix effectivement
obtenu.

## A.30 Strategy Version

Version immuable ou précisément identifiable d'une stratégie et de sa
configuration.

## A.31 VAH

**Value Area High.**

Borne supérieure de la Value Area.

## A.32 VAL

**Value Area Low.**

Borne inférieure de la Value Area.

## A.33 Value Area

Zone contenant une proportion déterminée du volume total du profil.

## A.34 Venue

Exchange, broker ou infrastructure externe sur laquelle les instruments
sont observés ou négociés.

## A.35 Walk-Forward

Méthode d'évaluation répétant entraînement/optimisation et validation
sur plusieurs fenêtres temporelles successives.

------------------------------------------------------------------------

# ANNEXE B --- ARCHITECTURE DECISION RECORDS

## B.1 Objectif

Les ADR conservent la raison des décisions structurantes.

Ils empêchent le projet de savoir *ce qu'il fait* tout en oubliant
*pourquoi il le fait*.

------------------------------------------------------------------------

## B.2 Emplacement

``` text
docs/adr/
```

------------------------------------------------------------------------

## B.3 Convention de nommage

``` text
ADR-0001-postgresql-primary-database.md
ADR-0002-event-driven-boundaries.md
ADR-0003-risk-engine-mandatory.md
```

------------------------------------------------------------------------

## B.4 Structure ADR

``` markdown
# ADR-XXXX — Titre

## Statut
Proposed / Accepted / Superseded / Rejected

## Date

## Contexte

## Décision

## Alternatives considérées

## Conséquences positives

## Conséquences négatives

## Risques

## Références
```

------------------------------------------------------------------------

## B.5 ADR initiaux recommandés

``` text
ADR-0001 PostgreSQL comme stockage transactionnel principal
ADR-0002 UTC comme standard temporel interne
ADR-0003 Risk Engine obligatoire avant Execution Engine
ADR-0004 Séparation Research / Production
ADR-0005 Architecture événementielle pour les événements métier
ADR-0006 Transactional Outbox
ADR-0007 UUID comme identifiant principal
ADR-0008 Parquet/Object Storage pour les datasets volumineux
ADR-0009 Expériences reproductibles et versionnées
ADR-0010 IA sans autorité directe de trading live
ADR-0011 Fail-closed sur les contrôles de risque
ADR-0012 Immutabilité des décisions et fills historiques
```

------------------------------------------------------------------------

## B.6 Règle ADR

Une décision importante ne doit pas être changée silencieusement.

Créer un nouvel ADR qui :

``` text
supersedes
```

l'ancien.

------------------------------------------------------------------------

# ANNEXE C --- CONVENTIONS GIT

## C.1 Branches principales

``` text
main
```

doit toujours représenter une version intégrable.

Branches temporaires :

``` text
feature/*
fix/*
refactor/*
docs/*
test/*
experiment/*
security/*
```

------------------------------------------------------------------------

## C.2 Exemples

``` text
feature/risk-daily-loss-limit
fix/order-reconciliation-timeout
docs/execution-engine
experiment/volume-profile-v2
```

------------------------------------------------------------------------

## C.3 Commits

Format recommandé :

``` text
type(scope): description
```

Types :

``` text
feat
fix
refactor
test
docs
perf
build
ci
security
chore
```

Exemples :

``` text
feat(risk): add daily loss limit
fix(execution): prevent duplicate order submission
test(data): add candle gap regression case
docs(api): document order idempotency
```

------------------------------------------------------------------------

## C.4 Commits atomiques

Un commit doit représenter une modification cohérente.

Éviter :

``` text
misc fixes
stuff
update
final-final-v2
```

L'archéologie Git est déjà assez pénible sans laisser des hiéroglyphes
volontaires.

------------------------------------------------------------------------

## C.5 Pull Requests

Toute PR doit indiquer :

``` text
objective
changes
tests
risks
migration impact
rollback impact
```

------------------------------------------------------------------------

## C.6 Review obligatoire

Review renforcée pour :

``` text
risk
execution
security
governance
database migrations
production deployment
```

------------------------------------------------------------------------

## C.7 Main Protection

``` text
no direct push
required CI
required review
```

------------------------------------------------------------------------

## C.8 Tags

Releases :

``` text
v1.0.0
v1.1.0
v1.1.1
```

------------------------------------------------------------------------

## C.9 Experiments

Les expériences doivent enregistrer le commit exact :

``` text
git SHA
```

------------------------------------------------------------------------

## C.10 Secrets

Aucun secret dans Git.

Un secret commité doit être considéré compromis même s'il est ensuite
supprimé.

------------------------------------------------------------------------

# ANNEXE D --- STANDARDS MARKDOWN

## D.1 Objectif

Tous les documents QuantLab doivent être lisibles :

``` text
GitHub
IDE
Claude Code
ChatGPT
documentation generators
```

------------------------------------------------------------------------

## D.2 Nom des fichiers

Format :

``` text
NN-Nom-Du-Document.md
```

Exemple :

``` text
11-Risk-Engine.md
```

Annexes :

``` text
ANNEX-A-Glossaire.md
ANNEX-B-ADR.md
```

------------------------------------------------------------------------

## D.3 Titres

Un seul H1 :

``` markdown
# Titre
```

Sections :

``` markdown
## Section
### Sous-section
```

------------------------------------------------------------------------

## D.4 Code

Utiliser des blocs typés :

``` text
```python
```

``` sql
```

``` yaml
```


    ---

    ## D.5 Diagrammes

    Préférer Mermaid lorsque le rendu cible le supporte.

    Sinon conserver un diagramme ASCII lisible.

    ---

    ## D.6 Listes

    Utiliser :

    ```text
    -

pour les listes non ordonnées.

------------------------------------------------------------------------

## D.7 Checklists

``` markdown
- [ ] À faire
- [x] Terminé
```

------------------------------------------------------------------------

## D.8 Liens internes

Utiliser des chemins relatifs.

------------------------------------------------------------------------

## D.9 Références croisées

Nommer explicitement le document :

``` text
Voir `11-Risk-Engine.md`.
```

------------------------------------------------------------------------

## D.10 Langue

La documentation projet peut être en français, tandis que :

``` text
code
identifiers
API fields
database fields
```

restent en anglais.

------------------------------------------------------------------------

## D.11 Normativité

Utiliser clairement :

``` text
DOIT
NE DOIT PAS
DEVRAIT
PEUT
```

lorsqu'une règle est normative.

------------------------------------------------------------------------

## D.12 Versions

Les documents structurants doivent indiquer :

``` text
Version
Statut
```

------------------------------------------------------------------------

# ANNEXE E --- DIAGRAMMES D'ARCHITECTURE

## E.1 Architecture générale

``` text
External Market Sources
        ↓
    Data Engine
        ↓
   Storage Engine
        ↓
Market Analysis Engine
        ↓
Market Structure Engine
        ↓
Volume Profile Engine
        ↓
SMC Engine
        ↓
   MarketContext
        ↓
   Scoring Engine
        ↓
  Decision Engine
        ↓
    Risk Engine
        ↓
 Execution Engine
        ↓
 Exchange / Broker
```

------------------------------------------------------------------------

## E.2 Boucle de contrôle

``` text
Execution
   ↓
Monitoring
   ↓
Knowledge
   ↓
Experiments
   ↓
Governance
   ↓
Deployment
   ↓
Execution
```

------------------------------------------------------------------------

## E.3 Pipeline de recherche

``` text
Dataset
   ↓
Replay
   ↓
Analysis
   ↓
Strategy
   ↓
Decision
   ↓
Risk Simulation
   ↓
Execution Simulation
   ↓
Metrics
   ↓
Experiment Registry
```

------------------------------------------------------------------------

## E.4 Pipeline live

``` text
Live Market Data
       ↓
MarketContext
       ↓
Strategy
       ↓
Score
       ↓
Decision
       ↓
Risk Evaluation
       ↓
Approved Order Intent
       ↓
Execution Engine
       ↓
Venue
       ↓
Order Events / Fills
       ↓
Positions
       ↓
Reconciliation
```

------------------------------------------------------------------------

## E.5 Gouvernance

``` text
Evidence
   ↓
Proposal
   ↓
Review
   ↓
Approval
   ↓
Deployment / Configuration Change
   ↓
Audit
```

------------------------------------------------------------------------

## E.6 IA

``` text
Knowledge Engine
      ↓
   AI Agent
      ↓
Proposal / Analysis / Code
      ↓
Validation
      ↓
Human + Governance
      ↓
Controlled Action
```

L'IA n'obtient pas un raccourci vers l'Execution Engine.

------------------------------------------------------------------------

## E.7 Données

``` text
External Source
      ↓
Raw Data
      ↓
Normalized Data
      ↓
Versioned Dataset
      ↓
Analysis Run
      ↓
Market Context
      ↓
Decision
```

------------------------------------------------------------------------

## E.8 Traçabilité ordre

``` text
Dataset / Live Data
        ↓
Analysis Run
        ↓
Market Context
        ↓
Score
        ↓
Decision
        ↓
Risk Evaluation
        ↓
Order
        ↓
Fill
        ↓
Position
```

------------------------------------------------------------------------

# ANNEXE F --- CHECKLISTS

## F.1 Nouvelle fonctionnalité

``` text
[ ] objectif défini
[ ] architecture cohérente
[ ] tests unitaires
[ ] tests d’intégration si nécessaire
[ ] logs
[ ] métriques
[ ] erreurs gérées
[ ] documentation mise à jour
[ ] sécurité évaluée
[ ] CI verte
```

------------------------------------------------------------------------

## F.2 Nouveau moteur

``` text
[ ] interface définie
[ ] inputs définis
[ ] outputs définis
[ ] versioning
[ ] configuration
[ ] déterminisme évalué
[ ] tests golden
[ ] edge cases
[ ] monitoring
[ ] documentation
```

------------------------------------------------------------------------

## F.3 Nouvelle stratégie

``` text
[ ] hypothèse
[ ] règles formelles
[ ] baseline
[ ] dataset versionné
[ ] backtest
[ ] coûts inclus
[ ] out-of-sample
[ ] robustness tests
[ ] reason codes
[ ] Risk Engine compatible
[ ] experiment enregistré
```

------------------------------------------------------------------------

## F.4 Promotion Paper

``` text
[ ] backtest reproductible
[ ] OOS acceptable
[ ] coûts réalistes
[ ] aucun bug critique
[ ] stratégie versionnée
[ ] risque configuré
[ ] monitoring disponible
```

------------------------------------------------------------------------

## F.5 Promotion Shadow

``` text
[ ] paper stable
[ ] exécution simulée stable
[ ] reconciliation stable
[ ] alertes testées
[ ] restart testé
[ ] comportement temps réel validé
```

------------------------------------------------------------------------

## F.6 Promotion Limited Live

``` text
[ ] shadow stable
[ ] sécurité validée
[ ] credentials live isolés
[ ] withdrawals disabled
[ ] Risk Engine fail-closed
[ ] kill switch testé
[ ] idempotency testée
[ ] reconciliation live testée
[ ] capital initial limité
[ ] stop conditions définies
[ ] gouvernance approuvée
```

------------------------------------------------------------------------

## F.7 Déploiement Production

``` text
[ ] commit approuvé
[ ] tests verts
[ ] scans sécurité verts
[ ] migration vérifiée
[ ] artifact hash enregistré
[ ] configuration validée
[ ] backup disponible
[ ] rollback défini
[ ] monitoring prêt
[ ] approbation obtenue
```

------------------------------------------------------------------------

## F.8 Migration Database

``` text
[ ] migration versionnée
[ ] test empty → latest
[ ] test previous → latest
[ ] compatibilité application
[ ] impact performance
[ ] backup
[ ] rollback/recovery plan
[ ] revue
```

------------------------------------------------------------------------

## F.9 Incident Trading

``` text
[ ] identifier le périmètre
[ ] bloquer nouvelle exposition si nécessaire
[ ] activer kill switch si nécessaire
[ ] vérifier ordres ouverts
[ ] vérifier fills
[ ] vérifier positions venue
[ ] réconcilier
[ ] préserver logs
[ ] créer timeline
[ ] documenter résolution
[ ] postmortem
```

------------------------------------------------------------------------

## F.10 Credential Leak

``` text
[ ] révoquer credential
[ ] générer nouveau credential
[ ] vérifier permissions
[ ] rechercher exposition
[ ] inspecter logs
[ ] vérifier activité venue
[ ] mettre à jour services
[ ] confirmer révocation
[ ] documenter incident
```

------------------------------------------------------------------------

## F.11 Kill Switch Test

``` text
[ ] nouvelles entrées bloquées
[ ] ordres concernés annulables
[ ] stratégies haltées
[ ] événement audité
[ ] alerte générée
[ ] état visible
[ ] reprise contrôlée
```

------------------------------------------------------------------------

## F.12 Reconciliation

``` text
[ ] comptes chargés
[ ] ordres comparés
[ ] fills comparés
[ ] positions comparées
[ ] balances comparées
[ ] mismatches enregistrés
[ ] mismatches critiques alertés
[ ] corrections auditées
```

------------------------------------------------------------------------

## F.13 Backtest Review

``` text
[ ] dataset versionné
[ ] commit enregistré
[ ] paramètres enregistrés
[ ] frais inclus
[ ] slippage inclus
[ ] look-ahead bias contrôlé
[ ] survivorship bias évalué
[ ] OOS
[ ] sensibilité paramètres
[ ] drawdown
[ ] résultats nets
```

------------------------------------------------------------------------

## F.14 Experiment Review

``` text
[ ] hypothèse définie avant résultat
[ ] baseline définie
[ ] métriques définies
[ ] critères d’acceptation définis
[ ] expérience reproductible
[ ] artefacts sauvegardés
[ ] résultat documenté
[ ] limitations documentées
[ ] décision enregistrée
```

------------------------------------------------------------------------

## F.15 AI Agent Release

``` text
[ ] rôle défini
[ ] outils autorisés listés
[ ] permissions minimales
[ ] sandbox
[ ] budgets
[ ] timeout
[ ] logs
[ ] audit tool calls
[ ] prompt versionné
[ ] modèle versionné
[ ] tests adversariaux
[ ] aucune route directe live
[ ] kill switch disponible
```

------------------------------------------------------------------------

## F.16 Security Review

``` text
[ ] authentification
[ ] autorisation
[ ] moindre privilège
[ ] secrets
[ ] réseau
[ ] chiffrement
[ ] validation inputs
[ ] dépendances
[ ] audit
[ ] alertes
[ ] recovery
```

------------------------------------------------------------------------

## F.17 Release Checklist

``` text
[ ] version définie
[ ] changelog
[ ] tests
[ ] documentation
[ ] migrations
[ ] security scans
[ ] artifact built
[ ] artifact hash
[ ] rollback
[ ] approval
[ ] deployment
[ ] post-deploy checks
```

------------------------------------------------------------------------

# G. Structure documentaire finale recommandée

``` text
docs/
├── 01-Vision-du-Projet.md
├── 02-Architecture-Generale.md
├── 03-Data-Engine.md
├── 04-Storage-Engine.md
├── 05-Market-Analysis-Engine.md
├── 06-Market-Structure-Engine.md
├── 07-Volume-Profile-Engine.md
├── 08-Smart-Money-Concepts-Engine.md
├── 09-Scoring-Engine.md
├── 10-Decision-Engine.md
├── 11-Risk-Engine.md
├── 12-Execution-Engine.md
├── 13-Monitoring-Engine.md
├── 14-Knowledge-Engine.md
├── 15-AI-and-Learning-Engine.md
├── 16-Governance-Engine.md
├── 17-AI-Development-Protocol.md
├── 18-Testing-Strategy.md
├── 19-Deployment-Guide.md
├── 20-Engineering-Principles.md
├── 21-Experiment-Registry.md
├── 22-API-Specification.md
├── 23-Database-Schema.md
├── 24-Security.md
├── 25-Roadmap.md
├── annexes/
│   ├── ANNEX-A-Glossaire.md
│   ├── ANNEX-B-ADR.md
│   ├── ANNEX-C-Conventions-Git.md
│   ├── ANNEX-D-Standards-Markdown.md
│   ├── ANNEX-E-Diagrammes-Architecture.md
│   └── ANNEX-F-Checklists.md
└── adr/
    ├── ADR-0001-...
    └── ...
```

------------------------------------------------------------------------

# H. Règle finale

Les annexes sont normatives lorsqu'elles définissent une convention
commune au projet.

En cas de contradiction :

``` text
specific engine document
→ architecture document
→ engineering principles
→ annex conventions
```

La contradiction doit ensuite être corrigée explicitement plutôt que
laissée comme une petite bombe documentaire à retardement.

------------------------------------------------------------------------

# I. Statut

**Version : 1.0**

Ce document complète la série principale QuantLab `01` à `25`.

La documentation de base du projet comprend désormais :

``` text
25 documents principaux
+
annexes transversales
+
ADR évolutifs
```
