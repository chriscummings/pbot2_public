import os
import sqlite3
import discord
from dotenv import load_dotenv
from pbot2 import database
from pbot2.message_processor import MessageProcessor
from pbot2.logger import logger


# Load .env environment variables
load_dotenv()

db_conn = sqlite3.connect("db.sqlite", isolation_level=None)
database.create_tables(db_conn)
database.seed_tables(db_conn, "./pbot2/raw_data/insults_seed.csv", "./pbot2/raw_data/targets_seed.csv")

client = discord.Client()
message_processor = MessageProcessor(db_conn)

# Events ----------------------------------------------------------------------


@client.event
async def on_ready():
	print('We have logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
	# Ignore own messages.
	if message.author == client.user or message.author.bot:
		return

	# Log msg.
	logger.debug(("{}.{}.{}: {}".format(message.guild.name, message.channel.name, message.author, message.content)))

	# Handle msg.
	response = message_processor.process_message(message)
	logger.debug(response)
	if response:
		await message.reply(response)

	# Prune old DB entries.
	database.delete_old_unconfirmed_insults(db_conn)

# Exec ------------------------------------------------------------------------

client.run(os.getenv('DISCORD_TOKEN'))