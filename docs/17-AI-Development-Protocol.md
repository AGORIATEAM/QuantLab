# 17 — AI Development Protocol

**Projet : QuantLab**  
**Document : AI Development Protocol**  
**Version : 1.0**  
**Statut : Standard d'ingénierie obligatoire**

---

# 1. Objectif

L'AI Development Protocol définit la méthode officielle utilisée pour développer QuantLab avec l'aide d'agents IA et de modèles de langage.

Son objectif est d'obtenir les avantages de l'IA :

- vitesse de développement ;
- génération de code ;
- génération de tests ;
- analyse ;
- documentation ;
- refactoring ;
- revue ;
- exploration technique ;

sans accepter les défauts classiques du développement assisté par IA :

- code inventé ;
- architecture incohérente ;
- duplication ;
- dépendances inutiles ;
- modifications incontrôlées ;
- tests superficiels ;
- changements trop larges ;
- perte de contexte ;
- violations silencieuses des invariants.

La règle générale est :

> **L'IA accélère l'ingénierie. Elle ne remplace ni les contrats, ni les tests, ni la revue, ni la gouvernance.**

---

# 2. Champ d'application

Ce protocole s'applique à tout code ou artefact produit avec assistance IA :

```text
application code
trading engines
data pipelines
database migrations
tests
infrastructure
configuration
prompts
documentation
scripts
research tooling
```

Il s'applique à tous les agents utilisés pour développer QuantLab.

---

# 3. Hiérarchie des sources de vérité

Un agent doit respecter cet ordre :

```text
1. Security constraints
2. Governance rules
3. Architecture documents
4. Component specifications
5. ADRs
6. API contracts
7. Database schema
8. Tests
9. Existing implementation
10. Task instructions
```

Une instruction ponctuelle ne doit pas silencieusement invalider une règle architecturale supérieure.

---

# 4. Documentation as Contract

Les documents `01` à `25` constituent la spécification du système.

L'IA doit les traiter comme des contrats d'ingénierie, pas comme de la prose décorative qu'on admire avant de faire exactement autre chose.

---

# 5. Repository Structure

Structure cible indicative :

```text
quantlab/
├── docs/
├── src/
│   ├── data/
│   ├── storage/
│   ├── market_analysis/
│   ├── market_structure/
│   ├── volume_profile/
│   ├── smc/
│   ├── scoring/
│   ├── decision/
│   ├── risk/
│   ├── execution/
│   ├── monitoring/
│   ├── knowledge/
│   ├── ai/
│   └── governance/
├── tests/
├── migrations/
├── scripts/
├── configs/
├── research/
└── infrastructure/
```

La structure définitive doit rester cohérente avec l'architecture générale.

---

# 6. Unité de travail

Chaque tâche IA doit être petite, explicite et vérifiable.

Mauvais exemple :

```text
Build the trading platform.
```

Meilleur exemple :

```text
Implement MarketEvent schema
according to 03-Data-Engine.md.

Add unit tests.
Do not modify unrelated modules.
```

---

# 7. Task Specification

Toute tâche importante doit préciser :

```text
objective
scope
inputs
outputs
constraints
acceptance criteria
allowed files
forbidden changes
required tests
```

---

# 8. Definition of Done

Une tâche n'est terminée que lorsque :

```text
implementation complete
tests written
tests passing
contracts respected
errors handled
observability considered
documentation updated if required
diff reviewed
```

`Le code compile` n'est pas une Definition of Done.

---

# 9. Context Gathering

Avant de modifier du code existant, l'agent doit examiner :

```text
relevant specification
existing interfaces
related tests
call sites
data models
configuration
```

---

# 10. No Blind Coding

L'agent ne doit pas commencer par réécrire un composant avant de comprendre son interface actuelle.

---

# 11. Plan Before Implementation

Pour une modification non triviale, produire d'abord un plan interne ou explicite comprenant :

```text
files affected
interfaces affected
migration impact
tests required
risks
```

---

# 12. Minimal Change Principle

Modifier le minimum nécessaire pour satisfaire la tâche.

Éviter :

```text
task = fix one parser
result = refactor half the repository
```

---

# 13. Scope Control

Si une amélioration hors scope est découverte :

```text
record it
```

mais ne pas l'intégrer automatiquement au changement courant.

---

# 14. Atomic Changes

Les changements doivent idéalement être atomiques.

Un commit doit répondre à une intention claire.

---

# 15. One Concern per Change

Éviter de mélanger :

```text
feature
refactor
dependency upgrade
formatting
```

dans le même changement sans nécessité.

---

# 16. Interface First

Pour un nouveau composant :

```text
define contract
↓
write tests
↓
implement
```

plutôt que :

```text
write lots of code
↓
discover interface afterward
```

---

# 17. Typed Contracts

Les interfaces critiques doivent utiliser des structures explicites et typées.

Exemple :

```python
@dataclass(frozen=True)
class TradeIntent:
    intent_id: str
    symbol: str
    side: Side
    requested_risk: Decimal
```

---

# 18. No Magic Dictionaries

Éviter de faire circuler partout :

```python
{"thing": ..., "value": ..., "stuff": ...}
```

pour les objets métier critiques.

---

# 19. Domain Models

Créer des modèles explicites pour :

```text
MarketEvent
MarketContext
ScoreContext
TradeIntent
RiskDecision
ExecutionOrder
Fill
TradeRecord
AIRecommendation
ChangeProposal
```

---

# 20. Immutability

Les événements historiques et décisions importantes doivent être immutables lorsque possible.

---

# 21. IDs

Les objets distribués doivent disposer d'identifiants stables.

Exemples :

```text
event_id
decision_id
trade_id
order_id
experiment_id
```

---

# 22. Correlation

Les IDs doivent permettre de reconstruire le lineage complet.

---

# 23. Time Handling

Règle obligatoire :

```text
internal timestamps = UTC
```

Les timestamps doivent être timezone-aware.

---

# 24. Numeric Precision

Pour les valeurs financières critiques, éviter les floats binaires lorsque leur imprécision peut avoir un effet opérationnel.

Utiliser selon le contexte :

```text
Decimal
integer ticks
integer smallest units
```

---

# 25. Configuration

Les paramètres configurables ne doivent pas être enfouis dans le code.

---

# 26. Configuration Versioning

Les configurations critiques doivent être versionnées.

---

# 27. Secrets

Jamais dans :

```text
source code
Git
test fixtures publiques
logs
prompts
documentation
```

---

# 28. Environment Variables

Les références aux secrets peuvent utiliser l'environnement ou un secret manager.

---

# 29. Dependency Policy

Avant d'ajouter une dépendance, l'agent doit vérifier :

```text
is it necessary?
is equivalent functionality already present?
is it maintained?
what is the security impact?
```

---

# 30. Dependency Minimalism

Une fonction de quinze lignes ne justifie pas toujours une nouvelle bibliothèque et ses quarante-sept dépendances transitoires. L'écosystème logiciel survivra à cette privation.

---

# 31. Architectural Boundaries

Chaque moteur doit respecter sa responsabilité.

Exemple :

```text
Scoring Engine
```

ne doit pas envoyer directement un ordre.

---

# 32. Dependency Direction

Les dépendances doivent suivre l'architecture définie.

Les modules bas niveau ne doivent pas dépendre arbitrairement des couches supérieures.

---

# 33. No Hidden Coupling

Éviter :

```text
global mutable state
implicit singleton
environment-dependent behavior
```

non documenté.

---

# 34. Dependency Injection

Les dépendances externes importantes doivent être injectables :

```text
clock
storage
exchange client
event bus
AI provider
```

afin de faciliter les tests.

---

# 35. External Systems

Tout appel externe doit considérer :

```text
timeout
retry
rate limit
partial failure
invalid response
```

---

# 36. Timeout Mandatory

Aucun appel réseau critique ne doit attendre indéfiniment.

---

# 37. Retry Policy

Les retries doivent être :

```text
bounded
observable
appropriate to idempotency
```

---

# 38. Idempotency

Les opérations sensibles doivent être conçues pour éviter les doubles effets.

Particulièrement :

```text
order submission
event processing
database writes
```

---

# 39. Error Handling

Ne pas utiliser :

```python
except Exception:
    pass
```

sur les chemins critiques.

---

# 40. Error Taxonomy

Définir des erreurs métier explicites.

Exemples :

```text
InvalidMarketData
RiskLimitExceeded
OrderRejected
StaleDecision
GovernanceDenied
```

---

# 41. Fail Closed

Pour toute action augmentant l'exposition :

```text
uncertain state
→ reject / NO_TRADE
```

---

# 42. Fail Safe

Pour les mécanismes de réduction du risque :

```text
close
cancel
kill switch
```

le système doit privilégier la sécurité opérationnelle.

---

# 43. Logging

Les logs doivent être structurés.

Exemple :

```json
{
  "event": "risk_decision",
  "decision_id": "...",
  "result": "REJECTED",
  "reason": "DAILY_LOSS_LIMIT"
}
```

---

# 44. No Secret Logging

Les logs ne doivent jamais contenir :

```text
API secret
private key
password
auth token
```

---

# 45. Observability

Tout nouveau service important doit exposer :

```text
health
metrics
logs
```

---

# 46. Metrics

Les métriques doivent être définies dès la conception, pas après le premier incident.

---

# 47. Deterministic Core

Les chemins critiques de risque et d'exécution doivent rester aussi déterministes que possible.

---

# 48. AI Boundary

Un LLM ne doit pas être placé directement dans une décision irréversible sans validation structurée.

---

# 49. Structured AI Outputs

Les outputs IA utilisés par du code doivent être validés contre un schéma.

---

# 50. AI Evidence

Toute recommandation IA importante doit référencer ses preuves.

---

# 51. AI Permissions

Les agents de développement ne doivent pas disposer par défaut :

```text
production secrets
live trading credentials
unrestricted database writes
```

---

# 52. Sandbox

Les agents doivent travailler dans un environnement isolé lorsque possible.

---

# 53. Read Before Write

Avant modification d'un fichier, l'agent doit lire la partie pertinente.

---

# 54. Search Before Create

Avant de créer :

```text
class
utility
service
schema
```

chercher si un équivalent existe déjà.

---

# 55. No Duplicate Abstractions

Deux abstractions presque identiques sont souvent le début d'une divergence future.

---

# 56. Existing Patterns

L'agent doit suivre les patterns du repository sauf raison documentée de les modifier.

---

# 57. Refactoring Rule

Un refactoring doit préserver le comportement observable sauf si la tâche indique explicitement un changement fonctionnel.

---

# 58. Refactoring Tests

Avant un refactoring important, renforcer les tests caractérisant le comportement existant.

---

# 59. No Opportunistic Rewrite

Ne pas remplacer une implémentation stable uniquement parce que l'agent préfère une autre syntaxe.

---

# 60. Test-Driven Changes

Pour les bugs :

```text
reproduce bug in test
↓
observe failure
↓
fix
↓
observe pass
```

---

# 61. Unit Tests

Chaque logique métier non triviale doit avoir des tests unitaires.

---

# 62. Integration Tests

Les frontières entre composants doivent être testées.

---

# 63. Contract Tests

Les producteurs et consommateurs d'événements/API doivent respecter les mêmes schémas.

---

# 64. Regression Tests

Tout bug corrigé doit idéalement laisser un test empêchant sa réapparition.

---

# 65. Property-Based Tests

Particulièrement utiles pour :

```text
risk invariants
numeric logic
serialization
```

---

# 66. Invariant Tests

Exemples :

```text
position risk <= approved risk
filled quantity <= allowed quantity
no order without approved intent
```

---

# 67. Failure Tests

Tester les erreurs, pas seulement le chemin heureux.

---

# 68. Boundary Tests

Tester :

```text
zero
negative
maximum
minimum
exact threshold
just above
just below
```

---

# 69. Time Tests

Tester :

```text
out-of-order events
stale data
clock boundaries
timezone behavior
```

---

# 70. Concurrency Tests

Pour les composants concurrents :

```text
duplicate events
race conditions
parallel updates
```

---

# 71. Replay Tests

Les moteurs analytiques doivent idéalement produire des résultats reproductibles lors d'un replay déterministe.

---

# 72. Backtest Tests

Le backtest doit vérifier :

```text
no future leakage
fees
slippage
order assumptions
```

---

# 73. AI-Generated Tests

Les tests générés par IA doivent être revus comme du code.

Un test qui vérifie simplement que l'implémentation fait ce qu'elle vient d'écrire ne constitue pas une preuve particulièrement bouleversante.

---

# 74. Independent Test Reasoning

Les tests doivent dériver des spécifications et invariants, pas uniquement de l'implémentation.

---

# 75. Test Naming

Les noms doivent décrire le comportement.

Exemple :

```text
test_rejects_trade_when_daily_loss_limit_exceeded
```

---

# 76. Test Fixtures

Les fixtures doivent être :

```text
small
explicit
deterministic
```

---

# 77. No Live API in Unit Tests

Les tests unitaires ne doivent pas dépendre d'un exchange ou service externe réel.

---

# 78. Mocks

Mocker les frontières externes, pas toute la logique interne.

---

# 79. CI Required

Tout changement doit passer le pipeline CI applicable.

---

# 80. CI Gates

Minimum :

```text
format
lint
type check
unit tests
integration tests
security checks
```

selon le composant.

---

# 81. Static Analysis

Utiliser des outils adaptés au langage pour détecter les erreurs avant runtime.

---

# 82. Type Checking

Le code Python critique devrait être typé et vérifié statiquement lorsque raisonnable.

---

# 83. Formatting

Le formatage doit être automatisé.

Les débats humains sur le nombre d'espaces sont une utilisation remarquablement coûteuse de cerveaux biologiques.

---

# 84. Linting

Le lint doit détecter :

```text
unused code
unsafe patterns
obvious mistakes
```

---

# 85. Security Scanning

Le pipeline doit progressivement inclure :

```text
dependency scanning
secret scanning
static security analysis
```

---

# 86. Code Review

Aucun changement critique généré par IA ne doit être accepté uniquement parce qu'il « a l'air correct ».

---

# 87. Review Checklist

Le reviewer doit vérifier :

```text
scope
correctness
architecture
tests
security
risk
observability
migration impact
```

---

# 88. Diff Review

Examiner le diff complet.

Les changements inattendus doivent être expliqués ou retirés.

---

# 89. Generated File Review

Les fichiers générés automatiquement doivent être identifiables lorsque pertinent.

---

# 90. Dead Code

Ne pas conserver des blocs inutilisés « au cas où ».

Git possède déjà une mémoire. Il n'est pas nécessaire de transformer le codebase en grenier.

---

# 91. TODO Policy

Un TODO doit indiquer :

```text
what
why
owner or issue
```

si le projet utilise un tracker.

---

# 92. No Silent TODO

Ne pas remplacer une fonctionnalité requise par :

```python
# TODO implement later
```

tout en déclarant la tâche terminée.

---

# 93. Database Changes

Toute migration doit être versionnée.

---

# 94. Migration Safety

Évaluer :

```text
backward compatibility
locking
data migration
rollback
```

---

# 95. Destructive Migration

Les opérations destructrices nécessitent une prudence accrue.

---

# 96. API Changes

Une modification d'API doit considérer les consommateurs existants.

---

# 97. Breaking API

Les breaking changes doivent être explicites et versionnés.

---

# 98. Event Schema Changes

Les événements distribués doivent gérer la compatibilité de schéma.

---

# 99. Documentation Update

Si le comportement contractuel change, la documentation correspondante doit être mise à jour dans le même changement.

---

# 100. ADR Requirement

Créer un ADR pour une décision architecturale importante.

---

# 101. ADR Structure

```text
Context
Decision
Alternatives
Consequences
Status
```

---

# 102. No Architecture by Accident

Une décision structurante ne doit pas émerger uniquement d'un détail d'implémentation généré par un agent.

---

# 103. Commit Convention

Format recommandé :

```text
type(scope): description
```

Exemples :

```text
feat(risk): add portfolio heat limit
fix(data): reject out-of-order candles
test(execution): add duplicate order protection
docs(ai): define model promotion workflow
```

---

# 104. Commit Types

```text
feat
fix
refactor
test
docs
chore
perf
security
```

---

# 105. Commit Scope

Utiliser le composant concerné :

```text
data
storage
analysis
structure
volume
smc
scoring
decision
risk
execution
monitoring
knowledge
ai
governance
```

---

# 106. Commit Message

Le message doit expliquer le changement, pas simplement :

```text
update stuff
```

---

# 107. Pull Request

Une PR doit contenir :

```text
summary
why
changes
tests
risk
rollback
```

selon l'importance.

---

# 108. AI Disclosure

Pour les changements fortement générés par IA, le projet peut enregistrer l'agent/modèle utilisé dans les métadonnées de développement.

---

# 109. Branch Strategy

Recommandation simple :

```text
main
+
short-lived feature branches
```

---

# 110. Main Branch

`main` doit rester déployable ou proche d'un état stable selon la stratégie CI/CD retenue.

---

# 111. No Long-Lived Divergence

Éviter les branches qui divergent pendant des semaines et deviennent de petites civilisations indépendantes.

---

# 112. Merge Gate

Avant merge :

```text
reviews complete
CI green
required approvals
no unresolved critical comments
```

---

# 113. Release Versioning

Les releases doivent être versionnées.

---

# 114. Semantic Versioning

Peut être utilisé pour les composants/API lorsque pertinent :

```text
MAJOR.MINOR.PATCH
```

---

# 115. Build Metadata

Conserver :

```text
commit SHA
build ID
artifact hash
```

---

# 116. Reproducible Build

Un artefact doit pouvoir être relié au code qui l'a produit.

---

# 117. AI Task Template

Template recommandé :

```text
TASK
Implement <feature>.

SOURCE OF TRUTH
<documents / interfaces>

SCOPE
<files/modules>

DO NOT
<forbidden changes>

REQUIREMENTS
<functional requirements>

TESTS
<required tests>

ACCEPTANCE
<definition of done>
```

---

# 118. Bug-Fix Prompt Template

```text
BUG
<observed behavior>

EXPECTED
<expected behavior>

REPRODUCTION
<steps/test>

CONSTRAINTS
<architecture/security>

TASK
Add failing regression test first,
then implement minimal fix.
```

---

# 119. Refactoring Prompt Template

```text
OBJECTIVE
Refactor <component>.

BEHAVIOR
Must remain unchanged.

SCOPE
<files>

REQUIRED
Existing tests must remain green.
Add characterization tests if needed.

DO NOT
Change public contracts unless explicitly requested.
```

---

# 120. Review Prompt Template

```text
Review this diff for:

correctness
architecture violations
security
financial risk
race conditions
error handling
missing tests
unintended changes

Do not rewrite code unless requested.
Return findings by severity.
```

---

# 121. Severity Levels

Pour les reviews :

```text
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

---

# 122. Critical Finding

Exemples :

```text
possible duplicate live order
risk limit bypass
secret exposure
future-data leakage
```

---

# 123. High Finding

Exemples :

```text
incorrect financial calculation
missing idempotency
unsafe migration
```

---

# 124. Medium Finding

Exemples :

```text
weak error handling
missing edge-case test
performance concern
```

---

# 125. Review Evidence

Chaque finding doit préciser :

```text
file
location
problem
impact
recommended correction
```

---

# 126. No Invented Findings

Un reviewer IA doit distinguer :

```text
confirmed defect
potential risk
style preference
```

---

# 127. Multi-Agent Development

Plusieurs agents peuvent être utilisés avec des rôles séparés.

Exemple :

```text
Agent A: implementation
Agent B: tests
Agent C: review
```

---

# 128. Independent Reviewer

Pour les changements critiques, utiliser si possible un contexte de revue indépendant afin de réduire le biais de l'agent auteur.

---

# 129. Agent Handoff

Un handoff doit contenir :

```text
task
changes made
files touched
tests
known issues
open questions
```

---

# 130. Context Compression

Pour les longues sessions, maintenir un résumé structuré du projet plutôt que de dépendre de l'historique conversationnel entier.

---

# 131. Project Context File

Créer éventuellement :

```text
docs/AI_CONTEXT.md
```

contenant :

```text
architecture summary
critical invariants
current milestones
development commands
```

---

# 132. Context Freshness

Le contexte IA doit être mis à jour lorsque l'architecture change.

---

# 133. Repository Instructions

Le repository peut contenir un fichier d'instructions pour les agents.

Exemple :

```text
AGENTS.md
```

---

# 134. AGENTS.md

Doit résumer :

```text
how to build
how to test
architecture boundaries
coding rules
critical safety rules
```

---

# 135. Instruction Hierarchy

Les instructions locales d'un sous-dossier peuvent compléter les règles globales mais ne doivent pas contourner la sécurité.

---

# 136. Command Safety

Avant d'exécuter une commande destructive :

```text
rm
drop
reset
force push
```

l'agent doit vérifier explicitement son impact.

---

# 137. No Destructive Guessing

Si la cible d'une opération destructive est ambiguë :

```text
STOP
```

---

# 138. Git Safety

Interdire par défaut aux agents :

```text
force push main
delete remote branches blindly
rewrite shared history
```

---

# 139. Database Safety

Interdire par défaut :

```text
DROP production table
TRUNCATE production data
```

sans procédure explicitement approuvée.

---

# 140. Production Access

Les agents de développement ne doivent pas avoir besoin d'accès production pour écrire du code.

---

# 141. Environment Separation

Les commandes doivent identifier clairement l'environnement.

---

# 142. Dry Run

Pour les opérations sensibles, supporter :

```text
--dry-run
```

lorsque possible.

---

# 143. Backups

Une opération irréversible sur des données importantes doit vérifier l'existence d'une stratégie de sauvegarde.

---

# 144. Security Review Trigger

Une revue sécurité renforcée est nécessaire si le changement touche :

```text
authentication
authorization
secrets
network exposure
cryptography
external input
```

---

# 145. Risk Review Trigger

Une revue Risk Engine est nécessaire si le changement touche :

```text
position size
leverage
loss limits
portfolio exposure
trade eligibility
```

---

# 146. Execution Review Trigger

Une revue renforcée est nécessaire si le changement touche :

```text
order submission
cancel/replace
fill handling
reconciliation
```

---

# 147. Data Review Trigger

Une revue data est nécessaire si le changement touche :

```text
timestamp semantics
deduplication
normalization
historical data
```

---

# 148. AI Review Trigger

Une revue AI spécifique est nécessaire si le changement touche :

```text
model
prompt
agent tools
training dataset
automatic recommendations
```

---

# 149. Governance Review Trigger

Toute modification des permissions, gates ou workflows d'approbation doit être considérée comme sensible.

---

# 150. Incident-Driven Development

Après un incident :

```text
incident
↓
root cause
↓
corrective action
↓
regression test
↓
documentation
```

---

# 151. No Patch Without Cause

Éviter de corriger uniquement le symptôme si la cause structurelle est identifiable.

---

# 152. Postmortem Integration

Les actions de postmortem doivent être reliées aux commits ou tâches correspondantes.

---

# 153. Performance Optimization

Ne pas optimiser sans mesure.

---

# 154. Benchmark First

Avant optimisation :

```text
measure baseline
```

Après :

```text
measure candidate
```

---

# 155. Financial Optimization

Toute optimisation d'une stratégie doit passer par l'Experiment Registry.

---

# 156. No Parameter Fishing

Ne pas ajuster des paramètres jusqu'à obtenir un beau backtest sans enregistrer l'espace de recherche.

---

# 157. Reproducible Research Code

Les scripts de recherche importants doivent être versionnés.

---

# 158. Research vs Production

Le code de recherche peut être plus flexible.

Le code production doit respecter des standards plus stricts.

---

# 159. Promotion from Research

Un notebook prometteur ne devient pas un service production par copier-coller direct.

Il doit être réimplémenté ou industrialisé proprement.

---

# 160. Notebook Policy

Les notebooks sont adaptés à :

```text
exploration
visualization
experiments
```

pas à la logique métier production principale.

---

# 161. Documentation Style

Les documents Markdown doivent utiliser :

```text
clear headings
short sections
code blocks
explicit examples
```

---

# 162. Terminology

Utiliser les termes définis dans le glossaire QuantLab.

---

# 163. Naming

Les noms dans le code doivent correspondre au domaine.

Éviter :

```text
Manager2
HelperNew
ThingProcessor
```

---

# 164. Comments

Les commentaires doivent expliquer :

```text
why
```

plutôt que répéter :

```text
what
```

déjà visible dans le code.

---

# 165. Docstrings

Les interfaces publiques importantes doivent être documentées.

---

# 166. Complexity

Préférer des fonctions courtes et des responsabilités limitées.

---

# 167. Clever Code

Éviter le code inutilement astucieux.

Le système devra être compris pendant un incident, probablement à un moment où personne n'a envie d'admirer une prouesse syntaxique.

---

# 168. Explicitness

Dans les chemins financiers critiques :

```text
explicit > magical
```

---

# 169. State Machines

Les workflows complexes doivent utiliser des états explicites.

Exemples :

```text
order lifecycle
strategy lifecycle
governance proposal
model promotion
```

---

# 170. Impossible States

Concevoir les modèles pour rendre les états invalides difficiles à représenter.

---

# 171. Validation at Boundaries

Valider les inputs :

```text
API
event bus
external provider
database deserialization
AI output
```

---

# 172. Internal Trust

Une fois les données validées, éviter de répéter inutilement la même validation partout.

---

# 173. Serialization

Les schémas sérialisés doivent être versionnés.

---

# 174. Backward Compatibility

Les consommateurs existants doivent être pris en compte avant modification.

---

# 175. Deprecation

Une interface obsolète doit avoir :

```text
deprecation notice
migration path
removal plan
```

---

# 176. Feature Flags

Les nouvelles fonctionnalités risquées peuvent être protégées par feature flag.

---

# 177. Feature Flag Governance

Les flags production doivent être versionnés et audités.

---

# 178. Dark Launch

Un nouveau composant peut recevoir du trafic sans influencer les décisions afin de mesurer son comportement.

---

# 179. Shadow Comparison

Comparer :

```text
current implementation
vs
candidate implementation
```

sur les mêmes inputs.

---

# 180. Rollback Readiness

Avant promotion :

```text
can we revert quickly?
```

Si la réponse est non, le changement nécessite une prudence supérieure.

---

# 181. Change Budget

Éviter les déploiements contenant trop de changements critiques simultanés.

---

# 182. Blast Radius

Chaque changement doit évaluer son rayon d'impact.

---

# 183. Progressive Rollout

Lorsque possible :

```text
test
→ shadow
→ limited
→ full
```

---

# 184. AI Model Change

Changer de modèle LLM peut modifier le comportement même si le prompt reste identique.

Cela doit être traité comme une modification versionnée.

---

# 185. Prompt Change

Même règle pour les prompts.

---

# 186. Evaluation Before AI Promotion

Une nouvelle version d'agent doit passer une suite d'évaluation avant promotion.

---

# 187. AI Regression Suite

Conserver des cas de référence pour :

```text
tool selection
schema compliance
grounding
security boundaries
```

---

# 188. Prompt Injection Tests

Tester les agents exposés à du contenu externe.

---

# 189. Tool Permission Tests

Vérifier qu'un agent ne peut appeler que les outils autorisés.

---

# 190. Hallucination Tests

Inclure des cas où l'information nécessaire est absente.

Résultat attendu :

```text
uncertainty / request evidence
```

et non invention.

---

# 191. Evidence Tests

Une recommandation doit pointer vers des sources réelles.

---

# 192. AI Failure Handling

Si un agent échoue :

```text
record failure
do not silently fabricate completion
```

---

# 193. Partial Completion

L'agent doit distinguer :

```text
completed
partially completed
blocked
```

---

# 194. No False Success

Une commande qui échoue ne doit pas être présentée comme réussie.

---

# 195. Verification

Après une modification, vérifier effectivement :

```text
files changed
tests executed
result
```

---

# 196. Evidence of Completion

Une tâche technique doit idéalement produire :

```text
diff
test output
build result
```

---

# 197. Development Audit

Pour les composants critiques, conserver :

```text
author
reviewer
commit
tests
approval
```

---

# 198. AI Run Metadata

Pour les workflows importants :

```text
agent
model
prompt/instructions version
timestamp
task
```

peuvent être conservés.

---

# 199. Cost Discipline

L'usage de modèles plus coûteux doit être justifié par la complexité de la tâche.

---

# 200. Model Selection

Utiliser :

```text
small/fast model
```

pour les tâches mécaniques et :

```text
strong reasoning model
```

pour les tâches architecturales ou critiques.

---

# 201. Parallel Agents

Le parallélisme est utile pour les tâches indépendantes.

Il devient dangereux lorsque plusieurs agents modifient simultanément les mêmes contrats.

---

# 202. Ownership Lock

Pour des modifications concurrentes, attribuer clairement les fichiers ou composants.

---

# 203. Merge Coordination

Les changements parallèles doivent être intégrés avec une revue des interactions.

---

# 204. Architectural Review

Avant une nouvelle abstraction majeure, vérifier :

```text
does the architecture already solve this?
is the abstraction necessary?
what dependency does it introduce?
```

---

# 205. YAGNI

Ne pas construire aujourd'hui une infrastructure gigantesque pour une possibilité théorique de 2029.

---

# 206. Extensibility

À l'inverse, les frontières importantes doivent permettre l'évolution sans réécriture totale.

---

# 207. Simplicity Rule

À fonctionnalité et sécurité équivalentes :

```text
simpler design wins
```

---

# 208. Production Standard

Le code production doit être :

```text
understandable
testable
observable
recoverable
secure
```

avant d'être sophistiqué.

---

# 209. AI Coding Workflow

Workflow standard :

```text
1. Read specification
2. Inspect repository
3. Define scope
4. Identify invariants
5. Plan
6. Add/update tests
7. Implement minimal change
8. Run targeted tests
9. Run broader tests
10. Review diff
11. Check architecture
12. Check security/risk
13. Update documentation
14. Submit for review
```

---

# 210. AI Review Workflow

```text
1. Read task
2. Read relevant specification
3. Inspect diff
4. Identify changed behavior
5. Check invariants
6. Check tests
7. Check failure paths
8. Check security
9. Check financial risk
10. Report findings by severity
```

---

# 211. Bug Workflow

```text
1. Reproduce
2. Create failing test
3. Identify root cause
4. Implement minimal fix
5. Pass regression test
6. Run related suite
7. Review side effects
```

---

# 212. New Feature Workflow

```text
specification
↓
contract
↓
tests
↓
implementation
↓
integration
↓
observability
↓
documentation
↓
governance
```

---

# 213. Critical Change Workflow

Pour :

```text
risk
execution
security
governance
```

ajouter :

```text
independent review
failure testing
rollback verification
explicit approval
```

---

# 214. AI-Generated Architecture

Une architecture proposée par IA doit être évaluée contre :

```text
requirements
failure modes
operational complexity
security
maintainability
```

avant adoption.

---

# 215. No Authority by Eloquence

Une proposition très bien rédigée reste une proposition.

La qualité littéraire d'un agent n'est pas une métrique d'architecture.

---

# 216. Documentation Synchronization

Après chaque milestone, vérifier que :

```text
docs
code
tests
configuration
```

décrivent toujours le même système.

---

# 217. Drift Detection

Les divergences documentation/code doivent être traitées comme de la dette technique.

---

# 218. Definition of Ready

Une tâche est prête pour implémentation lorsque :

```text
objective clear
scope clear
contract known
dependencies known
acceptance criteria defined
```

---

# 219. Blocked Task

Si une information critique manque, l'agent doit signaler le blocage plutôt qu'inventer le contrat.

---

# 220. Assumptions

Toute hypothèse nécessaire doit être explicitée.

---

# 221. Assumption Validation

Les hypothèses qui affectent l'architecture ou le risque doivent être validées avant implémentation.

---

# 222. Temporary Decisions

Une décision temporaire doit être marquée et suivie.

---

# 223. Technical Debt

La dette volontaire doit être documentée.

---

# 224. No Invisible Debt

Ne pas simplifier silencieusement une exigence en espérant que quelqu'un s'en aperçoive plus tard.

---

# 225. Engineering Metrics

Mesures possibles :

```text
CI success rate
test duration
deployment frequency
rollback rate
escaped defects
mean time to recovery
```

---

# 226. AI Development Metrics

Mesures possibles :

```text
AI-generated changes accepted
review findings
regression rate
rework rate
```

L'objectif n'est pas de maximiser le pourcentage de code écrit par IA.

---

# 227. Quality Over Generated Volume

Une IA capable de générer 10 000 lignes par heure n'améliore pas le projet si 8 000 lignes n'auraient jamais dû exister.

---

# 228. V1 Mandatory Rules

Dès la V1 :

- read specification before coding ;
- small scoped tasks ;
- minimal changes ;
- typed domain contracts ;
- UTC timestamps ;
- no secrets in code ;
- tests required ;
- regression tests for bugs ;
- CI required ;
- review required for critical code ;
- no AI production credentials ;
- no direct AI deployment ;
- no self-approval ;
- structured error handling ;
- explicit observability ;
- Git history preserved ;
- documentation updated with contract changes.

---

# 229. V2

Ajouter :

- automated architecture checks ;
- dependency policies ;
- stronger static analysis ;
- AI evaluation harness ;
- prompt registry ;
- automated ADR checks ;
- advanced security scanning.

---

# 230. V3

Ajouter :

- multi-agent review workflows ;
- automatic specification-to-test validation ;
- policy-as-code enforcement ;
- automated documentation drift detection ;
- AI-assisted incident remediation proposals.

---

# 231. V4

Ajouter :

- controlled autonomous development loops ;
- automatic candidate implementation ;
- independent AI review ;
- automated test generation ;
- shadow deployment proposal ;
- governance-controlled promotion.

---

# 232. Critères d'acceptation

Le protocole est correctement appliqué lorsque :

- un agent peut identifier les documents de référence ;
- les tâches sont limitées en scope ;
- les changements critiques disposent de tests ;
- les bugs créent des tests de régression ;
- les agents ne disposent pas de secrets live ;
- les outputs IA automatisés sont validés ;
- les changements architecturaux sont documentés ;
- les dépendances sont contrôlées ;
- les migrations sont versionnées ;
- les diffs sont revus ;
- les commandes destructrices ne sont pas exécutées aveuglément ;
- chaque build peut être relié à un commit ;
- le code, les tests et les documents restent cohérents ;
- les modifications live passent par le Governance Engine.

---

# 233. Règle fondatrice

> **L'IA doit réduire le temps nécessaire pour produire du code fiable, pas réduire le niveau de preuve nécessaire pour considérer ce code comme fiable.**

QuantLab doit utiliser l'IA comme multiplicateur de capacité d'ingénierie.

La boucle recherchée est :

```text
SPECIFY
↓
IMPLEMENT
↓
TEST
↓
REVIEW
↓
VERIFY
↓
GOVERN
↓
DEPLOY
```

et jamais :

```text
PROMPT
↓
CODE
↓
PRODUCTION
```

---

# 234. Statut

**Version : 1.0**

Documents directement liés :

- `01-Vision-du-Projet.md`
- `02-Architecture-Generale.md`
- `13-Monitoring-Engine.md`
- `15-AI-and-Learning-Engine.md`
- `16-Governance-Engine.md`
- `18-Testing-Strategy.md`
- `19-Deployment-Guide.md`
- `20-Engineering-Principles.md`
- `21-Experiment-Registry.md`
- `22-API-Specification.md`
- `23-Database-Schema.md`
- `24-Security.md`
- `25-Roadmap.md`

**Prochain document : `18-Testing-Strategy.md`**
