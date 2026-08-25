# QuantLab

Plateforme de recherche quantitative modulaire. Phase actuelle : **Phase 0 — Foundation**.

La référence du projet est la documentation dans `docs/` (documents 01 → 25 + annexes).
Toute décision contredisant la vision doit passer par un ADR (`docs/adr/`).

## Démarrage rapide

```bash
make install            # installe le projet + outils dev
cp .env.example .env    # configuration locale (jamais commitée)
make db-up              # PostgreSQL 16 via Docker
make migrate            # applique migrations/*.sql
make seed               # BINANCE + BTC/USDT + ETH/USDT
make ci                 # lint + typecheck + tests (comme la CI)
```

## Environnements

`development`, `test`, `research`, `paper`, `shadow`, `production`.
La production est refusée sans `QUANTLAB_ALLOW_PRODUCTION=true` (fail closed).

## Definition of Done — Phase 0 (Roadmap §19)

- [x] repository operational
- [x] docs versioned (`docs/`)
- [x] CI pipeline (lint, type check, tests, dependency scan, secret scan)
- [x] tests executable (`make test`)
- [x] migrations working (`make migrate`, runner déterministe avec hash)
- [x] configuration versionnée (`configs/` en couches par environnement)
- [x] logs structurés JSON avec request_id / correlation_id
- [x] secrets protégés (aucun secret dans Git, `.env` ignoré, gitleaks en CI et pre-commit)
- [x] environments defined

## Règles non négociables

- Les données historiques sont immuables (insert only, jamais d'update).
- `audit_events` est append-only (trigger en base).
- Toute valeur financière est `NUMERIC` / `Decimal`, jamais `float`.
- Tous les timestamps sont UTC et timezone-aware.
- `trading_enabled` reste `false` dans toutes les configurations commitées jusqu'à la Phase 6+.
