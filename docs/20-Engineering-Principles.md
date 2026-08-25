# 20 --- Engineering Principles

**Projet : QuantLab**\
**Document : Engineering Principles**\
**Version : 1.0**\
**Statut : Principes d'ingénierie fondamentaux**

------------------------------------------------------------------------

# 1. Objectif

Ce document définit les principes techniques qui doivent guider toutes
les décisions d'ingénierie de QuantLab.

Ces principes servent de cadre lorsque :

-   plusieurs architectures sont possibles ;
-   une spécification est ambiguë ;
-   une nouvelle fonctionnalité est proposée ;
-   un compromis performance / complexité apparaît ;
-   une décision doit être prise rapidement ;
-   un agent IA génère ou modifie du code ;
-   une dette technique doit être évaluée.

La règle générale est :

> **QuantLab doit optimiser en priorité la fiabilité, la traçabilité, la
> maîtrise du risque et la capacité d'évolution, pas la quantité de
> fonctionnalités ni la sophistication apparente.**

------------------------------------------------------------------------

# 2. Ordre des priorités

En cas de conflit, l'ordre de priorité recommandé est :

``` text
1. CAPITAL SAFETY
2. DATA INTEGRITY
3. CORRECTNESS
4. SECURITY
5. OBSERVABILITY
6. REPRODUCIBILITY
7. MAINTAINABILITY
8. PERFORMANCE
9. DEVELOPMENT SPEED
10. CONVENIENCE
```

Une optimisation de latence ne justifie pas de contourner une règle de
risque.

Une accélération du développement ne justifie pas de supprimer les
tests.

------------------------------------------------------------------------

# 3. Safety First

Toute décision technique doit commencer par la question :

``` text
What happens if this component is wrong?
```

Plus l'impact potentiel est élevé, plus le niveau de preuve requis doit
être important.

------------------------------------------------------------------------

# 4. Fail Closed

Lorsqu'une information nécessaire à une nouvelle exposition est inconnue
:

``` text
DO NOT TRADE
```

Exemples :

``` text
risk engine unavailable
market data stale
position state unknown
configuration invalid
```

------------------------------------------------------------------------

# 5. Risk Reduction Must Remain Possible

Un état dégradé ne doit pas empêcher les actions destinées à réduire le
risque lorsque celles-ci sont sûres.

------------------------------------------------------------------------

# 6. Capital Is a Production Dependency

Le capital réel doit être traité comme une ressource critique.

Le système ne doit jamais utiliser le marché live comme environnement de
test par défaut.

------------------------------------------------------------------------

# 7. Deterministic Core

Les chemins critiques doivent rester aussi déterministes que possible :

``` text
market state
→ scoring
→ decision
→ risk
→ execution intent
```

------------------------------------------------------------------------

# 8. AI Outside the Hard Safety Boundary

Les modèles IA peuvent :

``` text
analyze
research
suggest
classify
summarize
```

mais les contraintes de sécurité critiques doivent rester vérifiables
par du code déterministe.

------------------------------------------------------------------------

# 9. Explicit Over Implicit

Préférer :

``` text
explicit state
explicit configuration
explicit permissions
explicit contracts
```

aux comportements implicites.

------------------------------------------------------------------------

# 10. No Hidden Magic

Une fonction critique ne doit pas modifier silencieusement :

``` text
risk
position
configuration
global state
```

sans contrat clair.

------------------------------------------------------------------------

# 11. Simple Systems Win

À sécurité et fonctionnalité équivalentes :

``` text
simpler architecture > more sophisticated architecture
```

------------------------------------------------------------------------

# 12. Complexity Has a Cost

Chaque abstraction ajoute :

``` text
maintenance
failure modes
debugging cost
learning cost
```

Elle doit donc justifier son existence.

------------------------------------------------------------------------

# 13. YAGNI

Ne pas construire une infrastructure complexe uniquement parce qu'elle
pourrait devenir utile un jour.

------------------------------------------------------------------------

# 14. Build for Evolution, Not Prediction

Prévoir des interfaces propres et des frontières stables.

Ne pas essayer de prédire toutes les fonctionnalités futures.

------------------------------------------------------------------------

# 15. Modular Architecture

QuantLab doit rester composé de moteurs aux responsabilités distinctes.

------------------------------------------------------------------------

# 16. Single Responsibility

Chaque module doit avoir une raison principale de changer.

------------------------------------------------------------------------

# 17. Clear Boundaries

Exemples :

``` text
Scoring Engine scores
Decision Engine decides
Risk Engine authorizes risk
Execution Engine executes
```

------------------------------------------------------------------------

# 18. No Boundary Bypass

Aucun module ne doit contourner une frontière critique pour gagner
quelques lignes de code.

------------------------------------------------------------------------

# 19. Dependency Direction

Les dépendances doivent suivre une direction architecturale explicite.

------------------------------------------------------------------------

# 20. Loose Coupling

Les composants doivent connaître le minimum nécessaire sur leurs
voisins.

------------------------------------------------------------------------

# 21. High Cohesion

Les responsabilités liées doivent rester regroupées.

------------------------------------------------------------------------

# 22. Contracts Before Implementations

Définir :

``` text
inputs
outputs
errors
invariants
```

avant d'optimiser l'implémentation.

------------------------------------------------------------------------

# 23. Stable Interfaces

Les interfaces critiques doivent évoluer plus lentement que leurs
implémentations.

------------------------------------------------------------------------

# 24. Typed Domain Models

Utiliser des modèles métier explicites pour les objets critiques.

------------------------------------------------------------------------

# 25. Domain Language

Le code doit utiliser le vocabulaire métier QuantLab.

------------------------------------------------------------------------

# 26. Avoid Generic Names

Éviter :

``` text
Manager
Helper
Processor
Thing
Data2
```

lorsqu'un nom métier précis existe.

------------------------------------------------------------------------

# 27. Make Invalid States Difficult

Les modèles doivent réduire la possibilité de représenter des états
impossibles.

------------------------------------------------------------------------

# 28. Immutability Where Valuable

Les événements historiques et décisions doivent être immutables lorsque
possible.

------------------------------------------------------------------------

# 29. IDs Everywhere They Matter

Les objets distribués doivent disposer d'identifiants stables.

------------------------------------------------------------------------

# 30. End-to-End Lineage

Le système doit pouvoir reconstruire :

``` text
market data
→ analysis
→ score
→ decision
→ risk
→ order
→ fill
→ position
```

------------------------------------------------------------------------

# 31. Time Is a First-Class Concept

Tous les composants doivent traiter explicitement :

``` text
event time
processing time
freshness
ordering
```

------------------------------------------------------------------------

# 32. UTC Internally

Tous les timestamps internes doivent être en UTC et timezone-aware.

------------------------------------------------------------------------

# 33. Never Assume Ordering

Les systèmes distribués doivent tolérer ou détecter :

``` text
duplicate events
late events
out-of-order events
```

------------------------------------------------------------------------

# 34. Idempotency by Design

Toute opération susceptible d'être rejouée doit être idempotente lorsque
nécessaire.

------------------------------------------------------------------------

# 35. At-Least-Once Reality

Les systèmes de messages peuvent livrer plusieurs fois.

Le système métier doit survivre à cette réalité peu glamour.

------------------------------------------------------------------------

# 36. Data Is a Product

Les données doivent avoir :

``` text
schema
quality rules
ownership
version
lineage
```

------------------------------------------------------------------------

# 37. Raw Data Preservation

Lorsque possible, conserver les données brutes nécessaires à la
reconstruction.

------------------------------------------------------------------------

# 38. Derived Data Must Be Rebuildable

Les données dérivées doivent idéalement pouvoir être recalculées depuis
des sources versionnées.

------------------------------------------------------------------------

# 39. Point-in-Time Correctness

Aucune analyse historique ne doit utiliser des informations
indisponibles au moment simulé.

------------------------------------------------------------------------

# 40. No Silent Data Repair

Toute correction de données importante doit être identifiable.

------------------------------------------------------------------------

# 41. Data Validation at Boundaries

Valider les données dès leur entrée dans le système.

------------------------------------------------------------------------

# 42. Trust but Verify External Data

Une API externe qui retourne HTTP 200 n'a pas nécessairement retourné
une donnée correcte. L'optimisme n'est pas un validateur de schéma.

------------------------------------------------------------------------

# 43. Numeric Correctness

Les valeurs financières doivent utiliser une représentation adaptée.

------------------------------------------------------------------------

# 44. Avoid Unsafe Floating-Point Assumptions

Pour les calculs monétaires critiques, préférer :

``` text
Decimal
integer ticks
integer smallest units
```

selon le contexte.

------------------------------------------------------------------------

# 45. Units Must Be Explicit

Ne jamais laisser ambigu :

``` text
percent
basis points
fraction
currency
contracts
shares
```

------------------------------------------------------------------------

# 46. Precision Is Part of the Contract

Les règles d'arrondi doivent être définies.

------------------------------------------------------------------------

# 47. Configuration Is Code

Les configurations critiques doivent être :

``` text
versioned
validated
reviewed
auditable
```

------------------------------------------------------------------------

# 48. No Magic Numbers

Les paramètres métier doivent avoir un nom et une origine.

------------------------------------------------------------------------

# 49. Defaults Must Be Safe

Un paramètre absent ne doit pas automatiquement produire une
configuration plus risquée.

------------------------------------------------------------------------

# 50. Environment-Specific Configuration

Séparer :

``` text
test
paper
shadow
production
```

------------------------------------------------------------------------

# 51. Secrets Are Not Configuration

Les secrets doivent être gérés séparément.

------------------------------------------------------------------------

# 52. Least Privilege

Chaque service et agent doit disposer uniquement des permissions
nécessaires.

------------------------------------------------------------------------

# 53. Zero Trust Between Critical Boundaries

Les inputs externes ou provenant de zones moins fiables doivent être
validés.

------------------------------------------------------------------------

# 54. Security by Design

La sécurité doit être intégrée dès l'architecture.

------------------------------------------------------------------------

# 55. No Secret in Git

Jamais.

------------------------------------------------------------------------

# 56. No Secret in Logs

Jamais non plus. Deux interdictions, parce que l'humanité a
manifestement besoin des deux.

------------------------------------------------------------------------

# 57. Authentication Is Not Authorization

Savoir qui appelle un service ne signifie pas qu'il a le droit
d'effectuer l'action.

------------------------------------------------------------------------

# 58. Explicit Authorization

Les actions sensibles doivent vérifier les permissions.

------------------------------------------------------------------------

# 59. Defense in Depth

Ne pas dépendre d'un unique contrôle de sécurité.

------------------------------------------------------------------------

# 60. Audit Critical Actions

Toute action importante doit laisser une trace.

------------------------------------------------------------------------

# 61. Observability Is a Feature

Un composant qui fonctionne mais dont personne ne peut comprendre l'état
n'est pas terminé.

------------------------------------------------------------------------

# 62. Structured Logging

Les logs doivent être structurés et corrélables.

------------------------------------------------------------------------

# 63. Metrics by Design

Définir les métriques importantes avant production.

------------------------------------------------------------------------

# 64. Health Is Not Binary

Distinguer :

``` text
alive
ready
degraded
halted
```

------------------------------------------------------------------------

# 65. Alert on Actionable Conditions

Une alerte doit correspondre à une action potentielle.

------------------------------------------------------------------------

# 66. Avoid Alert Fatigue

Une alerte ignorée quotidiennement n'est plus une alerte.

------------------------------------------------------------------------

# 67. Correlation IDs

Les workflows distribués doivent être corrélables.

------------------------------------------------------------------------

# 68. Deployment Markers

Les changements de version doivent apparaître dans l'observabilité.

------------------------------------------------------------------------

# 69. Reproducibility

Une décision historique doit pouvoir être reconstruite autant que
possible.

------------------------------------------------------------------------

# 70. Version Everything That Changes Behavior

Versionner :

``` text
code
strategy
configuration
model
prompt
schema
risk policy
dataset
```

------------------------------------------------------------------------

# 71. Immutable Artifacts

Un artefact publié ne doit pas changer.

------------------------------------------------------------------------

# 72. Same Inputs, Same Outputs

Pour les composants déterministes :

``` text
same version
same config
same input
=
same output
```

------------------------------------------------------------------------

# 73. Controlled Randomness

Lorsque la randomisation est nécessaire :

``` text
seed
record
reproduce
```

------------------------------------------------------------------------

# 74. Research Must Be Reproducible

Un résultat quantitatif sans dataset/version/configuration connue ne
constitue pas une preuve exploitable.

------------------------------------------------------------------------

# 75. Testing Is Part of Design

Les tests ne sont pas une phase finale.

------------------------------------------------------------------------

# 76. Test Behavior, Not Implementation Trivia

Tester ce que le composant garantit.

------------------------------------------------------------------------

# 77. Bugs Become Regression Tests

Chaque bug important doit enrichir la suite.

------------------------------------------------------------------------

# 78. Test Failure Modes

Les chemins d'erreur doivent être testés explicitement.

------------------------------------------------------------------------

# 79. Test Boundaries

Les bugs vivent souvent aux frontières :

``` text
network
database
serialization
time
concurrency
```

------------------------------------------------------------------------

# 80. Property Tests for Invariants

Les invariants critiques méritent des tests génératifs.

------------------------------------------------------------------------

# 81. Replay Is a Core Capability

Le replay doit permettre de vérifier les changements sur des scénarios
connus.

------------------------------------------------------------------------

# 82. Backtest Is Not Proof of Production Performance

Un backtest mesure une simulation historique sous hypothèses.

Il ne garantit pas le futur.

------------------------------------------------------------------------

# 83. Out-of-Sample Matters

Toute optimisation quantitative doit réserver des données réellement
hors optimisation.

------------------------------------------------------------------------

# 84. Robustness Over Peak Performance

Préférer une stratégie robuste sur plusieurs conditions à une stratégie
parfaite sur une fenêtre étroite.

------------------------------------------------------------------------

# 85. Parameter Stability

Un bon système ne doit pas dépendre d'un paramètre réglé au troisième
chiffre après la virgule.

------------------------------------------------------------------------

# 86. Costs Must Be Included

Les performances doivent intégrer :

``` text
fees
spread
slippage
```

------------------------------------------------------------------------

# 87. Execution Reality Matters

Une stratégie non exécutable n'est pas une stratégie rentable.

------------------------------------------------------------------------

# 88. Measure Before Optimize

Toute optimisation de performance doit commencer par une mesure.

------------------------------------------------------------------------

# 89. Benchmark Changes

Comparer avant / après.

------------------------------------------------------------------------

# 90. Optimize Bottlenecks

Ne pas optimiser les parties qui ne limitent rien.

------------------------------------------------------------------------

# 91. Latency Has a Budget

Chaque composant critique doit connaître son ordre de grandeur attendu.

------------------------------------------------------------------------

# 92. Predictable Performance

Une latence légèrement supérieure mais stable peut être préférable à une
latence moyenne faible avec de gros spikes.

------------------------------------------------------------------------

# 93. Backpressure

Les systèmes doivent gérer explicitement la surcharge.

------------------------------------------------------------------------

# 94. Bounded Resources

Éviter les queues, caches ou retries sans limite.

------------------------------------------------------------------------

# 95. Timeouts Everywhere External

Tout appel externe doit avoir un timeout.

------------------------------------------------------------------------

# 96. Retries Are Not Free

Les retries augmentent :

``` text
load
latency
duplication risk
```

------------------------------------------------------------------------

# 97. Retry Only When Safe

La politique de retry dépend de l'idempotence.

------------------------------------------------------------------------

# 98. Exponential Backoff

Utiliser lorsque pertinent pour les dépendances externes.

------------------------------------------------------------------------

# 99. Circuit Breakers

Peuvent être utilisés pour éviter de saturer une dépendance défaillante.

------------------------------------------------------------------------

# 100. Graceful Degradation

Les fonctionnalités secondaires doivent pouvoir échouer sans détruire le
cœur du système.

------------------------------------------------------------------------

# 101. Core Safety Independence

Le Risk Engine ne doit pas dépendre d'un service IA externe pour
appliquer une limite dure.

------------------------------------------------------------------------

# 102. Failure Isolation

Une panne locale doit avoir le plus petit blast radius possible.

------------------------------------------------------------------------

# 103. Bulkheads

Séparer les ressources lorsque la saturation d'un composant pourrait
affecter les autres.

------------------------------------------------------------------------

# 104. Recovery Is a Feature

Tout composant critique doit avoir une stratégie de récupération.

------------------------------------------------------------------------

# 105. Restart Safety

Un restart ne doit pas créer de double effet métier.

------------------------------------------------------------------------

# 106. Reconciliation

Les systèmes stateful doivent pouvoir comparer leur état avec la source
d'autorité externe.

------------------------------------------------------------------------

# 107. Database Is Not Always the World

Pour l'exécution live, l'exchange peut être l'autorité ultime sur :

``` text
orders
fills
positions
```

------------------------------------------------------------------------

# 108. Unknown State Is a Real State

Ne pas convertir arbitrairement :

``` text
UNKNOWN
```

en :

``` text
FAILED
```

ou :

``` text
SUCCESS
```

------------------------------------------------------------------------

# 109. State Machines for Complex Lifecycles

Utiliser des états explicites pour :

``` text
orders
strategies
models
governance proposals
deployments
```

------------------------------------------------------------------------

# 110. Valid Transitions Only

Les transitions doivent être vérifiées.

------------------------------------------------------------------------

# 111. Event-Driven Where It Helps

L'architecture événementielle est adaptée aux changements d'état et au
lineage.

------------------------------------------------------------------------

# 112. Do Not Event-Source Everything by Religion

Utiliser les patterns lorsqu'ils résolvent un problème réel.

Pas parce qu'un diagramme devient plus impressionnant.

------------------------------------------------------------------------

# 113. Synchronous When Simpler

Un appel synchrone est parfois préférable à trois queues et cinq
consumers.

------------------------------------------------------------------------

# 114. Async When Decoupling Matters

Utiliser l'asynchrone pour :

``` text
independent processing
fan-out
buffering
resilience
```

------------------------------------------------------------------------

# 115. Database Transactions

Utiliser des transactions lorsque plusieurs modifications doivent être
atomiques.

------------------------------------------------------------------------

# 116. Avoid Distributed Transactions Where Possible

Préférer :

``` text
idempotency
eventual consistency
reconciliation
```

lorsque cela convient.

------------------------------------------------------------------------

# 117. Eventual Consistency Must Be Explicit

Documenter ce qui peut être temporairement incohérent.

------------------------------------------------------------------------

# 118. Source of Truth

Chaque donnée critique doit avoir une source d'autorité définie.

------------------------------------------------------------------------

# 119. Cache Is Not Source of Truth

Un cache doit pouvoir être reconstruit.

------------------------------------------------------------------------

# 120. Derived State Must Be Recoverable

Éviter les états calculés impossibles à reconstruire.

------------------------------------------------------------------------

# 121. Database Schema Is an API

Un schéma partagé doit être traité avec le même soin qu'une API.

------------------------------------------------------------------------

# 122. Migrations Must Be Versioned

Toute modification de schéma doit être traçable.

------------------------------------------------------------------------

# 123. Backward Compatibility

Préférer les changements compatibles pendant les déploiements
progressifs.

------------------------------------------------------------------------

# 124. Expand Before Contract

Pour les migrations complexes :

``` text
expand
migrate
switch
contract
```

------------------------------------------------------------------------

# 125. API Design

Les APIs doivent être :

``` text
predictable
typed
versioned
consistent
```

------------------------------------------------------------------------

# 126. Errors Are Part of the API

Les erreurs doivent avoir :

``` text
code
message
context
```

------------------------------------------------------------------------

# 127. Stable Error Codes

Les machines doivent pouvoir réagir aux erreurs sans parser du texte
humain.

------------------------------------------------------------------------

# 128. Input Validation

Valider au bord du système.

------------------------------------------------------------------------

# 129. Output Validation

Valider les outputs provenant de composants non déterministes ou
externes.

------------------------------------------------------------------------

# 130. AI Output Is Untrusted Input

Toute réponse d'un modèle IA consommée par du code doit être traitée
comme une donnée externe non fiable.

------------------------------------------------------------------------

# 131. Structured AI Interfaces

Préférer des schémas structurés aux réponses libres pour
l'automatisation.

------------------------------------------------------------------------

# 132. Grounding

Une recommandation IA importante doit être liée à des données ou sources
identifiables.

------------------------------------------------------------------------

# 133. Uncertainty Must Be Representable

Le système doit permettre :

``` text
UNKNOWN
INSUFFICIENT_DATA
LOW_CONFIDENCE
```

------------------------------------------------------------------------

# 134. Do Not Force Decisions

L'absence de décision est parfois la meilleure décision.

------------------------------------------------------------------------

# 135. NO_TRADE Is a Valid Output

QuantLab doit considérer :

``` text
NO_TRADE
```

comme une décision de première classe.

------------------------------------------------------------------------

# 136. Abstention Over Fabrication

Si les données sont insuffisantes :

``` text
ABSTAIN
```

plutôt qu'inventer une certitude.

------------------------------------------------------------------------

# 137. Human Oversight Where Consequences Matter

Les changements augmentant significativement le risque doivent
nécessiter une approbation adaptée.

------------------------------------------------------------------------

# 138. Separation of Duties

Éviter qu'un même acteur puisse :

``` text
create
approve
deploy
```

un changement critique sans contrôle.

------------------------------------------------------------------------

# 139. AI Cannot Self-Approve

Un agent ne doit pas être son propre contrôleur final.

------------------------------------------------------------------------

# 140. Governance Must Be Enforced Technically

Une règle écrite mais contournable n'est qu'une suggestion.

------------------------------------------------------------------------

# 141. Policy as Code

Les politiques importantes doivent progressivement devenir exécutables.

------------------------------------------------------------------------

# 142. Emergency Paths Must Exist

Les procédures d'urgence doivent être prévues avant l'urgence.

------------------------------------------------------------------------

# 143. Emergency Does Not Mean Unlogged

Les actions break-glass doivent être auditées.

------------------------------------------------------------------------

# 144. Rollback Is Normal

Tout changement important doit avoir un plan de retour.

------------------------------------------------------------------------

# 145. Reversibility Is a Design Criterion

Entre deux solutions équivalentes, préférer celle qui peut être annulée
plus facilement.

------------------------------------------------------------------------

# 146. Small Changes

Les changements petits sont plus simples à :

``` text
review
test
deploy
rollback
```

------------------------------------------------------------------------

# 147. Atomic Commits

Un commit doit avoir une intention claire.

------------------------------------------------------------------------

# 148. Short-Lived Branches

Réduire les divergences longues.

------------------------------------------------------------------------

# 149. Continuous Integration

Intégrer souvent.

------------------------------------------------------------------------

# 150. Main Must Stay Healthy

La branche principale doit rester dans un état exploitable.

------------------------------------------------------------------------

# 151. Code Review Is Risk Management

La revue n'est pas un rituel social.

Elle sert à détecter :

``` text
incorrect assumptions
hidden coupling
security issues
missing tests
```

------------------------------------------------------------------------

# 152. Review the Diff

Le reviewer doit comprendre chaque changement important.

------------------------------------------------------------------------

# 153. No Drive-By Refactors

Ne pas mélanger des refactorings sans rapport dans une modification
ciblée.

------------------------------------------------------------------------

# 154. Refactor Under Tests

Renforcer les tests avant de modifier profondément une implémentation
stable.

------------------------------------------------------------------------

# 155. Delete Dead Code

Git conserve l'historique.

Le codebase n'a pas besoin de conserver des fossiles « au cas où ».

------------------------------------------------------------------------

# 156. Comments Explain Why

Le code explique généralement ce qu'il fait.

Les commentaires doivent expliquer pourquoi.

------------------------------------------------------------------------

# 157. Documentation Is Part of the System

Les documents d'architecture et contrats doivent rester synchronisés
avec le code.

------------------------------------------------------------------------

# 158. Documentation Drift Is Technical Debt

Une documentation fausse est parfois pire qu'une documentation absente.

------------------------------------------------------------------------

# 159. ADR for Important Decisions

Les décisions structurantes doivent être enregistrées.

------------------------------------------------------------------------

# 160. Record Alternatives

Un ADR doit expliquer les alternatives rejetées.

------------------------------------------------------------------------

# 161. Engineering Decisions Need Context

Une décision qui semble absurde deux ans plus tard peut avoir été
rationnelle dans son contexte.

Conserver ce contexte évite de réinventer les mêmes débats.

------------------------------------------------------------------------

# 162. Operational Simplicity

Le coût d'exploitation compte autant que le coût d'écriture.

------------------------------------------------------------------------

# 163. Minimize Moving Parts

Chaque service supplémentaire est :

``` text
another deployment
another dashboard
another failure mode
```

------------------------------------------------------------------------

# 164. Managed Services When Sensible

Utiliser des services managés lorsque cela réduit réellement le risque
opérationnel.

------------------------------------------------------------------------

# 165. Avoid Vendor Lock-In Paranoia

Ne pas créer dix couches d'abstraction inutiles pour pouvoir
hypothétiquement changer de fournisseur demain.

------------------------------------------------------------------------

# 166. Abstract Stable Concepts

Abstraire :

``` text
market data source
storage interface
execution venue
AI provider
```

lorsque plusieurs implémentations sont plausibles.

------------------------------------------------------------------------

# 167. Do Not Abstract Every Library

Une abstraction sans alternative réelle peut simplement déplacer la
complexité.

------------------------------------------------------------------------

# 168. Build vs Buy

Évaluer :

``` text
strategic value
security
cost
maintenance
control
```

------------------------------------------------------------------------

# 169. Build the Differentiation

QuantLab doit concentrer son ingénierie propriétaire sur ce qui crée
réellement son avantage.

------------------------------------------------------------------------

# 170. Buy Commodity Infrastructure

Ne pas reconstruire une base de données ou un système de métriques sans
raison sérieuse.

------------------------------------------------------------------------

# 171. Performance Must Serve the Strategy

La latence nécessaire dépend du style de trading.

------------------------------------------------------------------------

# 172. Avoid HFT Architecture Without HFT Need

Ne pas construire une infrastructure microseconde pour une stratégie qui
prend des décisions toutes les quinze minutes.

------------------------------------------------------------------------

# 173. Measure End-to-End Latency

Mesurer la chaîne complète :

``` text
market event
→ analysis
→ decision
→ risk
→ order submission
```

------------------------------------------------------------------------

# 174. Tail Latency Matters

Surveiller :

``` text
p95
p99
```

pas uniquement la moyenne.

------------------------------------------------------------------------

# 175. Capacity Headroom

Prévoir une marge pour les pics.

------------------------------------------------------------------------

# 176. Cost Awareness

Chaque composant doit considérer :

``` text
compute
storage
network
AI inference
data providers
```

------------------------------------------------------------------------

# 177. Optimize Cost After Visibility

Mesurer avant de réduire.

------------------------------------------------------------------------

# 178. AI Cost Governance

Les modèles coûteux doivent être utilisés lorsque leur gain est
justifié.

------------------------------------------------------------------------

# 179. Cache Expensive AI Work Carefully

Seulement lorsque les inputs et versions permettent une réutilisation
sûre.

------------------------------------------------------------------------

# 180. Research and Production Are Different

Le code de recherche privilégie la vitesse d'exploration.

Le code production privilégie la fiabilité.

------------------------------------------------------------------------

# 181. Promotion Requires Industrialization

Une idée de notebook doit être transformée en composant :

``` text
typed
tested
observable
versioned
```

avant production.

------------------------------------------------------------------------

# 182. Experiment Everything Important

Les changements quantitatifs doivent être traités comme des expériences.

------------------------------------------------------------------------

# 183. Hypothesis Before Result

Définir l'hypothèse avant d'observer les métriques lorsque possible.

------------------------------------------------------------------------

# 184. Record Negative Results

Les expériences ratées évitent de répéter les mêmes erreurs.

------------------------------------------------------------------------

# 185. Avoid P-Hacking

Ne pas tester suffisamment de variantes pour finir statistiquement par «
découvrir » quelque chose.

------------------------------------------------------------------------

# 186. Baselines Matter

Toute amélioration doit être comparée à une baseline.

------------------------------------------------------------------------

# 187. Simpler Baseline First

Avant un modèle complexe, tester une règle simple.

------------------------------------------------------------------------

# 188. Complexity Must Earn Its Keep

Un modèle plus complexe doit apporter une amélioration suffisamment
robuste pour justifier :

``` text
latency
maintenance
explainability cost
operational risk
```

------------------------------------------------------------------------

# 189. Explainability Where Needed

Les décisions financières critiques doivent pouvoir être expliquées
suffisamment pour l'audit et le debugging.

------------------------------------------------------------------------

# 190. Reason Codes

Les décisions importantes doivent produire des raisons structurées.

------------------------------------------------------------------------

# 191. Confidence Is Not Probability Unless Calibrated

Un score `0.9` ne signifie pas automatiquement 90 % de probabilité.

------------------------------------------------------------------------

# 192. Calibration Matters

Si un score est interprété probabilistiquement, sa calibration doit être
testée.

------------------------------------------------------------------------

# 193. Model Drift Is Expected

Le marché change.

Les modèles doivent être surveillés dans le temps.

------------------------------------------------------------------------

# 194. Strategy Decay Is Expected

Une stratégie rentable n'obtient pas un contrat à durée indéterminée
avec la réalité.

------------------------------------------------------------------------

# 195. Continuous Validation

Les stratégies et modèles doivent être revalidés après déploiement.

------------------------------------------------------------------------

# 196. Production Data Feeds Learning

Les observations production doivent enrichir :

``` text
monitoring
research
tests
experiments
```

------------------------------------------------------------------------

# 197. Incident Learning

Chaque incident doit améliorer le système.

------------------------------------------------------------------------

# 198. Blameless Technical Analysis

Chercher :

``` text
why system allowed failure
```

plutôt que simplement :

``` text
who clicked wrong button
```

------------------------------------------------------------------------

# 199. Human Error Is a Design Input

Si une erreur humaine est facile et catastrophique, l'interface ou le
processus est mal conçu.

------------------------------------------------------------------------

# 200. Automate Repetitive Safety

Automatiser :

``` text
checks
validation
deployments
reconciliation
```

lorsque cela réduit les erreurs.

------------------------------------------------------------------------

# 201. Do Not Automate Ambiguity

Une décision mal comprise ne devient pas meilleure parce qu'elle est
automatisée.

------------------------------------------------------------------------

# 202. Human Approval, Machine Execution

Pour les actions sensibles :

``` text
human decides
machine executes repeatably
```

est souvent le meilleur compromis.

------------------------------------------------------------------------

# 203. Operational Checklists

Les procédures critiques doivent utiliser des checklists.

------------------------------------------------------------------------

# 204. Runbooks

Les incidents prévisibles doivent avoir des procédures écrites.

------------------------------------------------------------------------

# 205. Test the Runbooks

Une procédure jamais testée reste théorique.

------------------------------------------------------------------------

# 206. Backups Must Be Restored

Tester les restaurations.

------------------------------------------------------------------------

# 207. Disaster Recovery Is Not a PDF

Un plan de reprise doit être exercé.

------------------------------------------------------------------------

# 208. Ownership

Chaque composant critique doit avoir un propriétaire identifiable.

------------------------------------------------------------------------

# 209. Ownership Includes Operations

Être propriétaire signifie aussi :

``` text
monitor
debug
maintain
document
```

------------------------------------------------------------------------

# 210. No Orphan Services

Un service sans propriétaire finit généralement par devenir un mystère
coûteux.

------------------------------------------------------------------------

# 211. Standards Should Be Automatable

Lorsque possible, transformer les standards en :

``` text
lint
CI
schema validation
policy checks
```

------------------------------------------------------------------------

# 212. Prefer Mechanical Enforcement

Une règle automatiquement vérifiée est plus fiable qu'une règle que
chacun doit se rappeler.

------------------------------------------------------------------------

# 213. Exceptions Must Be Explicit

Toute exception à un standard critique doit être :

``` text
documented
justified
approved
temporary when possible
```

------------------------------------------------------------------------

# 214. Technical Debt Must Be Visible

Enregistrer :

``` text
debt
impact
reason
priority
```

------------------------------------------------------------------------

# 215. Intentional Debt Is Sometimes Rational

Une solution temporaire peut être acceptable si son coût et sa durée
sont connus.

------------------------------------------------------------------------

# 216. Invisible Debt Is Dangerous

Une simplification cachée devient souvent une surprise production.

------------------------------------------------------------------------

# 217. Delete Complexity

La réduction de complexité est une amélioration légitime même sans
nouvelle fonctionnalité.

------------------------------------------------------------------------

# 218. Fewer Lines Can Be Better

La quantité de code n'est pas une mesure de progrès.

------------------------------------------------------------------------

# 219. Fewer Services Can Be Better

Même principe pour les microservices.

------------------------------------------------------------------------

# 220. Fewer Models Can Be Better

Même principe pour les modèles IA.

------------------------------------------------------------------------

# 221. Architecture Must Match Scale

Ne pas résoudre des problèmes de milliards d'événements si QuantLab en
traite des milliers.

------------------------------------------------------------------------

# 222. Design for Current Constraints

Mesurer la réalité actuelle.

------------------------------------------------------------------------

# 223. Keep Escape Hatches

Les interfaces doivent permettre l'évolution lorsque la réalité change.

------------------------------------------------------------------------

# 224. Progressive Sophistication

Ajouter la complexité lorsque les métriques prouvent qu'elle est
nécessaire.

------------------------------------------------------------------------

# 225. V1 Should Be Boring

Une bonne V1 doit être :

``` text
clear
testable
observable
safe
```

Même si elle n'impressionne personne sur un diagramme LinkedIn.

------------------------------------------------------------------------

# 226. Production Should Be Boring

Le comportement production doit être prévisible.

Les surprises sont acceptables en recherche, beaucoup moins avec du
capital.

------------------------------------------------------------------------

# 227. Debuggability

Concevoir pour comprendre rapidement :

``` text
what happened
when
why
with which version
```

------------------------------------------------------------------------

# 228. Failure Messages

Les erreurs doivent fournir assez de contexte pour agir.

------------------------------------------------------------------------

# 229. No Silent Failure

Une erreur importante ne doit jamais disparaître sans trace.

------------------------------------------------------------------------

# 230. No False Success

Un système ne doit pas déclarer une opération réussie avant confirmation
suffisante.

------------------------------------------------------------------------

# 231. Unknown Outcome Handling

Pour les actions externes :

``` text
UNKNOWN
→ reconcile
```

------------------------------------------------------------------------

# 232. Consistency Over Convenience

Ne pas mettre à jour localement un état critique uniquement pour rendre
l'UI plus agréable avant confirmation réelle.

------------------------------------------------------------------------

# 233. Eventual UI Optimism Is Separate

Les optimisations d'interface ne doivent pas contaminer l'état métier
réel.

------------------------------------------------------------------------

# 234. APIs Must Support Automation

Les opérations importantes doivent pouvoir être effectuées de manière
structurée et reproductible.

------------------------------------------------------------------------

# 235. CLI / Tooling

Les opérations techniques récurrentes peuvent disposer de commandes
dédiées.

------------------------------------------------------------------------

# 236. Dry Run

Les commandes sensibles devraient supporter un mode :

``` text
dry-run
```

lorsque possible.

------------------------------------------------------------------------

# 237. Confirmation for Destructive Operations

Les opérations destructrices doivent nécessiter une intention claire.

------------------------------------------------------------------------

# 238. Production Commands Must Be Obvious

Une commande production doit être difficile à confondre avec une
commande test.

------------------------------------------------------------------------

# 239. Safe Defaults in Tooling

Les outils internes doivent cibler par défaut un environnement non
production.

------------------------------------------------------------------------

# 240. Automation Identity

Toute automation doit utiliser une identité propre et auditable.

------------------------------------------------------------------------

# 241. AI Agent Identity

Chaque agent IA exécutant une action importante doit être identifiable.

------------------------------------------------------------------------

# 242. AI Permission Scope

Les agents doivent recevoir des permissions par tâche.

------------------------------------------------------------------------

# 243. AI Context Minimization

Donner à un agent uniquement le contexte nécessaire.

------------------------------------------------------------------------

# 244. AI Output Verification

Ne pas accepter une modification simplement parce qu'un modèle affirme
qu'elle est correcte.

------------------------------------------------------------------------

# 245. AI Review Independence

Pour les changements critiques, séparer autant que possible :

``` text
author agent
review agent
```

------------------------------------------------------------------------

# 246. AI Cannot Replace Tests

La confiance d'un modèle n'est pas une suite de tests.

------------------------------------------------------------------------

# 247. AI Cannot Replace Governance

Une recommandation IA n'est pas une approbation.

------------------------------------------------------------------------

# 248. AI Cannot Replace Measurement

Une explication plausible n'est pas une preuve quantitative.

------------------------------------------------------------------------

# 249. Engineering Evidence

Les décisions doivent s'appuyer sur :

``` text
tests
benchmarks
metrics
experiments
incidents
```

plutôt que sur des intuitions seules.

------------------------------------------------------------------------

# 250. State Assumptions Explicitly

Lorsqu'une décision dépend d'une hypothèse, l'écrire.

------------------------------------------------------------------------

# 251. Challenge Assumptions

Chercher activement :

``` text
what could make this false?
```

------------------------------------------------------------------------

# 252. Prefer Falsifiable Claims

Une hypothèse doit pouvoir être invalidée par des données.

------------------------------------------------------------------------

# 253. Separate Fact from Hypothesis

Dans les documents :

``` text
FACT
HYPOTHESIS
DECISION
UNKNOWN
```

doivent être distinguables.

------------------------------------------------------------------------

# 254. Avoid Confirmation Bias

Les analyses doivent chercher les preuves contraires.

------------------------------------------------------------------------

# 255. Record Rejected Alternatives

Cela réduit le risque de refaire le même débat six mois plus tard.

------------------------------------------------------------------------

# 256. Decisions Can Be Revisited

Un ADR n'est pas une loi physique.

Il doit pouvoir être remplacé lorsqu'une nouvelle réalité le justifie.

------------------------------------------------------------------------

# 257. Optimize for Learning Early

Au début du projet, privilégier les architectures permettant d'apprendre
rapidement sans compromettre la sécurité.

------------------------------------------------------------------------

# 258. Optimize for Stability Later

À mesure que le système devient critique, augmenter :

``` text
governance
testing
operational discipline
```

------------------------------------------------------------------------

# 259. Scale Controls with Risk

Les contrôles doivent augmenter avec :

``` text
capital
automation
complexity
number of users
```

------------------------------------------------------------------------

# 260. No Premature Autonomy

L'autonomie doit être accordée progressivement.

------------------------------------------------------------------------

# 261. Observe Before Automate

Une action devrait être observée manuellement ou en shadow avant
automatisation complète lorsque le risque le justifie.

------------------------------------------------------------------------

# 262. Automate After Understanding

Automatiser un processus mal compris crée simplement des erreurs plus
rapides.

------------------------------------------------------------------------

# 263. Reversibility Before Autonomy

Une fonction autonome doit disposer d'un mécanisme d'arrêt et de
rollback.

------------------------------------------------------------------------

# 264. Kill Switch Is Mandatory

Toute capacité live importante doit pouvoir être désactivée.

------------------------------------------------------------------------

# 265. Kill Switch Must Be Tested

Un bouton rouge décoratif ne compte pas.

------------------------------------------------------------------------

# 266. Kill Switch Must Be Independent

Autant que possible, il ne doit pas dépendre du composant qu'il doit
arrêter.

------------------------------------------------------------------------

# 267. Risk Limits Must Be Hard

Les limites critiques ne doivent pas être de simples recommandations.

------------------------------------------------------------------------

# 268. Risk Overrides Must Be Harder Than Normal Actions

Augmenter une limite doit être plus difficile que réduire le risque.

------------------------------------------------------------------------

# 269. No Strategy Above Risk

Aucune stratégie n'a autorité pour contourner le Risk Engine.

------------------------------------------------------------------------

# 270. No AI Above Risk

Même règle pour l'IA.

------------------------------------------------------------------------

# 271. No Operator Above Audit

Même une action humaine privilégiée doit laisser une trace.

------------------------------------------------------------------------

# 272. Market Reality Wins

Lorsque :

``` text
model
documentation
expectation
```

contredisent les observations réelles, il faut enquêter.

Le marché n'est pas obligé de respecter notre architecture.

------------------------------------------------------------------------

# 273. Execution Truth Wins

Pour les ordres live, l'état confirmé par l'exchange doit être
réconcilié avec l'état interne.

------------------------------------------------------------------------

# 274. Measurement Truth Wins

Une optimisation théorique qui dégrade les métriques réelles doit être
remise en cause.

------------------------------------------------------------------------

# 275. Operational Reality Wins

Une architecture élégante mais impossible à exploiter correctement est
une mauvaise architecture.

------------------------------------------------------------------------

# 276. Developer Experience Matters

Les workflows doivent rester simples pour réduire les erreurs.

------------------------------------------------------------------------

# 277. One Command for Common Tasks

Lorsque possible :

``` text
test
lint
run
build
```

doivent être facilement exécutables.

------------------------------------------------------------------------

# 278. Fast Feedback

Les développeurs doivent obtenir rapidement les erreurs simples.

------------------------------------------------------------------------

# 279. Local Reproducibility

Un problème CI doit pouvoir être reproduit localement autant que
possible.

------------------------------------------------------------------------

# 280. Development Environment Documentation

Les étapes de setup doivent être documentées.

------------------------------------------------------------------------

# 281. No Tribal Knowledge

Une procédure critique connue uniquement d'une personne est une
dépendance cachée.

------------------------------------------------------------------------

# 282. Onboarding Through Documentation

Un ingénieur ou agent doit pouvoir comprendre progressivement le système
via le repository.

------------------------------------------------------------------------

# 283. Repository as Knowledge Base

Le repository doit contenir les connaissances nécessaires pour
construire, tester et exploiter le système.

------------------------------------------------------------------------

# 284. Documentation Hierarchy

Structure recommandée :

``` text
vision
architecture
component specifications
ADRs
API/schema
runbooks
checklists
```

------------------------------------------------------------------------

# 285. Code and Docs Together

Une modification contractuelle doit mettre à jour les deux.

------------------------------------------------------------------------

# 286. Naming Consistency

Les mêmes concepts doivent avoir les mêmes noms dans :

``` text
code
database
API
documentation
monitoring
```

------------------------------------------------------------------------

# 287. Avoid Synonym Drift

Ne pas appeler le même concept :

``` text
trade intent
signal order
candidate trade
```

dans trois modules différents sans raison.

------------------------------------------------------------------------

# 288. Standard Error Taxonomy

Les erreurs métier importantes doivent être standardisées.

------------------------------------------------------------------------

# 289. Standard Status Taxonomy

Les états importants doivent être définis centralement.

------------------------------------------------------------------------

# 290. Standard Reason Codes

Les décisions de rejet doivent utiliser des reason codes structurés.

------------------------------------------------------------------------

# 291. Compatibility Is a Feature

Les changements doivent considérer les consommateurs existants.

------------------------------------------------------------------------

# 292. Deprecate Before Remove

Lorsque possible :

``` text
announce
support transition
remove
```

------------------------------------------------------------------------

# 293. Version Breaking Contracts

Les breaking changes doivent être explicites.

------------------------------------------------------------------------

# 294. Avoid Permanent Compatibility Layers

Les anciennes interfaces doivent avoir une date ou condition de retrait.

------------------------------------------------------------------------

# 295. Cost of Change

Une bonne architecture réduit le coût des changements futurs sans
sur-construire le présent.

------------------------------------------------------------------------

# 296. Local Reasoning

Un ingénieur doit pouvoir comprendre un module sans charger mentalement
tout QuantLab.

------------------------------------------------------------------------

# 297. Global Invariants

Quelques règles globales doivent toutefois rester universelles :

``` text
risk
security
time
identity
audit
```

------------------------------------------------------------------------

# 298. Architecture Fitness Functions

À terme, automatiser la vérification de certaines règles :

``` text
forbidden dependencies
required schemas
security boundaries
```

------------------------------------------------------------------------

# 299. Governance Fitness Functions

Automatiser les règles telles que :

``` text
no production deployment without approval
no risk increase without required role
```

------------------------------------------------------------------------

# 300. Engineering Review Questions

Avant d'accepter une solution :

``` text
Is it correct?
Is it safe?
Is it observable?
Is it testable?
Is it reversible?
Is it simpler than the alternatives?
Does it preserve architectural boundaries?
Can we explain its failure modes?
```

------------------------------------------------------------------------

# 301. V1 Mandatory Principles

Pour la V1, appliquer obligatoirement :

-   safety first ;
-   fail closed for new exposure ;
-   explicit architecture boundaries ;
-   typed contracts ;
-   UTC internally ;
-   idempotency ;
-   data validation ;
-   versioned configuration ;
-   no secrets in Git ;
-   least privilege ;
-   structured logs ;
-   health checks ;
-   reproducible builds ;
-   tests for critical logic ;
-   replay capability ;
-   hard risk limits ;
-   execution reconciliation ;
-   immutable artifacts ;
-   controlled deployment ;
-   rollback capability ;
-   AI outside hard safety boundaries ;
-   governance for critical changes.

------------------------------------------------------------------------

# 302. V2 Maturity

Ajouter :

-   automated architecture checks ;
-   property-based testing ;
-   stronger policy-as-code ;
-   systematic performance budgets ;
-   broader failure injection ;
-   configuration drift detection.

------------------------------------------------------------------------

# 303. V3 Maturity

Ajouter :

-   automated resilience testing ;
-   continuous strategy robustness testing ;
-   advanced supply-chain security ;
-   stronger multi-agent engineering workflows ;
-   automated lineage validation.

------------------------------------------------------------------------

# 304. V4 Maturity

Ajouter :

-   controlled autonomous operations ;
-   automated policy verification ;
-   continuous production experiments ;
-   self-diagnosis under governance ;
-   automated rollback recommendations.

------------------------------------------------------------------------

# 305. Critères d'acceptation

Ces principes sont correctement appliqués lorsque :

-   les composants ont des responsabilités claires ;
-   les décisions critiques sont traçables ;
-   les limites de risque ne peuvent pas être contournées ;
-   les données invalides sont détectées ;
-   les opérations rejouées ne créent pas de doubles effets ;
-   les secrets sont isolés ;
-   les services sont observables ;
-   les versions actives sont identifiables ;
-   les changements sont testables et réversibles ;
-   les incidents peuvent être reconstruits ;
-   les stratégies peuvent être rejouées ;
-   les hypothèses quantitatives sont enregistrées ;
-   les agents IA restent soumis aux mêmes règles d'ingénierie ;
-   la complexité est introduite seulement lorsqu'elle apporte une
    valeur mesurable.

------------------------------------------------------------------------

# 306. Anti-Patterns à éviter

QuantLab doit activement éviter :

``` text
GOD SERVICE
SHARED MUTABLE GLOBAL STATE
MAGIC CONFIGURATION
UNBOUNDED RETRIES
UNBOUNDED QUEUES
SILENT EXCEPTIONS
MANUAL PRODUCTION PATCHES
UNVERSIONED MODELS
UNVERSIONED PROMPTS
DIRECT STRATEGY → EXCHANGE PATH
AI → LIVE ORDER WITHOUT HARD CONTROLS
BACKTEST WITHOUT COSTS
BACKTEST WITH LOOK-AHEAD
TESTS THAT ONLY TEST MOCKS
DOCUMENTATION THAT CONTRADICTS CODE
```

------------------------------------------------------------------------

# 307. Hiérarchie de décision

Lorsqu'un compromis est difficile :

``` text
Protect capital
↓
Preserve correctness
↓
Preserve data
↓
Preserve security
↓
Preserve observability
↓
Preserve reversibility
↓
Optimize performance
↓
Optimize convenience
```

------------------------------------------------------------------------

# 308. Règle fondatrice

> **QuantLab doit être conçu pour survivre aux erreurs de données, de
> code, de modèles, d'infrastructure, d'agents IA et d'humains sans
> transformer automatiquement chacune de ces erreurs en perte
> financière.**

L'architecture recherchée n'est donc pas celle qui suppose que tout
fonctionne.

C'est celle qui reste contrôlable lorsque quelque chose ne fonctionne
pas.

``` text
CLEAR CONTRACTS
+
HARD INVARIANTS
+
OBSERVABILITY
+
REPRODUCIBILITY
+
REVERSIBILITY
+
GOVERNANCE
=
ENGINEERING DISCIPLINE
```

------------------------------------------------------------------------

# 309. Statut

**Version : 1.0**

Documents directement liés :

-   `01-Vision-du-Projet.md`
-   `02-Architecture-Generale.md`
-   `03-Data-Engine.md`
-   `04-Storage-Engine.md`
-   `05-Market-Analysis-Engine.md`
-   `06-Market-Structure-Engine.md`
-   `07-Volume-Profile-Engine.md`
-   `08-Smart-Money-Concepts-Engine.md`
-   `09-Scoring-Engine.md`
-   `10-Decision-Engine.md`
-   `11-Risk-Engine.md`
-   `12-Execution-Engine.md`
-   `13-Monitoring-Engine.md`
-   `14-Knowledge-Engine.md`
-   `15-AI-and-Learning-Engine.md`
-   `16-Governance-Engine.md`
-   `17-AI-Development-Protocol.md`
-   `18-Testing-Strategy.md`
-   `19-Deployment-Guide.md`
-   `21-Experiment-Registry.md`
-   `22-API-Specification.md`
-   `23-Database-Schema.md`
-   `24-Security.md`
-   `25-Roadmap.md`

**Prochain document : `21-Experiment-Registry.md`**
