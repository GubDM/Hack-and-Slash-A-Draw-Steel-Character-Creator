from enum import IntEnum	# for state tracking and array indexing
from time import strftime 	# for character file name
from textwrap import wrap 	# for printing descriptions

from src.character import CharacterData
from src.choiceselector import *
from src.dataloader import *

class ProcessStep(IntEnum):
	TITLECARD 		= 00
	NAME			= 10
	ANCESTRY		= 20
	CULTURE			= 30
	CAREER			= 40
	COMPLICATION	= 45 # it's my software and I can put the complications choice where I want it
	CLASS 			= 50 # choose your character class
	CLASS_STATS		= 51 # assign characteristics array
	CLASS_SUB		= 52 # choose subclass and followups
	CLASS_FEATS		= 53 # choose signature and heroic class features
	KITS			= 60
	KIT_BONUSES		= 61 # except in the case of field arsenal, this step is automatic and the UI skips to Skills
	SKILLS			= 80
	LANGUAGES		= 90
	ANTICIPATION	= 99
	SUMMARY			= 100
	QUIT			= 110

def get_printmessage(print_process_step, simstate):
	message = ''
	prompt = ''

	if print_process_step == ProcessStep.TITLECARD:
		message = '%s\n\nEnter Q to quit at any time.' % print_titlecard()
		prompt = 'Enter to continue.'

	elif print_process_step == ProcessStep.NAME:
		prompt = 'Who are you?'

	elif print_process_step >= ProcessStep.ANCESTRY and print_process_step <= ProcessStep.LANGUAGES:
		message = ALL_CHOICES[simstate.currchoice].print_options(simstate)

	elif print_process_step == ProcessStep.ANTICIPATION:
		prompt = '%s, your hour of destiny has come.\nFor the sake of us all:\n\n' % simstate.my_char.name
		prompt += 'Go bravely and DRAW STEEL!\n\n'
		prompt += 'Enter to continue to character sheet.'

	elif print_process_step == ProcessStep.SUMMARY:
		simstate.filename = simstate.my_char.name+simstate.filename
		message = ('Character data exported to Characters/%s' % simstate.filename)

	return (message, prompt)

def setup_step(simstate, next_process_step):
	if next_process_step == ProcessStep.NAME:
		# no choice, just text entry
		pass
	elif next_process_step == ProcessStep.ANCESTRY:
		# initial choice and followups set in dataloader
		pass
	elif next_process_step == ProcessStep.CULTURE:
		simstate.currchoice = 'Environment'
		simstate.followups = ['Organization', 'Upbringing']
	elif next_process_step == ProcessStep.CAREER:
		simstate.currchoice = 'career'
	elif next_process_step == ProcessStep.COMPLICATION:
		simstate.currchoice = 'complication'
	elif next_process_step == ProcessStep.CLASS:
		simstate.currchoice = 'class'
	elif next_process_step == ProcessStep.CLASS_STATS:
		simstate.currchoice = 'Characteristic Array'
	elif next_process_step == ProcessStep.CLASS_SUB:
		simstate.currchoice = 'subclass-%s' % simstate.my_char.char_class
	elif next_process_step == ProcessStep.CLASS_FEATS:
		class_name = simstate.my_char.char_class
		choices_dict = ALL_DATA['classes'][class_name]
		for choice_name in choices_dict['choices']:
			# read dynamic choices and add to ALL_CHOICES
			choice_data = choices_dict['choices'][choice_name]
			choice_key = '%s_%s' % (class_name, choice_name)
			if ALL_CHOICES[choice_key] == 'dynamic':
				dynamic_choice_data = {}
				dynamic_choice_data['description'] = choice_data['description']
				dynamic_choice_data['choose'] = {}
				if isinstance(choice_data['choose']['budget'], str):
					dynamic_choice_data['choose']['budget'] = simstate.my_char.string_replace_with_otherdata(
						choice_data['choose']['budget']
					)
				else:
					dynamic_choice_data['choose']['budget'] = choice_data['choose']['budget']
				dynamic_choice_data['choose']['options'] = []
				for opt in simstate.my_char.otherdata_dict[choice_data['choose_dynamic']]:
					dynamic_choice_data['choose']['options'].append(ALL_FEATURES[opt]['option'])
				ALL_CHOICES[choice_key] = ChoiceSelector(choice_name, dynamic_choice_data['choose'])
				if dynamic_choice_data['description'] != '':
					ALL_CHOICES[choice_key].set_description(dynamic_choice_data['description'])
			else:
				ALL_CHOICES[choice_key].set_description(choice_data['description'])
			# add all choices to followup
			simstate.followups.append(choice_key)
		# go to the first choice in list
		simstate.currchoice = simstate.followups.pop(0)
	elif next_process_step == ProcessStep.KITS:
		# setup first kit choice
		kit_choice = ChoiceSelector()
		kit_choice.choice_name = 'Kits'
		kit_choice.prompt = 'Choose a kit for your character.'
		kit_choice.budget = '1'

		these_kits_data = {}
		for kit_type in simstate.my_char.first_kit_options:
			these_kits_data.update(ALL_DATA['kits'][kit_type])

		kit_choice.number_of_options = len(these_kits_data)
		kit_choice.costs = [1] * len(ALL_DATA['allkits'])
		kit_choice.names = [
			these_kits_data[val]['name'] for val in these_kits_data
		]
		kit_choice.scripts = [
			these_kits_data[val]['script'] for val in these_kits_data
		]
		kit_choice.has_description = True
		
		ALL_CHOICES['first-kit'] = kit_choice
		simstate.currchoice = 'first-kit'

		if simstate.my_char.second_kit_options:
			kit_choice = ChoiceSelector()
			kit_choice.choice_name = 'Kits'
			kit_choice.prompt = 'Choose a second kit for your character.'
			kit_choice.budget = '1'

			these_kits_data = {}
			for kit_type in simstate.my_char.second_kit_options:
				these_kits_data.update(ALL_DATA['kits'][kit_type])

			kit_choice.number_of_options = len(these_kits_data)
			kit_choice.costs = [1] * len(ALL_DATA['allkits'])
			kit_choice.names = [
				these_kits_data[val]['name'] for val in these_kits_data
			]
			kit_choice.scripts = [
				these_kits_data[val]['script'] for val in these_kits_data
			]
			kit_choice.has_description = True
			kit_choice.ignore_field_names = ['kits']

			ALL_CHOICES['second-kit'] = kit_choice
			simstate.followups.append('second-kit')
	elif next_process_step == ProcessStep.KIT_BONUSES:
		simstate.followups = []
		# for each kit bonus, it there's a choice, add it to followups,
		# otherwise, just implement the script of the choice
		for bonus_key in simstate.my_char.kit_bonuses:
			bonus_feats = list(simstate.my_char.kit_bonuses[bonus_key])
			num_bonus_feats = len(bonus_feats)
			if num_bonus_feats > 1:
				bonus_choice = ChoiceSelector()
				bonus_choice.choice_name = 'Kit Bonus'
				bonus_choice.prompt = 'Choose which bonus from your kits to apply.'
				bonus_choice.budget = '1'
				bonus_choice.number_of_options = num_bonus_feats
				bonus_choice.costs = [1] * num_bonus_feats
				bonus_choice.names = [ALL_FEATURES[feat]['name'] for feat in bonus_feats]
				bonus_choice.scripts = [ALL_FEATURES[feat]['script'] for feat in bonus_feats]
				bonus_choice.descriptions = [ALL_FEATURES[feat]['effect'] for feat in bonus_feats]
				bonus_choice.has_description = True
				bonus_choice.implement_child = False

				ALL_CHOICES['kit_bonus-%s' % bonus_key] = bonus_choice
				simstate.followups.append('kit_bonus-%s' % bonus_key)
			else:
				# uncontested bonus of this type, just implement it
				implement_script(simstate, ALL_FEATURES[bonus_feats[0]]['script'])
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
			return ProcessStep.KIT_BONUSES
		else:
			# skip to skills (TODO: actually point this to Complication)
			setup_step(simstate, ProcessStep.SKILLS)
			return ProcessStep.SKILLS

	elif next_process_step == ProcessStep.SKILLS:
		# skip chosing from skills that have no budget
		skill_list = ['Crafting', 'Exploration', 'Interpersonal', 'Intrigue', 'Lore']
		for i in range(5):
			if simstate.my_char.num_skill_picks[i] > 0:
				simstate.followups.append('%s Skills' % skill_list[i])
		simstate.currchoice = simstate.followups.pop(0)

	elif next_process_step == ProcessStep.LANGUAGES:
		lang_choice = ChoiceSelector()
		lang_choice.choice_name = 'Language'

		num_langs = simstate.my_char.num_languages
		if num_langs > 1:
			lang_choice.prompt = 'Your character is fluent in %d languages.' % num_langs
			lang_choice.budget = str(num_langs)
		else:
			# always get one language, even if your number of languages is 0 or less somehow
			lang_choice.prompt = 'Your character is fluent in a single language.'
			lang_choice.budget = '1'
		lang_data = ALL_DATA['language']['choices']['Languages']['choose']['options']
		lang_choice.number_of_options = len(lang_data)
		lang_choice.costs = [1] * len(lang_data)
		lang_choice.names = [lang_dict['name'] for lang_dict in lang_data]
		lang_choice.scripts = [lang_dict['script'] for lang_dict in lang_data]
		lang_choice.descriptions = [lang_dict['description'] for lang_dict in lang_data]
		lang_choice.has_description = True

		ALL_CHOICES['language'] = lang_choice
		simstate.currchoice = 'language'

def handle_input(input_line, simstate):
	next_process_step = simstate.process_step

	# evaluate input to chardata, put any followup choices in simstate
	input_error = None
	if simstate.process_step == ProcessStep.NAME:
		simstate.my_char.name = input_line.strip()
	elif simstate.process_step >= ProcessStep.ANCESTRY and simstate.process_step <= ProcessStep.LANGUAGES:
		input_error = ALL_CHOICES[simstate.currchoice].get_choice_from_input(input_line, simstate)

	# one of the inputted numbers was out of range
	if input_error:
		return input_error, ''

	# find and setup next step (and next choice, if applicable)
	if simstate.process_step == ProcessStep.TITLECARD:
		next_process_step = ProcessStep.NAME
	# character name
	elif simstate.process_step == ProcessStep.NAME:
		next_process_step = ProcessStep.ANCESTRY
		simstate.currchoice = 'ancestry'
	# ancestry
	elif simstate.process_step == ProcessStep.ANCESTRY:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.CULTURE
			setup_step(simstate, next_process_step)

	# culture
	elif simstate.process_step == ProcessStep.CULTURE:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.CAREER
			setup_step(simstate, next_process_step)
	# career
	elif simstate.process_step == ProcessStep.CAREER:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.COMPLICATION
			setup_step(simstate, next_process_step)
	# complication
	elif simstate.process_step == ProcessStep.COMPLICATION:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.CLASS
			setup_step(simstate, next_process_step)

	# initial class decision
	elif simstate.process_step == ProcessStep.CLASS:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.CLASS_STATS
			setup_step(simstate, next_process_step)

	# class-informed characteristics array allocation
	elif simstate.process_step == ProcessStep.CLASS_STATS:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
			if simstate.my_char.charcs_chosen == 'True':
				simstate.my_char.set_characteristics()
		else:
			next_process_step = ProcessStep.CLASS_SUB
			setup_step(simstate, next_process_step)

	# subclass or otherwise first class decision
	elif simstate.process_step == ProcessStep.CLASS_SUB:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.CLASS_FEATS
			setup_step(simstate, next_process_step)

	# all other class feature/ability choices
	elif simstate.process_step == ProcessStep.CLASS_FEATS:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.KITS
			setup_step(simstate, next_process_step)

	# kits
	elif simstate.process_step == ProcessStep.KITS:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.KIT_BONUSES
			# potentially no choices in kit bonuses, just implementation, straight to skills
			next_process_step = setup_step(simstate, next_process_step)
	# kit bonuses
	elif simstate.process_step == ProcessStep.KIT_BONUSES:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.SKILLS
			setup_step(simstate, next_process_step)
	# skills
	elif simstate.process_step == ProcessStep.SKILLS:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.LANGUAGES
			setup_step(simstate, next_process_step)

	# languages
	elif simstate.process_step == ProcessStep.LANGUAGES:
		if simstate.followups:
			simstate.currchoice = simstate.followups.pop(0)
		else:
			next_process_step = ProcessStep.ANTICIPATION
			setup_step(simstate, next_process_step)

	# anticipation
	elif simstate.process_step == ProcessStep.ANTICIPATION:
		next_process_step = ProcessStep.SUMMARY
	# summary
	elif simstate.process_step == ProcessStep.SUMMARY:
		next_process_step = ProcessStep.QUIT

	# get print message, print character summary at the end
	print_message, print_prompt = get_printmessage(next_process_step, simstate)
	if next_process_step == ProcessStep.SUMMARY:
		simstate.filecontent = simstate.my_char.summarize()
		simstate.export_to_file()
		print_message = "%s\n%s" % (simstate.filecontent, print_message)
		print_prompt = 'Enter to quit.'

	# update step, return messages
	simstate.process_step = next_process_step
	return print_message, print_prompt

class SimState():
	def __init__(self):
		self.my_char = CharacterData()
		self.process_step = ProcessStep.TITLECARD
		self.followups = [] # choices that follow other choices, e.g. class->subclass->...
		self.currchoice = None # keyword into ALL_CHOICES
		self.filename = strftime('%Y%M%d-%H%M%S')
		self.filecontent = ''

	def export_to_file(self):
		print_content = self.my_char.summarize()
		with open('./Characters/%s.txt' % self.filename, 'w') as f:
			f.write(print_content)

def print_titlecard():
	result = ''
	with open('./src/titlecard.txt') as f:
		for line in f:
			result += '%s' % line

	return result

def main():
	load_data_and_setup_choices()

	#from pprint import pprint
	#pprint(ALL_DATA['ancestries']['human']['features'])

	simstate = SimState()
	message, prompt = get_printmessage(simstate.process_step, simstate)
	input_line = ''

	# repl
	while True:
		print(message)
		print(prompt)
		input_line = input('>> ')

		# check for early quit
		if input_line in ['q', 'Q']:
			quit()

		# check for malformed input
		split_input = input_line.split(',')
		bad_input = False
		if split_input:
			for val in split_input:
				if (simstate.process_step == ProcessStep.NAME and val==''):
					bad_input = True
					break
			if bad_input:
				continue

		# evaluate input
		message, prompt = handle_input(input_line, simstate)

		# end of process, quit out
		if simstate.process_step == ProcessStep.QUIT:
			quit()
		else:
			print()

if __name__=='__main__':
	main()