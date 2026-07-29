"""The card answer, checked against Discord's limits and the corpus shape.

Never against exact card text: the corpus is live, and upstream moves it.
"""

import asyncio
import inspect
import re
import urllib.parse

import hikari
import krcg
import krcg.models
import krcg_bot
import pytest

#: https://docs.discord.com/developers/resources/message#embed-object-embed-limits
FIELD_VALUE = 1024
FIELD_NAME = 256
DESCRIPTION = 4096
TITLE = 256
EMBED_TOTAL = 6000
EMBEDS = 10
#: components and autocomplete
ROWS = 5
BUTTONS = 5
LABEL = 80
CUSTOM_ID = 100
CHOICES = 25


def find(cards, predicate):
    """Lowest-id card matching predicate, so the pick is stable across runs.

    Cards are picked by shape, never by name: upstream renames a card far more
    often than it changes what a card *is*.
    """
    matches = sorted((c for c in cards.cards() if predicate(c)), key=lambda c: c.id)
    assert matches, "no card matches: the corpus shape changed, fix the test"
    return matches[0]


def fields(embed) -> dict[str, str]:
    return {field.name: field.value for field in embed.fields}


def embed_length(embeds) -> int:
    return sum(
        len(e.title or "")
        + len(e.description or "")
        + len(e.footer.text if e.footer and e.footer.text else "")
        + sum(len(f.name) + len(f.value) for f in e.fields)
        for e in embeds
    )


# ################################################################################# embeds
def test_embeds_crypt(cards):
    card = find(
        cards,
        lambda c: isinstance(c, krcg.CryptCard) and c.disciplines and c.capacity and c.group,
    )
    embed = krcg_bot._build_embeds(None, card)[0]
    assert embed.title == card.unique_name
    assert urllib.parse.quote_plus(card.full_name) in embed.url
    assert fields(embed)["Type"] == "Vampire"
    assert card.clan in fields(embed)["Clan"]
    assert f"Capacity {card.capacity}" in fields(embed)["Clan"]
    assert f"Group {card.group.removeprefix('G')}" in fields(embed)["Clan"]
    assert fields(embed)["Disciplines"]
    assert fields(embed)["Card Text"]
    assert "Cost" not in fields(embed)
    # a known clan carries its own colour, not the fallback
    assert embed.color is not None
    assert str(embed.color) != krcg_bot.DEFAULT_COLOR


def test_embeds_variant_card_title_disambiguates(cards):
    """Same printed name, several cards: the title has to say which one this is."""
    card = find(cards, lambda c: len(c.variants) > 1)
    embed = krcg_bot._build_embeds(None, card)[0]
    assert embed.title == card.unique_name
    assert card.suffix in embed.title
    for variant in card.variants:
        assert embed.title != cards[variant.id].unique_name


def test_embeds_library_cost(cards):
    card = find(cards, lambda c: isinstance(c, krcg.LibraryCard) and c.cost)
    embed = krcg_bot._build_embeds(None, card)[0]
    assert fields(embed)["Cost"] == f"{card.cost.value} {card.cost.type}"
    assert "Disciplines" not in fields(embed)


def test_embeds_library_clan_requirement(cards):
    card = find(cards, lambda c: isinstance(c, krcg.LibraryCard) and c.clan_requirement)
    embed = krcg_bot._build_embeds(None, card)[0]
    for clan in card.clan_requirement:
        assert clan in fields(embed)["Clan"]


def test_embeds_burn_option(cards):
    """Burn option is a property of every card that has it, clan requirement or not."""
    card = find(
        cards,
        lambda c: isinstance(c, krcg.LibraryCard) and c.burn_option and not c.clan_requirement,
    )
    embed = krcg_bot._build_embeds(None, card)[0]
    assert "(Burn Option)" in fields(embed)["Type"]


def test_embeds_card_names_render_as_italics(cards):
    """Card text marks cards <Name>: the markers never reach the reader."""
    card = find(cards, lambda c: "<" in c.text)
    text = fields(krcg_bot._build_embeds(None, card)[0])["Card Text"]
    assert "<" not in text and ">" not in text
    assert f"*{card.cards[0].printed_name}*" in text


def test_embeds_slashes_italicise_in_pairs(cards):
    """A /pair/ becomes italics; a lone slash stays a slash, not a stray asterisk."""
    paired = find(cards, lambda c: re.search(r"/[^/]+/", c.text))
    text = fields(krcg_bot._build_embeds(None, paired)[0])["Card Text"]
    assert "/" not in text
    assert "*" in text

    lone = find(cards, lambda c: c.text.count("/") == 1 and "<" not in c.text)
    text = fields(krcg_bot._build_embeds(None, lone)[0])["Card Text"]
    assert "/" in text
    assert "*" not in text


def test_embeds_image_is_cache_busted(cards):
    card = find(cards, lambda c: c.url)
    embed = krcg_bot._build_embeds(None, card)[0]
    assert embed.image is not None
    assert re.search(r"/bust/\d{10}/", embed.image.url), embed.image.url


def test_embeds_attribution(cards):
    """Dark Pack attribution is not optional: it ships on every card answer."""
    card = find(cards, lambda c: True)
    embed = krcg_bot._build_embeds(None, card)[0]
    assert embed.footer is not None
    assert embed.footer.icon is not None
    assert "dark-pack" in embed.footer.icon.url


def test_embeds_rulings_markup(cards):
    card = find(cards, lambda c: any(r.references and r.cards for r in c.rulings))
    embeds = krcg_bot._build_embeds(None, card)
    text = "".join(f.value for e in embeds for f in e.fields)
    text += "".join(e.description or "" for e in embeds)
    ruling = next(r for r in card.rulings if r.references and r.cards)
    # cards cited in a ruling render as italics, references as markdown links
    assert f"*{ruling.cards[0].unique_name}*" in text
    assert f"[[{ruling.references[0].label}]]({ruling.references[0].url})" in text
    assert "{" not in text and "}" not in text


def test_embeds_banned(cards):
    card = find(cards, lambda c: c.banned)
    embeds = krcg_bot._build_embeds(None, card)
    text = "".join(f.value for e in embeds for f in e.fields)
    text += "".join(e.description or "" for e in embeds)
    assert f"BANNED since {card.banned}" in text


def test_embeds_long_rulings_split(cards):
    """Rulings past a field's 1024 chars move to their own embeds, not a truncated field."""
    card = find(cards, lambda c: sum(len(r.text) for r in c.rulings) > FIELD_VALUE)
    embeds = krcg_bot._build_embeds(None, card)
    assert len(embeds) > 1
    assert "Rulings" not in fields(embeds[0])
    for embed in embeds[1:]:
        assert embed.description
        assert card.unique_name in embed.title


@pytest.fixture
def guild(cards):
    """A guild that defines every discipline and icon emoji, as on_connected would."""
    guild_id = 1234567890
    names = [n for n in cards.search_dimensions["discipline"] if n]
    krcg_bot.EMOJIS[guild_id] = {
        krcg_bot.EMOJI_NAME_MAP.get(n, n): 999 for n in names + list(krcg_bot.EMOJI_NAME_MAP)
    }
    yield guild_id
    del krcg_bot.EMOJIS[guild_id]


def test_embeds_disciplines_become_emojis(cards, guild):
    card = find(cards, lambda c: isinstance(c, krcg.CryptCard) and c.disciplines)
    plain = fields(krcg_bot._build_embeds(None, card)[0])["Disciplines"]
    emojied = fields(krcg_bot._build_embeds(guild, card)[0])["Disciplines"]
    assert "<:" not in plain
    assert emojied.count("<:") == len(card.disciplines)


def test_embeds_card_text_tokens_become_emojis(cards, guild):
    """The one optional nicety the bot promises: [tokens] in text render as guild emojis."""
    card = find(cards, lambda c: re.search(r"\[[A-Za-z]+\]", c.text))
    tokens = set(re.findall(r"\[([A-Za-z]+)\]", card.text))
    plain = fields(krcg_bot._build_embeds(None, card)[0])["Card Text"]
    emojied = fields(krcg_bot._build_embeds(guild, card)[0])["Card Text"]
    assert all(f"[{token}]" in plain for token in tokens)
    assert not re.search(r"\[[A-Za-z]+\]", emojied), emojied
    assert emojied.count("<:") >= len(tokens)


def test_embeds_hold_discord_limits(cards):
    """Every card in the corpus, since the corpus is what the bot serves."""
    for card in cards.cards():
        embeds = krcg_bot._build_embeds(None, card)
        assert len(embeds) <= EMBEDS, card.full_name
        assert embed_length(embeds) <= EMBED_TOTAL, card.full_name
        for embed in embeds:
            assert len(embed.title or "") <= TITLE, card.full_name
            assert len(embed.description or "") <= DESCRIPTION, card.full_name
            for field in embed.fields:
                assert len(field.name) <= FIELD_NAME, card.full_name
                assert len(field.value) <= FIELD_VALUE, (card.full_name, field.name)


# ############################################################################# components
def test_components_variants(cards):
    card = find(cards, lambda c: len(c.variants) > 1)
    rows = krcg_bot._build_components(card, public=False)
    buttons = {b.label: b.custom_id for row in rows for b in row.components}
    for variant in card.variants:
        label = "Base" if variant.type == krcg.models.Variant.Type.BASE else variant.suffix
        assert krcg_bot._parse_stack(buttons[label]) == [variant.id]


def test_components_variants_inherit_the_trail(cards):
    """A variant is another version of the card on screen, not a step down from it."""
    card = find(cards, lambda c: len(c.variants) > 1)
    rows = krcg_bot._build_components(card, public=False, stack=[100001, 100002])
    buttons = {b.label: b.custom_id for row in rows for b in row.components}
    for variant in card.variants:
        label = "Base" if variant.type == krcg.models.Variant.Type.BASE else variant.suffix
        assert krcg_bot._parse_stack(buttons[label]) == [100001, 100002, variant.id]


def test_components_public_button(cards):
    card = find(cards, lambda c: True)
    ephemeral = {
        b.custom_id for row in krcg_bot._build_components(card, False) for b in row.components
    }
    public = {b.custom_id for row in krcg_bot._build_components(card, True) for b in row.components}
    assert f"public-{card.id}" in ephemeral
    assert f"public-{card.id}" not in public


def test_components_back_button(cards):
    """< Back walks up one frame and carries the rest of the trail with it."""
    card = find(cards, lambda c: True)
    rows = krcg_bot._build_components(card, public=False, stack=[100001, 100002, 100003])
    buttons = {b.label: b.custom_id for row in rows for b in row.components}
    assert krcg_bot._parse_stack(buttons["< Back"]) == [100001, 100002, 100003]


def test_components_no_back_button_at_the_root(cards):
    card = find(cards, lambda c: True)
    rows = krcg_bot._build_components(card, public=False)
    assert "< Back" not in {b.label for row in rows for b in row.components}


def test_components_ruling_links(cards):
    """A ruling link descends: the card on screen becomes the trail's last frame."""
    card = find(cards, lambda c: any(r.cards for r in c.rulings))
    rows = krcg_bot._build_components(card, public=False, stack=[100001])
    buttons = {b.custom_id for row in rows for b in row.components}
    cited = next(r for r in card.rulings if r.cards).cards[0]
    assert krcg_bot._switch_id([100001, card.id], cited.id) in buttons


def test_components_trail_truncates_at_the_oldest_frame(cards):
    """Past the ceiling the trail shortens from its far end, never 400s."""
    deep = [100001 + i for i in range(krcg_bot.MAX_FRAMES + 5)]
    custom_id = krcg_bot._switch_id(deep, 200000)
    assert len(custom_id) <= CUSTOM_ID
    assert krcg_bot._parse_stack(custom_id) == (deep + [200000])[-krcg_bot.MAX_FRAMES :]


def test_components_ping_pong_trail_draws_no_duplicate(cards):
    """A→B→A→B is real (58 mutually-citing pairs); a duplicate custom_id is a 400.

    At the full ceiling < Back and a ruling link would spell the same trail, so
    _build_components keeps the rendered stack one frame short.
    """
    card = find(cards, lambda c: any(r.cards for r in c.rulings))
    other = next(link for r in card.rulings if r.cards for link in r.cards)
    for depth in range(krcg_bot.MAX_FRAMES + 3):
        stack = [(card.id if i % 2 == 0 else other.id) for i in range(depth)]
        rows = krcg_bot._build_components(card, public=False, stack=stack)
        ids = [b.custom_id for row in rows for b in row.components]
        assert len(ids) == len(set(ids)), (depth, ids)
        for custom_id in ids:
            assert len(custom_id) <= CUSTOM_ID, (depth, custom_id)


def test_parse_stack_refuses_a_previous_release_button(cards):
    """A deploy leaves old-format buttons live; they must not reach the funnel.

    The unversioned T-010 trail is the case width alone cannot catch: it is
    digits in multiples of ID_WIDTH, exactly like the format that replaced it.
    """
    stale = ["switch-0-200123", "switch-100001-100002", "switch-", "switch-12345"]
    # the T-010 encoding at every depth it could have emitted, library and crypt
    for first in (100001, 200001):
        stale += [
            "switch-" + "".join(f"{first + i:0{krcg_bot.ID_WIDTH}d}" for i in range(depth))
            for depth in range(1, krcg_bot.MAX_FRAMES + 1)
        ]
    for custom_id in stale:
        with pytest.raises(krcg_bot.CommandFailed):
            krcg_bot._parse_stack(custom_id)


def test_card_lookup_refuses_a_retired_id(cards):
    """The failure T-010 introduces: a button outliving the card it names."""
    absent = 2
    assert absent not in cards
    with pytest.raises(krcg_bot.CommandFailed):
        krcg_bot._card(absent)


def test_card_ids_are_fixed_width(cards):
    """The whole custom_id encoding rests on this: a wider id desyncs every frame."""
    for card in cards.cards():
        assert len(str(card.id)) == krcg_bot.ID_WIDTH, card.full_name


def test_components_hold_discord_limits(cards):
    # the deepest trail production can reach: switch_card peels the target off a
    # full custom_id, so a rendered stack is never longer than MAX_FRAMES - 1
    deepest = [card.id for card in list(cards.cards())[: krcg_bot.MAX_FRAMES - 1]]
    for card in cards.cards():
        for public in (False, True):
            rows = krcg_bot._build_components(card, public, stack=deepest)
            assert len(rows) <= ROWS, card.full_name
            ids = [b.custom_id for row in rows for b in row.components]
            # a repeated custom_id is a 400 from Discord, not a duplicate button
            assert len(ids) == len(set(ids)), card.full_name
            for row in rows:
                assert 0 < len(row.components) <= BUTTONS, card.full_name
                for button in row.components:
                    assert 0 < len(button.label) <= LABEL, (card.full_name, button.label)
                    assert len(button.custom_id) <= CUSTOM_ID, card.full_name
                    assert button.custom_id[:6] in krcg_bot.COMPONENTS, button.custom_id


def test_component_dispatch_keys_are_sliceable():
    """Dispatch reads custom_id[:6]: a key of another length can never be reached."""
    assert all(len(prefix) == 6 for prefix in krcg_bot.COMPONENTS)


# ########################################################################### autocomplete
class FakeInteraction:
    """Enough of an AutocompleteInteraction to capture what the bot answers."""

    def __init__(self):
        self.choices = None

    async def create_response(self, choices):
        self.choices = choices


def test_the_fake_matches_the_interaction_it_stands_for(cards):
    """A fake that drifts from hikari keeps the suite green while autocomplete breaks."""
    real = inspect.signature(hikari.AutocompleteInteraction.create_response)
    fake = inspect.signature(FakeInteraction.create_response)
    assert list(real.parameters) == list(fake.parameters)
    # the error funnel falls back to a webhook because of this absence
    assert not hasattr(hikari.AutocompleteInteraction, "create_initial_response")


def complete(name):
    interaction = FakeInteraction()
    asyncio.run(krcg_bot.autocomplete_name(interaction, name))
    return interaction.choices


def test_autocomplete_matches_a_partial_name(cards):
    choices = complete("blood")
    assert choices
    assert all("blood" in choice.name.lower() for choice in choices)
    # what the user picks is sent back as `value`: it is the value that must resolve
    assert all(choice.value in cards for choice in choices)
    assert all(choice.name in cards for choice in choices)


def test_autocomplete_offers_the_full_25(cards):
    assert len(complete("blo")) == CHOICES


def test_autocomplete_finds_every_card_by_its_full_name(cards):
    """Autocomplete is the whole interface: a card it cannot offer cannot be asked for."""
    for card in cards.cards():
        assert card.full_name in krcg_bot._autocomplete_cache(card.full_name), card.full_name


@pytest.mark.parametrize("name", ["", None])
def test_autocomplete_ignores_an_empty_name(cards, name):
    assert complete(name) == []


def test_autocomplete_answers_empty_when_it_cannot(cards, monkeypatch):
    """An autocomplete interaction cannot be answered by the error funnel: never raise."""
    monkeypatch.setattr(krcg_bot, "CARDS", krcg.CardDict())
    krcg_bot._autocomplete_cache.cache_clear()
    try:
        assert complete("blood") == []
    finally:
        krcg_bot._autocomplete_cache.cache_clear()
