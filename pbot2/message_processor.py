from pbot2.die import roll_die
from pbot2 import insults


class MessageProcessor:
    """ This class acts as an interface between the discord-related app file and
	various internal modules, extracting required strings from the Message
	object and passing them on.
	"""

    def __init__(self, db_conn):
        self.db_conn = db_conn

    def process_message(self, message):
        """ Handle Discord Message objects. """

        # Help
        if message.content.strip() == "pbot!help":
            return ("Instructions for pbot usage\n"
                    "===========================\n"
                    "Top-level commands:\n"
                    "* pbot!roll - Roll die.\n"
                    "* pbot!insult - Insult yourself.\n"
                    "* pbot!add_insult - Add insults.")

        # Roll die
        if message.content.startswith("pbot!roll"):
            # Handle no roll condition.
            if message.content.strip() == "pbot!roll":
                return "Missing die to roll. Example: pbot!roll 2d4"

            message_parts = message.content.lower().strip().split(" ")
            return roll_die(message_parts[1])

        # Insults -------------------------------------------------------------

        # Insult yourself
        if message.content.strip() == "pbot!insult":
            return insults.get_insult(message.author.nick, self.db_conn)

        # Explain adding insult
        if message.content.strip() == "pbot!add_insult":
            return insults.add_insult_help()

        # Add insult short
        if message.content.startswith("pbot!add_insult_short"):
            _, arg = self._divide_cmd_and_arg(message.content)
            return insults.add_insult_short(message, arg, self.db_conn)

        # Add insult long
        if message.content.startswith("pbot!add_insult_long"):
            _, arg = self._divide_cmd_and_arg(message.content)
            return insults.add_insult_long(message, arg, self.db_conn)

        # Confirm insult
        if message.content.startswith("pbot!confirm_insult"):
            _, arg = self._divide_cmd_and_arg(message.content)
            return insults.confirm_insult(arg, self.db_conn)

        # Discard insult
        if message.content.startswith("pbot!discard_insult"):
            _, arg = self._divide_cmd_and_arg(message.content)
            return insults.discard_insult(arg, self.db_conn)

        insult = insults.potentially_get_insult(message.author.nick, self.db_conn)
        if insult:
            return insult

        return None

    # PRIVATE -----------------------------------------------------------------

    def _divide_cmd_and_arg(self, cmd_and_arg):
        # Split on whitespace.
        cmd_list = cmd_and_arg.split(sep=None, maxsplit=-1)

        # Get first index item.
        cmd = cmd_list[0]

        # Rejoin following indexes.
        arg = " ".join(cmd_list[1::])

        return cmd, arg
