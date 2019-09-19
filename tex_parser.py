from parse import *
import Queue

# constants
BEGIN = "\\begin{"
END = "\\end{"
BEGIN_LEN = len("\\begin{")
END_LEN = len("\\end{")
GROUPING_ARGS = ['cluster', 'flex']

# given a dictionary of key phrases mapped to their labels, write them to file_name
def write_to_file(dictionary, file_name):
	output = open(file_name, "w+")
	result_str = ""
	for keyphrase, label in dictionary.items():
		result_str += keyphrase + "\t"
		result_str += label + "\n"
	print result_str
	output.write(result_str)
	output.close()

# find an atom word with stirng
def find_atom_word(string):
	index = string.find(BEGIN)
	begin_str = string[index + BEGIN_LEN:]
	atom_word = begin_str[:begin_str.find("}")]
	return atom_word

# return a list of key phrases from string
def find_keyphrases(string):
	defn_index = string.find("\\defn{")
	if (defn_index == -1):
		return list()
	end_index = string.find("}", defn_index)
	new_string = string[end_index+1:]
	subarray = find_keyphrases(new_string)
	subarray.append(string[defn_index+len("\\defn{"):end_index])
	return subarray

# Returns true if latex string contains an atom and false otws
def contains_atom(tex_str):
	begin_start_index = tex_str.find(BEGIN)
	if (begin_start_index == -1):
		return False
	prefix_length = begin_start_index + BEGIN_LEN
	begin_finish_index = tex_str.find('}', prefix_length)
	command = tex_str[prefix_length:begin_finish_index]

	end_start_index = tex_str.find("\\end{" + command + "}")
	if (end_start_index == -1):
		return False
	return True

# Returns (start_index_of_atom, end_index_of_atom) of tex_str if 
# atom exists and false otws
def find_atom(tex_str):
	begin_start_index = tex_str.find(BEGIN)
	if (begin_start_index == -1):
		return (-1, -1)
	prefix_length = begin_start_index + BEGIN_LEN
	begin_finish_index = tex_str.find('}', prefix_length)
	command = tex_str[prefix_length:begin_finish_index]
	end_start_index = tex_str.find("\\end{" + command + "}")
	if (end_start_index == -1):
		return (-1, -1)
	end_finish_index = end_start_index + len("\\end{" + command + "}")
	return (begin_start_index, end_finish_index)

def parser(tex_str):
	label_to_atom = {}
	while (len(tex_str)):
		token_arg = find_atom_word(tex_str)
		(begin_index, end_index) = find_atom(tex_str)
		
		if (begin_index == -1 and end_index == -1):
			tex_str = ""
		# elif (not (token_arg.strip() in GROUPING_ARGS) and token_arg != "example"):
		elif (token_arg.strip() in ["definition", "theorem"]):
			atom = tex_str[begin_index:end_index]
			tex_str = tex_str[end_index:]
			label_index = atom.find("\\label{")

			keyphrases = find_keyphrases(atom)
			if (label_index != -1 and keyphrases != []):
				end_label_index = atom.find("}", label_index)
				label = atom[label_index + BEGIN_LEN:end_label_index]
				for keyphrase in keyphrases:
					label_to_atom[keyphrase] = label
		else:
			tmp = tex_str.strip().split('\n')
			tex_str = "\n".join(tmp[1:])
	return label_to_atom

# return true if end of string[:index] contains an argument to a command
def is_argument(string, index):
	last_open_brace = string.rfind("{", 0, index)
	last_close_brace = string.rfind("}", 0, index)
	last_literal_brace = string.rfind("\\{", 0, index)
	# if most recent open brace is after the most recent close brace, 
	# the index is probably an argument
	# print(string[index:index+30])
	if (last_open_brace > last_close_brace):
		if (last_literal_brace == -1 or last_literal_brace + 1 != last_open_brace):
			return True

	# TODO: make sure to check \[ and \]
	last_open_bracket = string.rfind("[", 0, index)
	last_close_bracket = string.rfind("]", 0, index)
	if (last_open_bracket > last_close_bracket):
		return True
	return False

# return true if end of string[:index] is a command
def is_command(string, index):
	backslash_index = string.rfind("\\", 0, index)
	substr = string[backslash_index + 1: index]
	return (len(substr.split()) < 2)

# return true if string[index] is within a a math expression
def is_math_expression(string, index):
	num_literal_dollar_signs = string.count("\$", 0, index)
	if (string.count("$$", 0, index) % 2):
		return True
	elif ((string.count("$", 0, index) - num_literal_dollar_signs) % 2):
		return True
	elif (string.count("\[", 0, index) - string.count("\]", 0, index) == 1):
		return True
	return False

# given string and map of keyphrases to labels, identify the key pheases
# and insert the labels as necessary
def insert_label(string, def_to_Label):
	lowercase_copy = string.lower()
	for definition, label in def_to_Label.items()[0:1]:
		prev_end = 0
		# only use lowercase_copy for finding occurrence case-insensitive
		index = lowercase_copy.find(definition.lower())
		str_iref = ""
		while (index != -1):
			# if string[index: index+len(definition)] is valid key phrase
			if (not is_math_expression(string, index) 
				and not is_argument(string, index)
				and not is_command(string, index)):
				iref = "\\iref{" + label + "}{" + definition + "}"
				str_iref += string[prev_end:index]
				str_iref += iref
				# if keyphrase is replaced by label, update prev_start to be last updated index
				prev_end = index + len(definition)
			index = lowercase_copy.find(definition, index+len(definition))
		str_iref += string[prev_end:]
	return str_iref

if __name__=='__main__':
	f = open("Chapter_01_Strings_and_Encodings.tex", "r")
	tex_str = f.read()
	result = parser(tex_str)
	new_latex = insert_label(tex_str, result)