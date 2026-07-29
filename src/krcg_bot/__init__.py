"""Discord Bot."""

import asyncio
import datetime
import functools
import logging
import os
import re
import typing
import urllib.parse

from hikari.api import MessageActionRowBuilder

import aiohttp
import hikari
from hikari.impl.special_endpoints import AutocompleteChoiceBuilder

import krcg
import krcg.models

logger = logging.getLogger()
logging.basicConfig(format="[%(levelname)7s] %(message)s")

bot = hikari.GatewayBot(os.getenv("DISCORD_TOKEN") or "")

#: The card corpus, loaded at startup by load_cards()
CARDS: krcg.CardDict = krcg.CardDict()

#: Remove buttons after that many seconds
COMPONENTS_TIMEOUT = 300

#: An interaction token dies 15 minutes after its message. Never wait past that:
#: the strip would fail and leave live buttons over state we had already dropped.
TOKEN_LIFETIME = 900
TOKEN_MARGIN = 30

#: Discord's component ceilings — exceeding any of them is a 400 on the interaction
BUTTONS_PER_ROW = 5
MAX_ACTION_ROWS = 5
LABEL_MAX = 80
CUSTOM_ID_MAX = 100

#: A switch button carries its whole navigation stack as fixed-width card ids,
#: the target last: every id in the corpus is exactly 6 digits, so no separator
#: is needed and the depth the 100-char custom_id affords is a constant.
#: The version char is what a later encoding change bumps: without it a new
#: format that is also a multiple of ID_WIDTH digits parses as plausible ids
#: and answers with the wrong cards.
ID_WIDTH = 6
SWITCH_PREFIX = "switch-1"
MAX_FRAMES = (CUSTOM_ID_MAX - len(SWITCH_PREFIX)) // ID_WIDTH

#: Disciplines emojis in guilds
EMOJIS: dict[hikari.Snowflake, dict[str, hikari.Snowflake]] = {}
EMOJI_NAME_MAP: dict[str, str] = {
    "action": "ACTION",
    "modifier": "ACTION MODIFIER",
    "reaction": "REACTION",
    "combat": "COMBAT",
    "political": "POLITICAL ACTION",
    "ally": "ALLY",
    "retainer": "RETAINER",
    "equipment": "EQUIPMENT",
    "merged": "MERGED",
    "flight": "FLIGHT",
    "conviction": "1 CONVICTION",
}
NAME_EMOJI_MAP = {v: k for k, v in EMOJI_NAME_MAP.items()}
#: message id -> loop clock after which its buttons are stripped, pushed back by
#: each navigation so the timeout measures idleness, not age. An entry exists if
#: and only if a watcher is parked on that message: a click that finds none is
#: on a message that outlived the process that answered it, and re-arms one.
EXPIRY: dict[hikari.Snowflake, float] = {}


class CommandFailed(Exception):
    """A "normal" failure: a message explains why the command was not performed"""


@bot.listen()
async def on_ready(event: hikari.StartedEvent) -> None:
    """Login success informative log."""
    me = bot.get_me()
    if me is not None:
        logger.info("Logged in as %s", me.username)
    application = await bot.rest.fetch_application()
    commands = [
        bot.rest.slash_command_builder("card", "Display card and rulings")
        .add_option(
            hikari.CommandOption(
                type=hikari.OptionType.STRING,
                name="name",
                description="The card name",
                is_required=True,
                min_length=3,
                autocomplete=True,
            )
        )
        .add_option(
            hikari.CommandOption(
                type=hikari.OptionType.BOOLEAN,
                name="public",
                description="Display publicly",
                is_required=False,
            )
        )
    ]
    try:
        registered_commands = await bot.rest.fetch_application_commands(
            application=application,
        )
        if set(c.name for c in commands) ^ set(c.name for c in registered_commands):
            logger.info("Updating commands: %s", commands)
            registered_commands = await bot.rest.set_application_commands(
                application=application,
                commands=commands,
            )
    except hikari.ForbiddenError:
        logger.exception("Bot does not have commands permission")
        return
    except hikari.BadRequestError:
        logger.exception("Bot did not manage to update commands")
        return
    for command in registered_commands:
        try:
            COMMANDS[command.id] = COMMANDS_TO_REGISTER[command.name]
        except KeyError:
            logger.exception("Received unknow command %s", command)


@bot.listen()
async def on_connected(event: hikari.GuildAvailableEvent) -> None:
    """Connected to a guild."""
    me = bot.get_me()
    if me is not None:
        logger.info("Logged in %s as %s", event.guild.name, me.username)
    emojis = await bot.rest.fetch_guild_emojis(event.guild.id)
    # emojis named for the convention (flight) or for the card text token (FLIGHT)
    valid_names = (
        set(CARDS.search_dimensions["discipline"]) | set(EMOJI_NAME_MAP) | set(NAME_EMOJI_MAP)
    )
    valid_emojis = [emoji for emoji in emojis if emoji.name in valid_names]
    EMOJIS[event.guild.id] = {
        EMOJI_NAME_MAP.get(emoji.name, emoji.name): emoji.id for emoji in valid_emojis
    }
    logger.info("Emojis %s", EMOJIS)


async def _interaction_response(interaction: hikari.PartialInteraction, content: str) -> None:
    """Default response to interaction (in case of error)"""
    try:
        if hasattr(interaction, "create_initial_response"):
            await interaction.create_initial_response(
                hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE,
                content,
                flags=hikari.MessageFlag.EPHEMERAL,
                embeds=[],
                components=[],
            )
        else:
            # Fallback for interactions that don't support create_initial_response
            raise TypeError("Incompatible interaction")
    # in case the interaction has been acknowledged already, or is incompatiable,
    # try a follow-up message
    except (hikari.BadRequestError, TypeError):
        await bot.rest.execute_webhook(interaction.application_id, interaction.token, content)


@bot.listen()
async def on_interaction(event: hikari.InteractionCreateEvent) -> None:
    """Handle interactions."""
    if not event.interaction:
        return
    logger.info(
        "Interaction %s from %s (Guild %s - Channel %s). Args: %s",
        getattr(
            event.interaction,
            "command_name",
            getattr(event.interaction, "custom_id", "?"),
        ),
        event.interaction.user.username,
        event.interaction.guild_id,
        event.interaction.channel_id,
        {
            option.name: option.value
            for option in (getattr(event.interaction, "options", None) or [])
        },
    )
    try:
        if isinstance(event.interaction, hikari.CommandInteraction):
            assert event.interaction.type == hikari.InteractionType.APPLICATION_COMMAND
            command = COMMANDS[event.interaction.command_id]
            await command(
                event.interaction,
                **{option.name: option.value for option in event.interaction.options or []},
            )
        elif isinstance(event.interaction, hikari.AutocompleteInteraction):
            assert event.interaction.type == hikari.InteractionType.AUTOCOMPLETE
            options = {option.name: option.value for option in event.interaction.options or []}
            name = options.get("name")
            if isinstance(name, str):
                await autocomplete_name(event.interaction, name)
            else:
                await autocomplete_name(event.interaction, None)
        elif isinstance(event.interaction, hikari.ComponentInteraction):
            assert event.interaction.type == hikari.InteractionType.MESSAGE_COMPONENT
            component = COMPONENTS[event.interaction.custom_id[:6]]
            await component(event.interaction)
    except CommandFailed as exc:
        logger.info("Command failed: %s - %s", event.interaction, exc.args)
        if exc.args:
            await _interaction_response(event.interaction, exc.args[0])
    except asyncio.TimeoutError:
        logger.info("Command failed: Timeout")
        await _interaction_response(
            event.interaction,
            "Error: too many commands, wait a bit and try again.",
        )
    except Exception:
        logger.exception("Command failed: %s", event.interaction)
        await _interaction_response(event.interaction, "Command error")


async def load_cards() -> None:
    """Load the card corpus from the KRCG static server."""
    global CARDS
    async with aiohttp.ClientSession() as session:
        CARDS = await krcg.load_online(session)
    # a wider id spells a wider frame and desyncs every trail parsed after it,
    # silently: refuse to serve rather than answer with the wrong cards
    for card_data in CARDS.cards():
        if not 0 <= card_data.id < 10**ID_WIDTH:
            raise RuntimeError(
                f"Card id {card_data.id} does not fit {ID_WIDTH} digits: buttons cannot spell it"
            )
    logger.info("Loaded %s cards", len(CARDS))


def main() -> None:
    """Entrypoint for the Discord Bot."""
    logger.setLevel(logging.DEBUG if __debug__ else logging.INFO)
    # use latest card texts
    asyncio.run(load_cards())
    bot.run()
    # reset log level so as to not mess up tests
    logger.setLevel(logging.NOTSET)


# ############################################################################# commands
async def card(
    interaction: hikari.CommandInteraction,
    name: str,
    public: bool = False,
) -> None:
    if name not in CARDS:
        raise CommandFailed("Unknown card: use the completion!")
    flags = hikari.MessageFlag.EPHEMERAL if not public else hikari.MessageFlag.NONE
    card_data = CARDS[name]
    embeds = _build_embeds(interaction.guild_id, card_data)
    components = _build_components(card_data, public)
    await interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE,
        embeds=embeds,
        components=components,
        flags=flags,
    )
    await _expire_components(interaction)


def _now() -> float:
    return asyncio.get_running_loop().time()


def _idle_until() -> float:
    """Loop clock at which an unused message loses its buttons."""
    return _now() + COMPONENTS_TIMEOUT


async def _expire_components(
    interaction: hikari.CommandInteraction | hikari.ComponentInteraction,
    message: hikari.Message | None = None,
) -> None:
    """Strip the buttons once the message has gone COMPONENTS_TIMEOUT unused.

    A caller that already holds the message passes it, so the claim lands before
    this coroutine's first await. The caller that does not must learn the id
    first, and a click arriving inside that round-trip re-arms a watcher of its
    own — hence the claim is also a check: whoever gets there first owns the
    message, the loser leaves without touching the winner's entry.
    """
    if message is None:
        try:
            message = await interaction.fetch_initial_response()
        # dismissed or expired before we ever learned the message id, so there is
        # nothing to key a cleanup on. Bounded by the next restart
        except hikari.ClientHTTPResponseError:
            return
    if message.id in EXPIRY:
        return
    # a watcher strips through the token it was handed, and every caller parks one
    # straight after answering, so that token dies TOKEN_LIFETIME from here. Never
    # sleep past it, however far navigation pushes the idle deadline. This clock,
    # not the message's age: a watcher re-armed on an hours-old message holds a
    # brand-new token, and anchoring on the message would strip it on the spot
    token_death = _now() + TOKEN_LIFETIME - TOKEN_MARGIN
    # claimed before the first sleep, not after the first navigation: the entry
    # is what tells a later click a watcher is already parked here
    EXPIRY[message.id] = _idle_until()
    try:
        while True:
            while (left := min(EXPIRY.get(message.id, 0), token_death) - _now()) > 0:
                await asyncio.sleep(left)
            # our token ran out before the reader did. Stripping here would take
            # the buttons off a reader mid-argument, and they no longer need us:
            # they carry their own trail, so they still answer, and the next
            # click re-arms a watcher on a fresh token to strip once it is over
            if EXPIRY.get(message.id, 0) > token_death:
                return
            honoured = EXPIRY.get(message.id, 0)
            await interaction.edit_initial_response(components=[])
            # a navigation landed while that strip was in flight and re-rendered
            # the buttons. Leaving now would drop the entry and the watcher both,
            # on a message that has buttons again: honour the deadline it set
            if EXPIRY.get(message.id, 0) <= honoured:
                break
    # genuinely gone — dismissed, or make_public deleted it. No reader left to
    # strand, so our state is just litter
    except hikari.NotFoundError:
        pass
    # the token died while the message still answers clicks, each one minting a
    # fresh token. This watcher can never strip it, so release the claim: the
    # next click re-arms one on a token young enough to reach the message
    except hikari.ClientHTTPResponseError:
        logger.warning("left components in place on interaction %s", interaction.id)
    finally:
        EXPIRY.pop(message.id, None)


@functools.lru_cache(4096)
def _autocomplete_cache(name: str) -> list[str]:
    """Cached call to try to speed things up."""
    # not CARDS.complete(): it caps at 10 candidates, discord takes 25
    cards = CARDS.search_index.name.search_flat(name, 25)
    candidates = [card.full_name for card in cards]
    if not candidates and name in CARDS:
        candidates = [CARDS[name].full_name]
    return candidates


async def autocomplete_name(
    interaction: hikari.AutocompleteInteraction, name: str | None = None
) -> None:
    """Autocomplete a card name"""
    # an autocomplete interaction has no create_initial_response: the error funnel
    # cannot answer it, so never let an unloaded corpus raise here
    if not name or not CARDS:
        await interaction.create_response([])
        return
    candidates = _autocomplete_cache(name)
    await interaction.create_response(
        [AutocompleteChoiceBuilder(name=n, value=n) for n in candidates]
    )


async def switch_card(interaction: hikari.ComponentInteraction) -> None:
    """Switch card (for vampires with multiple versions)."""
    *stack, new_id = _parse_stack(interaction.custom_id)
    logger.debug("SWITCH to %s over %s", new_id, stack)
    card_data = _card(new_id)
    embeds = _build_embeds(interaction.guild_id, card_data)
    ephemeral = interaction.message.flags & hikari.MessageFlag.EPHEMERAL
    # a public message is never navigated in place: it answers with a new ephemeral,
    # which starts its own trail
    components = _build_components(card_data, False, stack if ephemeral else [])
    if ephemeral:
        await interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_UPDATE, embeds=embeds, components=components
        )
        if interaction.message.id in EXPIRY:
            EXPIRY[interaction.message.id] = _idle_until()
        # no watcher: this message outlived the process that answered it. The
        # button still worked — it carries its own stack — so re-arm the strip
        else:
            await _expire_components(interaction, interaction.message)
    # do not change the original message if it was public
    else:
        await interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE,
            embeds=embeds,
            components=components,
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        await _expire_components(interaction)


async def make_public(interaction: hikari.ComponentInteraction) -> None:
    """Repost the message publicly (from an ephemeral)."""
    card_data = _card(int(interaction.custom_id[7:]))
    embeds = _build_embeds(interaction.guild_id, card_data)
    components = _build_components(card_data, True) if interaction.guild_id else []
    # work around to delete the original ephemeral
    await interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_UPDATE,
        "...",
        embeds=[],
        components=[],
    )
    # its watcher is left alone: popping here would strand a parked watcher with
    # no entry, and its own 404 on the deleted message releases the claim anyway
    _, message = await asyncio.gather(
        interaction.delete_initial_response(),
        bot.rest.execute_webhook(
            interaction.application_id,
            interaction.token,
            embeds=embeds,
            components=components,
        ),
    )
    # remove components after 5 minutes
    await asyncio.sleep(COMPONENTS_TIMEOUT)
    try:
        await bot.rest.edit_webhook_message(
            interaction.application_id, interaction.token, message.id, components=[]
        )
    except hikari.NotFoundError:
        pass


def _split_text(s: str, limit: int) -> tuple[str, str]:
    """Utility function to split a text at a convenient spot."""
    if len(s) < limit:
        return s, ""
    index = s.rfind("\n", 0, limit)
    rindex = index + 1
    if index < 0:
        index = s.rfind(" ", 0, limit)
        rindex = index + 1
        if index < 0:
            index = limit
            rindex = index
    return s[:index], s[rindex:]


def _emoji(guild_emojis: dict[str, hikari.Snowflake], name: str) -> str:
    """Helper function to get a Discord emoji."""
    server_name = NAME_EMOJI_MAP.get(name, name)
    return f"<:{server_name}:{guild_emojis[name]}>"


def _replace_disciplines(guild_id: hikari.Snowflake | None, text: str) -> str:
    """Replace disciplines text with discord emojis if available."""
    guild_emojis = EMOJIS.get(guild_id, {}) if guild_id else {}
    if not guild_emojis:
        return text
    return re.sub(
        f"\\[({'|'.join(guild_emojis.keys())})\\]",
        lambda x: _emoji(guild_emojis, x.group(1)),
        text,
    )


def _build_embeds(guild_id: hikari.Snowflake | None, card_data: krcg.Card) -> list[hikari.Embed]:
    """Build the embeds to display a card."""
    codex_url = "https://codex-of-the-damned.org/en/card-search.html?" + urllib.parse.urlencode(
        {"card": card_data.full_name}
    )
    card_type = "/".join(card_data.types)
    color = COLOR_MAP.get(card_type, DEFAULT_COLOR)
    if isinstance(card_data, krcg.CryptCard):
        color = COLOR_MAP.get(card_data.clan, color)
    embed = hikari.Embed(title=card_data.unique_name, url=codex_url, color=color)
    # cache busting
    parsed_url = urllib.parse.urlparse(card_data.url)
    image_url = parsed_url._replace(
        path=f"/bust/{datetime.datetime.now():%Y%m%d%H}" + parsed_url.path
    ).geturl()
    embed.set_image(image_url)
    if isinstance(card_data, krcg.LibraryCard) and card_data.burn_option:
        card_type += " (Burn Option)"
    embed.add_field(name="Type", value=card_type, inline=True)
    if isinstance(card_data, krcg.CryptCard):
        text = card_data.clan
        if card_data.capacity:
            text += f" - Capacity {card_data.capacity}"
        if card_data.group:
            text += f" - Group {card_data.group.removeprefix('G')}"
        embed.add_field(name="Clan", value=text, inline=True)
        if card_data.disciplines:
            guild_emojis = EMOJIS.get(guild_id, {}) if guild_id else {}
            disciplines = [
                f"<:{d}:{guild_emojis[d]}>" if d in guild_emojis else d
                for d in reversed(card_data.disciplines)
            ]
            embed.add_field(name="Disciplines", value=" ".join(disciplines), inline=False)
    elif isinstance(card_data, krcg.LibraryCard):
        if card_data.clan_requirement:
            embed.add_field(name="Clan", value="/".join(card_data.clan_requirement), inline=True)
        if card_data.cost:
            embed.add_field(
                name="Cost", value=f"{card_data.cost.value} {card_data.cost.type}", inline=True
            )
    # cards are marked <Card Name>, italics /like this/: both render as italics
    card_text = re.sub(r"<([^>]+)>", r"*\1*", card_data.text)
    card_text = re.sub(r"/([^/]+)/", r"*\1*", card_text)
    card_text = _replace_disciplines(guild_id, card_text)
    embed.add_field(
        name="Card Text",
        value=card_text,
        inline=False,
    )
    embed.set_footer(
        "Click the title to submit new rulings or rulings corrections",
        icon="https://static.krcg.org/dark-pack.png",
    )
    embeds = [embed]

    if card_data.banned or card_data.rulings:
        rulings = ""
        if card_data.banned:
            rulings += f"**BANNED since {card_data.banned}**\n"
        for ruling in card_data.rulings:
            # replace cards with simple italics, eg.
            # {KRCG News Radio} -> *KRCG News Radio*
            ruling_text = re.sub(r"\{([^}]+)\}", r"*\1*", ruling.text)
            # replace reference with markdown link, eg.
            # [LSJ 20101010] -> [[LSJ 20101010]](https://googlegroupslink)
            for reference in ruling.references:
                ruling_text = ruling_text.replace(
                    reference.text, f"[[{reference.label}]]({reference.url})"
                )
            rulings += f"- {ruling_text}\n"
        rulings = _replace_disciplines(guild_id, rulings)
        # discord limits field content to 1024
        if len(rulings) < 1024:
            embed.add_field(name="Rulings", value=rulings, inline=False)
        else:
            while rulings:
                part, rulings = _split_text(rulings, 4096)
                embeds.append(
                    hikari.Embed(
                        title=f"{card_data.unique_name} — Rulings",
                        color=color,
                        description=part,
                    )
                )
    logger.info("Displaying %s", card_data.full_name)
    logger.debug(
        "Embeds for %s: %s",
        card_data.full_name,
        [bot.entity_factory.serialize_embed(e) for e in embeds],
    )
    return embeds


def _card(card_id: int) -> krcg.Card:
    """The card a button names, which upstream may have retired since it was drawn."""
    try:
        return CARDS[card_id]
    except KeyError:
        raise CommandFailed("This card is gone from the corpus: use the completion again!")


def _switch_id(stack: list[int], target: int) -> str:
    """A switch button: the trail to walk back, then the card to display.

    The oldest frames are the ones dropped at the ceiling — the trail shortens
    from its far end and the button stays under 100 characters, never a 400.
    """
    frames = (stack + [target])[-MAX_FRAMES:]
    return SWITCH_PREFIX + "".join(f"{card_id:0{ID_WIDTH}d}" for card_id in frames)


def _parse_stack(custom_id: str) -> list[int]:
    """Ancestors then target, the reverse of _switch_id.

    A deploy leaves the previous release's buttons live on open messages for as
    long as their tokens last, and those spell the trail differently. They are
    not answerable, but they must say so rather than reach the error funnel.
    The version is checked first: width and digits alone cannot tell one
    encoding from another that happens to agree on both.
    """
    if not custom_id.startswith(SWITCH_PREFIX):
        raise CommandFailed("This button is out of date: use the completion again!")
    digits = custom_id[len(SWITCH_PREFIX) :]
    if not digits or len(digits) % ID_WIDTH:
        raise CommandFailed("This button is out of date: use the completion again!")
    try:
        return [int(digits[i : i + ID_WIDTH]) for i in range(0, len(digits), ID_WIDTH)]
    except ValueError:
        raise CommandFailed("This button is out of date: use the completion again!")


def _build_components(
    card_data: krcg.Card, public: bool, stack: list[int] | None = None
) -> list[MessageActionRowBuilder]:
    # one frame short of the ceiling, so < Back is always shorter than a ruling
    # link and the two can never spell the same custom_id — which they would on
    # a trail that ping-pongs between two cards, and Discord 400s a duplicate.
    # switch_card already peels the target off, but the guarantee belongs here
    stack = (stack or [])[-(MAX_FRAMES - 1) :]
    ret: list[MessageActionRowBuilder] = []
    row = bot.rest.build_message_action_row()

    def add(style: hikari.InteractiveButtonTypesT, custom_id: str, label: str) -> bool:
        nonlocal row
        if len(row.components) >= BUTTONS_PER_ROW:
            ret.append(row)
            row = bot.rest.build_message_action_row()
        if len(ret) >= MAX_ACTION_ROWS:
            return False
        if len(label) > LABEL_MAX:
            label = label[: LABEL_MAX - 1] + "…"
        row.add_interactive_button(style, custom_id, label=label)
        return True

    links = set()
    # "Make public" and "< Back" go in first and so are never the ones dropped:
    # < Back is the reader's only way back up the trail
    if not public:
        add(hikari.ButtonStyle.SUCCESS, f"public-{card_data.id}", "Make public")
    # the parent is deliberately not added to links: < Back walks up to it while
    # that card's ruling-link button descends into it, so both are offered
    if stack and not public:
        add(hikari.ButtonStyle.PRIMARY, _switch_id(stack[:-1], stack[-1]), "< Back")
    # a variant is another version of the card on screen, not a step down from
    # it: it inherits the trail rather than extending it
    for variant in sorted(card_data.variants, key=lambda v: v.suffix):
        links.add(variant.id)
        if not add(
            hikari.ButtonStyle.PRIMARY,
            _switch_id(stack, variant.id),
            "Base" if variant.type == krcg.models.Variant.Type.BASE else variant.suffix,
        ):
            logger.warning("%s: dropped variant buttons, no room", card_data.full_name)
            break
    # links to cards referenced in rulings start their own row, and are the first
    # sacrificed: unlike < Back, they are all reachable again through autocomplete
    if len(row.components):
        ret.append(row)
        row = bot.rest.build_message_action_row()
    for card in (card for r in card_data.rulings for card in r.cards):
        if card.id in links:
            continue
        links.add(card.id)
        if not add(
            hikari.ButtonStyle.SECONDARY,
            _switch_id(stack + [card_data.id], card.id),
            card.unique_name,
        ):
            logger.warning("%s: dropped ruling links, no room", card_data.full_name)
            break
    if len(row.components):
        ret.append(row)
    return ret


#: Response embed color depends on card type / clan
DEFAULT_COLOR = "#FFFFFF"
COLOR_MAP = {
    "Master": "#35624E",
    "Action": "#2A4A5D",
    "Action Modifier": "#4B4636",
    "Reaction": "#455773",
    "Combat": "#6C221C",
    "Retainer": "#9F613C",
    "Ally": "#413C50",
    "Equipment": "#806A61",
    "Political Action": "#805A3A",
    "Event": "#E85949",
    "Imbued": "#F0974F",
    "Power": "#BE5B47",
    "Conviction": "#A95743",
    "Abomination": "#30183C",
    "Ahrimane": "#868A91",
    "Akunanse": "#744F4E",
    "Baali": "#A73C38",
    "Banu Haqim": "#E9474A",
    "Blood Brother": "#B65A47",
    "Brujah": "#2C2D57",
    "Brujah antitribu": "#39282E",
    "Caitiff": "#582917",
    "Daughter of Cacophony": "#FCEF9B",
    "Gangrel": "#2C342E",
    "Gangrel antitribu": "#2A171A",
    "Gargoyle": "#574B45",
    "Giovanni": "#1F2229",
    "Guruhi": "#1F2229",
    "Harbinger of Skulls": "#A2A7A6",
    "Hecata": "#1F2229",
    "Ishtarri": "#865043",
    "Kiasyd": "#916D32",
    "Lasombra": "#C5A259",
    "Malkavian": "#C5A259",
    "Malkavian antitribu": "#C5A259",
    "Ministry": "#AB9880",
    "Nagaraja": "#D17D58",
    "Nosferatu": "#5C5853",
    "Nosferatu antitribu": "#442B23",
    "Osebo": "#6B5C47",
    "Pander": "#714225",
    "Ravnos": "#82292F",
    "Salubri": "#DA736E",
    "Salubri antitribu": "#D3CDC9",
    "Samedi": "#D28F3E",
    "Toreador": "#DF867F",
    "Toreador antitribu": "#C13B5E",
    "Tremere": "#3F2F45",
    "Tremere antitribu": "#3F2448",
    "True Brujah": "#A12F2E",
    "Tzimisce": "#67724C",
    "Ventrue": "#430F28",
    "Ventrue antitribu": "#5D4828",
}


COMMANDS_TO_REGISTER = {
    "card": card,
}
COMMANDS: dict[hikari.Snowflake, typing.Callable] = {}
COMPONENTS = {
    "public": make_public,
    "switch": switch_card,
}
