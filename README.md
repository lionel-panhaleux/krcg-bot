# KRCG Discord Bot

[![Test](https://github.com/lionel-panhaleux/krcg-bot/actions/workflows/test.yml/badge.svg)](https://github.com/lionel-panhaleux/krcg-bot/actions/workflows/test.yml)
[![Python version](https://img.shields.io/badge/python-3.8-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-blue)](https://opensource.org/licenses/MIT)
[![Code Style](https://img.shields.io/badge/code%20style-black-black)](https://github.com/psf/black)

A discord bot to display V:tES cards, using
the VEKN [official card texts](http://www.vekn.net/card-lists) and
[rulings database](https://github.com/vtes-biased/vtes-rulings) rulings list.

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

## Development

`just serve` runs the bot against a test guild, reading a `DISCORD_TOKEN` from a
`.env` file at the root of the repository (ignored by git). The development
token is shared through the repo, age-encrypted to the keys in
`ansible/secrets/age-recipients.txt` — decrypt it into place:

```bash
age -d -i ~/.ssh/<your-key> -o .env ansible/secrets/dev-env.age
```

Or use your own bot's token from the
[Discord applications page](https://discord.com/developers/applications):

```bash
export DISCORD_TOKEN="discord_token_of_your_bot"
```

`just test` runs the suite, which needs the network — it asserts against the
live card corpus. The deploy of the hosted instance lives in
[`ansible/`](ansible/README.md).
