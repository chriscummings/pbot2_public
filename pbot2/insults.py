import random
from pbot2 import database


def add_insult_short(message, insult_str, db_conn):
	return _add_insult(message, insult_str, db_conn, 0)


def add_insult_long(message, insult_str, db_conn):
	return _add_insult(message, insult_str, db_conn, 1)


def confirm_insult(insult_code, db_conn):
	result_dict = database.find_insult(db_conn, id=insult_code)

	if result_dict["success"]:
		result_dict = database._approve_insult(insult_code, db_conn)
		if result_dict["success"]:
			return "Insult \"{}\" confirmed.".format(insult_code)
		else:
			return "Error: \"{}\"".format(result_dict["error"])
	else:
		return "No insult by id=\"{}\" found!".format(insult_code)


def discard_insult(insult_code, db_conn):
	result_dict = database.find_insult(db_conn, id=insult_code)

	if result_dict["success"]:
		# import pdb
		# pdb.set_trace()
		if result_dict["payload"]["is_confirmed"]:
			return "Insult \"{}\" is already confirmed".format(insult_code)

		result_dict = database._discard_insult(insult_code, db_conn)
		if result_dict["success"]:
			return "Insult \"{}\" discarded.".format(insult_code)
		else:
			return "Error: \"{}\"".format(result_dict["error"])
	else:
		return "No insult by id=\"{}\" found!".format(insult_code)


def get_insult(name, db_conn):
	result_dict = database.get_random_insult(db_conn)
	if result_dict["success"]:
		varied_insult = _vary_insult(name, result_dict["payload"]["body"])	
		return varied_insult


def potentially_get_insult(target, db_conn):
	result_dict = database.chance_by_name(target, db_conn)
	if result_dict["success"]:
		if result_dict["payload"] >= random.random():
			return get_insult(target, db_conn)
		else:
			return None
	else:
		# FIXME: handle this condition.
		return None


def add_insult_help():
	return (
		"INSTRUCTIONS FOR ADDING INSULTS"
		"\n==============================="
		"There are two insult formats: shortform and longform. A shortform insult is a noun or adjective noun such as: "
		"\"fool\", \"damned fool\", or \"idiotic fool\". Longform insults have a target, indicated by \"<t>\" and are "
		"complete sentences. Examples are: \"<t>, you are a bucket head. Do you hear me, <t>?\" The target substrings "
		"will be replaced with the target's nickname.\n\n"
		"* To add a shortform insult: \"pbot!add_insult_short nerf herder\"\n"
		"* To add a longform insult: \"pbot!add_insult_long You know what you are, <t>? You're a fuss-budget!\"\n"
		"\n-you will then be asked to confirm or discard the insult.")

# PRIVATE ---------------------------------------------------------------------


def _vary_insult(name, insult_str):
	varied_insult = insult_str

	# Handle longform insults - replace <t> substrings with target's name.
	if "<t>" in varied_insult:
		varied_insult = varied_insult.replace("<t>", name)

	# Handle shortform insults - vary delivery slightly.
	else:
		flip = random.randint(0, 1)
		if flip == 0:
			varied_insult = "{}!".format(varied_insult.upper())
		else:
			varied_insult = "{}, you're a {}.".format(name, varied_insult.lower())

	return varied_insult


def _add_insult(message, insult_str, db_conn, is_longform):
	# Find insult by body string.
	result_dict = database.find_insult(db_conn, insult=insult_str)

	if result_dict["success"]:
		return "Insult \"{}\" already exists.".format(insult_str)

	else:
		result_dict = database.create_insult(
			message.guild.name,
			message.guild.id,
			message.channel.name,
			message.channel.id,
			insult_str,
			message.author.nick,
			is_longform,
			db_conn)

		if result_dict["error"]:
			return "Error: \"{}\".".format(result_dict["error"])

		row_id = result_dict["payload"]

		result_dict = database.find_insult(db_conn, id=row_id)

		if result_dict["error"]:
			return "Error: \"{}\".".format(result_dict["error"])
		else:
			return "Insult \"{}\" created. \n* To confirm insult, use \"pbot!confirm_insult {}\"\n* To discard, use \"pbot!discard_insult {}\"".format(result_dict["payload"]["body"], row_id, row_id)
		