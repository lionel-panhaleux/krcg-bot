"""Discord Bot."""
import asyncio
import collections
import datetime
import os
import re
import urllib.parse

import discord

from krcg import logging
from krcg import vtes

logger = logging.logger
client = discord.Client()

#: response emoji when multiple cards match
SELECTION_EMOJIS = collections.OrderedDict(
    [
        ("1️⃣", 1),
        ("2️⃣", 2),
        ("3️⃣", 3),
        ("4️⃣", 4),
        ("5️⃣", 5),
        ("6️⃣", 6),
        ("7️⃣", 7),
        ("8️⃣", 8),
        ("9️⃣", 9),
        ("🔟", 10),
    ]
)


@client.event
async def on_ready():
    """Login success informative log."""
    logger.info("Logged in as {}", client.user)


@client.event
async def on_message(message: discord.Message):
    """Main message loop."""
    if message.author == client.user:
        return

    if message.content.lower().startswith("krcg "):
        content = message.content[5:]
        logger.info("Received: {}", content)
        # initial message handling. If multiple cards match, candidates are returned
        # and stored to the COMPLETION_WAITING map
        response = handle_message(content)
        candidates = response.pop("candidates", [])
        response = await message.channel.send(**response)
        # If they are candidates, add response reactions in the form of
        # square numbers emoji
        try:
            for reaction in list(SELECTION_EMOJIS.keys())[: len(candidates)]:
                await response.add_reaction(reaction)
        except discord.Forbidden:
            logger.warning("Missing reaction permission")

        # Wait 30 seconds for an answer when multiple candidates are found
        def check(reaction, user):
            return user == message.author and str(reaction.emoji) in SELECTION_EMOJIS

        while candidates:
            try:
                reaction, _user = await client.wait_for(
                    "reaction_add", timeout=30, check=check
                )
            except asyncio.TimeoutError:
                candidates = []
                # try to clear reactions if the "message management" permission is up
                # (this is not the default setting for bots, it will likely fail)
                try:
                    await response.clear_reactions()
                except discord.Forbidden:
                    logger.warning("Missing message management permission")
            # reaction selected, modify message accordingly
            else:
                content = candidates[SELECTION_EMOJIS[reaction.emoji] - 1]
                try:
                    await response.edit(**handle_message(content, completion=False))
                # this should not fail: bots can modify their messages
                except discord.Forbidden:
                    logger.warning("Missing edit message permission")
                    await message.channel.send(
                        **handle_message(content, completion=False)
                    )


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


def handle_message(message: str, completion: bool = True) -> dict:
    """Message handling

    Args:
        message: The message received , without prefix

    Returns:
        Keyword args for the discord channel.send() function.
        It includes a "candidates" key if multiple cards match.
    """
    message = message.lower()
    # Check for card ID
    try:
        message = int(message)
    except ValueError:
        pass
    # Use completion by default
    if completion:
        try:
            candidates = vtes.VTES.complete(message)
        except AttributeError:
            candidates = []
        if len(candidates) == 1:
            message = candidates[0]
        elif len(candidates) > 10 and message not in vtes.VTES:
            logger.info("Too many candidates")
            return {"content": "Too many candidates, try a more complete card name."}
        elif 0 < len(candidates) <= 10:
            embed = {
                "type": "rich",
                "title": "What card did you mean ?",
                "color": DEFAULT_COLOR,
                "description": "\n".join(
                    f"{i}: {card}" for i, card in enumerate(candidates, 1)
                ),
                "footer": {"text": "Click a number as reaction."},
            }
            logger.info("Choice embed: {}", candidates)
            return {
                "content": "",
                "embed": discord.Embed.from_dict(embed),
                "candidates": candidates,
            }
    # Fuzzy match and known abbreviations only if completion did not help
    if message not in vtes.VTES:
        logger.info("No match for {}", message)
        return {"content": "No card match"}
    # card is found, build fields
    card = vtes.VTES[message]
    card_type = "/".join(card.types)
    clan = "/".join(card.clans or [])
    fields = [{"name": "Type", "value": card_type, "inline": True}]
    if card.clans:
        text = clan
        if card.burn_option:
            text += " (Burn Option)"
        if card.capacity:
            text += f" - Capacity {card.capacity}"
        if card.group:
            text += f" - Group {card.group}"
        fields.append({"name": "Clan", "value": text, "inline": True})
    if card.pool_cost:
        fields.append(
            {"name": "Cost", "value": f"{card.pool_cost} Pool", "inline": True}
        )
    if card.blood_cost:
        fields.append(
            {"name": "Cost", "value": f"{card.blood_cost} Blood", "inline": True}
        )
    if card.conviction_cost:
        fields.append(
            {
                "name": "Cost",
                "value": f"{card.conviction_cost} Conviction",
                "inline": True,
            }
        )
    if card.crypt and card.disciplines:
        fields.append(
            {
                "name": "Disciplines",
                "value": " ".join(card.disciplines) or "None",
                "inline": False,
            }
        )
    fields.append(
        {
            "name": "Card Text",
            "value": card.card_text.replace("{", "").replace("}", ""),
            "inline": False,
        }
    )
    # build rulings field
    # if need be use the footer to indicate there are more of them available
    footer = "Click the title to submit new rulings or rulings corrections"
    if card.banned or card.rulings["text"]:
        rulings = ""
        if card.banned:
            rulings += f"**BANNED since {card.banned}**\n"
        for ruling in card.rulings["text"]:
            # replace reference with markdown link, eg.
            # [LSJ 20101010] -> [[LSJ 20101010]](https://googlegroupslink)
            ruling = re.sub(r"{|}", "*", ruling)
            for reference, link in card.rulings["links"].items():
                ruling = ruling.replace(reference, f"[{reference}]({link})")
            # discord limits field content to 1024
            # make sure we have the room for 3 dots
            if len(rulings) + len(ruling) > 1021:
                rulings += "..."
                footer = "More rulings available, click the title to see them"
                break
            rulings += f"- {ruling}\n"
        fields.append({"name": "Rulings", "value": rulings, "inline": False})
    # handle title, image, link, color
    card_name = card.name
    codex_url = "https://codex-of-the-damned.org/en/card-search.html?"
    codex_url += urllib.parse.urlencode({"card": card_name})
    image_url = card.url
    image_url += f"#{datetime.datetime.now():%Y%m%d%H}"  # timestamp cache busting
    color = COLOR_MAP.get(card_type, DEFAULT_COLOR)
    if card_type == "Vampire":
        color = COLOR_MAP.get(clan, DEFAULT_COLOR)
    embed = {
        "type": "rich",
        "title": card_name,
        "url": codex_url,
        "color": color,
        "fields": fields,
        "image": {"url": image_url},
        "footer": {"text": footer},
    }
    logger.info("Embed for {}", embed["url"])
    return {
        "content": "",
        "embed": discord.Embed.from_dict(embed),
    }


def main():
    """Entrypoint for the Discord Bot."""
    logger.setLevel(logging.INFO)
    # use latest card texts
    vtes.VTES.load()
    client.COMPLETION_WAITING = {}
    client.run(os.getenv("DISCORD_TOKEN"))
    # reset log level so as to not mess up tests
    logger.setLevel(logging.NOTSET)
