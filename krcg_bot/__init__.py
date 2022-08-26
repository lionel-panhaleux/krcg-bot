"""Discord Bot."""
import asyncio
import datetime
import logging
import os
import re
import urllib.parse

import interactions

from krcg import vtes

logger = logging.getLogger()
logging.basicConfig(format="[%(levelname)7s] %(message)s")

bot = interactions.Client(
    token=os.getenv("DISCORD_TOKEN") or "",
    intents=interactions.Intents.DEFAULT | interactions.Intents.GUILD_MESSAGE_CONTENT,
)

#: Disciplines emojis in guilds
EMOJIS = {}
EMOJI_NAME_MAP = {
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

#: the library does not cleanup the interactions once they've been used, keep track
BUTTONS = set()


@bot.event
async def on_ready():
    """Login success informative log."""
    logger.info("Logged in as %s", bot.me.name)
    results = await asyncio.gather(*(guild.get_all_emoji() for guild in bot.guilds))
    for guild, emojis in zip(bot.guilds, results):
        valid_emojis = [
            emoji
            for emoji in emojis
            if emoji.name
            in vtes.VTES.search_dimensions["discipline"] + list(EMOJI_NAME_MAP.keys())
        ]

        EMOJIS[guild] = {
            EMOJI_NAME_MAP.get(emoji.name, emoji.name): emoji.id
            for emoji in valid_emojis
        }
    logger.info("Emojis %s", EMOJIS)


@bot.command(
    name="card",
    description="Display VTES cards information",
    options=[
        interactions.Option(
            name="name",
            description="Card name",
            type=interactions.OptionType.STRING,
            required=True,
            min_length=3,
            autocomplete=True,
        ),
        interactions.Option(
            name="public",
            description="share the card with everyone",
            type=interactions.OptionType.BOOLEAN,
            required=False,
        ),
    ],
)
async def card(
    ctx: interactions.CommandContext,
    name: str,
    public: bool = False,
):
    if name not in vtes.VTES:
        await ctx.send("Unknown card: use the completion!", ephemeral=True)
        return
    ephemeral = None if public else True
    await ctx.defer(ephemeral)  # we need to defer, to avoid an error on ctx.edit
    card_data = vtes.VTES[name]
    embeds = _build_embeds(ctx.guild, card_data)
    components = _build_components(card_data)
    await ctx.send(embeds=embeds, components=components, ephemeral=ephemeral)
    # editing message does not work in private messages just stop there
    if not public or not ctx.guild:
        return
    await asyncio.sleep(60)
    await ctx.edit(embeds=embeds, components=[])


async def switch_card(ctx: interactions.ComponentContext):
    card_id = int(ctx.custom_id[7:])
    card_data = vtes.VTES[card_id]
    embeds = _build_embeds(ctx.guild, card_data)
    # edit just sends a new message in direct messages
    if ctx.guild:
        components = _build_components(card_data)
    else:
        components = []
    await ctx.edit(embeds=embeds, components=components)


@bot.autocomplete(command="card", name="name")
async def autocomplete_name(ctx: interactions.CommandContext, name: str = None):
    if not name:
        return
    name = name.lower().strip()
    try:
        candidates = vtes.VTES.complete(name)
    except AttributeError:
        candidates = []
    if not candidates:
        if name in vtes.VTES:
            candidates = [vtes.VTES[name].name]
    await ctx.populate([interactions.Choice(name=n, value=n) for n in candidates[:25]])


@bot.event(name="on_message_create")
async def on_message_create(message: interactions.Message):
    """Main message loop."""
    logger.debug("Got message: %s / %s", message, message.content)
    if message.author.id == bot.me.id:
        return

    if message.content.lower().startswith("krcg "):
        await message.reply("This bot switched to slash commands. Use `/card` instead.")


def _split_text(s, limit):
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


def _emoji(guild_emojis, name):
    server_name = NAME_EMOJI_MAP.get(name, name)
    return f"<:{server_name}:{guild_emojis[name]}>"


def _replace_disciplines(guild: interactions.Guild, text: str) -> str:
    guild_emojis = EMOJIS.get(guild, {})
    if not guild_emojis:
        return text
    return re.sub(
        f"\\[({'|'.join(guild_emojis.keys())})\\]",
        lambda x: _emoji(guild_emojis, x.group(1)),
        text,
    )


def _build_embeds(guild, card_data):
    codex_url = "https://codex-of-the-damned.org/en/card-search.html?"
    codex_url += urllib.parse.urlencode({"card": card_data.name})
    image_url = card_data.url
    image_url += f"#{datetime.datetime.now():%Y%m%d%H}"  # timestamp cache busting
    card_type = "/".join(card_data.types)
    color = COLOR_MAP.get(card_type, DEFAULT_COLOR)
    if card_type == "Vampire":
        color = COLOR_MAP.get(card_data.clans[0], DEFAULT_COLOR)

    embed = interactions.Embed(title=card_data.usual_name, url=codex_url, color=color)
    embed.set_image(url=image_url)
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
            f"<:{d}:{EMOJIS[guild][d]}>" if d in EMOJIS.get(guild, {}) else d
            for d in reversed(card_data.disciplines)
        ]
        embed.add_field(
            name="Disciplines",
            value=" ".join(disciplines) or "None",
            inline=False,
        )
    card_text = card_data.card_text.replace("{", "").replace("}", "")
    card_text = _replace_disciplines(guild, card_text)
    embed.add_field(
        name="Card Text",
        value=card_text,
        inline=False,
    )
    embed.set_footer(
        "Click the title to submit new rulings or rulings corrections",
        icon_url="https://static.krcg.org/dark-pack.png",
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
        rulings = _replace_disciplines(guild, rulings)
        # discord limits field content to 1024
        if len(rulings) < 1024:
            embed.add_field(name="Rulings", value=rulings, inline=False)
        else:
            while rulings:
                part, rulings = _split_text(rulings, 4096)
                embeds.append(
                    interactions.Embed(
                        title=f"{card_data.usual_name} — Rulings",
                        color=color,
                        description=part,
                    )
                )
    logger.info("Displaying %s", card_data.name)
    return embeds


def _build_components(card_data):
    components = []
    for i, (key, variant_id) in enumerate(sorted(card_data.variants.items())):
        custom_id = f"switch-{variant_id}"
        button = interactions.Button(
            style=interactions.ButtonStyle.PRIMARY,
            label="Base" if i == 0 and card_data.adv else key,
            custom_id=custom_id,
        )
        components.append(button)
        if custom_id not in BUTTONS:
            BUTTONS.add(custom_id)
            bot.component(custom_id)(switch_card)
    return components


#: Response embed color depends on card type / clan
DEFAULT_COLOR = int("FFFFFF", 16)
COLOR_MAP = {
    "Master": int("35624E", 16),
    "Action": int("2A4A5D", 16),
    "Modifier": int("4B4636", 16),
    "Reaction": int("455773", 16),
    "Combat": int("6C221C", 16),
    "Retainer": int("9F613C", 16),
    "Ally": int("413C50", 16),
    "Equipment": int("806A61", 16),
    "Political Action": int("805A3A", 16),
    "Event": int("E85949", 16),
    "Imbued": int("F0974F", 16),
    "Power": int("BE5B47", 16),
    "Conviction": int("A95743", 16),
    "Abomination": int("30183C", 16),
    "Ahrimane": int("868A91", 16),
    "Akunanse": int("744F4E", 16),
    "Assamite": int("E9474A", 16),
    "Baali": int("A73C38", 16),
    "Blood Brother": int("B65A47", 16),
    "Brujah": int("2C2D57", 16),
    "Brujah antitribu": int("39282E", 16),
    "Caitiff": int("582917", 16),
    "Daughter of Cacophony": int("FCEF9B", 16),
    "Follower of Set": int("AB9880", 16),
    "Gangrel": int("2C342E", 16),
    "Gangrel antitribu": int("2A171A", 16),
    "Gargoyle": int("574B45", 16),
    "Giovanni": int("1F2229", 16),
    "Guruhi": int("1F2229", 16),
    "Harbinger of Skulls": int("A2A7A6", 16),
    "Ishtarri": int("865043", 16),
    "Kiasyd": int("916D32", 16),
    "Lasombra": int("C5A259", 16),
    "Malkavian": int("C5A259", 16),
    "Malkavian antitribu": int("C5A259", 16),
    "Nagaraja": int("D17D58", 16),
    "Nosferatu": int("5C5853", 16),
    "Nosferatu antitribu": int("442B23", 16),
    "Osebo": int("6B5C47", 16),
    "Pander": int("714225", 16),
    "Ravnos": int("82292F", 16),
    "Salubri": int("DA736E", 16),
    "Salubri antitribu": int("D3CDC9", 16),
    "Samedi": int("D28F3E", 16),
    "Toreador": int("DF867F", 16),
    "Toreador antitribu": int("C13B5E", 16),
    "Tremere": int("3F2F45", 16),
    "Tremere antitribu": int("3F2448", 16),
    "True Brujah": int("A12F2E", 16),
    "Tzimisce": int("67724C", 16),
    "Ventrue": int("430F28", 16),
    "Ventrue antitribu": int("5D4828", 16),
}


def main():
    """Entrypoint for the Discord Bot."""
    logger.setLevel(logging.DEBUG if os.getenv("DEBUG") else logging.INFO)
    # use latest card texts
    vtes.VTES.load()
    bot.start()
    # reset log level so as to not mess up tests
    logger.setLevel(logging.NOTSET)
