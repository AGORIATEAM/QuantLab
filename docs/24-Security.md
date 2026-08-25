# 24 --- Security

**Projet : QuantLab**\
**Document : Security**\
**Version : 1.0**\
**Statut : Politique et architecture de sécurité de référence**

------------------------------------------------------------------------

# 1. Objectif

Ce document définit les principes de sécurité de QuantLab.

QuantLab manipule des composants capables de :

-   consommer des données de marché ;
-   prendre des décisions ;
-   calculer du risque ;
-   envoyer des ordres ;
-   accéder à des comptes de trading ;
-   exécuter du code ;
-   utiliser des agents IA ;
-   modifier des configurations ;
-   déployer des composants en production.

La sécurité doit donc être considérée comme une propriété structurelle
du système.

> **Aucun composant, utilisateur ou agent ne doit disposer de plus
> d'autorité que nécessaire pour accomplir sa fonction.**

------------------------------------------------------------------------

# 2. Objectifs de sécurité

QuantLab doit protéger :

``` text
CONFIDENTIALITY
INTEGRITY
AVAILABILITY
AUTHENTICITY
TRACEABILITY
RECOVERABILITY
```

------------------------------------------------------------------------

# 3. Priorité absolue

Pour le trading live :

``` text
CAPITAL PROTECTION
>
AVAILABILITY OF NEW TRADING
```

Si QuantLab doit choisir entre continuer à trader dans un état incertain
ou bloquer temporairement les nouvelles expositions :

``` text
FAIL CLOSED
```

est le comportement par défaut.

------------------------------------------------------------------------

# 4. Threat Model

Les menaces incluent notamment :

-   compromission de credentials ;
-   vol de clés API exchange ;
-   accès non autorisé ;
-   erreur humaine ;
-   agent IA sur-privilégié ;
-   dépendance compromise ;
-   supply-chain attack ;
-   injection ;
-   fuite de secrets ;
-   modification non autorisée du Risk Engine ;
-   ordre dupliqué ;
-   déploiement malveillant ;
-   corruption de données ;
-   exfiltration ;
-   attaque sur infrastructure ;
-   déni de service ;
-   mauvaise configuration cloud ;
-   accès production depuis un environnement de recherche.

------------------------------------------------------------------------

# 5. Trust Nothing by Location

Un composant situé « dans le réseau interne » n'est pas automatiquement
fiable.

L'identité et les permissions doivent être vérifiées.

------------------------------------------------------------------------

# 6. Zero Trust Principle

Chaque interaction sensible doit vérifier :

``` text
WHO
WHAT
WHERE
WHICH RESOURCE
WHICH ENVIRONMENT
WHICH PERMISSION
```

------------------------------------------------------------------------

# 7. Identity

Toute action critique doit être associée à une identité.

Types :

``` text
HUMAN
SERVICE
AI_AGENT
CI_CD
OPERATOR
```

------------------------------------------------------------------------

# 8. Unique Identities

Pas de comptes partagés pour les opérations sensibles.

------------------------------------------------------------------------

# 9. Human Authentication

Pour les interfaces sensibles :

``` text
SSO
MFA
```

doivent être privilégiés.

------------------------------------------------------------------------

# 10. MFA

Obligatoire pour :

``` text
production administration
secret management
cloud administration
governance approval
exchange administration
```

------------------------------------------------------------------------

# 11. Service Identities

Chaque service doit avoir une identité distincte.

Exemple :

``` text
data-engine
risk-engine
execution-engine
monitoring-engine
```

------------------------------------------------------------------------

# 12. No Shared Service Credential

Éviter :

``` text
QUANTLAB_MASTER_API_KEY
```

utilisée par tous les composants.

Ce genre de raccourci est très pratique jusqu'au jour où il transforme
un incident local en incident global.

------------------------------------------------------------------------

# 13. Short-Lived Credentials

Préférer les credentials temporaires aux secrets permanents lorsque
l'infrastructure le permet.

------------------------------------------------------------------------

# 14. Authorization

L'authentification répond :

``` text
Who are you?
```

L'autorisation répond :

``` text
What are you allowed to do?
```

Les deux sont nécessaires.

------------------------------------------------------------------------

# 15. Least Privilege

Chaque identité reçoit uniquement les droits nécessaires.

------------------------------------------------------------------------

# 16. Permission Model

Exemples :

``` text
market_data.read
analysis.execute
strategy.read
strategy.modify
risk.evaluate
risk.modify
execution.submit
execution.cancel
governance.propose
governance.approve
deployment.execute
audit.read
```

------------------------------------------------------------------------

# 17. Separation of Duties

Les rôles critiques doivent être séparés.

Exemple :

``` text
developer
≠
production approver
```

lorsque le niveau de risque le justifie.

------------------------------------------------------------------------

# 18. Research Isolation

Les outils de recherche ne doivent pas pouvoir envoyer directement des
ordres live.

------------------------------------------------------------------------

# 19. AI Isolation

Un agent IA de recherche ne doit pas posséder de permission d'exécution
live.

------------------------------------------------------------------------

# 20. Production Boundary

Architecture :

``` text
Research
   │
   X
   │
Production Execution
```

La transition doit passer par :

``` text
validation
governance
deployment
risk controls
```

------------------------------------------------------------------------

# 21. Environment Separation

Séparer :

``` text
development
test
research
paper
shadow
limited-live
production
```

------------------------------------------------------------------------

# 22. Separate Credentials

Chaque environnement utilise des credentials différents.

------------------------------------------------------------------------

# 23. Separate Databases

Production doit disposer d'une base isolée.

------------------------------------------------------------------------

# 24. Separate Exchange Keys

Les clés live ne doivent jamais être utilisées en test ou recherche.

------------------------------------------------------------------------

# 25. Exchange API Permissions

Une clé de trading ne doit disposer que des permissions nécessaires.

Lorsque possible :

``` text
trading = enabled
withdrawals = disabled
```

------------------------------------------------------------------------

# 26. Withdrawal Permission

Les clés utilisées par QuantLab ne doivent pas disposer de permissions
de retrait sauf justification exceptionnelle explicitement gouvernée.

------------------------------------------------------------------------

# 27. IP Restrictions

Lorsque les venues le permettent :

``` text
IP allowlisting
```

doit être activé pour les clés live.

------------------------------------------------------------------------

# 28. Key Rotation

Les credentials critiques doivent pouvoir être renouvelés sans
interruption majeure.

------------------------------------------------------------------------

# 29. Secret Management

Les secrets doivent être stockés dans un secret manager dédié.

------------------------------------------------------------------------

# 30. Secrets Prohibited Locations

Jamais dans :

``` text
Git
source code
README
Markdown docs
Docker images
experiment artifacts
logs
database dumps
chat prompts
```

------------------------------------------------------------------------

# 31. Environment Variables

Les variables d'environnement peuvent transporter des références/secrets
runtime, mais ne constituent pas à elles seules un système complet de
gestion des secrets.

------------------------------------------------------------------------

# 32. Secret References

Préférer :

``` text
secret://production/exchange/api-key
```

ou mécanisme équivalent.

------------------------------------------------------------------------

# 33. Secret Rotation

Prévoir :

``` text
create new
deploy new
validate
revoke old
```

------------------------------------------------------------------------

# 34. Secret Exposure Response

En cas de fuite supposée :

``` text
revoke
rotate
investigate
audit
```

Ne pas attendre une preuve d'exploitation.

------------------------------------------------------------------------

# 35. Secret Scanning

La CI doit détecter les secrets accidentellement commités.

------------------------------------------------------------------------

# 36. Pre-Commit Secret Detection

Ajouter une protection locale lorsque possible.

------------------------------------------------------------------------

# 37. Git History

Supprimer un secret du dernier commit ne suffit pas s'il reste dans
l'historique.

Le secret doit être considéré compromis et renouvelé.

------------------------------------------------------------------------

# 38. Encryption in Transit

Toutes les communications sensibles utilisent :

``` text
TLS
```

------------------------------------------------------------------------

# 39. Encryption at Rest

Les données persistantes sensibles doivent être chiffrées au repos.

------------------------------------------------------------------------

# 40. Database Encryption

Utiliser le chiffrement fourni par l'infrastructure et des contrôles
d'accès stricts.

------------------------------------------------------------------------

# 41. Backup Encryption

Les backups doivent également être chiffrés.

------------------------------------------------------------------------

# 42. Object Storage

Activer :

``` text
encryption
private access
versioning where useful
```

------------------------------------------------------------------------

# 43. Key Management

Les clés de chiffrement doivent être gérées via :

``` text
KMS
HSM
```

ou mécanisme équivalent selon maturité.

------------------------------------------------------------------------

# 44. Key Separation

Séparer les clés entre environnements.

------------------------------------------------------------------------

# 45. API Security

Toutes les APIs sensibles doivent appliquer :

``` text
authentication
authorization
validation
rate limiting
audit
```

------------------------------------------------------------------------

# 46. Input Validation

Toute entrée externe est non fiable.

------------------------------------------------------------------------

# 47. Schema Validation

Les payloads doivent respecter des schemas stricts.

------------------------------------------------------------------------

# 48. Injection Protection

Protéger contre :

``` text
SQL injection
command injection
template injection
path traversal
```

------------------------------------------------------------------------

# 49. Parameterized Queries

Les accès SQL utilisent des requêtes paramétrées ou ORM sûr.

------------------------------------------------------------------------

# 50. Command Execution

Éviter de construire des commandes shell à partir d'inputs externes.

------------------------------------------------------------------------

# 51. Path Validation

Les accès fichiers doivent empêcher les sorties du périmètre autorisé.

------------------------------------------------------------------------

# 52. Deserialization

Ne pas désérialiser des objets non fiables avec des formats capables
d'exécuter du code.

------------------------------------------------------------------------

# 53. API Rate Limiting

Protéger contre :

``` text
abuse
bugs
runaway loops
AI agents
```

------------------------------------------------------------------------

# 54. Request Size Limits

Limiter les payloads.

------------------------------------------------------------------------

# 55. Error Handling

Les erreurs externes ne doivent pas exposer :

``` text
stack traces
secrets
internal paths
database credentials
```

------------------------------------------------------------------------

# 56. Authentication Errors

Ne pas révéler inutilement si un compte sensible existe.

------------------------------------------------------------------------

# 57. Session Security

Pour les interfaces web :

``` text
secure cookies
HttpOnly
SameSite
session expiration
```

selon architecture.

------------------------------------------------------------------------

# 58. CSRF

Protéger les actions state-changing utilisant des sessions navigateur.

------------------------------------------------------------------------

# 59. CORS

Configurer une allowlist explicite.

------------------------------------------------------------------------

# 60. Content Security Policy

Pour les interfaces web :

``` text
CSP
```

doit être envisagée.

------------------------------------------------------------------------

# 61. Security Headers

Configurer les headers modernes appropriés.

------------------------------------------------------------------------

# 62. Dependency Security

Toutes les dépendances tierces sont des composants potentiellement
hostiles.

------------------------------------------------------------------------

# 63. Dependency Pinning

Les dépendances doivent être versionnées précisément.

------------------------------------------------------------------------

# 64. Lock Files

Utiliser les lock files du gestionnaire de dépendances.

------------------------------------------------------------------------

# 65. Vulnerability Scanning

La CI doit scanner :

``` text
dependencies
containers
OS packages
```

------------------------------------------------------------------------

# 66. Dependency Updates

Les mises à jour de sécurité critiques doivent être prioritaires.

------------------------------------------------------------------------

# 67. Supply Chain

Évaluer :

``` text
package provenance
maintainer reputation
download source
unexpected dependency changes
```

------------------------------------------------------------------------

# 68. Typosquatting

Vérifier les nouveaux packages.

Une lettre de différence dans un nom de dépendance peut coûter plus cher
qu'un bug de stratégie.

------------------------------------------------------------------------

# 69. Minimal Dependencies

Éviter une dépendance entière pour quelques lignes triviales.

------------------------------------------------------------------------

# 70. Build Security

Les builds production doivent être reproductibles autant que possible.

------------------------------------------------------------------------

# 71. Artifact Integrity

Chaque artefact de production doit avoir :

``` text
version
hash
provenance
```

------------------------------------------------------------------------

# 72. Signed Artifacts

À maturité, signer les artefacts de production.

------------------------------------------------------------------------

# 73. Container Security

Les images doivent :

``` text
use minimal base images
run as non-root
remove unnecessary tools
avoid embedded secrets
```

------------------------------------------------------------------------

# 74. Image Scanning

Scanner les images avant déploiement.

------------------------------------------------------------------------

# 75. Immutable Infrastructure

Préférer remplacer un artefact plutôt que modifier manuellement un
serveur live.

------------------------------------------------------------------------

# 76. Production Shell Access

Limiter fortement l'accès shell production.

------------------------------------------------------------------------

# 77. Break-Glass Access

Un accès d'urgence doit être :

``` text
temporary
strongly authenticated
logged
reviewed
```

------------------------------------------------------------------------

# 78. No Permanent Root Access

Éviter les accès administrateur permanents.

------------------------------------------------------------------------

# 79. Network Segmentation

Séparer les composants selon leur niveau de sensibilité.

------------------------------------------------------------------------

# 80. Execution Network

L'Execution Engine doit avoir uniquement les accès réseau nécessaires.

------------------------------------------------------------------------

# 81. Database Network

La base production ne doit pas être publiquement accessible.

------------------------------------------------------------------------

# 82. Private Networking

Utiliser des réseaux privés pour les composants internes lorsque
possible.

------------------------------------------------------------------------

# 83. Egress Control

Les services sensibles ne doivent pas pouvoir contacter arbitrairement
Internet.

------------------------------------------------------------------------

# 84. AI Agent Egress

Les agents pouvant lire des informations sensibles doivent avoir des
destinations réseau contrôlées.

------------------------------------------------------------------------

# 85. DNS Security

Surveiller les comportements DNS anormaux dans les environnements
sensibles lorsque pertinent.

------------------------------------------------------------------------

# 86. Firewall Policy

Utiliser :

``` text
default deny
explicit allow
```

pour les segments critiques.

------------------------------------------------------------------------

# 87. Cloud IAM

Les permissions cloud doivent suivre le moindre privilège.

------------------------------------------------------------------------

# 88. No Human Long-Lived Cloud Keys

Préférer :

``` text
SSO
temporary sessions
role assumption
```

------------------------------------------------------------------------

# 89. CI/CD Identity

Le pipeline possède une identité dédiée.

------------------------------------------------------------------------

# 90. CI/CD Permissions

Le pipeline de test ne doit pas pouvoir déployer en production.

------------------------------------------------------------------------

# 91. Production Deployment

Nécessite une identité et une politique distinctes.

------------------------------------------------------------------------

# 92. Protected Branches

La branche principale doit utiliser :

``` text
pull requests
reviews
status checks
```

------------------------------------------------------------------------

# 93. Branch Protection

Interdire les pushes directs pour les zones critiques.

------------------------------------------------------------------------

# 94. CODEOWNERS

Utiliser des reviewers obligatoires pour :

``` text
risk
execution
security
deployment
governance
```

------------------------------------------------------------------------

# 95. Signed Commits

Peuvent être exigés pour certains workflows sensibles.

------------------------------------------------------------------------

# 96. Security Review

Les changements critiques nécessitent une revue sécurité explicite.

------------------------------------------------------------------------

# 97. Threat Modeling

À réaliser pour :

``` text
new execution path
new external integration
new AI capability
new authentication flow
new privileged service
```

------------------------------------------------------------------------

# 98. Security ADR

Les décisions importantes doivent être documentées.

------------------------------------------------------------------------

# 99. Static Analysis

La CI doit exécuter des outils de sécurité statique adaptés au stack.

------------------------------------------------------------------------

# 100. Dynamic Testing

Les services exposés doivent être testés dynamiquement lorsque
pertinent.

------------------------------------------------------------------------

# 101. SAST

Analyse du code pour détecter des patterns dangereux.

------------------------------------------------------------------------

# 102. DAST

Tests contre une application en fonctionnement.

------------------------------------------------------------------------

# 103. Dependency Audit

Automatiser l'analyse des CVE connues.

------------------------------------------------------------------------

# 104. Secret Scan

Bloquer la CI si un secret probable est détecté.

------------------------------------------------------------------------

# 105. Infrastructure as Code Scan

Analyser les configurations cloud/IaC.

------------------------------------------------------------------------

# 106. Container Scan

Analyser les vulnérabilités des images.

------------------------------------------------------------------------

# 107. SBOM

À maturité, générer un :

``` text
Software Bill of Materials
```

pour les releases.

------------------------------------------------------------------------

# 108. Provenance

Pouvoir répondre :

``` text
Which source produced this artifact?
```

------------------------------------------------------------------------

# 109. Trading Safety Boundary

Workflow obligatoire :

``` text
Decision Engine
↓
Risk Engine
↓
Execution Engine
↓
Venue
```

------------------------------------------------------------------------

# 110. No Execution Bypass

Aucun service stratégique ne doit pouvoir contourner le Risk Engine.

------------------------------------------------------------------------

# 111. Hard Risk Limits

Les limites critiques doivent être appliquées indépendamment de la
stratégie.

------------------------------------------------------------------------

# 112. Kill Switch

Le système doit pouvoir :

``` text
block new orders
cancel eligible orders
halt strategies
```

selon procédure.

------------------------------------------------------------------------

# 113. Kill Switch Permissions

Activation :

``` text
broad enough for emergency
```

Désactivation :

``` text
more restrictive
```

------------------------------------------------------------------------

# 114. Kill Switch Audit

Toute activation/désactivation est enregistrée.

------------------------------------------------------------------------

# 115. Fail Closed

Si le Risk Engine est indisponible :

``` text
new strategic exposure = blocked
```

------------------------------------------------------------------------

# 116. Stale Data

Si les données critiques sont trop anciennes :

``` text
new trading = blocked or degraded
```

selon stratégie.

------------------------------------------------------------------------

# 117. Clock Integrity

Les systèmes critiques doivent utiliser une synchronisation temporelle
fiable.

------------------------------------------------------------------------

# 118. Clock Drift Monitoring

Une dérive importante doit générer une alerte.

------------------------------------------------------------------------

# 119. Replay Protection

Les commandes critiques doivent empêcher les replays involontaires ou
malveillants.

------------------------------------------------------------------------

# 120. Idempotency

Les opérations d'exécution doivent être idempotentes.

------------------------------------------------------------------------

# 121. Order IDs

Utiliser des identifiants uniques côté QuantLab.

------------------------------------------------------------------------

# 122. Exchange Reconciliation

Ne jamais considérer un timeout comme une preuve d'échec.

------------------------------------------------------------------------

# 123. Unknown State

Le système doit accepter l'état :

``` text
UNKNOWN
```

et réconcilier avant nouvelle action dangereuse.

------------------------------------------------------------------------

# 124. Duplicate Fill Defense

Les fills doivent être dédupliqués.

------------------------------------------------------------------------

# 125. Position Reconciliation

Comparer régulièrement :

``` text
QuantLab state
vs
venue state
```

------------------------------------------------------------------------

# 126. Account Balance Reconciliation

Comparer les balances critiques.

------------------------------------------------------------------------

# 127. Security Monitoring

Le Monitoring Engine doit détecter :

``` text
failed authentication
permission denials
secret access anomalies
unexpected network calls
unusual order activity
config changes
```

------------------------------------------------------------------------

# 128. Security Events

Les événements doivent avoir :

``` text
severity
identity
resource
timestamp
correlation ID
```

------------------------------------------------------------------------

# 129. Security Alert Levels

Exemple :

``` text
INFO
LOW
MEDIUM
HIGH
CRITICAL
```

------------------------------------------------------------------------

# 130. Critical Alerts

Exemples :

``` text
production credential leak
unexpected withdrawal permission
unauthorized risk modification
unknown production deployment
execution anomaly
```

------------------------------------------------------------------------

# 131. Alert Routing

Les alertes critiques doivent utiliser plusieurs canaux lorsque
nécessaire.

------------------------------------------------------------------------

# 132. Alert Fatigue

Ne pas transformer chaque warning banal en alarme critique.

Sinon l'être humain apprend rapidement à ignorer exactement le système
censé le sauver.

------------------------------------------------------------------------

# 133. Audit Logging

Toute action sensible doit être auditée.

------------------------------------------------------------------------

# 134. Audit Fields

``` text
actor
action
resource
environment
request_id
correlation_id
result
timestamp
```

------------------------------------------------------------------------

# 135. Audit Protection

Les logs d'audit doivent être protégés contre modification.

------------------------------------------------------------------------

# 136. Audit Retention

Conservation longue pour les actions critiques.

------------------------------------------------------------------------

# 137. Sensitive Log Redaction

Masquer :

``` text
API keys
tokens
passwords
authorization headers
private keys
```

------------------------------------------------------------------------

# 138. Structured Logging

Utiliser des logs structurés.

------------------------------------------------------------------------

# 139. Security Log Access

Limiter l'accès aux logs sensibles.

------------------------------------------------------------------------

# 140. Incident Response

Workflow :

``` text
DETECT
↓
CONTAIN
↓
ERADICATE
↓
RECOVER
↓
REVIEW
```

------------------------------------------------------------------------

# 141. Incident Severity

Définir une classification.

Exemple :

``` text
SEV-1
SEV-2
SEV-3
SEV-4
```

------------------------------------------------------------------------

# 142. SEV-1

Exemples :

``` text
unauthorized live trading
capital at immediate risk
production secrets compromised
```

------------------------------------------------------------------------

# 143. Immediate Containment

Pour SEV-1 :

``` text
activate kill switch if needed
revoke credentials
isolate affected systems
preserve evidence
```

------------------------------------------------------------------------

# 144. Evidence Preservation

Ne pas détruire les logs nécessaires à l'analyse.

------------------------------------------------------------------------

# 145. Incident Timeline

Construire :

``` text
what happened
when
who/what acted
what systems were affected
```

------------------------------------------------------------------------

# 146. Postmortem

Tout incident important doit produire un postmortem.

------------------------------------------------------------------------

# 147. Blameless but Accountable

Le postmortem cherche les causes systémiques, sans supprimer la
responsabilité opérationnelle.

------------------------------------------------------------------------

# 148. Security Findings

Les findings doivent avoir :

``` text
severity
owner
deadline
status
```

------------------------------------------------------------------------

# 149. Vulnerability Management

Workflow :

``` text
discover
triage
prioritize
fix
verify
close
```

------------------------------------------------------------------------

# 150. Severity-Based SLA

Définir des délais de correction selon la criticité.

------------------------------------------------------------------------

# 151. Critical Vulnerability

Une vulnérabilité critique exploitable sur production doit être traitée
immédiatement.

------------------------------------------------------------------------

# 152. Patch Management

Les systèmes doivent recevoir les mises à jour de sécurité selon une
politique définie.

------------------------------------------------------------------------

# 153. Unsupported Software

Les composants non maintenus doivent être remplacés.

------------------------------------------------------------------------

# 154. Data Security

Les données doivent être classifiées.

------------------------------------------------------------------------

# 155. Data Classes

``` text
PUBLIC
INTERNAL
CONFIDENTIAL
SECRET
```

------------------------------------------------------------------------

# 156. Market Data

Peut être soumis à des licences et restrictions contractuelles.

------------------------------------------------------------------------

# 157. Trading Data

Positions, ordres, performances et stratégies :

``` text
CONFIDENTIAL
```

par défaut.

------------------------------------------------------------------------

# 158. Credentials

``` text
SECRET
```

------------------------------------------------------------------------

# 159. Data Minimization

Ne stocker que ce qui est nécessaire.

------------------------------------------------------------------------

# 160. Data Retention

Définir des durées selon :

``` text
operational need
audit need
contract
regulation
```

------------------------------------------------------------------------

# 161. Secure Deletion

Prévoir un mécanisme adapté pour les données qui doivent être
supprimées.

------------------------------------------------------------------------

# 162. Backups

Les backups doivent être :

``` text
encrypted
access-controlled
tested
```

------------------------------------------------------------------------

# 163. Backup Credentials

Les identités de backup doivent être séparées.

------------------------------------------------------------------------

# 164. Recovery Security

Une restauration ne doit pas contourner les politiques de sécurité.

------------------------------------------------------------------------

# 165. Disaster Recovery

Le plan DR doit inclure les aspects sécurité.

------------------------------------------------------------------------

# 166. Compromised Backup Scenario

Prévoir le cas où :

``` text
production + credentials
```

sont compromis simultanément.

------------------------------------------------------------------------

# 167. AI Security

Les systèmes IA introduisent des risques spécifiques.

------------------------------------------------------------------------

# 168. AI Is Untrusted Decision Support

Une sortie IA doit être traitée comme une entrée non fiable jusqu'à
validation.

------------------------------------------------------------------------

# 169. Prompt Injection

Les agents consommant du contenu externe doivent supposer que ce contenu
peut contenir des instructions malveillantes.

------------------------------------------------------------------------

# 170. Instruction/Data Separation

Un document lu par un agent n'acquiert pas automatiquement le droit de
modifier les instructions de l'agent.

------------------------------------------------------------------------

# 171. Tool Permissions

Chaque outil accessible à un agent doit avoir un scope limité.

------------------------------------------------------------------------

# 172. Read vs Write Tools

Séparer explicitement :

``` text
read
write
execute
deploy
trade
```

------------------------------------------------------------------------

# 173. Human Approval

Les actions IA à fort impact nécessitent une approbation humaine ou une
gouvernance équivalente explicitement validée.

------------------------------------------------------------------------

# 174. AI Production Trading

Un modèle IA ne doit pas envoyer directement un ordre live hors du
pipeline :

``` text
Decision
→ Risk
→ Execution
```

------------------------------------------------------------------------

# 175. AI Code Generation

Le code généré doit passer :

``` text
tests
review
security checks
governance
```

------------------------------------------------------------------------

# 176. AI Dependency Suggestions

Toute nouvelle dépendance proposée par IA doit être vérifiée.

------------------------------------------------------------------------

# 177. AI Secret Access

Les agents ne doivent pas recevoir de secrets bruts sauf nécessité
exceptionnelle.

------------------------------------------------------------------------

# 178. AI Context Minimization

Ne fournir aux modèles que les données nécessaires.

------------------------------------------------------------------------

# 179. Sensitive Prompt Logging

Éviter de conserver des prompts contenant des données sensibles sans
besoin explicite.

------------------------------------------------------------------------

# 180. Model Provider Risk

Pour un provider externe, évaluer :

``` text
data retention
training policy
regional processing
security controls
contractual guarantees
```

------------------------------------------------------------------------

# 181. AI Output Validation

Les outputs structurés doivent être validés par schema.

------------------------------------------------------------------------

# 182. AI Hallucination Defense

Une affirmation IA ne doit pas devenir un fait opérationnel sans source
ou validation.

------------------------------------------------------------------------

# 183. AI Autonomy Budget

Limiter :

``` text
number of actions
compute
tokens
time
permissions
```

------------------------------------------------------------------------

# 184. AI Kill Switch

Les workflows autonomes doivent pouvoir être suspendus.

------------------------------------------------------------------------

# 185. AI Audit

Enregistrer :

``` text
agent
model
prompt version
tool calls
actions
result
```

------------------------------------------------------------------------

# 186. Agent Identity

Chaque agent doit avoir sa propre identité.

------------------------------------------------------------------------

# 187. No Agent Credential Sharing

Deux agents aux rôles différents ne doivent pas partager un credential
privilégié.

------------------------------------------------------------------------

# 188. Agent Sandbox

Le code généré ou exécuté automatiquement doit être isolé.

------------------------------------------------------------------------

# 189. Sandbox Restrictions

Limiter :

``` text
filesystem
network
CPU
memory
execution time
secrets
```

------------------------------------------------------------------------

# 190. Arbitrary Code Execution

Toute capacité d'exécuter du code arbitraire doit être considérée comme
hautement privilégiée.

------------------------------------------------------------------------

# 191. Research Sandbox

Les expériences IA doivent être séparées de production.

------------------------------------------------------------------------

# 192. External Content

Traiter :

``` text
web pages
documents
Git repositories
third-party APIs
```

comme non fiables.

------------------------------------------------------------------------

# 193. SSRF Protection

Les services capables d'effectuer des requêtes réseau doivent limiter
les destinations.

------------------------------------------------------------------------

# 194. URL Validation

Empêcher l'accès arbitraire aux réseaux internes via URLs contrôlées par
utilisateur.

------------------------------------------------------------------------

# 195. File Upload Security

Les fichiers uploadés doivent être :

``` text
size-limited
type-validated
stored outside executable paths
```

------------------------------------------------------------------------

# 196. Malware Scanning

À ajouter si QuantLab accepte des fichiers provenant de sources non
fiables.

------------------------------------------------------------------------

# 197. Archive Bombs

Limiter les décompressions et tailles finales.

------------------------------------------------------------------------

# 198. Git Security

Le repository doit protéger :

``` text
main branch
release tags
CI configuration
deployment workflows
```

------------------------------------------------------------------------

# 199. Pull Request Security

Les changements sensibles doivent être revus.

------------------------------------------------------------------------

# 200. CI Configuration Changes

Les modifications de CI/CD sont elles-mêmes des changements de sécurité
critiques.

------------------------------------------------------------------------

# 201. Third-Party Actions

Les actions CI tierces doivent être versionnées précisément.

------------------------------------------------------------------------

# 202. Fork Security

Les workflows provenant de forks ne doivent pas recevoir de secrets
production.

------------------------------------------------------------------------

# 203. Build Secrets

Les secrets utilisés au build ne doivent pas être persistés dans les
layers d'image.

------------------------------------------------------------------------

# 204. Deployment Security

Le déploiement suit :

``` text
approved commit
↓
verified build
↓
artifact hash
↓
governance approval
↓
deployment
```

------------------------------------------------------------------------

# 205. Artifact Substitution Defense

L'artefact déployé doit être exactement celui qui a été approuvé.

------------------------------------------------------------------------

# 206. Rollback Security

Un rollback doit utiliser un artefact connu et vérifié.

------------------------------------------------------------------------

# 207. Configuration Security

Les configurations doivent être versionnées et validées.

------------------------------------------------------------------------

# 208. Risk Configuration

Les limites de risque sont des paramètres de sécurité.

------------------------------------------------------------------------

# 209. Risk Limit Changes

Nécessitent :

``` text
authorization
audit
governance
```

selon impact.

------------------------------------------------------------------------

# 210. No Runtime Risk Editing by Strategy

Une stratégie ne peut pas augmenter ses propres limites.

------------------------------------------------------------------------

# 211. Feature Flags

Les flags sensibles doivent être :

``` text
authenticated
authorized
audited
```

------------------------------------------------------------------------

# 212. Dangerous Defaults

Les defaults doivent privilégier la sécurité.

Exemple :

``` text
live_trading_enabled = false
```

------------------------------------------------------------------------

# 213. Secure Bootstrap

Une nouvelle installation démarre :

``` text
non-live
minimum permissions
no production credentials
```

------------------------------------------------------------------------

# 214. Production Enablement

Le live doit être une action explicite.

------------------------------------------------------------------------

# 215. Security Configuration Validation

Le système doit refuser de démarrer si :

``` text
required secret missing
TLS disabled unexpectedly
production DB misconfigured
unsafe permissions detected
```

------------------------------------------------------------------------

# 216. Security Tests

La stratégie de tests doit inclure :

``` text
authentication
authorization
injection
secret leakage
idempotency
privilege escalation
```

------------------------------------------------------------------------

# 217. Negative Security Tests

Tester explicitement ce qui doit être refusé.

------------------------------------------------------------------------

# 218. Permission Matrix Tests

Chaque rôle critique doit avoir une matrice :

``` text
allowed
denied
```

------------------------------------------------------------------------

# 219. Production Simulation

Tester les scénarios :

``` text
risk engine unavailable
exchange timeout
credential revoked
database read-only
network partition
stale market data
```

------------------------------------------------------------------------

# 220. Chaos Security

À maturité, injecter des pannes contrôlées.

------------------------------------------------------------------------

# 221. Penetration Testing

Effectuer périodiquement des tests adaptés à la surface exposée.

------------------------------------------------------------------------

# 222. External Review

Une revue indépendante est recommandée avant une montée importante en
capital ou exposition.

------------------------------------------------------------------------

# 223. Security Metrics

Suivre :

``` text
critical vulnerabilities
mean time to remediate
failed auth
permission denials
secret leaks
security incidents
```

------------------------------------------------------------------------

# 224. Security SLO

Pour certains contrôles critiques, définir des objectifs mesurables.

------------------------------------------------------------------------

# 225. Access Reviews

Revoir périodiquement :

``` text
human accounts
service accounts
cloud roles
exchange keys
database roles
AI agent permissions
```

------------------------------------------------------------------------

# 226. Dormant Accounts

Désactiver les comptes inutilisés.

------------------------------------------------------------------------

# 227. Offboarding

Lors du départ d'un collaborateur :

``` text
revoke access
rotate shared exposure if any
remove sessions
review recent activity
```

------------------------------------------------------------------------

# 228. Asset Inventory

Maintenir un inventaire :

``` text
services
databases
repositories
cloud resources
credentials
external integrations
```

------------------------------------------------------------------------

# 229. Ownership

Chaque actif critique doit avoir un owner.

------------------------------------------------------------------------

# 230. Security Exceptions

Toute exception doit documenter :

``` text
reason
risk
owner
expiration
compensating controls
```

------------------------------------------------------------------------

# 231. Expiring Exceptions

Les exceptions doivent expirer automatiquement lorsque possible.

------------------------------------------------------------------------

# 232. No Permanent Temporary Fix

« Temporaire » ne doit pas devenir une catégorie d'architecture.

------------------------------------------------------------------------

# 233. Compliance

Les exigences réglementaires dépendront :

``` text
jurisdiction
broker/exchange
capital structure
clients
data handled
```

------------------------------------------------------------------------

# 234. Legal Review

Une revue juridique spécialisée est nécessaire avant toute activité
réglementée ou gestion de fonds tiers.

------------------------------------------------------------------------

# 235. Security vs Compliance

La conformité ne remplace pas la sécurité.

Cocher une case n'arrête pas un ordre non autorisé.

------------------------------------------------------------------------

# 236. V1 Security Baseline

Avant tout live :

``` text
MFA
secret manager
separate environments
separate live exchange keys
withdrawals disabled
least privilege
TLS
encrypted storage
branch protection
dependency scanning
secret scanning
audit logs
Risk Engine mandatory
kill switch
idempotent execution
backup + restore test
monitoring + alerts
```

------------------------------------------------------------------------

# 237. V1 Human Access

Accès production :

``` text
minimum people
MFA
named accounts
audited
```

------------------------------------------------------------------------

# 238. V1 Service Access

Chaque service :

``` text
dedicated identity
minimal DB role
minimal network access
minimal secrets
```

------------------------------------------------------------------------

# 239. V1 AI Access

Agents IA :

``` text
research-only by default
sandboxed
no production secrets
no direct live execution
audited tool calls
```

------------------------------------------------------------------------

# 240. V1 CI/CD

Pipeline :

``` text
lint
tests
security scan
dependency scan
secret scan
build
artifact hash
approval
deploy
```

------------------------------------------------------------------------

# 241. V1 Production Checklist

``` text
[ ] MFA enabled
[ ] production credentials isolated
[ ] withdrawal permission disabled
[ ] secret manager configured
[ ] database private
[ ] TLS enforced
[ ] audit logging enabled
[ ] kill switch tested
[ ] Risk Engine fail-closed tested
[ ] order idempotency tested
[ ] reconciliation tested
[ ] backups tested
[ ] monitoring active
[ ] alerts tested
[ ] branch protections active
[ ] security scans passing
```

------------------------------------------------------------------------

# 242. V2

Ajouter :

-   stronger workload identity ;
-   automated key rotation ;
-   SBOM ;
-   signed artifacts ;
-   richer SIEM integration ;
-   policy-as-code ;
-   automated access reviews.

------------------------------------------------------------------------

# 243. V3

Ajouter :

-   HSM-backed critical keys ;
-   stronger network segmentation ;
-   advanced anomaly detection ;
-   automated containment ;
-   external penetration testing cadence ;
-   hardened production operator workflows.

------------------------------------------------------------------------

# 244. V4

Ajouter :

-   continuous authorization ;
-   autonomous security agents avec permissions limitées ;
-   adaptive anomaly detection ;
-   machine-verifiable deployment provenance ;
-   automated security evidence collection.

------------------------------------------------------------------------

# 245. Critères d'acceptation V1

La sécurité V1 est valide lorsque :

-   aucun secret n'est stocké dans Git ;
-   les clés live sont séparées des environnements de recherche ;
-   les retraits sont désactivés sur les credentials QuantLab lorsque
    possible ;
-   MFA protège les accès humains critiques ;
-   chaque service possède une identité dédiée ;
-   les permissions suivent le moindre privilège ;
-   la production est isolée ;
-   la base production n'est pas publiquement accessible ;
-   TLS protège les communications sensibles ;
-   les données persistantes critiques sont chiffrées ;
-   les dépendances sont scannées ;
-   les secrets sont scannés ;
-   les branches critiques sont protégées ;
-   le code sensible nécessite review ;
-   aucun agent IA ne peut trader directement ;
-   le Risk Engine ne peut pas être contourné ;
-   le système bloque les nouvelles expositions lorsque le risque ne
    peut pas être validé ;
-   le kill switch fonctionne ;
-   les ordres sont idempotents ;
-   les états inconnus sont réconciliés ;
-   les actions critiques sont auditées ;
-   les logs masquent les secrets ;
-   les backups sont restaurables ;
-   un incident critique peut être contenu rapidement.

------------------------------------------------------------------------

# 246. Risques principaux

## Credential Theft

Une clé compromise donne accès à une capacité critique.

## Excess Privilege

Un service ou agent possède plus de droits que nécessaire.

## Research-to-Production Escape

Un outil expérimental atteint les systèmes live.

## Supply Chain Compromise

Une dépendance ou pipeline introduit du code malveillant.

## AI Tool Abuse

Un agent utilise légitimement un outil d'une manière dangereuse.

## Risk Bypass

Une route secondaire permet d'exécuter sans validation de risque.

## Silent Configuration Change

Une limite critique change sans audit.

## False Sense of Security

Des contrôles existent sur le papier mais ne sont jamais testés.

------------------------------------------------------------------------

# 247. Architecture de sécurité cible

``` text
Human / Service / AI Agent
          ↓
       Identity
          ↓
     Authentication
          ↓
     Authorization
          ↓
     Policy Engine
          ↓
     API / Service
          ↓
Domain Validation
          ↓
Risk / Governance Boundary
          ↓
Sensitive Operation
          ↓
Audit + Monitoring
```

Pour le trading :

``` text
Strategy
   ↓
Decision Engine
   ↓
Risk Engine
   ↓
Execution Engine
   ↓
Exchange API Key
   ↓
Venue
```

avec :

``` text
NO WITHDRAWAL
LEAST PRIVILEGE
AUDIT
RECONCILIATION
KILL SWITCH
```

------------------------------------------------------------------------

# 248. Règle fondatrice

> **Dans QuantLab, aucune stratégie, aucun développeur, aucun service et
> aucun agent IA ne doit être considéré comme suffisamment fiable pour
> contourner les contrôles de sécurité et de risque.**

La sécurité doit supposer que :

``` text
software fails
humans make mistakes
credentials leak
dependencies break
models hallucinate
networks partition
exchanges behave unexpectedly
```

Le système doit donc rester capable de :

``` text
LIMIT
BLOCK
ISOLATE
REVOKE
RECONCILE
RECOVER
AUDIT
```

La sécurité de QuantLab ne consiste pas à garantir qu'aucune erreur
n'arrivera.

Elle consiste à empêcher qu'une erreur locale puisse devenir facilement
une perte incontrôlée ou une compromission générale.

------------------------------------------------------------------------

# 249. Statut

**Version : 1.0**

Documents directement liés :

-   `02-Architecture-Generale.md`
-   `03-Data-Engine.md`
-   `04-Storage-Engine.md`
-   `10-Decision-Engine.md`
-   `11-Risk-Engine.md`
-   `12-Execution-Engine.md`
-   `13-Monitoring-Engine.md`
-   `15-AI-and-Learning-Engine.md`
-   `16-Governance-Engine.md`
-   `17-AI-Development-Protocol.md`
-   `18-Testing-Strategy.md`
-   `19-Deployment-Guide.md`
-   `20-Engineering-Principles.md`
-   `21-Experiment-Registry.md`
-   `22-API-Specification.md`
-   `23-Database-Schema.md`
-   `25-Roadmap.md`

**Prochain document : `25-Roadmap.md`**
