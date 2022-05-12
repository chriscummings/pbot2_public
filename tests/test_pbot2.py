import os
import sqlite3
import gc
from pbot2.message_processor import MessageProcessor
from pbot2 import database
from pbot2 import insults


class MockAuthor:
    def __init__(self, uid, name, nick):
        self.id = uid
        self.name = name
        self.nick = nick


class MockChannel:
    def __init__(self, uid, name):
        self.id = uid
        self.name = name


class MockGuild:
    def __init__(self, uid, name):
        self.id = uid
        self.name = name


class MockMessage:
    def __init__(self, msg_body=""):
        self.content = msg_body
        self.channel = MockChannel(87634092134, "general")
        self.guild = MockGuild(9823192837, "bot_playground")
        self.author = MockAuthor(92038498, "randomcharacters", "Bilbo-420-247")


def get_db_conn(delete_existing=True):
    test_db_path = "test.sqlite"

    # Force garbage collection to clean up old DB connections.
    gc.collect(2)

    if delete_existing:
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

    db_conn = sqlite3.connect(test_db_path, isolation_level=None)
    database.create_tables(db_conn)

    return db_conn


def seed_database(db_conn):
    database.seed_tables(db_conn, "./pbot2/raw_data/insults_test_seed.csv", "./pbot2/raw_data/targets_seed.csv")


# TEST INSULTS ----------------------------------------------------------------

def test_vary_insult():
    insult = insults._vary_insult("Bilbo", "<t>, you're a thief!")
    assert "Bilbo, you're a thief!" in insult

    insult = insults._vary_insult("Frodo", "fussbudget")
    assert "fussbudget" in insult.lower()


def test_get_insult_with_longform():
    insult = "<t>, you a busta!"
    conn   = get_db_conn()
    msg    = MockMessage()

    # Create a confirmed insult.
    result_dict = database.create_insult(msg.guild.name, msg.guild.id, msg.channel.name, msg.channel.id, insult,
                                         msg.author.nick, 1, conn)
    assert result_dict["success"] == True
    insults.confirm_insult(result_dict["payload"], conn)

    result = insults.get_insult("Bilbo", conn)

    assert "Bilbo" in result
    assert "you a busta" in result.lower()


def test_get_insult_with_shortform():
    insult = "dumb baby"
    conn = get_db_conn()
    msg = MockMessage()

    # Create a confirmed insult.
    result_dict = database.create_insult(msg.guild.name, msg.guild.id, msg.channel.name, msg.channel.id, insult,
                                         msg.author.nick, 0, conn)
    assert result_dict["success"] == True
    insults.confirm_insult(result_dict["payload"], conn)

    result = insults.get_insult("Bilbo", conn)

    assert insult in result.lower()


def test_get_random_insult_without_confirmed_insults():
    insult = "dumpster baby"
    conn = get_db_conn()
    msg = MockMessage()

    # Create an unconfirmed insult.
    result_dict = database.create_insult(msg.guild.name, msg.guild.id, msg.channel.name, msg.channel.id, insult,
                                         msg.author.nick, 0, conn)
    assert result_dict["success"] == True

    # Ensure it isn't returned.
    result_dict = database.get_random_insult(conn)
    assert result_dict["success"] == False
    assert result_dict["payload"] is None


def test_get_random_insult():
    insult = "blasted fool"
    conn = get_db_conn()
    msg = MockMessage()

    # Create a confirmed insult.
    result_dict = database.create_insult(msg.guild.name, msg.guild.id, msg.channel.name, msg.channel.id, insult,
                                         msg.author.nick, 0, conn)
    insults.confirm_insult(result_dict["payload"], conn)

    result_dict = database.get_random_insult(conn)
    assert result_dict["success"] == True
    assert insult in result_dict["payload"]["body"]


def test_discarding_a_confirmed_insult():
    insult = "donkey brains"
    conn = get_db_conn()
    msg = MockMessage()

    # Create insult
    result_dict = database.create_insult(msg.guild.name, msg.guild.id, msg.channel.name, msg.channel.id, insult,
                                         msg.author.nick, 0, conn)
    assert result_dict["success"] == True
    row_id = result_dict["payload"]

    result_dict = database.find_insult(conn, id=row_id)
    assert result_dict["payload"]["is_confirmed"] == 0

    # Confirm insult
    result = insults.confirm_insult(row_id, conn)
    assert "confirmed" in result

    result_dict = database.find_insult(conn, id=row_id)
    assert result_dict["payload"]["is_confirmed"] == 1

    result = insults.discard_insult(row_id, conn)
    assert "already confirmed" in result


def test_discard_insult():
    insult = "unpopular v-tuber"
    conn = get_db_conn()
    msg = MockMessage()
    row_id = None

    # Create an unconfirmed insult.
    result_dict = database.create_insult(msg.guild.name, msg.guild.id, msg.channel.name, msg.channel.id, insult,
                                         msg.author.nick, 0, conn)
    assert result_dict["success"] == True
    row_id = result_dict["payload"]

    # Discard insult.
    insults.discard_insult(row_id, conn)

    # Verify it's gone.
    result_dict = database.find_insult(conn, id=row_id)
    assert result_dict["success"] == False
    assert "not found" in result_dict["error"].lower()


def test_confirm_insult():
    insult = "dirt grub"
    conn = get_db_conn()
    msg = MockMessage("pbot!roll 1d1")
    row_id = None

    # Create an unconfirmed insult.
    result_dict = database.create_insult(msg.guild.name, msg.guild.id, msg.channel.name, msg.channel.id, insult,
                                         msg.author.nick, 0, conn)
    assert result_dict["success"] == True

    row_id = result_dict["payload"]

    # Verify it's unconfirmed.
    result_dict = database.find_insult(conn, id=row_id)
    assert result_dict["success"] == True
    assert result_dict["payload"]["is_confirmed"] == 0

    # Confirm insult.
    insults.confirm_insult(row_id, conn)

    # Verify insult is confirmed.
    result_dict = database.find_insult(conn, id=row_id)
    assert result_dict["success"] == True
    assert result_dict["payload"]["is_confirmed"] == 1


def test_add_insult_long_duplicates():
    insult = "You know what you are, <t>? You're a fuss budget!"
    conn = get_db_conn()
    msg = MockMessage()

    _ = insults.add_insult_long(msg, insult, conn)

    # Try to recreate same insult.
    returned_string = insults.add_insult_long(msg, insult, conn)

    assert "already exists" in returned_string


def test_add_insult_short_duplicates():
    insult = "feline aids"
    conn = get_db_conn()
    msg = MockMessage()

    _ = insults.add_insult_short(msg, insult, conn)

    # Try to recreate same insult.
    returned_string = insults.add_insult_short(msg, insult, conn)

    assert insult in returned_string
    assert "already exists" in returned_string


def test_add_insult_with_problematic_chars():
    insult = '''sda?;',d"fsfs'''
    conn = get_db_conn()
    msg = MockMessage()

    returned_string = insults.add_insult_short(msg, insult, conn)

    assert insult in returned_string


def test_add_insult_long():
    insult = "You know what you are, <t>? You're a fuss-budget!"
    conn = get_db_conn()
    msg = MockMessage()

    returned_string = insults.add_insult_long(msg, insult, conn)

    assert insult in returned_string
    assert "confirm" in returned_string


def test_add_insult_short():
    insult = "filthy little healer"
    conn = get_db_conn()
    msg = MockMessage()

    returned_string = insults.add_insult_short(msg, insult, conn)

    assert insult in returned_string
    assert "confirm" in returned_string


def test_potentially_get_insult():
    # Can only sort of tests this...
    conn = get_db_conn()
    # database.seed_tables(conn)
    seed_database(conn)

    # Test with a user that has 100% chance to get an insult.
    result = insults.potentially_get_insult("Bilbo-420-247", conn)
    assert bool(result) == True


# TEST Database ---------------------------------------------------------------

def test_chance_by_name():
    conn = get_db_conn()
    # database.seed_tables(conn)
    seed_database(conn)

    default_chance = .05  # FIXME: hardcoded value

    # Check default.
    result_dict = database.chance_by_name("default", conn)
    assert result_dict["payload"] == default_chance
    assert result_dict["success"] == True

    # Check non-existant name uses default.
    result_dict = database.chance_by_name("noone", conn)
    assert result_dict["success"] == True
    assert result_dict["payload"] == default_chance


def test_create_insult_duplicates():
    insult = "hammer"
    conn = get_db_conn()

    result_dict = database.create_insult("guild name", 123213, "channel name", 32432324, insult, "author", 0, conn)
    assert result_dict["success"] == True

    result_dict = database.create_insult("guild name", 123213, "channel name", 32432324, insult, "author", 0, conn)
    assert result_dict["success"] == False
    assert "duplicate" in result_dict["error"].lower()


def test_create_and_find_insult():
    insult = "You know what you are? You're a bugbear!"
    conn = get_db_conn()

    result_dict = database.find_insult(conn, insult=insult)
    assert result_dict["success"] == False
    assert result_dict["payload"] == None

    result_dict = database.create_insult("guild name", 123213, "channel name", 32432324, insult, "author", 0, conn)
    assert result_dict["success"] == True
    assert result_dict["payload"] == 1

    result_dict = database.find_insult(conn, insult=insult)
    assert result_dict["success"] == True
    assert result_dict["payload"]["body"] == insult


def test_seed_tables():
    conn = get_db_conn()

    result_dict = database.get_random_insult(conn)
    assert result_dict["success"] == False
    assert result_dict["payload"] == None

    # database.seed_tables(conn)
    seed_database(conn)

    result_dict = database.get_random_insult(conn)
    assert result_dict["success"] == True
    assert bool(result_dict["payload"]["author"]) == True


# TEST DIE ROLLS --------------------------------------------------------------

def test_die_rolls():
    processor = MessageProcessor(None)

    # Handle die roll.
    msg = MockMessage("pbot!roll 1d1")
    assert "1d1: 1" in processor.process_message(msg)

    # Handle die roll.
    msg = MockMessage("pbot!roll 2d4")
    assert "2d4: " in processor.process_message(msg)

    # Complains if given absurd input.
    msg = MockMessage("pbot!roll 99999d99999")
    assert "out of range" in processor.process_message(msg)

    # Complains if not given a roll param. 
    msg = MockMessage("pbot!roll")
    assert "Missing die to roll" in processor.process_message(msg)

    # It ignores trailing space. 
    msg = MockMessage("pbot!roll ")
    assert "Missing die to roll" in processor.process_message(msg)
