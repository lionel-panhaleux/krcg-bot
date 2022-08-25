# KRCG Discord Bot

[![PyPI version](https://badge.fury.io/py/krcg-bot.svg)](https://badge.fury.io/py/krcg-bot)
[![Validation](https://github.com/lionel-panhaleux/krcg-bot/workflows/Validation/badge.svg)](https://github.com/lionel-panhaleux/krcg-bot/actions)
[![Python version](https://img.shields.io/badge/python-3.8-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://opensource.org/licenses/MIT)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)

A discord bot to display V:tES cards, using
the VEKN [official card texts](http://www.vekn.net/card-lists) and
[KRCG](https://github.com/lionel-panhaleux/krcg) rulings list.

Portions of the materials are the copyrights and trademarks of Paradox Interactive AB,
and are used with permission. All rights reserved.
For more information please visit [white-wolf.com](http://www.white-wolf.com).

![Dark Pack](dark-pack.png)

## Use it

This bot lets you retrieve cards official text, image and rulings:
![Bot Example](https://raw.githubusercontent.com/lionel-panhaleux/krcg-bot/master/bot-example.png)

To call the bot, use slash commands: `/card` followed by a card name.
Make sure you use the name autocompletion or you might not get the result you want.
By default, the bot answers to you with a private message other members do not see.
You can use the optional `public` paramater to your slash command to make the message
visible for everyone in the channel.

It is online and free to use,
[install it on your Discord server](https://discordapp.com/oauth2/authorize?client_id=703921850270613505&scope=bot%20applications.commands).

## Contribute

**Contributions are welcome !**

This bot is an offspring of the [KRCG](https://github.com/lionel-panhaleux/krcg)
python package, so please refer to that repository for issues, discussions
and contributions guidelines.

## Hosting the bot

If you need to host a new version of the bot yourself,
[Python 3](https://www.python.org/downloads/) is required, as well as an
environment variable `DISCORD_TOKEN`.
The token can be found on your
[Discord applications page](https://discord.com/developers/applications).

The preferred way to run the bot is to use a python virtualenv:

```bash
/usr/bin/python3 -m venv venv
source venv/bin/activate
pip install krcg-bot
DISCORD_TOKEN=discord_token_of_your_bot
krcg-bot
```

A [systemd](https://en.wikipedia.org/wiki/Systemd) unit can be used
to configure the bot as a system service:

```ini
[Unit]
Description=krcg-bot
After=network-online.target

[Service]
Type=simple
Restart=always
WorkingDirectory=directory_where_krcg_is_installed
Environment=DISCORD_TOKEN=discord_token_of_your_bot
ExecStart=/bin/bash -c 'source venv/bin/activate && krcg-bot'

[Install]
WantedBy=multi-user.target
```

For development, the environment variable `DISCORD_TOKEN` can be provided
by a personal `.env` file at the root of the krcg folder (ignored by git):

```bash
export DISCORD_TOKEN="discord_token_of_your_bot"
```
