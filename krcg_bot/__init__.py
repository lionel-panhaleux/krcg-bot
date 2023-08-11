"""Discord Bot."""
import asyncio
import collections
import datetime
import functools
import itertools
import logging
import os
import re
import urllib.parse

import hikari
from hikari.impl.special_endpoints import AutocompleteChoiceBuilder

from krcg import vtes

logger = logging.getLogger()
logging.basicConfig(format="[%(levelname)7s] %(message)s")

bot = hikari.GatewayBot(os.getenv("DISCORD_TOKEN") or "")

#: Remove buttons after that many seconds
COMPONENTS_TIMEOUT = 300

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
HISTORY: dict[hikari.Snowflake, list[int]] = collections.defaultdict(list)


class CommandFailed(Exception):
    """A "normal" failure: a message explains why the command was not performed"""


@bot.listen()
async def on_ready(event: hikari.StartedEvent) -> None:
    """Login success informative log."""
    logger.info("Logged in as %s", bot.get_me().username)
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
    logger.info("Logged in %s as %s", event.guild.name, bot.get_me().username)
    emojis = await bot.rest.fetch_guild_emojis(event.guild.id)
    valid_emojis = [
        emoji
        for emoji in emojis
        if emoji.name
        in vtes.VTES.search_dimensions["discipline"] + list(EMOJI_NAME_MAP.keys())
    ]
    EMOJIS[event.guild.id] = {
        EMOJI_NAME_MAP.get(emoji.name, emoji.name): emoji.id for emoji in valid_emojis
    }
    logger.info("Emojis %s", EMOJIS)


async def _interaction_response(interaction, content):
    """Default response to interaction (in case of error)"""
    try:
        await interaction.create_initial_response(
            hikari.interactions.base_interactions.ResponseType.MESSAGE_CREATE,
            content,
            flags=hikari.MessageFlag.EPHEMERAL,
            embeds=[],
            components=[],
        )
    # in case the interaction has been acknowledged already, try a follow-up message
    except hikari.BadRequestError:
        await bot.rest.execute_webhook(
            interaction.application_id, interaction.token, content
        )


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
        if event.interaction.type == hikari.InteractionType.APPLICATION_COMMAND:
            command = COMMANDS[event.interaction.command_id]
            await command(
                event.interaction,
                **{
                    option.name: option.value
                    for option in event.interaction.options or []
                },
            )
        elif event.interaction.type == hikari.InteractionType.AUTOCOMPLETE:
            await autocomplete_name(
                event.interaction,
                **{
                    option.name: option.value
                    for option in event.interaction.options or []
                },
            )
        elif event.interaction.type == hikari.InteractionType.MESSAGE_COMPONENT:
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


def main():
    """Entrypoint for the Discord Bot."""
    logger.setLevel(logging.DEBUG if __debug__ else logging.INFO)
    # use latest card texts
    vtes.VTES.load()
    bot.run()
    # reset log level so as to not mess up tests
    logger.setLevel(logging.NOTSET)


# ############################################################################# commands
async def card(
    interaction: hikari.CommandInteraction,
    name: str,
    public: bool = False,
):
    if name not in vtes.VTES:
        raise CommandFailed("Unknown card: use the completion!")
    flags = None if public else hikari.MessageFlag.EPHEMERAL
    card_data = vtes.VTES[name]
    embeds = _build_embeds(interaction.guild_id, card_data)
    components = _build_components(card_data, public)
    await interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_CREATE,
        embeds=embeds,
        components=components,
        flags=flags,
    )
    # remove components and history after 5 minute
    await asyncio.sleep(COMPONENTS_TIMEOUT)
    try:
        message = await interaction.edit_initial_response(components=[])
        HISTORY.pop(message.id, None)
    except hikari.NotFoundError:
        pass


@functools.lru_cache(4096)
def _autocomplete_cache(name: str):
    """Cached call to try to speed things up."""
    try:
        candidates = vtes.VTES.complete(name)
    except AttributeError:
        candidates = []
    if not candidates and name in vtes.VTES:
        candidates = [vtes.VTES[name].name]
    return candidates[:25]


async def autocomplete_name(
    interaction: hikari.AutocompleteInteraction, name: str = None
):
    """Autocomplete a card name"""
    if not name:
        await interaction.create_response([])
        return
    candidates = _autocomplete_cache(name)
    await interaction.create_response(
        [AutocompleteChoiceBuilder(name=n, value=n) for n in candidates]
    )


async def switch_card(interaction: hikari.ComponentInteraction):
    """Switch card (for vampires with multiple versions)."""
    origin_id = None
    ids = interaction.custom_id[7:].split("-")
    if len(ids) > 1:
        origin_id = int(ids.pop(0))
    new_id = int(ids.pop(0))
    logger.debug("SWITCH from %s to %s", origin_id, new_id)
    card_data = vtes.VTES[new_id]
    embeds = _build_embeds(interaction.guild_id, card_data)
    ephemeral = interaction.message.flags & hikari.MessageFlag.EPHEMERAL
    # no history management on public messages, we create a new message
    if ephemeral:
        # no origin if we're not tracking history (eg. vampire variations)
        if origin_id is None:
            pass
        elif origin_id > 0:
            HISTORY[interaction.message.id].append(origin_id)
        # a zero origin_id means we're coming back
        elif HISTORY[interaction.message.id]:
            HISTORY[interaction.message.id].pop()
            if HISTORY[interaction.message.id]:
                origin_id = HISTORY[interaction.message.id][-1]
            else:
                origin_id = None
    components = _build_components(card_data, False, origin_id if ephemeral else None)
    if ephemeral:
        await interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_UPDATE, embeds=embeds, components=components
        )
    # do not change the original message if it was public
    else:
        await interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_CREATE,
            embeds=embeds,
            components=components,
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        # remove components and history after 5 minute
        await asyncio.sleep(COMPONENTS_TIMEOUT)
        try:
            message = await interaction.edit_initial_response(components=[])
            HISTORY.pop(message.id, None)
        except hikari.NotFoundError:
            pass


async def make_public(interaction: hikari.ComponentInteraction):
    """Repost the message publicly (from an ephemeral)."""
    card_id = int(interaction.custom_id[7:])
    card_data = vtes.VTES[card_id]
    embeds = _build_embeds(interaction.guild_id, card_data)
    components = _build_components(card_data, True) if interaction.guild_id else []
    # work around to delete the original ephemeral
    await interaction.create_initial_response(
        hikari.ResponseType.MESSAGE_UPDATE,
        "...",
        embeds=[],
        components=[],
    )
    HISTORY.pop(interaction.message.id, None)
    _, message = await asyncio.gather(
        interaction.delete_initial_response(),
        bot.rest.execute_webhook(
            interaction.application_id,
            interaction.token,
            embeds=embeds,
            components=components,
        ),
    )
    # remove components and history after 5 minute
    await asyncio.sleep(COMPONENTS_TIMEOUT)
    try:
        await bot.rest.edit_webhook_message(
            interaction.application_id, interaction.token, message.id, components=[]
        )
        HISTORY.pop(message.id, None)
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


def _emoji(guild_emojis: dict[str, hikari.Snowflake], name: str):
    """Helper function to get a Discord emoji."""
    server_name = NAME_EMOJI_MAP.get(name, name)
    return f"<:{server_name}:{guild_emojis[name]}>"


def _replace_disciplines(guild_id: hikari.Snowflake, text: str) -> str:
    """Replace disciplines text with discord emojis if available."""
    guild_emojis = EMOJIS.get(guild_id, {})
    if not guild_emojis:
        return text
    return re.sub(
        f"\\[({'|'.join(guild_emojis.keys())})\\]",
        lambda x: _emoji(guild_emojis, x.group(1)),
        text,
    )


def _build_embeds(guild_id: hikari.Snowflake, card_data):
    """Build the embeds to display a card."""
    codex_url = (
        "https://codex-of-the-damned.org/en/card-search.html?"
        + urllib.parse.urlencode({"card": card_data.name})
    )
    card_type = "/".join(card_data.types)
    color = COLOR_MAP.get(card_type, DEFAULT_COLOR)
    if card_type == "Vampire":
        color = COLOR_MAP.get(card_data.clans[0], DEFAULT_COLOR)
    embed = hikari.Embed(title=card_data.usual_name, url=codex_url, color=color)
    image_url = urllib.parse.urlparse(card_data.url)
    # cache busting
    image_url = image_url._replace(
        path=f"/bust/{datetime.datetime.now():%Y%m%d%H}" + image_url.path
    ).geturl()
    embed.set_image(image_url)
    embed.add_field(name="Type", value=card_type, inline=True)
    if card_data.clans:
        text = "/".join(card_data.clans or [])
        if card_data.burn_option:
            text += " (Burn Option)"
        if card_data.capacity:
            text += f" - Capacity {card_data.capacity}"
        if card_data.group:
            text += f" - Group {card_data.group}"
        embed.add_field(name="Clan", value=text, inline=True)
    if card_data.pool_cost:
        embed.add_field(name="Cost", value=f"{card_data.pool_cost} Pool", inline=True)
    if card_data.blood_cost:
        embed.add_field(name="Cost", value=f"{card_data.blood_cost} Blood", inline=True)
    if card_data.conviction_cost:
        embed.add_field(
            name="Cost",
            value=f"{card_data.conviction_cost} Conviction",
            inline=True,
        )
    if card_data.crypt and card_data.disciplines:
        disciplines = [
            f"<:{d}:{EMOJIS[guild_id][d]}>" if d in EMOJIS.get(guild_id, {}) else d
            for d in reversed(card_data.disciplines)
        ]
        embed.add_field(
            name="Disciplines",
            value=" ".join(disciplines) or "None",
            inline=False,
        )
    card_text = card_data.card_text.replace("{", "").replace("}", "").replace("/", "*")
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

    if card_data.banned or card_data.rulings["text"]:
        rulings = ""
        if card_data.banned:
            rulings += f"**BANNED since {card_data.banned}**\n"
        for ruling in card_data.rulings["text"]:
            # replace reference with markdown link, eg.
            # [LSJ 20101010] -> [[LSJ 20101010]](https://googlegroupslink)
            ruling = re.sub(r"{|}", "*", ruling)
            for reference, link in card_data.rulings["links"].items():
                ruling = ruling.replace(reference, f"[{reference}]({link})")
            rulings += f"- {ruling}\n"
        rulings = _replace_disciplines(guild_id, rulings)
        # discord limits field content to 1024
        if len(rulings) < 1024:
            embed.add_field(name="Rulings", value=rulings, inline=False)
        else:
            while rulings:
                part, rulings = _split_text(rulings, 4096)
                embeds.append(
                    hikari.Embed(
                        title=f"{card_data.usual_name} — Rulings",
                        color=color,
                        description=part,
                    )
                )
    logger.info("Displaying %s", card_data.name)
    logger.debug(
        "Embeds for %s: %s",
        card_data.name,
        [bot.entity_factory.serialize_embed(e) for e in embeds],
    )
    return embeds


def _build_components(card_data: vtes.cards.Card, public: bool, origin_id: int = None):
    ret = []
    row = bot.rest.build_message_action_row()
    links = set()
    if not public:
        row.add_interactive_button(
            hikari.ButtonStyle.SUCCESS,
            f"public-{card_data.id}",
            label="Make public",
        )
    if origin_id and not public:
        links.add(int(origin_id))
        row.add_interactive_button(
            hikari.ButtonStyle.PRIMARY,
            f"switch-0-{origin_id}",
            label="< Back",
        )
    for i, (key, variant_id) in enumerate(sorted(card_data.variants.items())):
        links.add(int(variant_id))
        row.add_interactive_button(
            hikari.ButtonStyle.PRIMARY,
            f"switch-{variant_id}",
            label="Base" if i == 0 and card_data.adv else key,
        )
    if len(row.components):
        ret.append(row)
    # add links to cards referenced in rulings
    row = bot.rest.build_message_action_row()
    for text in itertools.chain([card_data.card_text], card_data.rulings["text"]):
        if len(ret) >= 5:
            break
        for card_name in re.findall(r"(?:{|/)[^}/]+(?:}|/)", text):
            if len(ret) >= 5:
                break
            card_name = card_name[1:-1]
            if card_name not in vtes.VTES:
                continue
            card = vtes.VTES[card_name]
            if card.id in links:
                continue
            links.add(int(card.id))
            row.add_interactive_button(
                hikari.ButtonStyle.SECONDARY,
                f"switch-{card_data.id}-{card.id}",
                label=card.name,
            )
            if len(row.components) >= 5:
                ret.append(row)
                row = bot.rest.build_message_action_row()
    if len(row.components):
        ret.append(row)
    return ret


#: Response embed color depends on card type / clan
DEFAULT_COLOR = "#FFFFFF"
COLOR_MAP = {
    "Master": "#35624E",
    "Action": "#2A4A5D",
    "Modifier": "#4B4636",
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
    "Assamite": "#E9474A",
    "Baali": "#A73C38",
    "Blood Brother": "#B65A47",
    "Brujah": "#2C2D57",
    "Brujah antitribu": "#39282E",
    "Caitiff": "#582917",
    "Daughter of Cacophony": "#FCEF9B",
    "Follower of Set": "#AB9880",
    "Gangrel": "#2C342E",
    "Gangrel antitribu": "#2A171A",
    "Gargoyle": "#574B45",
    "Giovanni": "#1F2229",
    "Guruhi": "#1F2229",
    "Harbinger of Skulls": "#A2A7A6",
    "Ishtarri": "#865043",
    "Kiasyd": "#916D32",
    "Lasombra": "#C5A259",
    "Malkavian": "#C5A259",
    "Malkavian antitribu": "#C5A259",
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
COMMANDS = {}
COMPONENTS = {
    "public": make_public,
    "switch": switch_card,
}
