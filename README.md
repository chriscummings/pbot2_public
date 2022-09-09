# pbot2 a Discord Insult Bot

### Features

* Randomly insults chatting users.
* Give specific usernames a weighted chance to be randomly insulted.
* Add your own insults via a seed .CSV file or via chatting with bot.
* Prompts to confirm or discard newly created insults.
* Automatically deletes unconfirmed insults after 24 hours.
* Rolls die!
* There's nothing stopping you from using this to give affirmations instead of insults. =D
* Logging, tests, etc.

### Requirements
* Python 3.7+
* [Poetry](https://python-poetry.org/) installed.

See specific dependencies in the poetry.lock file.

### Running the bot:

* `poetry install` to install dependencies.
* `poetry run python app.py` to run the bot.
* `poetry run pytest` to run the tests. (generates a `./test.sqlite` file)

### Top-Level Chat Commands:

* `pbot!help` - Help text.
* `pbot!roll` - Get die roll help.
* `pbot!insult` - Get insulted.
* `pbot!add_insult` - Get help adding an insult.

### Configuration:

* Add your discord developer token to the environment file - `.env` (REQUIRED)
* Edit the insults seed file - `pbot2/raw_data/insults_seed.csv`
* Edit the targets seed file - `pbot2/raw_data/targets_seed.csv`
* Edit the sqlite database - `db.sqlite` (created on start up)

### To Do:

* Use UUIDs instead of row ids for confirming and discarding insults. (already generating uuids)
* Date insult upon usage & only use newer insults?
* Find reference link(s) for creating & adding a discord bot.
* Fix the assumption of a nickname (bug)

### Reference

* https://discord.com/developers - for bot management.
