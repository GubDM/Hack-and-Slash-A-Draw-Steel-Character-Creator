from textwrap import wrap 	# for printing descriptions

ALL_DATA = {}
ALL_CHOICES = {}
ALL_FEATURES = {}

class ChoiceSelector():
	def __init__(self, feature_name=None, data_dict=None):
		self.prompt = ''
		self.prompt_desc = ''
		self.has_description = False
		self.choice_name = ''

		self.budget = None # int
		self.budgetfield = None # string name of field in simstate.my_char
		self.budgetfield_index = None # int, index into list field budgetfield
		self.number_of_options = 0

		self.names = []
		self.descriptions = []

		self.costs = []
		self.scripts = []

		self.ignore_field_names = []
		self.ignore_options = []
		self.followup_choices = []
		self.implement_child = True

		if data_dict != None:
			self.load_choice_data(feature_name, data_dict)

	def set_description(self, description):
		self.prompt_desc = description
		self.has_description = True

	def load_choice_data(self, feature_name, data_dict):
		# general choice data
		if not isinstance(data_dict['budget'], int) and ',' in data_dict['budget']:
			budgetdata = data_dict['budget'].split(',')
			self.budgetfield = budgetdata[1]
			if len(budgetdata) > 2:
				self.budgetfield_index = budgetdata[2]
		else:
			self.budget = int(data_dict['budget'])

		self.choice_name = feature_name

		# special case: load choice options from skills choices
		if 'options_skills' in data_dict:
			options_list = data_dict['options_skills'].split('|')
			data_dict['options'] = []
			for options_choice in options_list:
				keyword, options = options_choice.split(':')
				options = options.split(',')
				if (keyword == 'skill' or keyword == 'skills'):
					for skill_name in options:
						skillchoice = ALL_DATA['skills']['allskills'][skill_name]
						# add the group the field belongs to
						self.ignore_field_names.append(skillchoice['group'])
						data_dict['options'].append(ALL_DATA['skills']['allskills'][skill_name])
				elif (keyword == 'group' or keyword == 'groups'):
					for group_name in options:
						skillchoicename = ALL_DATA['skills'][group_name]['name']
						# automatically ignore skill group
						self.ignore_field_names.append(
							ALL_DATA['skills'][group_name]['choices'][skillchoicename]['choose']['ignore']
						)
						for opt_dict in ALL_DATA['skills'][group_name]['choices'][skillchoicename]['choose']['options']:
							data_dict['options'].append(opt_dict)

		# we do this manually for the special case of options_skills above,
		# this is for all other cases without options_skills.
		# since we did this above for options skills, we elif here
		elif 'ignore' in data_dict:
			self.ignore_field_names = data_dict['ignore'].split('|')

		self.number_of_options = len(data_dict['options'])

		# load choice options
		for opt in data_dict['options']:
			self.names.append(opt['name'])
			self.costs.append(int(opt['cost']))
			self.descriptions.append(opt['description'])
			self.scripts.append(opt['script'])
			# at some point, in classes probably (e.g. fury->stormwight->kit)
			# we'll need to chain multiple followups here
			self.followup_choices.append(opt['followups'])

	def print_options(self, simstate=None):
		result = ''
		print_prompt_desc = self.prompt_desc
		print_prompt = self.prompt

		if self.has_description:
			print_prompt_desc = simstate.my_char.string_replace_with_otherdata(print_prompt_desc)
			print_prompt_desc = '\n'.join(wrap(print_prompt_desc, 74, subsequent_indent=''))
			print_prompt = '%s\n%s' % (print_prompt_desc, print_prompt)

		# used by final skill choice to read budget from num_skill_picks field
		if self.budgetfield != None:
			this_budget = getattr(simstate.my_char, self.budgetfield)
			if self.budgetfield_index != None:
				self.budget = this_budget[int(self.budgetfield_index)]
			print_prompt = print_prompt.format(self.budget)

		# field arsenal grammar correction
		if simstate != None and len(simstate.my_char.kits) > 1:
			print_prompt.replace('a kit', 'another kit')

		print_prompt = simstate.my_char.string_replace_with_otherdata(print_prompt)

		this_budget = int(self.budget)
		if this_budget == 1:
			print_prompt += '\nChoose from the following:'
		else:
			print_prompt += '\nChoose from the following. Your cost cannot exceed %d.' % this_budget
			print_prompt += '\nSeparate multiple choices with commas.'

		result += '%s\n\n' % print_prompt

		# if costs are actually important, be sure to print them
		show_costs = sum(self.costs) != len(self.costs)

		# collect ignore options
		for ignore_field in self.ignore_field_names:
			ignore_list = getattr(simstate.my_char, ignore_field)
			for option_name in ignore_list:
				self.ignore_options.append(option_name)

		# print each option's name, maybe the cost, description, and name of the choice in front
		for i in range(self.number_of_options):
			print_index = str(i+1)
			if self.names[i] in self.ignore_options:
				print_index = '-'
			if i > 0:
				result += '\n'
			option_line = ''
			option_line += '\t%s:\t' % print_index
			option_name = simstate.my_char.string_replace_with_otherdata(self.names[i])
			
			if show_costs:
				option_name += ' (cost %s)' % self.costs[i]
			if self.choice_name != '':
				# if choice has a description already, no need to repeat
				if self.has_description:
					option_name = '%s' % (option_name)
				else:
					option_name = '%s: %s' % (self.choice_name, option_name)
			option_line += option_name
			result += option_line

			if self.descriptions and self.descriptions[0] != '': # length is > 0
				desc_line = '\t\t\t'
				desc_line += '\n'.join(wrap(self.descriptions[i], 76, subsequent_indent='\t\t\t'))
				result += '\n%s' % desc_line

		return result

	# update simstate based on choice (read from input)
	# add followup choices
	def get_choice_from_input(self, inputline, simstate):

		force_budget = False
		updated_inputline = inputline
		if inputline.startswith('*'):
			force_budget = True
			updated_inputline = inputline[1:]

		split_choices = updated_inputline.split(',')

		# check if any choices are repeated
		if len(list(set(split_choices))) < len(split_choices):
			return 'You cannot choose the same option more than once.'

		# check for other bad input
		for choice in split_choices:
			if choice == '-':
				return '"-" is an option you already have. You cannot choose it again.'

			choice_index = -1
			try:
				choice_index = int(choice)-1
			except:
				return '"%s" is not a valid input.' % str(choice)

			# check that choice is within range
			if choice_index < 0 or choice_index >= self.number_of_options:
				return '"%s" is not a valid input.' % str(inputline)

			# check if choice is being ignored
			if self.names[choice_index] in self.ignore_options:
				result = 'You already have option %s: %s.' % (choice, self.names[choice_index])
				result += ' You cannot choose it again.'
				return result

		# calculate total cost and check against budget
		total_cost = 0
		for choice in split_choices:
			choice_index = int(choice)-1
			total_cost += self.costs[choice_index]

		intbudget = int(self.budget)
		if total_cost > intbudget:
			warning = 'Your budget is %d, your options amount to %d.' % (intbudget, total_cost)
			warning += ' Please stay within the budget.'
			return warning
		if total_cost < intbudget:
			if not force_budget:
				warning = 'Your budget is %d, your options amount to %d.' % (intbudget, total_cost)
				warning += '\nIf you are sure you want only these options,'
				warning += 'select them again with "*" at the start: *%s' % inputline
				return warning

		# read choices (or just the one, in most cases)
		for ci in range(len(split_choices)):
			choice = split_choices[ci]
			choice_index = int(choice)-1

			# add followup choices to simstate
			if self.followup_choices:
				simstate.followups.extend(self.followup_choices[choice_index])

			# read scripts of choice
			feature_script = self.scripts[choice_index]
			if feature_script != '':
				feature_script = simstate.my_char.string_replace_with_otherdata(feature_script)
				implement_script(simstate, feature_script, option_index=ci, implement_child=self.implement_child)

def implement_script(simstate, feature_script, option_index=-1, implement_child=False):
	split_scripts = feature_script.split('|')

	#print('implement:', feature_script, implement_child)

	chars_set = False # special case for class json user experience improvement

	for i in range(len(split_scripts)):
		func, keyword, value = split_scripts[i].split(',')

		otherdata = False
		if func.startswith('&'):
			otherdata = True
			func = func[1:]

		if func == '=':
			if ':' in value:
				value = [int(v) for v in value.split(':')]
			simstate.my_char.set_value(keyword, value, otherdata)

			# special case for adding CHAR1 and CHAR2 to otherdata via class
			# only doing this so the json of the class is easier to use for homebrewers
			if otherdata and keyword in ['CHAR1', 'CHAR2']:
				chars_set = True

		elif func == '*' or func == '*0':
			insert_at_start_of_list = (func == '*0')
			simstate.my_char.append_value(keyword, value, otherdata, insert_at_start_of_list=insert_at_start_of_list)

			# if adding a feature and the feature has a script, do that script too
			if (implement_child and value in ALL_FEATURES.keys()):
				child_script = ALL_FEATURES[value]['script']
				if child_script != '':
					child_script = simstate.my_char.string_replace_with_otherdata(child_script)
					implement_script(simstate, child_script)

		elif func == '+':
			result = value

			# check if adding tuples together, then check if subtracting with a minimum
			minval = None
			if ':' in result:
				splitresult = result.split(':')
				if splitresult[0] == 'optindex':
					assert(option_index >= 0, 'optindex script needs non-negative index')
					result = int(splitresult[option_index+1])
				else:
					result = [int(x) for x in splitresult]
			else:
				spval = result.split('m')
				if len(spval)>1:
					result = int(spval[0])
					minval = int(spval[1])
				else:
					result = int(result)

			if minval != None:
				simstate.my_char.add_value(keyword, spval[0], otherdata, minimum=int(spval[1]))
			else:
				simstate.my_char.add_value(keyword, result, otherdata)

		elif func == 'choose':
			# "choose,wyrmplate,Cold Immunity"
			# TODO: maybe allow doing "choose,<choice name>,value" also? Not just FEATURES?
			# 		...see how it looks in the final feature list and determine if we want that
			feature_choice = {
				'name' : ALL_FEATURES[value]['name'],
				'effect' : ALL_FEATURES[value]['effect']
			}
			simstate.my_char.add_feature_choice(keyword, feature_choice)
		elif func == 'kit_bonus':
			simstate.my_char.add_kit_bonus(keyword, value)
		elif func == 'kit_equipment':
			pass

	if chars_set:
		simstate.my_char.set_characteristic_names()