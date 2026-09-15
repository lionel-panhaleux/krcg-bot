# Discord — the platform we run on

Standing knowledge of Discord and of `hikari`, scoped to what a card-display bot touches. Every
claim names its source; hikari claims are against the locked **2.5.0**. Re-check sources in
`/upkeep`, not code.

## Reading the docs (2026-07-28)

Discord's docs live at `docs.discord.com/developers/*`; `discord.com/developers/docs/*` 301s
**cross-host** to them. Three ways a lookup lies: that redirect, pages past ~2500 lines that
truncate, and a summarising fetch that drops sentences from a page that arrived whole —
indistinguishable from success. The page's own source is the `.mdx` in `discord/discord-api-docs`,
and it is greppable. A failed fetch is not an absence: a claim that could not be checked is
recorded **"unverified"**, never "undocumented".

## Interactions

- **An interaction must get its initial response within 3 seconds**; its token is valid for
  **15 minutes**, and edits through it only work inside that window.
  [receiving-and-responding](https://docs.discord.com/developers/interactions/receiving-and-responding)
  — why autocomplete is cached, and why a button watcher never waits past its token.
- **Ephemeral** responses (the `EPHEMERAL` flag) are visible only to the invoking user. [same page]
- **An autocomplete interaction has no initial response** — only its choices. An error funnel that
  answers with a message cannot answer it, so autocomplete must never raise. [hikari 2.5,
  `AutocompleteInteraction` has no `create_initial_response`; pinned by a test]
- **Gateway, not an HTTP interactions endpoint.** The gateway dials out, so the dev token runs the
  real bot from a laptop against a test guild; an interactions endpoint needs a public HTTPS URL
  Discord can reach. Testability is the whole argument — whether a tunnel answers it is unverified
  (on the board).

## Slash commands

- **A bulk overwrite replaces the whole set** (hikari `set_application_commands`). The bot overwrites
  only when the registered command names differ from its own.
  [application-commands](https://docs.discord.com/developers/interactions/application-commands#bulk-overwrite-global-application-commands)
- **Slash commands live on Discord, not on the host.** Stopping the process does not remove them.
  [server-setup `OPERATIONS.md`, "Retiring a service"]

## Components

- **≤5 action rows per message, ≤5 buttons per row, ≤80-character labels, ≤100-character
  `custom_id`**, unique within a message; a breach is a 400 on the whole interaction.
  [components/reference](https://docs.discord.com/developers/components/reference), 2026-07-28
- The row cap is the *legacy* message limit. The wider 40-component ceiling needs the
  `IS_COMPONENTS_V2` flag, under which `content` and `embeds` stop working — reaching for it means
  giving up the embed every answer is built on. [same page, 2026-07-28]
- **hikari 2.5 validates only that a row's components share a type**, so an over-full row reaches
  Discord and 400s: the bot enforces the ceilings itself. [hikari 2.5 source]
- **≤25 autocomplete choices.**
  [application-commands](https://docs.discord.com/developers/interactions/application-commands)

## Embeds

Title ≤256, description ≤4096, field name ≤256, field value ≤1024, ≤10 embeds and ≤6000 characters
in total per message.
[message#embed-object-embed-limits](https://docs.discord.com/developers/resources/message#embed-object-embed-limits)

## hikari traps

- **`GatewayBot.__init__` parses the token**, and the bot is built at import: importing the module
  needs a well-formed token, which the test conftest assembles. A major hikari bump can make the
  module unimportable — hence the `<3` ceiling. [hikari 2.5 source, `impl/gateway_bot.py`]
- **HTTP errors map on status alone**, never on Discord's JSON code: 401 → `UnauthorizedError`,
  404 → `NotFoundError`, both under `ClientHTTPResponseError`. [hikari 2.5 source, `internal/net.py`]
- **What Discord returns for an expired interaction token is unverified** (docs source re-checked
  2026-07-29): `50027 Invalid webhook token provided` is in the error-code table, but nothing pairs it
  with interaction tokens or gives it a status. Catch the superclass; a narrower catch bets on an
  unverified fact.
