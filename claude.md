# CLAUDE.md — Règles de travail pour QuantLab

## Source de vérité
La documentation `docs/01` → `docs/25` + annexes est le contrat du projet.
En cas de conflit : docs > ce fichier > préférences implicites.
Toute décision contredisant les docs exige un ADR dans `docs/adr/` AVANT implémentation.
Le protocole de développement complet est dans `docs/17-AI-Development-Protocol.md` — le lire avant toute tâche non triviale.

## Phase actuelle
Phase 1 — Data Platform (voir `docs/25-Roadmap.md` §20-§34).
Périmètre validé : BTC/USDT et ETH/USDT spot (Binance). Rien d'autre.
Ne JAMAIS implémenter en avance sur la roadmap sans demande explicite.

## Règles non négociables
- Aucune stratégie n'est supposée rentable : tout est hypothèse à tester (docs/01 §5.1).
- Données historiques immuables : INSERT only, jamais d'UPDATE sur candles/fills/audit/decisions.
- `audit_events` est append-only (trigger en base — ne pas contourner).
- Valeurs financières : NUMERIC en base, Decimal en Python. float interdit.
- Timestamps : TIMESTAMPTZ, UTC, timezone-aware partout. Datetime naïf = bug.
- IDs : UUIDv7 via `quantlab.core.ids.new_id()`.
- `trading_enabled: false` dans toutes les configs commitées jusqu'à Phase 6 validée.
- Production refusée sans `QUANTLAB_ALLOW_PRODUCTION=true` (fail closed).
- Secrets : jamais dans le code, Git, logs, fixtures ou prompts. Références env uniquement.
- Migrations : fichiers SQL dans `migrations/`, appliquées par `scripts/migrate.py`.
  Une migration appliquée ne se modifie JAMAIS — on en crée une nouvelle.

## Workflow obligatoire (docs/17)
1. Lire la spec/docs concernées avant de coder (No Blind Coding).
2. Proposer un plan avant d'implémenter les changements non triviaux.
3. Changements atomiques : une préoccupation par changement.
4. Interfaces et contrats typés d'abord (Protocols dans `storage/repositories.py`).
5. Pas de dictionnaires magiques : modèles pydantic frozen dans `domain/`.
6. Tests unitaires pour toute logique domaine/risque. `make ci` doit passer avant tout commit.

## Commandes
- `make install` / `make ci` (lint + typecheck + tests) / `make test`
- `make db-up` / `make migrate` / `make seed`
- Base locale : `postgresql://quantlab:quantlab_local_only@localhost:5432/quantlab_dev`

## Style
- Python 3.12, ruff (line-length 100), mypy strict sur le code applicatif.
- Ne pas toucher aux fichiers dans `docs/` (référence, exclus du formatage).
- Langage du code et des commits : anglais. Discussions : français OK.
