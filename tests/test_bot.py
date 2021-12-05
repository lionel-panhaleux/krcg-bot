import datetime

import krcg_bot


def test_bot():
    response = krcg_bot.handle_message("krcg")
    assert not response.get("content")
    assert response["embed"]
    assert response["embed"].to_dict() == {
        "color": 3498574,
        "fields": [
            {"inline": True, "name": "Type", "value": "Master"},
            {"inline": True, "name": "Cost", "value": "2 Pool"},
            {
                "inline": False,
                "name": "Card Text",
                "value": "Unique location.\n"
                "Lock to give a minion you control +1 intercept. Lock "
                "and burn 1 pool to give a minion controlled by another "
                "Methuselah +1 intercept.",
            },
        ],
        "footer": {
            "text": "Click the title to submit new rulings or rulings corrections"
        },
        "image": {
            "url": (
                "https://static.krcg.org/card/krcgnewsradio.jpg"
                f"#{datetime.datetime.now():%Y%m%d%H}"
            )
        },
        "title": "KRCG News Radio",
        "type": "rich",
        "url": (
            "https://codex-of-the-damned.org/en/card-search.html"
            "?card=KRCG+News+Radio"
        ),
    }
    # matching isn't easy
    response = krcg_bot.handle_message("monastery")
    assert not response.get("content")
    assert response["embed"]
    assert response["embed"].to_dict() == {
        "color": 3498574,
        "fields": [
            {"inline": True, "name": "Type", "value": "Master"},
            {"inline": True, "name": "Cost", "value": "3 Pool"},
            {
                "inline": False,
                "name": "Card Text",
                "value": "Unique location.\n"
                "+1 hand size. Lock to give a vampire with capacity 8 or "
                "more +1 stealth.",
            },
        ],
        "footer": {
            "text": "Click the title to submit new rulings or rulings corrections"
        },
        "image": {
            "url": (
                "https://static.krcg.org/card/monasteryofshadows.jpg"
                f"#{datetime.datetime.now():%Y%m%d%H}"
            )
        },
        "title": "Monastery of Shadows",
        "type": "rich",
        "url": (
            "https://codex-of-the-damned.org/en/card-search.html"
            "?card=Monastery+of+Shadows"
        ),
    }
    # multiple possibilities gives you a choice
    response = krcg_bot.handle_message("isabel")
    assert not response.get("content")
    assert response["embed"]
    assert response["embed"].to_dict() == {
        "color": 16777215,
        "description": "1: Isabel Giovanni\n" "2: Isabel de Leon",
        "footer": {"text": "Click a number as reaction."},
        "title": "What card did you mean ?",
        "type": "rich",
    }
    # too many possibilities (> 10) gives you an error
    response = krcg_bot.handle_message("the")
    assert response["content"] == "Too many candidates, try a more complete card name."
    assert not response.get("embed")
    # vampire with advanced version
    response = krcg_bot.handle_message("kemintiri")
    assert response["embed"]
    assert response["embed"].to_dict() == {
        "color": 16777215,
        "description": "1: Kemintiri\n" "2: Kemintiri (ADV)",
        "footer": {"text": "Click a number as reaction."},
        "title": "What card did you mean ?",
        "type": "rich",
    }
    # vampire with evolution
    response = krcg_bot.handle_message("theo bell")
    assert response["embed"]
    assert response["embed"].to_dict() == {
        "color": 16777215,
        "description": "1: Theo Bell\n2: Theo Bell (ADV)\n3: Theo Bell (G6)",
        "footer": {"text": "Click a number as reaction."},
        "title": "What card did you mean ?",
        "type": "rich",
    }
    # vampire with comma in the name
    response = krcg_bot.handle_message("tariq")
    assert response["embed"]
    assert response["embed"].to_dict() == {
        "color": 16777215,
        "description": "1: Tariq, The Silent\n" "2: Tariq, The Silent (ADV)",
        "footer": {"text": "Click a number as reaction."},
        "title": "What card did you mean ?",
        "type": "rich",
    }
    # card with column in the name
    response = krcg_bot.handle_message("condemnation")
    assert response["embed"]
    assert response["embed"].to_dict() == {
        "color": 16777215,
        "description": "1: Condemnation: Betrayed\n"
        "2: Condemnation: Doomed\n"
        "3: Condemnation: Languid\n"
        "4: Condemnation: Mute\n"
        "5: Consanguineous Condemnation",
        "footer": {"text": "Click a number as reaction."},
        "title": "What card did you mean ?",
        "type": "rich",
    }
    # fuzzy match
    response = krcg_bot.handle_message("enchant kidnred")
    assert response["embed"]
    assert response["embed"].title == "Enchant Kindred"
    # no match
    response = krcg_bot.handle_message("foobar")
    assert not response.get("embed")
    assert response["content"] == "No card match"
    # rulings
    response = krcg_bot.handle_message("rotschreck")
    assert response["embed"].to_dict() == {
        "color": 3498574,
        "fields": [
            {"inline": True, "name": "Type", "value": "Master"},
            {
                "inline": False,
                "name": "Card Text",
                "value": (
                    "Master: out-of-turn. Frenzy.\n"
                    "Put this card on a vampire when an opposing minion "
                    "attempts to inflict aggravated damage on him or her, "
                    "whether the damage would be successfully inflicted or "
                    "not. Combat ends. This vampire is locked and sent to "
                    "torpor. This vampire does not unlock as normal. During "
                    "this vampire's next unlock phase, burn this card."
                ),
            },
            {
                "inline": False,
                "name": "Rulings",
                "value": (
                    "- Can only be played during the strike announcement "
                    "phase, on the opponent, when a minion attempts to make "
                    "a strike that is effective at the current range and "
                    "would inflict aggravated damage to this opponent, even "
                    "if the opponent treats aggravated damage as normal. "
                    "[[RTR 19961113]](https://groups.google.com/d/msg/"
                    "rec.games.trading-cards.jyhad/VbMEQmJjI_w/hkDh73Y1IukJ) "
                    "[[RTR 19980623]](https://groups.google.com/d/msg/"
                    "rec.games.trading-cards.jyhad/tSpd9dtTElc/-CuHJF54_n0J) "
                    "[[RTR 19980928]](https://groups.google.com/d/msg/"
                    "rec.games.trading-cards.jyhad/Xva4_IRavxM/F-_fjzTmo88J) "
                    "[[RTR 20041202]](https://groups.google.com/d/msg/"
                    "rec.games.trading-cards.jyhad/WUWh7AdooDU/vojisZMCSnsJ) "
                    "[[ANK 20200130-1]](http://www.vekn.net/forum/rules-questions/"
                    "78400-rotshreck#98821)\n"
                    "**... (Click the title for more rulings)**"
                ),
            },
        ],
        "footer": {
            "text": "Click the title to submit new rulings or rulings corrections"
        },
        "image": {
            "url": (
                "https://static.krcg.org/card/rotschreck.jpg"
                f"#{datetime.datetime.now():%Y%m%d%H}"
            )
        },
        "title": "Rötschreck",
        "type": "rich",
        "url": (
            "https://codex-of-the-damned.org/en/"
            "card-search.html?card=R%C3%B6tschreck"
        ),
    }
