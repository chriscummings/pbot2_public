import random


def roll_die(die_string):
	die_parts = die_string.split('d')
	die_count = int(die_parts[0])
	die_type  = int(die_parts[1])

	# Handle absurd input.
	if die_count > 1000 or die_type > 1000:
		return "Value(s) out of range. Try <= 1000."

	die_sum = 0
	for n in range(die_count):
		die_sum += random.randint(1, die_type)

	return "{}: {}".format(die_string, die_sum)
