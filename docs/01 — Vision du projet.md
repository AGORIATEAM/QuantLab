# 01 — Vision du projet

**Projet : QuantLab**  
**Document : Vision du projet**  
**Version : 1.0**  
**Statut : Draft fondateur / à valider avant implémentation**  
**Dernière mise à jour : 2026-08-24**

---

## 1. Résumé exécutif

QuantLab est une plateforme de recherche quantitative et d'automatisation du trading conçue pour analyser, tester, comparer et éventuellement exécuter des stratégies de trading sur plusieurs classes d'actifs.

Le projet doit être conçu comme une **infrastructure de recherche quantitative évolutive**, et non comme un simple bot de trading basé sur quelques indicateurs techniques.

La première ambition de QuantLab est de construire un système capable de :

1. collecter des données de marché fiables ;
2. normaliser ces données ;
3. analyser automatiquement le contexte de marché ;
4. identifier la structure du marché ;
5. analyser les distributions de volume ;
6. détecter des configurations inspirées du Market Profile, Volume Profile et Smart Money Concepts ;
7. combiner ces informations dans un moteur de scoring ;
8. transformer le scoring en décisions de trading selon des règles explicites ;
9. appliquer un système strict de gestion du risque ;
10. exécuter éventuellement les ordres via des brokers, exchanges ou protocoles décentralisés ;
11. enregistrer intégralement les données, décisions et résultats ;
12. apprendre progressivement de l'historique des expériences ;
13. proposer de nouvelles hypothèses et configurations ;
14. tester ces hypothèses avant toute utilisation en production ;
15. conserver une traçabilité complète de toutes les décisions.

QuantLab ne doit jamais être conçu autour de l'hypothèse qu'une stratégie donnée est intrinsèquement rentable.

Les concepts utilisés dans le système sont des **hypothèses de recherche**.

Une hypothèse n'est conservée que si elle démontre un avantage statistique suffisamment robuste après validation hors échantillon et tests de robustesse.

---

# 2. Vision à long terme

La vision à long terme est de construire un **laboratoire quantitatif autonome**, capable d'accumuler des données, de conduire des expériences, de comparer des stratégies et d'améliorer progressivement les modèles de décision.

Le système doit évoluer progressivement selon les phases suivantes :

### Phase 1 — Research Platform

Construire l'infrastructure fondamentale :

- collecte de données ;
- stockage ;
- normalisation ;
- analyse ;
- backtesting ;
- journalisation ;
- visualisation ;
- gestion des expérimentations.

À ce stade, aucune intelligence artificielle autonome ne doit pouvoir modifier une stratégie de production.

### Phase 2 — Rule-Based Trading Engine

Implémenter des stratégies déterministes basées notamment sur :

- Market Structure ;
- Market Profile ;
- Volume Profile ;
- Smart Money Concepts ;
- volatilité ;
- contexte multi-timeframe ;
- sessions de marché ;
- événements macroéconomiques ;
- gestion du risque.

Chaque règle doit être explicitement définie et testable.

### Phase 3 — Multi-Asset Research

Étendre progressivement le système à plusieurs marchés.

Priorité initiale :

- BTC ;
- ETH.

Puis :

- autres crypto-actifs liquides ;
- XAU/USD ;
- autres marchés traditionnels ;
- futures ;
- éventuellement actions et indices.

### Phase 4 — Adaptive Research

Introduire un moteur capable d'identifier les changements de régime de marché et de proposer des adaptations.

Exemples :

- marché en tendance ;
- marché en range ;
- volatilité faible ;
- volatilité élevée ;
- changement de régime ;
- comportement inhabituel du volume ;
- changement de liquidité.

Le système peut proposer des adaptations, mais celles-ci doivent être testées avant activation.

### Phase 5 — AI-Assisted Quant Research

Introduire progressivement des modèles d'intelligence artificielle capables de :

- analyser les historiques ;
- détecter des régularités ;
- générer des hypothèses ;
- proposer des variantes de stratégies ;
- identifier des anomalies ;
- comparer des régimes de marché ;
- rechercher des paramètres robustes ;
- analyser les causes de performance ou de sous-performance.

L'IA ne doit pas être considérée comme une autorité.

Elle est un **moteur de recherche et de génération d'hypothèses**.

### Phase 6 — Controlled Autonomous Research

À terme, QuantLab pourra fonctionner comme une boucle de recherche semi-autonome :

```text
DATA
  ↓
ANALYSIS
  ↓
HYPOTHESIS GENERATION
  ↓
EXPERIMENT
  ↓
BACKTEST
  ↓
OUT-OF-SAMPLE TEST
  ↓
ROBUSTNESS TEST
  ↓
PAPER TRADING
  ↓
HUMAN / GOVERNANCE APPROVAL
  ↓
PRODUCTION
  ↓
MONITORING
  ↓
NEW DATA
  ↓
NEW RESEARCH
```

L'autonomie doit augmenter uniquement lorsque la fiabilité du système augmente.

---

# 3. Problème que QuantLab cherche à résoudre

Les stratégies de trading discrétionnaires souffrent généralement de plusieurs problèmes :

- interprétation subjective ;
- manque de reproductibilité ;
- absence de statistiques fiables ;
- biais cognitifs ;
- sur-optimisation ;
- difficulté à mesurer précisément l'efficacité d'une règle ;
- difficulté à comparer plusieurs stratégies ;
- absence de journalisation complète ;
- difficulté à détecter les changements de régime ;
- difficulté à distinguer une vraie inefficience d'un simple hasard statistique.

QuantLab doit transformer ces problèmes en processus mesurables.

Exemple :

Au lieu de dire :

> "Un liquidity sweep suivi d'un CHOCH fonctionne souvent."

Le système doit permettre de répondre :

- combien de fois le pattern apparaît ;
- sur quels actifs ;
- sur quels timeframes ;
- dans quels régimes ;
- pendant quelles sessions ;
- avec quelle volatilité ;
- avec quel volume ;
- quelle excursion maximale favorable ;
- quelle excursion maximale défavorable ;
- quel taux de réussite ;
- quelle expectancy ;
- quel drawdown ;
- quelle performance après frais ;
- quelle performance après slippage ;
- quelle performance hors échantillon ;
- quelle stabilité sur différentes périodes.

La plateforme doit transformer une intuition de trading en **hypothèse quantifiable**.

---

# 4. Positionnement du projet

QuantLab n'est pas :

- un simple indicateur TradingView ;
- un bot basé sur RSI/MACD ;
- un système qui prédit systématiquement le prochain mouvement ;
- une boîte noire IA ;
- une stratégie unique ;
- une machine à profits garantie ;
- un système qui modifie automatiquement ses paramètres sans contrôle.

QuantLab est :

- une plateforme de recherche ;
- une infrastructure de données ;
- un framework de stratégies ;
- un laboratoire d'expérimentation ;
- un système de validation statistique ;
- une infrastructure d'exécution ;
- un système de monitoring ;
- une mémoire historique des expériences ;
- une plateforme permettant progressivement l'utilisation de l'IA.

---

# 5. Philosophie fondamentale

## 5.1 Principe n°1 — Toute stratégie est une hypothèse

Aucune stratégie ne doit être considérée comme vraie avant validation.

Exemple :

```text
Hypothèse :
Un liquidity sweep suivi d'une confirmation de structure possède
une expectancy positive sur BTC en timeframe 5 minutes pendant
les heures de forte liquidité.
```

Cette hypothèse doit être testée.

---

## 5.2 Principe n°2 — Objectiver les concepts subjectifs

Des concepts tels que :

- Smart Money ;
- Order Block ;
- Fair Value Gap ;
- Liquidity Sweep ;
- Break of Structure ;
- Change of Character ;
- absorption ;
- accumulation ;
- distribution ;

peuvent être utiles comme cadres d'analyse.

Cependant, leurs définitions doivent être transformées en règles mathématiques et algorithmiques.

Exemple :

```text
"Le prix a pris la liquidité."

```

n'est pas une définition exploitable.

Une définition exploitable pourrait être :

```text
Un liquidity sweep est identifié lorsqu'un niveau de liquidité
préalablement défini est franchi par le prix puis que la bougie
clôture à l'intérieur de la zone précédente dans une fenêtre
temporelle donnée.
```

La définition exacte devra être spécifiée dans le module correspondant.

---

# 6. Marchés ciblés

## 6.1 Marché prioritaire

La première version de QuantLab doit se concentrer sur les crypto-actifs liquides.

Actifs prioritaires :

- BTC/USDT ;
- ETH/USDT.

Cette limitation est volontaire.

Elle permet de réduire la complexité initiale et de construire une architecture suffisamment générale sans tenter de traiter simultanément tous les marchés existants.

---

## 6.2 Extension crypto

Après validation de l'infrastructure initiale :

- SOL ;
- BNB ;
- autres actifs liquides ;
- marchés perpétuels ;
- futures crypto ;
- plusieurs exchanges.

Chaque nouvel actif doit être intégré via une abstraction commune.

---

## 6.3 Marchés décentralisés

Une extension spécifique devra permettre l'analyse des marchés DeFi et DEX.

Cette couche devra tenir compte de caractéristiques spécifiques :

- pools de liquidité ;
- AMM ;
- slippage ;
- profondeur réelle ;
- liquidité disponible ;
- MEV ;
- frais de réseau ;
- frais de swap ;
- impact du prix ;
- fragmentation de liquidité ;
- risques de smart contracts ;
- qualité des données on-chain.

Les marchés DEX ne doivent pas être traités comme une simple copie des exchanges centralisés.

---

## 6.4 Or

XAU/USD doit constituer une extension importante du système.

L'objectif est notamment de vérifier si les hypothèses construites sur les crypto-actifs restent valides sur un actif traditionnel.

Cette comparaison est importante car elle permet de tester la robustesse des hypothèses.

Exemple :

```text
Hypothèse H001 :
Un liquidity sweep suivi d'une rupture de structure
présente une expectancy positive.

Test :
BTC
ETH
XAU/USD
```

Si l'effet disparaît totalement sur certains marchés, cette information est elle-même utile.

---

# 7. Horizons temporels

QuantLab doit être conçu pour supporter plusieurs horizons.

### Macro / contexte

- 1D ;
- 4H.

### Structure intermédiaire

- 1H ;
- 30m ;
- 15m.

### Exécution

- 5m ;
- 3m ;
- 1m.

Le système doit permettre une analyse multi-timeframe.

Exemple :

```text
1D → contexte macro
4H → structure principale
1H → structure intermédiaire
15m → setup
5m → confirmation
1m → exécution éventuelle
```

Ces timeframes doivent être configurables.

---

# 8. Style de trading initial

Le système doit être capable de supporter plusieurs styles :

- intraday ;
- swing ;
- mean reversion ;
- trend following ;
- breakout ;
- liquidity-based trading ;
- market profile trading ;
- stratégies hybrides.

Cependant, la première stratégie de recherche devra rester suffisamment simple pour permettre une validation claire.

La complexité ne doit pas être utilisée pour masquer l'absence d'edge.

---

# 9. Architecture conceptuelle

La plateforme doit être composée de modules indépendants.

Architecture conceptuelle :

```text
                    ┌─────────────────────┐
                    │     DATA SOURCES    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │      DATA ENGINE    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    STORAGE ENGINE   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
        Market Analysis   Market Structure   Volume Profile
              │                │                │
              └────────────────┼────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   SMC ENGINE        │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   SCORING ENGINE    │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   DECISION ENGINE   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │     RISK ENGINE     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  EXECUTION ENGINE   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  MONITORING ENGINE  │
                    └─────────────────────┘

                               │
                               ▼
                    ┌─────────────────────┐
                    │   KNOWLEDGE ENGINE  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ AI & LEARNING ENGINE│
                    └─────────────────────┘
```

---

# 10. Rôle de l'intelligence artificielle

L'intelligence artificielle doit être introduite progressivement.

Les modèles IA pourront notamment être utilisés pour :

- recherche ;
- génération d'hypothèses ;
- classification de régimes ;
- analyse de données ;
- détection d'anomalies ;
- optimisation contrôlée ;
- analyse des expériences ;
- génération de rapports ;
- assistance au développement ;
- analyse de logs ;
- recherche documentaire ;
- code review.

Cependant :

> L'IA ne doit jamais être considérée comme une preuve de rentabilité.

Une sortie générée par une IA est une hypothèse ou une recommandation jusqu'à sa validation quantitative.

---

# 11. Claude et autres systèmes IA

QuantLab doit être conçu pour pouvoir fonctionner avec plusieurs systèmes d'IA.

Claude pourra notamment être utilisé comme :

- agent de développement ;
- assistant de recherche ;
- générateur de code ;
- analyste de résultats ;
- générateur d'hypothèses ;
- reviewer technique.

D'autres modèles pourront être utilisés pour :

- comparaison de résultats ;
- validation indépendante ;
- génération alternative d'hypothèses ;
- analyse de données ;
- documentation.

Le système ne doit jamais dépendre d'un fournisseur IA unique.

---

# 12. Knowledge Engine

Le Knowledge Engine constitue la mémoire du système.

Il doit conserver notamment :

- données de marché ;
- configurations ;
- stratégies ;
- versions de stratégies ;
- expériences ;
- résultats de backtests ;
- paramètres ;
- signaux ;
- décisions ;
- trades ;
- erreurs ;
- métriques ;
- régimes de marché ;
- hypothèses ;
- résultats d'expériences ;
- changements de configuration ;
- commentaires de recherche.

L'objectif est d'empêcher la perte de connaissance.

Chaque expérience importante doit pouvoir être retrouvée et reproduite.

---

# 13. Apprentissage du système

L'expression "apprendre par lui-même" doit être définie précisément.

QuantLab ne doit pas simplement :

```text
observer → modifier → trader
```

Le cycle cible est :

```text
observer
   ↓
analyser
   ↓
identifier une anomalie ou opportunité
   ↓
formuler une hypothèse
   ↓
générer une expérience
   ↓
backtester
   ↓
tester hors échantillon
   ↓
tester la robustesse
   ↓
paper trading
   ↓
validation
   ↓
activation contrôlée
```

L'apprentissage autonome doit donc être **contraint par un système de gouvernance**.

---

# 14. Supabase et stockage

Supabase pourra être utilisé comme infrastructure de stockage et de backend applicatif.

Il pourra notamment héberger :

- métadonnées ;
- expériences ;
- stratégies ;
- résultats ;
- configurations ;
- journaux structurés ;
- données analytiques ;
- informations du Knowledge Engine.

Cependant, l'architecture doit rester abstraite.

Le code métier ne doit pas dépendre directement d'un fournisseur de stockage.

Principe :

```text
Application
     ↓
Repository Interface
     ↓
Storage Adapter
     ↓
Supabase / PostgreSQL
```

Cela permettra de remplacer ou compléter Supabase ultérieurement si les volumes de données l'exigent.

---

# 15. Scalabilité

QuantLab doit être capable d'évoluer progressivement.

### Niveau 1

Un utilisateur.

Quelques actifs.

Quelques stratégies.

Backtests locaux.

### Niveau 2

Plusieurs actifs.

Plusieurs exchanges.

Pipeline de données permanent.

### Niveau 3

Backtests parallélisés.

Recherche automatisée.

Machine learning.

### Niveau 4

Infrastructure distribuée.

Calcul cloud.

Data lake.

Multiples sources de données.

### Niveau 5

Laboratoire quantitatif autonome.

Recherche continue.

Validation automatique.

Déploiement contrôlé.

---

# 16. Principes de robustesse

Le système doit respecter les principes suivants :

### Reproductibilité

Une expérience doit pouvoir être reproduite avec les mêmes données et paramètres.

### Traçabilité

Toute décision doit pouvoir être expliquée.

### Versioning

Les stratégies et paramètres doivent être versionnés.

### Isolation

Les expériences doivent être isolées de la production.

### Validation

Aucune stratégie ne doit passer directement de recherche à production.

### Observabilité

Le système doit savoir expliquer son propre état.

### Fail-safe

En cas d'incertitude ou de dysfonctionnement, le système doit préférer ne pas trader.

---

# 17. Critères de réussite

La réussite de QuantLab ne doit pas être mesurée uniquement par le rendement.

Les métriques importantes comprennent :

- expectancy ;
- Sharpe ratio ;
- Sortino ratio ;
- maximum drawdown ;
- Calmar ratio ;
- profit factor ;
- taux de réussite ;
- average win ;
- average loss ;
- payoff ratio ;
- stabilité temporelle ;
- stabilité inter-actifs ;
- stabilité inter-régimes ;
- sensibilité aux frais ;
- sensibilité au slippage ;
- robustesse des paramètres ;
- performance hors échantillon.

Une stratégie présentant un rendement élevé mais une forte instabilité peut être rejetée.

---

# 18. Critères de rejet

Une stratégie doit être rejetée ou placée en observation si :

- elle dépend excessivement d'un seul paramètre ;
- elle disparaît hors échantillon ;
- elle dépend d'une période spécifique ;
- elle présente une forte dégradation après frais ;
- elle présente une forte sensibilité au slippage ;
- elle dépend d'un nombre trop faible d'observations ;
- elle présente une instabilité extrême ;
- elle semble résulter d'une optimisation excessive ;
- elle ne peut pas être reproduite ;
- son avantage statistique n'est pas suffisamment robuste.

---

# 19. Prévention du surapprentissage

Le surapprentissage constitue l'un des risques principaux du projet.

Le système doit donc appliquer :

- séparation train/test ;
- validation hors échantillon ;
- walk-forward analysis ;
- tests sur plusieurs périodes ;
- tests sur plusieurs actifs ;
- tests sur plusieurs régimes ;
- tests de sensibilité des paramètres ;
- tests Monte Carlo lorsque pertinents ;
- validation avec coûts réalistes.

L'optimisation doit être limitée.

Le meilleur backtest historique n'est pas nécessairement la meilleure stratégie future.

---

# 20. Philosophie de recherche

QuantLab doit favoriser les stratégies :

- simples ;
- explicables ;
- robustes ;
- reproductibles ;
- économiquement plausibles ;
- statistiquement validées.

Une stratégie complexe ne doit être conservée que si sa complexité apporte une amélioration mesurable et robuste.

---

# 21. Philosophie de développement

Chaque fonctionnalité doit être développée selon le cycle :

```text
SPECIFICATION
     ↓
IMPLEMENTATION
     ↓
UNIT TEST
     ↓
INTEGRATION TEST
     ↓
BACKTEST / RESEARCH
     ↓
VALIDATION
     ↓
DOCUMENTATION
     ↓
VERSIONING
```

Aucune modification critique ne doit être introduite directement en production.

---

# 22. Séparation Research / Paper / Production

QuantLab doit disposer de trois environnements conceptuellement séparés.

## Research

Expérimentation libre.

Aucun capital réel.

## Paper

Simulation proche des conditions réelles.

Objectif : tester l'exécution et la stabilité.

## Production

Capital réel.

Accès strictement contrôlé.

Les stratégies doivent progresser :

```text
Research
   ↓
Validation
   ↓
Paper
   ↓
Production Candidate
   ↓
Production
```

---

# 23. Principe fondamental de sécurité

Le système doit considérer que :

> Ne pas trader est une décision valide.

L'absence de signal suffisamment fiable doit produire :

```text
NO TRADE
```

et non forcer une position.

Le système doit également pouvoir arrêter automatiquement :

- l'ouverture de nouvelles positions ;
- une stratégie ;
- un actif ;
- un exchange ;
- ou l'ensemble du moteur de trading.

---

# 24. Vision finale

À terme, QuantLab doit devenir une plateforme capable de transformer continuellement des idées de trading en connaissances quantitatives.

Le système idéal suit cette boucle :

```text
DATA
 ↓
OBSERVATION
 ↓
ANALYSIS
 ↓
HYPOTHESIS
 ↓
EXPERIMENT
 ↓
VALIDATION
 ↓
STRATEGY
 ↓
PAPER TRADING
 ↓
PRODUCTION
 ↓
MONITORING
 ↓
NEW DATA
 ↓
NEW KNOWLEDGE
 ↓
NEW HYPOTHESES
```

L'objectif n'est donc pas de construire une stratégie parfaite.

L'objectif est de construire une **machine de recherche capable d'identifier, mesurer, conserver et éliminer systématiquement les idées de trading**, jusqu'à faire émerger les stratégies les plus robustes.

---

# 25. Résumé des principes fondateurs

1. QuantLab est une plateforme de recherche quantitative, pas simplement un bot.
2. Toute stratégie est une hypothèse.
3. Toute hypothèse doit être testable.
4. Les concepts subjectifs doivent être objectivés.
5. Les résultats doivent être reproductibles.
6. Les données doivent être versionnées et traçables.
7. Les stratégies doivent être testées hors échantillon.
8. Le surapprentissage doit être activement combattu.
9. L'IA génère et analyse des hypothèses, mais ne constitue pas une preuve.
10. Le système doit pouvoir apprendre progressivement sans modifier aveuglément la production.
11. Supabase/PostgreSQL constitue une couche de stockage importante, mais doit rester abstraite.
12. Research, Paper et Production doivent être séparés.
13. Le Risk Engine possède une autorité supérieure au Decision Engine.
14. Le système doit toujours pouvoir décider de ne pas trader.
15. Toute décision critique doit être journalisée.
16. Toute stratégie en production doit être monitorée.
17. Toute modification doit être versionnée.
18. Toute performance doit être évaluée après coûts réalistes.
19. La simplicité et la robustesse sont préférées à la complexité inutile.
20. L'objectif final est de construire une infrastructure de recherche quantitative durable et évolutive.

---

## 26. Dépendances documentaires

Ce document constitue la vision fondatrice de QuantLab.

Les documents suivants doivent être cohérents avec cette vision :

- `02-Architecture-Generale.md`
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
- `17-AI-Development-Protocol.md`
- `18-Testing-Strategy.md`
- `19-Deployment-Guide.md`
- `20-Engineering-Principles.md`
- `21-Experiment-Registry.md`
- `22-API-Specification.md`
- `23-Database-Schema.md`
- `24-Security.md`
- `25-Roadmap.md`

---

## 27. Statut

**Version : 1.0**

Ce document constitue la référence de haut niveau du projet.

Toute décision d'architecture ou de développement qui entre en contradiction avec cette vision doit être explicitement documentée dans un Architecture Decision Record (ADR).

Une modification importante de cette vision doit entraîner une mise à jour de la version du document.