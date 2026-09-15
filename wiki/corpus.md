# Corpus — upstream `krcg`

The card and rulings data, as the bot reads it from the `krcg` package (upstream
`lionel-panhaleux/krcg`), locked at **5.9**. Claims are from the krcg 5.9 source unless marked;
re-check them against the locked version in `/upkeep`.

## Loading

- At start, `load_cards()` calls `krcg.load_online()` over an `aiohttp` session and keeps the whole
  corpus in memory. **A restart is the only refresh**, hence the daily scheduled restart
  ([operations.md](operations.md#deploy)). Never krcg's plain `load()`: it reads a cached pickle
  first and would serve a stale corpus forever on an unattended host.
- **`load_online` swallows every failure** and falls back to `load()` — a pickle cached in `TMPDIR`,
  then krcg's packaged VEKN CSVs — without saying so. On success it writes that pickle (~14 MB), so a
  KRCG static-server outage degrades to the last good corpus rather than a crash. The pickle is keyed
  by krcg version, so a krcg bump empties the fallback; and a degraded corpus looks like a fresh one
  in the logs.
- **The cache is a UID trap.** When the pickle in `TMPDIR` belongs to another user, `load_online`
  swallows the `PermissionError` and reads it: the bot is pinned to a stale corpus, silently, with the
  unit `active`. The unit gives the service its own `TMPDIR`.

## Shape the bot reads

- `CardDict`, keyed by id **and** by name. `CryptCard` / `LibraryCard`, told apart by `isinstance`;
  typed `Ruling` objects with `references` and `cards`; `variants` a list.
- Card text marks cards `<Name>` and italics `/like this/`. Ruling text marks cards `{id|Name}` —
  rendered by the id's `unique_name`, so advanced and group variants resolve exactly; the older bare
  `{Name}` still parses. Every embedded name equals its id's `unique_name` today, so rendering the
  embedded name would pass the suite too.
- Guild emoji names come from `search_dimensions["discipline"]` plus the bot's icon-name map.

## Card ids

Every id is **exactly 6 digits** today. The button trail depends on it ([buttons.md](buttons.md)):
`load_cards` raises at start on any id that does not fit, and a test sweeps the corpus in CI — both,
because the test fires only on a push, and a quiet month would let a live bot answer with the wrong
cards first.

## Couplings the `<6` ceiling guards

The ceiling is deliberate: v5 was a rewrite, its cadence is hot (5.0→5.9 in 22 days), and krcg ships
`py.typed`, so a minor bump can break field access and the type check at once. **Bumping krcg is a
code change, not a lockfile refresh.** Two couplings it holds:

- `krcg.models.Variant.Type.BASE` — `Variant` is not in krcg's `__all__`.
- `CARDS.search_index.name.search_flat(name, 25)` for autocomplete, because `CardDict.complete()`
  caps at 10 candidates, under Discord's 25. An `n` argument on `complete()` upstream would retire it.
