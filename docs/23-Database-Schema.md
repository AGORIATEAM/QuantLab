# 23 --- Database Schema

**Projet : QuantLab**\
**Document : Database Schema**\
**Version : 1.0**\
**Statut : Schéma de données de référence**

------------------------------------------------------------------------

# 1. Objectif

Ce document définit le modèle de données persistant de QuantLab.

La base de données doit permettre de reconstruire l'ensemble de la
chaîne :

``` text
MARKET DATA
→ ANALYSIS
→ SCORE
→ DECISION
→ RISK
→ ORDER
→ FILL
→ POSITION
→ PERFORMANCE
→ EXPERIMENT
→ GOVERNANCE
→ AUDIT
```

Le schéma doit privilégier :

-   intégrité ;
-   traçabilité ;
-   reproductibilité ;
-   auditabilité ;
-   évolutivité ;
-   séparation des responsabilités ;
-   conservation de l'historique.

> **Une donnée critique ne doit pas seulement exister. QuantLab doit
> pouvoir déterminer d'où elle vient, quand elle a été produite, par
> quelle version du système et quelles décisions elle a provoquées.**

------------------------------------------------------------------------

# 2. Technologie de référence

Pour la V1 :

``` text
PostgreSQL
```

constitue la base transactionnelle principale.

Les données volumineuses peuvent être externalisées vers :

``` text
object storage
Parquet
time-series storage
```

selon leur nature.

------------------------------------------------------------------------

# 3. Séparation logique

Domaines recommandés :

``` text
core
market
analysis
trading
risk
execution
research
governance
monitoring
knowledge
audit
```

La séparation peut être réalisée par schemas PostgreSQL ou conventions
de tables.

------------------------------------------------------------------------

# 4. Principes de modélisation

Toutes les tables critiques doivent considérer :

``` text
primary key
created_at
updated_at where relevant
version
source
status
auditability
```

------------------------------------------------------------------------

# 5. Identifiants

Préférence :

``` text
UUID / UUIDv7
```

ou identifiants opaques équivalents.

Les IDs métier lisibles peuvent coexister :

``` text
EXP-20260824-001
STR-001
```

------------------------------------------------------------------------

# 6. Timestamps

Tous les timestamps :

``` text
TIMESTAMPTZ
UTC
```

------------------------------------------------------------------------

# 7. Valeurs financières

Utiliser :

``` text
NUMERIC
```

avec précision adaptée.

Éviter `FLOAT` pour les valeurs financières critiques.

------------------------------------------------------------------------

# 8. Enums

Les états métier doivent être contrôlés.

Selon le besoin :

``` text
PostgreSQL ENUM
CHECK constraint
reference table
application enum
```

------------------------------------------------------------------------

# 9. Soft Delete

Ne pas supprimer silencieusement les objets historiques critiques.

Lorsque nécessaire :

``` text
archived_at
deleted_at
```

avec politique explicite.

------------------------------------------------------------------------

# 10. Immutabilité

Les tables historiques telles que :

``` text
fills
audit events
decisions
experiment results
```

doivent être append-only autant que possible.

------------------------------------------------------------------------

# 11. Table `assets`

``` sql
CREATE TABLE assets (
    asset_id UUID PRIMARY KEY,
    symbol TEXT NOT NULL,
    asset_class TEXT NOT NULL,
    base_asset TEXT,
    quote_asset TEXT,
    price_precision INTEGER,
    quantity_precision INTEGER,
    tick_size NUMERIC,
    lot_size NUMERIC,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(symbol)
);
```

------------------------------------------------------------------------

# 12. Table `venues`

``` sql
CREATE TABLE venues (
    venue_id UUID PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    venue_type TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 13. Table `instruments`

Un même actif peut être négocié sur plusieurs venues.

``` sql
CREATE TABLE instruments (
    instrument_id UUID PRIMARY KEY,
    venue_id UUID NOT NULL REFERENCES venues(venue_id),
    asset_id UUID REFERENCES assets(asset_id),
    venue_symbol TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    tick_size NUMERIC NOT NULL,
    lot_size NUMERIC NOT NULL,
    min_quantity NUMERIC,
    min_notional NUMERIC,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(venue_id, venue_symbol)
);
```

------------------------------------------------------------------------

# 14. Table `market_trades`

``` sql
CREATE TABLE market_trades (
    market_trade_id UUID PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    venue_trade_id TEXT,
    event_time TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    price NUMERIC NOT NULL,
    quantity NUMERIC NOT NULL,
    aggressor_side TEXT,
    source TEXT NOT NULL
);
```

------------------------------------------------------------------------

# 15. Index market trades

``` sql
CREATE INDEX idx_market_trades_instrument_time
ON market_trades(instrument_id, event_time DESC);
```

------------------------------------------------------------------------

# 16. Table `candles`

``` sql
CREATE TABLE candles (
    candle_id UUID PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    timeframe TEXT NOT NULL,
    open_time TIMESTAMPTZ NOT NULL,
    close_time TIMESTAMPTZ NOT NULL,
    open NUMERIC NOT NULL,
    high NUMERIC NOT NULL,
    low NUMERIC NOT NULL,
    close NUMERIC NOT NULL,
    volume NUMERIC NOT NULL,
    trade_count BIGINT,
    source TEXT NOT NULL,
    data_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(instrument_id, timeframe, open_time, source)
);
```

------------------------------------------------------------------------

# 17. Candle integrity

Contraintes :

``` text
high >= open
high >= close
high >= low
low <= open
low <= close
volume >= 0
```

------------------------------------------------------------------------

# 18. Table `order_book_snapshots`

Pour les snapshots conservés :

``` sql
CREATE TABLE order_book_snapshots (
    snapshot_id UUID PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    event_time TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    sequence_number BIGINT,
    bids JSONB NOT NULL,
    asks JSONB NOT NULL,
    source TEXT NOT NULL
);
```

Pour des volumes très importants, préférer object storage ou stockage
spécialisé.

------------------------------------------------------------------------

# 19. Table `data_quality_events`

``` sql
CREATE TABLE data_quality_events (
    event_id UUID PRIMARY KEY,
    dataset_type TEXT NOT NULL,
    instrument_id UUID,
    severity TEXT NOT NULL,
    code TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    details JSONB,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 20. Table `analysis_runs`

Chaque calcul analytique significatif doit pouvoir être relié à un run.

``` sql
CREATE TABLE analysis_runs (
    analysis_run_id UUID PRIMARY KEY,
    engine_name TEXT NOT NULL,
    engine_version TEXT NOT NULL,
    config_version TEXT,
    instrument_id UUID REFERENCES instruments(instrument_id),
    timeframe TEXT,
    input_start TIMESTAMPTZ,
    input_end TIMESTAMPTZ,
    computed_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    metadata JSONB
);
```

------------------------------------------------------------------------

# 21. Table `market_structure_states`

``` sql
CREATE TABLE market_structure_states (
    structure_state_id UUID PRIMARY KEY,
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(analysis_run_id),
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    timeframe TEXT NOT NULL,
    trend TEXT NOT NULL,
    last_bos_direction TEXT,
    last_bos_time TIMESTAMPTZ,
    last_choch_direction TEXT,
    last_choch_time TIMESTAMPTZ,
    state JSONB NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL
);
```

------------------------------------------------------------------------

# 22. Table `swing_points`

``` sql
CREATE TABLE swing_points (
    swing_id UUID PRIMARY KEY,
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(analysis_run_id),
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    timeframe TEXT NOT NULL,
    swing_type TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    price NUMERIC NOT NULL,
    strength NUMERIC,
    metadata JSONB
);
```

------------------------------------------------------------------------

# 23. Table `volume_profiles`

``` sql
CREATE TABLE volume_profiles (
    profile_id UUID PRIMARY KEY,
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(analysis_run_id),
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    timeframe TEXT,
    range_start TIMESTAMPTZ NOT NULL,
    range_end TIMESTAMPTZ NOT NULL,
    poc NUMERIC,
    vah NUMERIC,
    val NUMERIC,
    total_volume NUMERIC,
    value_area_fraction NUMERIC,
    profile_data JSONB,
    computed_at TIMESTAMPTZ NOT NULL
);
```

------------------------------------------------------------------------

# 24. Table `smc_events`

``` sql
CREATE TABLE smc_events (
    smc_event_id UUID PRIMARY KEY,
    analysis_run_id UUID NOT NULL REFERENCES analysis_runs(analysis_run_id),
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    timeframe TEXT NOT NULL,
    event_type TEXT NOT NULL,
    direction TEXT,
    event_time TIMESTAMPTZ NOT NULL,
    price_low NUMERIC,
    price_high NUMERIC,
    confidence NUMERIC,
    metadata JSONB
);
```

Types possibles :

``` text
LIQUIDITY_POOL
LIQUIDITY_SWEEP
ORDER_BLOCK
FAIR_VALUE_GAP
IMBALANCE
BOS
CHOCH
```

------------------------------------------------------------------------

# 25. Table `market_contexts`

Agrège les informations nécessaires au scoring.

``` sql
CREATE TABLE market_contexts (
    context_id UUID PRIMARY KEY,
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    timeframe TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    analysis_version TEXT NOT NULL,
    structure_state_id UUID,
    profile_id UUID,
    context_data JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 26. Table `strategies`

``` sql
CREATE TABLE strategies (
    strategy_id UUID PRIMARY KEY,
    strategy_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT,
    status TEXT NOT NULL,
    current_version TEXT,
    owner TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 27. Table `strategy_versions`

``` sql
CREATE TABLE strategy_versions (
    strategy_version_id UUID PRIMARY KEY,
    strategy_id UUID NOT NULL REFERENCES strategies(strategy_id),
    version TEXT NOT NULL,
    code_commit TEXT NOT NULL,
    config_version TEXT NOT NULL,
    artifact_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(strategy_id, version)
);
```

------------------------------------------------------------------------

# 28. Table `scores`

``` sql
CREATE TABLE scores (
    score_id UUID PRIMARY KEY,
    strategy_version_id UUID NOT NULL REFERENCES strategy_versions(strategy_version_id),
    context_id UUID NOT NULL REFERENCES market_contexts(context_id),
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    total_score NUMERIC NOT NULL,
    score_version TEXT NOT NULL,
    components JSONB NOT NULL,
    reason_codes JSONB,
    computed_at TIMESTAMPTZ NOT NULL
);
```

------------------------------------------------------------------------

# 29. Score constraint

Si le score est normalisé sur 100 :

``` sql
CHECK (total_score >= 0 AND total_score <= 100)
```

------------------------------------------------------------------------

# 30. Table `decisions`

``` sql
CREATE TABLE decisions (
    decision_id UUID PRIMARY KEY,
    strategy_version_id UUID NOT NULL REFERENCES strategy_versions(strategy_version_id),
    score_id UUID REFERENCES scores(score_id),
    context_id UUID NOT NULL REFERENCES market_contexts(context_id),
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    action TEXT NOT NULL,
    confidence NUMERIC,
    decision_version TEXT NOT NULL,
    reason_codes JSONB,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ,
    status TEXT NOT NULL
);
```

------------------------------------------------------------------------

# 31. Decision actions

``` text
ENTER_LONG
ENTER_SHORT
EXIT
REDUCE
HOLD
NO_TRADE
```

------------------------------------------------------------------------

# 32. Decision immutability

Une décision créée ne doit pas être modifiée pour réécrire l'histoire.

Un changement produit une nouvelle décision.

------------------------------------------------------------------------

# 33. Table `risk_profiles`

``` sql
CREATE TABLE risk_profiles (
    risk_profile_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    limits JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(name, version)
);
```

------------------------------------------------------------------------

# 34. Table `risk_evaluations`

``` sql
CREATE TABLE risk_evaluations (
    risk_evaluation_id UUID PRIMARY KEY,
    decision_id UUID NOT NULL REFERENCES decisions(decision_id),
    risk_profile_id UUID NOT NULL REFERENCES risk_profiles(risk_profile_id),
    status TEXT NOT NULL,
    requested_quantity NUMERIC,
    approved_quantity NUMERIC,
    risk_amount NUMERIC,
    reason_codes JSONB,
    portfolio_snapshot_id UUID,
    created_at TIMESTAMPTZ NOT NULL,
    expires_at TIMESTAMPTZ
);
```

------------------------------------------------------------------------

# 35. Risk statuses

``` text
APPROVED
MODIFIED
REJECTED
```

------------------------------------------------------------------------

# 36. Table `risk_limit_events`

Toute modification de limite doit être historisée.

``` sql
CREATE TABLE risk_limit_events (
    risk_limit_event_id UUID PRIMARY KEY,
    risk_profile_id UUID NOT NULL REFERENCES risk_profiles(risk_profile_id),
    change_type TEXT NOT NULL,
    previous_value JSONB,
    new_value JSONB,
    reason TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    governance_proposal_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 37. Table `portfolio_snapshots`

``` sql
CREATE TABLE portfolio_snapshots (
    portfolio_snapshot_id UUID PRIMARY KEY,
    account_id UUID NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    equity NUMERIC NOT NULL,
    cash NUMERIC,
    unrealized_pnl NUMERIC,
    realized_pnl NUMERIC,
    gross_exposure NUMERIC,
    net_exposure NUMERIC,
    snapshot_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 38. Table `accounts`

``` sql
CREATE TABLE accounts (
    account_id UUID PRIMARY KEY,
    venue_id UUID REFERENCES venues(venue_id),
    account_code TEXT NOT NULL UNIQUE,
    environment TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 39. Environments

``` text
TEST
PAPER
SHADOW
LIMITED_LIVE
PRODUCTION
```

------------------------------------------------------------------------

# 40. Table `orders`

``` sql
CREATE TABLE orders (
    order_id UUID PRIMARY KEY,
    client_order_id TEXT NOT NULL UNIQUE,
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    decision_id UUID REFERENCES decisions(decision_id),
    risk_evaluation_id UUID REFERENCES risk_evaluations(risk_evaluation_id),
    venue_order_id TEXT,
    side TEXT NOT NULL,
    order_type TEXT NOT NULL,
    quantity NUMERIC NOT NULL,
    limit_price NUMERIC,
    stop_price NUMERIC,
    time_in_force TEXT,
    status TEXT NOT NULL,
    idempotency_key TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    submitted_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL
);
```

------------------------------------------------------------------------

# 41. Order constraints

``` text
quantity > 0
LIMIT → limit_price required
strategic live order → risk_evaluation_id required
```

------------------------------------------------------------------------

# 42. Table `order_events`

Ne pas seulement stocker l'état courant.

``` sql
CREATE TABLE order_events (
    order_event_id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(order_id),
    event_type TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    venue_event_id TEXT,
    event_time TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    payload JSONB
);
```

------------------------------------------------------------------------

# 43. Order event types

``` text
CREATED
SUBMITTED
ACKNOWLEDGED
PARTIAL_FILL
FILLED
CANCEL_REQUESTED
CANCELLED
REJECTED
EXPIRED
RECONCILED
UNKNOWN
```

------------------------------------------------------------------------

# 44. Table `fills`

``` sql
CREATE TABLE fills (
    fill_id UUID PRIMARY KEY,
    order_id UUID NOT NULL REFERENCES orders(order_id),
    venue_fill_id TEXT,
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    side TEXT NOT NULL,
    quantity NUMERIC NOT NULL,
    price NUMERIC NOT NULL,
    fee_amount NUMERIC,
    fee_currency TEXT,
    event_time TIMESTAMPTZ NOT NULL,
    received_at TIMESTAMPTZ NOT NULL,
    UNIQUE(order_id, venue_fill_id)
);
```

------------------------------------------------------------------------

# 45. Fill immutability

Les fills sont des faits historiques.

Ils ne doivent pas être réécrits silencieusement.

------------------------------------------------------------------------

# 46. Table `positions`

``` sql
CREATE TABLE positions (
    position_id UUID PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    instrument_id UUID NOT NULL REFERENCES instruments(instrument_id),
    quantity NUMERIC NOT NULL,
    average_entry_price NUMERIC,
    realized_pnl NUMERIC NOT NULL DEFAULT 0,
    unrealized_pnl NUMERIC,
    status TEXT NOT NULL,
    version BIGINT NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL,
    UNIQUE(account_id, instrument_id)
);
```

------------------------------------------------------------------------

# 47. Position source of truth

La position locale doit être régulièrement réconciliée avec la venue.

------------------------------------------------------------------------

# 48. Table `position_events`

``` sql
CREATE TABLE position_events (
    position_event_id UUID PRIMARY KEY,
    position_id UUID NOT NULL REFERENCES positions(position_id),
    event_type TEXT NOT NULL,
    quantity_before NUMERIC,
    quantity_after NUMERIC,
    source_fill_id UUID REFERENCES fills(fill_id),
    event_time TIMESTAMPTZ NOT NULL,
    metadata JSONB
);
```

------------------------------------------------------------------------

# 49. Table `reconciliation_runs`

``` sql
CREATE TABLE reconciliation_runs (
    reconciliation_run_id UUID PRIMARY KEY,
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    status TEXT NOT NULL,
    mismatch_count INTEGER NOT NULL DEFAULT 0,
    metadata JSONB
);
```

------------------------------------------------------------------------

# 50. Table `reconciliation_mismatches`

``` sql
CREATE TABLE reconciliation_mismatches (
    mismatch_id UUID PRIMARY KEY,
    reconciliation_run_id UUID NOT NULL REFERENCES reconciliation_runs(reconciliation_run_id),
    entity_type TEXT NOT NULL,
    entity_id TEXT,
    mismatch_type TEXT NOT NULL,
    local_value JSONB,
    external_value JSONB,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
```

------------------------------------------------------------------------

# 51. Table `experiments`

Alignée avec `21-Experiment-Registry.md`.

``` sql
CREATE TABLE experiments (
    experiment_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    experiment_type TEXT NOT NULL,
    status TEXT NOT NULL,
    owner TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    baseline_experiment_id TEXT REFERENCES experiments(experiment_id),
    parent_experiment_id TEXT REFERENCES experiments(experiment_id),
    code_commit TEXT NOT NULL,
    dataset_version TEXT NOT NULL,
    config_version TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);
```

------------------------------------------------------------------------

# 52. Table `experiment_runs`

``` sql
CREATE TABLE experiment_runs (
    run_id UUID PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
    environment TEXT NOT NULL,
    seed BIGINT,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    runtime_metadata JSONB
);
```

------------------------------------------------------------------------

# 53. Table `experiment_metrics`

``` sql
CREATE TABLE experiment_metrics (
    metric_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES experiment_runs(run_id),
    metric_name TEXT NOT NULL,
    metric_value NUMERIC,
    segment_type TEXT,
    segment_value TEXT,
    metadata JSONB
);
```

------------------------------------------------------------------------

# 54. Table `experiment_parameters`

``` sql
CREATE TABLE experiment_parameters (
    parameter_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES experiment_runs(run_id),
    parameter_name TEXT NOT NULL,
    parameter_value JSONB NOT NULL
);
```

------------------------------------------------------------------------

# 55. Table `experiment_artifacts`

``` sql
CREATE TABLE experiment_artifacts (
    artifact_id UUID PRIMARY KEY,
    run_id UUID NOT NULL REFERENCES experiment_runs(run_id),
    artifact_type TEXT NOT NULL,
    storage_uri TEXT NOT NULL,
    content_hash TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 56. Table `experiment_reviews`

``` sql
CREATE TABLE experiment_reviews (
    review_id UUID PRIMARY KEY,
    experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
    reviewer_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 57. Table `experiment_relationships`

``` sql
CREATE TABLE experiment_relationships (
    relationship_id UUID PRIMARY KEY,
    source_experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
    target_experiment_id TEXT NOT NULL REFERENCES experiments(experiment_id),
    relationship_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Types :

``` text
PARENT_OF
BASELINE_OF
REPRODUCES
SUPERSEDES
CHALLENGES
```

------------------------------------------------------------------------

# 58. Table `knowledge_items`

``` sql
CREATE TABLE knowledge_items (
    knowledge_id UUID PRIMARY KEY,
    title TEXT NOT NULL,
    knowledge_type TEXT NOT NULL,
    status TEXT NOT NULL,
    content TEXT NOT NULL,
    confidence NUMERIC,
    source_type TEXT,
    source_id TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 59. Knowledge statuses

``` text
DRAFT
VALIDATED
ACTIVE
SUPERSEDED
REJECTED
ARCHIVED
```

------------------------------------------------------------------------

# 60. Table `knowledge_sources`

``` sql
CREATE TABLE knowledge_sources (
    knowledge_source_id UUID PRIMARY KEY,
    knowledge_id UUID NOT NULL REFERENCES knowledge_items(knowledge_id),
    source_type TEXT NOT NULL,
    source_reference TEXT NOT NULL,
    metadata JSONB
);
```

------------------------------------------------------------------------

# 61. Table `ai_agents`

``` sql
CREATE TABLE ai_agents (
    agent_id UUID PRIMARY KEY,
    agent_code TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    status TEXT NOT NULL,
    model_provider TEXT,
    model_name TEXT,
    permission_profile_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 62. Table `ai_tasks`

``` sql
CREATE TABLE ai_tasks (
    ai_task_id UUID PRIMARY KEY,
    agent_id UUID NOT NULL REFERENCES ai_agents(agent_id),
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    input_reference JSONB,
    output_reference JSONB,
    prompt_version TEXT,
    model_version TEXT,
    correlation_id UUID,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 63. Table `ai_tool_calls`

``` sql
CREATE TABLE ai_tool_calls (
    tool_call_id UUID PRIMARY KEY,
    ai_task_id UUID NOT NULL REFERENCES ai_tasks(ai_task_id),
    tool_name TEXT NOT NULL,
    permission_scope JSONB,
    request_metadata JSONB,
    result_metadata JSONB,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Ne pas stocker les secrets bruts.

------------------------------------------------------------------------

# 64. Table `governance_proposals`

``` sql
CREATE TABLE governance_proposals (
    proposal_id UUID PRIMARY KEY,
    proposal_type TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    proposer_id TEXT NOT NULL,
    status TEXT NOT NULL,
    target_environment TEXT,
    artifact_hash TEXT,
    evidence JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);
```

------------------------------------------------------------------------

# 65. Governance statuses

``` text
DRAFT
SUBMITTED
UNDER_REVIEW
APPROVED
REJECTED
EXPIRED
EXECUTED
CANCELLED
```

------------------------------------------------------------------------

# 66. Table `governance_approvals`

``` sql
CREATE TABLE governance_approvals (
    approval_id UUID PRIMARY KEY,
    proposal_id UUID NOT NULL REFERENCES governance_proposals(proposal_id),
    approver_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    scope JSONB,
    artifact_hash TEXT,
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 67. Self-approval prevention

Les règles métier doivent empêcher les approbations interdites.

La base peut renforcer certaines règles, mais la politique principale
appartient au Governance Engine.

------------------------------------------------------------------------

# 68. Table `deployments`

``` sql
CREATE TABLE deployments (
    deployment_id UUID PRIMARY KEY,
    environment TEXT NOT NULL,
    service_name TEXT NOT NULL,
    artifact_version TEXT NOT NULL,
    artifact_hash TEXT NOT NULL,
    config_version TEXT,
    proposal_id UUID REFERENCES governance_proposals(proposal_id),
    status TEXT NOT NULL,
    deployed_by TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    rollback_of UUID REFERENCES deployments(deployment_id)
);
```

------------------------------------------------------------------------

# 69. Table `incidents`

``` sql
CREATE TABLE incidents (
    incident_id UUID PRIMARY KEY,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TIMESTAMPTZ NOT NULL,
    resolved_at TIMESTAMPTZ,
    owner TEXT,
    summary TEXT,
    metadata JSONB
);
```

------------------------------------------------------------------------

# 70. Incident statuses

``` text
OPEN
INVESTIGATING
MITIGATED
RESOLVED
CLOSED
```

------------------------------------------------------------------------

# 71. Table `alerts`

``` sql
CREATE TABLE alerts (
    alert_id UUID PRIMARY KEY,
    alert_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    source_service TEXT NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    triggered_at TIMESTAMPTZ NOT NULL,
    acknowledged_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ
);
```

------------------------------------------------------------------------

# 72. Table `system_health_events`

``` sql
CREATE TABLE system_health_events (
    health_event_id UUID PRIMARY KEY,
    service_name TEXT NOT NULL,
    status TEXT NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    details JSONB
);
```

États :

``` text
HEALTHY
DEGRADED
UNHEALTHY
HALTED
```

------------------------------------------------------------------------

# 73. Table `audit_events`

Table centrale append-only.

``` sql
CREATE TABLE audit_events (
    audit_event_id UUID PRIMARY KEY,
    actor_type TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    environment TEXT,
    request_id TEXT,
    correlation_id TEXT,
    result TEXT NOT NULL,
    metadata JSONB,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 74. Audit requirements

Auditer au minimum :

``` text
authentication-sensitive actions
risk changes
strategy activation
order actions
kill switch
governance approvals
deployments
admin changes
AI privileged actions
```

------------------------------------------------------------------------

# 75. Audit immutability

La table d'audit ne doit pas être modifiable par les rôles applicatifs
ordinaires.

------------------------------------------------------------------------

# 76. Table `idempotency_keys`

``` sql
CREATE TABLE idempotency_keys (
    idempotency_key TEXT PRIMARY KEY,
    actor_id TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    response_status INTEGER,
    response_body JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
);
```

------------------------------------------------------------------------

# 77. Table `outbox_events`

Pour publication transactionnelle fiable :

``` sql
CREATE TABLE outbox_events (
    outbox_event_id UUID PRIMARY KEY,
    aggregate_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_version INTEGER NOT NULL,
    payload JSONB NOT NULL,
    correlation_id TEXT,
    causation_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ
);
```

------------------------------------------------------------------------

# 78. Transactional Outbox

Workflow :

``` text
DB transaction
├── business state
└── outbox event
        ↓
publisher
        ↓
event bus
```

Cela évite le classique :

``` text
database committed
event publication failed
```

------------------------------------------------------------------------

# 79. Table `inbox_events`

Pour les consumers idempotents :

``` sql
CREATE TABLE inbox_events (
    consumer_name TEXT NOT NULL,
    event_id UUID NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (consumer_name, event_id)
);
```

------------------------------------------------------------------------

# 80. Configuration Registry

``` sql
CREATE TABLE configuration_versions (
    config_version_id UUID PRIMARY KEY,
    config_name TEXT NOT NULL,
    version TEXT NOT NULL,
    environment TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    storage_reference TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(config_name, version, environment)
);
```

------------------------------------------------------------------------

# 81. No Secrets in Configuration Tables

Les secrets doivent être référencés depuis un secret manager, jamais
stockés en clair.

------------------------------------------------------------------------

# 82. Model Registry

``` sql
CREATE TABLE model_versions (
    model_version_id UUID PRIMARY KEY,
    model_name TEXT NOT NULL,
    version TEXT NOT NULL,
    model_type TEXT NOT NULL,
    artifact_uri TEXT NOT NULL,
    artifact_hash TEXT NOT NULL,
    training_experiment_id TEXT REFERENCES experiments(experiment_id),
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(model_name, version)
);
```

------------------------------------------------------------------------

# 83. Prompt Registry

``` sql
CREATE TABLE prompt_versions (
    prompt_version_id UUID PRIMARY KEY,
    prompt_name TEXT NOT NULL,
    version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    storage_reference TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(prompt_name, version)
);
```

------------------------------------------------------------------------

# 84. Correlation

Les tables de workflow doivent conserver les liens nécessaires pour
reconstruire :

``` text
context_id
score_id
decision_id
risk_evaluation_id
order_id
fill_id
```

------------------------------------------------------------------------

# 85. End-to-End Query

Le système doit pouvoir répondre :

``` text
Why did order ord_123 exist?
```

et retrouver :

``` text
order
→ risk evaluation
→ decision
→ score
→ market context
→ analysis
→ source data
```

------------------------------------------------------------------------

# 86. Foreign Keys

Utiliser les foreign keys pour les relations critiques lorsque leur coût
reste acceptable.

------------------------------------------------------------------------

# 87. Avoid Referential Integrity Theater

Ne pas supprimer les FK uniquement parce qu'un benchmark synthétique
gagne quelques millisecondes.

L'intégrité coûte généralement moins cher qu'une enquête après
corruption.

------------------------------------------------------------------------

# 88. JSONB

Utiliser JSONB pour :

``` text
extensible metadata
engine-specific details
rarely queried payloads
```

------------------------------------------------------------------------

# 89. Avoid JSONB Everywhere

Les champs importants, filtrés ou contraints fréquemment doivent être
des colonnes structurées.

------------------------------------------------------------------------

# 90. Schema Evolution

Toute modification doit passer par une migration versionnée.

------------------------------------------------------------------------

# 91. Migration Naming

Exemple :

``` text
20260824_001_create_orders.sql
```

------------------------------------------------------------------------

# 92. Migration Tool

Utiliser un outil adapté au stack choisi.

Exemples possibles :

``` text
Alembic
Flyway
Liquibase
```

Un seul doit devenir le standard officiel.

------------------------------------------------------------------------

# 93. Forward-Only Preference

Les migrations production doivent privilégier des transformations
forward-safe.

------------------------------------------------------------------------

# 94. Expand / Migrate / Contract

Pour les changements importants :

``` text
1. add new schema
2. support both
3. migrate data
4. switch consumers
5. remove old schema later
```

------------------------------------------------------------------------

# 95. Destructive Migrations

Doivent nécessiter :

``` text
backup
review
approval
rollback/recovery plan
```

------------------------------------------------------------------------

# 96. Database Version

Le déploiement doit connaître la version du schéma attendue.

------------------------------------------------------------------------

# 97. Application Compatibility

Une application ne doit pas démarrer si la version DB est incompatible,
sauf stratégie explicitement prévue.

------------------------------------------------------------------------

# 98. Index Strategy

Créer des index selon les requêtes réelles.

Priorités probables :

``` text
timestamps
instrument + time
status
foreign keys
experiment IDs
order IDs
correlation IDs
```

------------------------------------------------------------------------

# 99. Index `orders`

``` sql
CREATE INDEX idx_orders_account_status
ON orders(account_id, status);

CREATE INDEX idx_orders_instrument_created
ON orders(instrument_id, created_at DESC);
```

------------------------------------------------------------------------

# 100. Index `decisions`

``` sql
CREATE INDEX idx_decisions_instrument_created
ON decisions(instrument_id, created_at DESC);
```

------------------------------------------------------------------------

# 101. Index `audit_events`

``` sql
CREATE INDEX idx_audit_events_resource
ON audit_events(resource_type, resource_id);

CREATE INDEX idx_audit_events_time
ON audit_events(event_time DESC);
```

------------------------------------------------------------------------

# 102. Partial Indexes

Utiliser lorsque pertinent.

Exemple :

``` sql
CREATE INDEX idx_open_orders
ON orders(account_id, instrument_id)
WHERE status IN ('SUBMITTED', 'ACKNOWLEDGED', 'PARTIALLY_FILLED');
```

------------------------------------------------------------------------

# 103. Partitioning

À envisager pour :

``` text
market_trades
candles
audit_events
order_events
```

si les volumes le justifient.

------------------------------------------------------------------------

# 104. Time Partitioning

Exemple :

``` text
monthly partitions
```

pour les données temporelles massives.

------------------------------------------------------------------------

# 105. No Premature Partitioning

La V1 ne doit pas devenir un musée de fonctionnalités PostgreSQL avant
d'avoir des volumes qui les justifient.

------------------------------------------------------------------------

# 106. Retention

Définir une politique par type de données.

------------------------------------------------------------------------

# 107. Market Raw Data Retention

Selon coût et licence :

``` text
hot
warm
archive
```

------------------------------------------------------------------------

# 108. Trading Records Retention

Les données d'exécution, risque et audit doivent avoir une rétention
longue.

------------------------------------------------------------------------

# 109. Experiment Retention

Les métadonnées d'expériences doivent être conservées durablement.

------------------------------------------------------------------------

# 110. Archival

Les données anciennes peuvent être transférées vers object storage.

------------------------------------------------------------------------

# 111. Backups

La base critique doit disposer de :

``` text
automated backups
point-in-time recovery
retention policy
```

------------------------------------------------------------------------

# 112. Restore Tests

Les backups doivent être restaurés périodiquement dans un environnement
isolé.

------------------------------------------------------------------------

# 113. RPO

Définir le Recovery Point Objective par environnement.

------------------------------------------------------------------------

# 114. RTO

Définir le Recovery Time Objective.

------------------------------------------------------------------------

# 115. Replication

À maturité :

``` text
primary
read replica
```

peut séparer certaines charges analytiques.

------------------------------------------------------------------------

# 116. No Research Queries on Critical Primary

Les recherches lourdes ne doivent pas saturer la base transactionnelle
live.

------------------------------------------------------------------------

# 117. Read Replica

Peut servir :

``` text
dashboards
analytics
reporting
```

avec prise en compte du lag.

------------------------------------------------------------------------

# 118. Connection Pooling

Utiliser un pool de connexions.

------------------------------------------------------------------------

# 119. Connection Limits

Chaque service doit avoir des limites explicites.

------------------------------------------------------------------------

# 120. Transaction Boundaries

Les transactions doivent être courtes et centrées sur une unité métier
cohérente.

------------------------------------------------------------------------

# 121. Long Transactions

Éviter les transactions longues qui bloquent :

``` text
vacuum
locks
concurrent writes
```

------------------------------------------------------------------------

# 122. Isolation Levels

Choisir explicitement selon le workflow.

------------------------------------------------------------------------

# 123. Optimistic Locking

Pour les ressources concurrentes :

``` text
version
```

peut être utilisé.

------------------------------------------------------------------------

# 124. Position Update Concurrency

Les positions nécessitent une stratégie stricte contre les lost updates.

------------------------------------------------------------------------

# 125. Unique Constraints

Utiliser pour empêcher les doublons métier.

Exemples :

``` text
client_order_id
venue fill ID
experiment ID
strategy version
```

------------------------------------------------------------------------

# 126. Check Constraints

Exemples :

``` text
quantity > 0
confidence between 0 and 1
approved_quantity <= requested_quantity
```

selon sémantique.

------------------------------------------------------------------------

# 127. Database Constraints Are Valuable

Ne pas dépendre uniquement de validations applicatives pour les
invariants simples.

------------------------------------------------------------------------

# 128. Application + Database Validation

Les deux couches se complètent.

------------------------------------------------------------------------

# 129. Security Roles

Rôles conceptuels :

``` text
ql_readonly
ql_application
ql_execution
ql_migration
ql_audit_reader
ql_admin
```

------------------------------------------------------------------------

# 130. Least Privilege

Chaque service doit avoir un rôle DB adapté.

------------------------------------------------------------------------

# 131. Execution Role

L'Execution Engine ne doit pas disposer de droits administratifs
généraux.

------------------------------------------------------------------------

# 132. Migration Role

Les migrations utilisent une identité distincte.

------------------------------------------------------------------------

# 133. Read-Only Analytics

Les outils analytiques doivent préférer un accès read-only.

------------------------------------------------------------------------

# 134. Row-Level Security

Peut être utilisée si QuantLab devient multi-tenant ou nécessite une
isolation fine.

------------------------------------------------------------------------

# 135. Encryption

Données :

``` text
encrypted in transit
encrypted at rest
```

------------------------------------------------------------------------

# 136. Sensitive Data

Minimiser le stockage de données personnelles ou secrets.

------------------------------------------------------------------------

# 137. Secret References

Stocker :

``` text
secret_reference
```

plutôt que le secret.

------------------------------------------------------------------------

# 138. Database Audit

Les changements administratifs doivent être auditables.

------------------------------------------------------------------------

# 139. Query Logging

Activer avec prudence pour éviter d'enregistrer des données sensibles.

------------------------------------------------------------------------

# 140. Performance Monitoring

Surveiller :

``` text
slow queries
locks
connections
cache hit ratio
replication lag
storage
```

------------------------------------------------------------------------

# 141. Slow Query Threshold

Définir un seuil adapté aux workloads.

------------------------------------------------------------------------

# 142. Query Plans

Analyser avec :

``` text
EXPLAIN
EXPLAIN ANALYZE
```

dans des environnements sûrs.

------------------------------------------------------------------------

# 143. N+1 Queries

Les APIs doivent éviter les patterns N+1.

------------------------------------------------------------------------

# 144. Bulk Inserts

Pour les données marché :

``` text
batching
COPY
```

peuvent être utilisés.

------------------------------------------------------------------------

# 145. Data Ingestion

Le Data Engine ne doit pas effectuer une transaction par tick si le
volume rend cela absurde.

------------------------------------------------------------------------

# 146. Time-Series Data

À grande échelle, évaluer :

``` text
TimescaleDB
ClickHouse
Parquet lake
```

mais uniquement sur preuve de besoin.

------------------------------------------------------------------------

# 147. Object Storage

Recommandé pour :

``` text
raw datasets
experiment artifacts
model artifacts
large reports
historical snapshots
```

------------------------------------------------------------------------

# 148. Database Stores Metadata

La DB relationnelle conserve les références, hashes et métadonnées des
artefacts externes.

------------------------------------------------------------------------

# 149. Content Hash

Tout artefact critique externe doit idéalement avoir :

``` text
SHA-256
```

ou équivalent.

------------------------------------------------------------------------

# 150. Dataset Registry

Table conceptuelle :

``` sql
CREATE TABLE datasets (
    dataset_id UUID PRIMARY KEY,
    dataset_name TEXT NOT NULL,
    version TEXT NOT NULL,
    storage_uri TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    source TEXT NOT NULL,
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    status TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(dataset_name, version)
);
```

------------------------------------------------------------------------

# 151. Dataset Lineage

``` sql
CREATE TABLE dataset_lineage (
    lineage_id UUID PRIMARY KEY,
    parent_dataset_id UUID NOT NULL REFERENCES datasets(dataset_id),
    child_dataset_id UUID NOT NULL REFERENCES datasets(dataset_id),
    transformation TEXT NOT NULL,
    code_commit TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 152. Reproducibility Chain

Une expérience doit pouvoir résoudre :

``` text
experiment
→ dataset version
→ dataset lineage
→ source data
```

------------------------------------------------------------------------

# 153. Reason Codes

Pour les reason codes très utilisés, une table de référence peut être
créée :

``` sql
CREATE TABLE reason_codes (
    reason_code TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT
);
```

------------------------------------------------------------------------

# 154. Event Schema

Table optionnelle :

``` sql
CREATE TABLE event_schema_versions (
    event_type TEXT NOT NULL,
    version INTEGER NOT NULL,
    schema_definition JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(event_type, version)
);
```

------------------------------------------------------------------------

# 155. Feature Registry

Pour ML :

``` sql
CREATE TABLE feature_sets (
    feature_set_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    definition JSONB NOT NULL,
    code_commit TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(name, version)
);
```

------------------------------------------------------------------------

# 156. Model Predictions

``` sql
CREATE TABLE model_predictions (
    prediction_id UUID PRIMARY KEY,
    model_version_id UUID NOT NULL REFERENCES model_versions(model_version_id),
    context_id UUID REFERENCES market_contexts(context_id),
    prediction_time TIMESTAMPTZ NOT NULL,
    prediction JSONB NOT NULL,
    confidence NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 157. Prediction Outcomes

Les outcomes peuvent être enregistrés séparément pour évaluer le drift.

------------------------------------------------------------------------

# 158. Table `model_evaluations`

``` sql
CREATE TABLE model_evaluations (
    evaluation_id UUID PRIMARY KEY,
    model_version_id UUID NOT NULL REFERENCES model_versions(model_version_id),
    evaluation_window_start TIMESTAMPTZ NOT NULL,
    evaluation_window_end TIMESTAMPTZ NOT NULL,
    metrics JSONB NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 159. Kill Switch State

``` sql
CREATE TABLE kill_switch_events (
    kill_switch_event_id UUID PRIMARY KEY,
    scope TEXT NOT NULL,
    action TEXT NOT NULL,
    reason TEXT NOT NULL,
    actor_id TEXT NOT NULL,
    proposal_id UUID,
    event_time TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 160. Current Kill Switch State

L'état courant doit pouvoir être dérivé ou conservé dans une table
dédiée avec versioning.

L'historique d'événements reste obligatoire.

------------------------------------------------------------------------

# 161. Table `service_versions`

``` sql
CREATE TABLE service_versions (
    service_name TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    artifact_hash TEXT,
    environment TEXT NOT NULL,
    deployed_at TIMESTAMPTZ NOT NULL
);
```

------------------------------------------------------------------------

# 162. Schema Metadata

``` sql
CREATE TABLE schema_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

------------------------------------------------------------------------

# 163. Naming Conventions

Tables :

``` text
snake_case
plural nouns
```

Colonnes :

``` text
snake_case
```

Foreign keys :

``` text
<entity>_id
```

------------------------------------------------------------------------

# 164. Boolean Naming

Préférer :

``` text
is_active
is_enabled
has_more
```

------------------------------------------------------------------------

# 165. Timestamp Naming

Préférer :

``` text
created_at
updated_at
event_time
received_at
expires_at
```

------------------------------------------------------------------------

# 166. Event Time vs Created At

Ne pas confondre :

``` text
event_time
=
moment métier/source

created_at
=
moment d’écriture locale
```

------------------------------------------------------------------------

# 167. Received At

Pour les données externes :

``` text
received_at
```

permet de mesurer la latence d'ingestion.

------------------------------------------------------------------------

# 168. Version Columns

Utiliser des versions lorsque les mises à jour concurrentes le
nécessitent.

------------------------------------------------------------------------

# 169. Status Columns

Les statuts doivent utiliser une taxonomie documentée.

------------------------------------------------------------------------

# 170. Metadata Columns

`metadata JSONB` est acceptable pour les extensions non essentielles.

------------------------------------------------------------------------

# 171. No Generic Data Blob for Core Domain

Ne pas réduire le système à :

``` text
id
type
data JSONB
```

pour tous les domaines.

Ce serait flexible jusqu'au jour où quelqu'un devra garantir quelque
chose.

------------------------------------------------------------------------

# 172. Materialized Views

Peuvent être utilisées pour :

``` text
performance dashboards
aggregated analytics
```

------------------------------------------------------------------------

# 173. Views

Créer des views pour simplifier certaines lectures sans dupliquer la
donnée.

------------------------------------------------------------------------

# 174. Current Position View

Peut combiner :

``` text
position
latest market price
PnL
```

mais la vue ne devient pas source d'autorité.

------------------------------------------------------------------------

# 175. Performance Tables

Les performances calculées peuvent être stockées comme snapshots.

``` sql
CREATE TABLE performance_snapshots (
    performance_snapshot_id UUID PRIMARY KEY,
    strategy_id UUID REFERENCES strategies(strategy_id),
    account_id UUID REFERENCES accounts(account_id),
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,
    metrics JSONB NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL
);
```

------------------------------------------------------------------------

# 176. Daily PnL

Une table dédiée peut accélérer les contrôles de risque :

``` sql
CREATE TABLE daily_account_metrics (
    account_id UUID NOT NULL REFERENCES accounts(account_id),
    trading_date DATE NOT NULL,
    realized_pnl NUMERIC NOT NULL DEFAULT 0,
    unrealized_pnl NUMERIC,
    fees NUMERIC NOT NULL DEFAULT 0,
    trade_count INTEGER NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY(account_id, trading_date)
);
```

------------------------------------------------------------------------

# 177. Risk Performance Tradeoff

Les données utilisées pour les hard limits live doivent être calculées
par un chemin fiable et contrôlé.

------------------------------------------------------------------------

# 178. Caches

Redis ou équivalent peut être utilisé pour :

``` text
ephemeral state
locks
rate limiting
fast cache
```

mais pas comme unique stockage de faits financiers critiques.

------------------------------------------------------------------------

# 179. Distributed Locks

À utiliser avec prudence.

Préférer une architecture évitant le besoin de locks distribués lorsque
possible.

------------------------------------------------------------------------

# 180. Advisory Locks

PostgreSQL advisory locks peuvent être utilisés dans certains workflows
internes clairement délimités.

------------------------------------------------------------------------

# 181. Leader Election

Ne pas improviser un protocole distribué artisanal si l'infrastructure
fournit déjà une solution éprouvée.

------------------------------------------------------------------------

# 182. Database Transactions for Order Creation

Exemple :

``` text
validate risk approval
↓
create order
↓
create order event
↓
create outbox event
↓
COMMIT
```

------------------------------------------------------------------------

# 183. Fill Transaction

``` text
insert fill
↓
insert order event
↓
update order state
↓
update position
↓
insert position event
↓
outbox event
↓
COMMIT
```

------------------------------------------------------------------------

# 184. Duplicate Fill Protection

La contrainte unique sur l'identifiant venue empêche les doubles effets.

------------------------------------------------------------------------

# 185. Reconciliation Overrides

Les corrections issues de reconciliation doivent produire des événements
explicites.

------------------------------------------------------------------------

# 186. No Silent Manual SQL

Les corrections production ne doivent pas être effectuées par SQL manuel
non audité sauf procédure break-glass.

------------------------------------------------------------------------

# 187. Break-Glass

Toute intervention directe doit enregistrer :

``` text
operator
reason
ticket/incident
before
after
timestamp
```

------------------------------------------------------------------------

# 188. Data Classification

Classer les données :

``` text
PUBLIC
INTERNAL
CONFIDENTIAL
SECRET
```

------------------------------------------------------------------------

# 189. Secret Classification

Les secrets ne doivent pas être dans PostgreSQL sauf nécessité
spécifique et mécanisme sécurisé explicitement validé.

------------------------------------------------------------------------

# 190. Access Reviews

Les droits DB doivent être revus périodiquement.

------------------------------------------------------------------------

# 191. Production Isolation

La base production doit être isolée des environnements :

``` text
development
test
research
```

------------------------------------------------------------------------

# 192. No Production Data by Default

Les développeurs et agents ne doivent pas avoir accès par défaut aux
données live sensibles.

------------------------------------------------------------------------

# 193. Test Database

Les tests d'intégration utilisent une base dédiée et reproductible.

------------------------------------------------------------------------

# 194. Migration Tests

La CI doit tester :

``` text
empty DB → latest
previous supported schema → latest
```

------------------------------------------------------------------------

# 195. Constraint Tests

Les invariants DB critiques doivent être testés.

------------------------------------------------------------------------

# 196. Backup Tests

La restauration doit être testée automatiquement ou périodiquement.

------------------------------------------------------------------------

# 197. Schema Documentation

Le repository doit contenir :

``` text
migrations/
schema docs/
ER diagrams/
```

------------------------------------------------------------------------

# 198. ER Diagram

Relations centrales :

``` text
Strategy Version
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

# 199. Research ER

``` text
Experiment
   ↓
Experiment Run
   ├── Metrics
   ├── Parameters
   ├── Artifacts
   └── Reviews
```

------------------------------------------------------------------------

# 200. Governance ER

``` text
Proposal
   ↓
Approvals
   ↓
Deployment / Risk Change / Strategy Activation
```

------------------------------------------------------------------------

# 201. Data Lineage ER

``` text
Raw Data
   ↓
Dataset
   ↓
Analysis Run
   ↓
Market Context
   ↓
Score
   ↓
Decision
```

------------------------------------------------------------------------

# 202. Audit ER

``` text
Actor
↓
Action
↓
Resource
↓
Result
↓
Correlation ID
```

------------------------------------------------------------------------

# 203. V1 Mandatory Tables

La V1 doit au minimum contenir :

``` text
assets
venues
instruments
candles
analysis_runs
market_contexts
strategies
strategy_versions
scores
decisions
risk_profiles
risk_evaluations
accounts
orders
order_events
fills
positions
position_events
portfolio_snapshots
experiments
experiment_runs
experiment_metrics
governance_proposals
governance_approvals
deployments
audit_events
idempotency_keys
outbox_events
```

------------------------------------------------------------------------

# 204. V1 Optional Tables

Selon priorité :

``` text
market_trades
order_book_snapshots
knowledge_items
ai_tasks
model registry
feature registry
```

------------------------------------------------------------------------

# 205. V1 Storage Architecture

``` text
PostgreSQL
│
├── transactional state
├── metadata
├── risk
├── execution
├── governance
└── audit references

Object Storage
│
├── raw market datasets
├── Parquet
├── experiment artifacts
├── models
└── large reports
```

------------------------------------------------------------------------

# 206. V1 Migration Policy

Aucune modification manuelle du schema production.

Tout passe par :

``` text
migration file
→ review
→ test
→ deployment
```

------------------------------------------------------------------------

# 207. V1 Backup Policy

Avant live :

``` text
automated backups
PITR
restore test
documented recovery
```

doivent exister.

------------------------------------------------------------------------

# 208. V1 Security Policy

Avant live :

``` text
separate DB roles
TLS
encrypted storage
secret manager
audit permissions
production isolation
```

------------------------------------------------------------------------

# 209. V1 Data Integrity

Avant live, les contraintes suivantes doivent être garanties :

``` text
no duplicate fills
no duplicate client orders
no negative order quantities
no orphan risk-approved live order
valid timestamps
valid instrument references
```

------------------------------------------------------------------------

# 210. V1 Observability

Surveiller :

``` text
DB availability
connections
query latency
locks
disk usage
replication/PITR status
failed migrations
```

------------------------------------------------------------------------

# 211. V2

Ajouter :

-   partitioning selon volume ;
-   read replicas ;
-   richer lineage ;
-   model/prompt registries ;
-   knowledge graph relations ;
-   automated archival ;
-   advanced database auditing.

------------------------------------------------------------------------

# 212. V3

Ajouter :

-   specialized analytical/time-series storage ;
-   automated tiering ;
-   multi-region recovery si nécessaire ;
-   stronger lineage validation ;
-   automated data contracts.

------------------------------------------------------------------------

# 213. V4

Ajouter :

-   policy-driven data lifecycle ;
-   autonomous anomaly detection ;
-   self-diagnosing query performance ;
-   automated schema compatibility analysis sous gouvernance.

------------------------------------------------------------------------

# 214. Critères d'acceptation

Le schéma V1 est valide lorsque :

-   PostgreSQL est la source transactionnelle principale ;
-   tous les IDs critiques sont uniques ;
-   tous les timestamps sont UTC ;
-   les valeurs financières utilisent une précision adaptée ;
-   les données critiques sont reliées par foreign keys ou contrats
    équivalents ;
-   les décisions sont immutables ;
-   les fills sont immutables ;
-   les doublons d'exécution sont empêchés ;
-   l'historique des ordres est conservé ;
-   les positions peuvent être réconciliées ;
-   chaque ordre stratégique peut remonter à une décision de risque ;
-   chaque décision peut remonter à son contexte de marché ;
-   les expériences sont reproductibles ;
-   les promotions sont reliées aux preuves ;
-   les actions sensibles sont auditées ;
-   les migrations sont versionnées ;
-   les backups sont automatiques ;
-   les restaurations sont testées ;
-   les rôles DB suivent le moindre privilège ;
-   aucun secret n'est stocké en clair ;
-   les artefacts externes disposent de références et hashes ;
-   les workloads de recherche ne peuvent pas compromettre la base live.

------------------------------------------------------------------------

# 215. Risques principaux

## Schema Drift

Le code suppose un schéma différent de la base réellement déployée.

## Duplicate Effects

Des événements rejoués créent plusieurs fills, ordres ou mises à jour.

## Hidden Mutation

Une donnée historique est modifiée sans audit.

## JSONB Overuse

La flexibilité détruit progressivement les contraintes et la lisibilité.

## Research Load

Une requête analytique lourde ralentit les chemins live.

## Privilege Creep

Les services accumulent des droits inutiles.

## Backup Illusion

Les backups existent, mais personne n'a vérifié qu'ils peuvent être
restaurés.

------------------------------------------------------------------------

# 216. Workflow de traçabilité

``` text
Candle / Market Data
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
Order Events
↓
Fill
↓
Position Event
↓
Portfolio Snapshot
↓
Performance
```

En parallèle :

``` text
Experiment
↓
Evidence
↓
Governance Proposal
↓
Approval
↓
Deployment
↓
Audit
```

------------------------------------------------------------------------

# 217. Règle fondatrice

> **La base QuantLab ne doit jamais être seulement un endroit où
> l'application dépose son état courant. Elle doit constituer une
> mémoire fiable de ce que le système savait, décidait, autorisait et
> exécutait à chaque étape importante.**

Le modèle de données doit permettre :

``` text
RECONSTRUCT
REPRODUCE
RECONCILE
AUDIT
RECOVER
```

Si un incident survient, QuantLab doit pouvoir répondre précisément :

``` text
What happened?
Why?
Using which data?
Using which version?
Who or what authorized it?
What did the venue actually execute?
```

------------------------------------------------------------------------

# 218. Statut

**Version : 1.0**

Documents directement liés :

-   `02-Architecture-Generale.md`
-   `03-Data-Engine.md`
-   `04-Storage-Engine.md`
-   `09-Scoring-Engine.md`
-   `10-Decision-Engine.md`
-   `11-Risk-Engine.md`
-   `12-Execution-Engine.md`
-   `13-Monitoring-Engine.md`
-   `14-Knowledge-Engine.md`
-   `15-AI-and-Learning-Engine.md`
-   `16-Governance-Engine.md`
-   `18-Testing-Strategy.md`
-   `19-Deployment-Guide.md`
-   `20-Engineering-Principles.md`
-   `21-Experiment-Registry.md`
-   `22-API-Specification.md`
-   `24-Security.md`
-   `25-Roadmap.md`

**Prochain document : `24-Security.md`**
