import csv
import datetime
import copy
import uuid


result_dictionary = {
	"success": False,
	"error": False,
	"payload": None
}


def _gen_uuid():
	uid = uuid.uuid4()
	uid_str = "".join(str(uid).split("-"))
	return uid_str[0:11]


def _approve_insult(insult_code, db_conn):
	cursor = db_conn.cursor()
	result = copy.deepcopy(result_dictionary)

	try:
		cursor.execute('''UPDATE insults SET is_confirmed = 1 WHERE id = "{}"'''.format(insult_code))
		result["success"] = True
		return result
	except Exception as err:
		result["success"] = False
		result["error"]   = err
		return result


def _discard_insult(insult_code, db_conn):
	cursor = db_conn.cursor()
	result = copy.deepcopy(result_dictionary)

	try:
		cursor.execute('''DELETE FROM insults WHERE id = "{}"'''.format(insult_code))
		result["success"] = True
	except Exception as err:
		result["success"] = False
		result["error"]   = err
		return result

	return result


def delete_old_unconfirmed_insults(db_conn):
	cursor = db_conn.cursor()
	cursor.execute('''DELETE FROM insults WHERE created_at <= date('now', '-1 day') AND is_confirmed = 0''')


def create_insult(guild_name, guild_id, chan_name, chan_id, insult, author, is_longform, db_conn):
	cursor = db_conn.cursor()
	result = copy.deepcopy(result_dictionary)

	result_dict = find_insult(db_conn, insult=insult)
	if result_dict["success"]:
		result["success"] = False
		result["error"] = "Duplicate insult."
		return result

	try:
		cursor.execute('''INSERT INTO insults (
		guild_name, guild_id, channel_name, channel_id, body, author, uuid, is_longform, created_at
		) VALUES (?,?,?,?,?,?,?,?,?)''', (
			guild_name, guild_id, chan_name, chan_id, insult, author, _gen_uuid(), is_longform, datetime.datetime.now()
		))
		result["success"] = True
		result["payload"] = cursor.lastrowid
		return result
	except Exception as err:
		result["success"] = False
		result["error"]   = err
		return result


def find_insult(db_conn, insult=None, id=None):
	cursor = db_conn.cursor()
	result = copy.deepcopy(result_dictionary)

	# Search for insult by id or insult body.
	if id:
		try:
			cursor.execute('''SELECT * FROM insults WHERE id="{}"'''.format(id))
		except Exception as err:
			result["success"] = False
			result["error"]   = err
			return result
	else:
		try:
			cursor.execute('''SELECT * FROM insults WHERE body="{}"'''.format(insult))
		except Exception as err:
			result["success"] = False
			result["error"]   = err
			return result

	row = cursor.fetchone()
	cursor.close()

	if row:
		result["success"] = True
		result["payload"] = {
			"id": row[0],
			"guild_name": row[1],
			"guild_id": row[2],
			"channel_name": row[3],
			"channel_id": row[4],
			"body": row[5],
			"author": row[6],
			"uuid": row[7],
			"is_longform": row[8],
			"is_confirmed": row[9]
		}
		return result
	else:
		result["success"] = False
		result["error"] = "Insult not found."
		return result


def get_random_insult(db_conn):
	cursor = db_conn.cursor()
	result = copy.deepcopy(result_dictionary)

	try:
		cursor.execute('''SELECT * FROM insults WHERE is_confirmed="1" ORDER BY RANDOM() LIMIT 1;''')
	except Exception as err:
		result["success"] = False
		result["error"]   = err
		return result

	row = cursor.fetchone()

	if row:
		row_id = row[0]
		result_dict = find_insult(db_conn, id=row_id)

		result["success"] = True
		result["payload"] = result_dict["payload"]
		return result
	else:
		result["success"] = False
		return result


def chance_by_name(name, db_conn):
	cursor = db_conn.cursor()
	result = copy.deepcopy(result_dictionary)

	try:
		cursor.execute('''SELECT * FROM targets WHERE username="{}"'''.format(name))
	except Exception as err:
		result["success"] = False
		result["error"]   = err
		return result

	row = cursor.fetchone()

	if row:
		result["success"] = True
		result["payload"] = row[2]
		return result
	else:
		try:
			cursor.execute('''SELECT * FROM targets WHERE username="{}"'''.format("default"))
			row = cursor.fetchone()
			result["success"] = True
			result["payload"] = row[2]
			return result
		except Exception as err:
			result["success"] = False
			result["error"]   = err
			return result


def create_tables(db_conn):
	cursor = db_conn.cursor()

	insults_table_sql = '''CREATE TABLE IF NOT EXISTS insults (
	id INTEGER PRIMARY KEY,
	guild_name TEXT NOT NULL,
	guild_id INTEGER NOT NULL,
	channel_name TEXT NOT NULL,
	channel_id INTEGER NOT NULL,
	body TEXT UNIQUE NOT NULL,
	author TEXT NOT NULL,
	uuid TEXT UNIQUE NOT NULL,
	is_longform INTEGER NOT NULL,
	is_confirmed INTEGER DEFAULT 0 NOT NULL,
	created_at TEXT
	)'''
	cursor.execute(insults_table_sql)

	targets_table_sql = '''CREATE TABLE IF NOT EXISTS targets (
	id INTEGER PRIMARY KEY,
	username TEXT NOT NULL,
	chance REAL NOT NULL,
	created_at TEXT NOT NULL
	)'''
	cursor.execute(targets_table_sql)


def seed_tables(db_conn, insults_seed_path, targets_seed_path):
	cursor = db_conn.cursor()

	# Seed insults --
	input_file = csv.DictReader(open(insults_seed_path))
	for row in input_file:
		cursor.execute('''SELECT * FROM insults WHERE body="{}"'''.format(row["body"]))

		record = cursor.fetchone()

		if not record:
			guild_name  = "Seed"
			guild_id    = "Seed"
			chan_name   = "Seed"
			chan_id     = "Seed"
			insult      = row["body"]
			author      = "Seed"
			is_longform = row["is_longform"]

			result_dict = create_insult(guild_name, guild_id, chan_name, chan_id, insult, author, is_longform, db_conn)

			if result_dict["success"]:
				_approve_insult(result_dict["payload"], db_conn)

	# Seed targets --
	input_file = csv.DictReader(open(targets_seed_path))
	for row in input_file:
		cursor.execute('''SELECT * FROM targets WHERE username="{}"'''.format(row["username"]))

		record = cursor.fetchone()

		if not record:
			username   = row["username"]
			chance     = row["chance"]

			cursor.execute('''INSERT INTO targets (username, chance, created_at) VALUES ("{}","{}","{}")'''.format(
				username, chance, datetime.datetime.now()
			))
