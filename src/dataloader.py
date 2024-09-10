import os					# for looping through json files
import json					# for reading json data

from src.choiceselector import *

def load_data_and_setup_choices(verbose=True):
	global ALL_DATA
	global ALL_CHOICES

	if verbose: print('Loading data...')

	###### LOAD DATA & FEATURES ##########################
	# load ancestries direct into json, no manipulation
	if verbose: print(' Data/ancestries')
	ALL_DATA['ancestries'] = {}
	directory = os.fsencode('./Data/ancestries')
	for file in os.listdir(directory):
		filename = os.fsdecode(file)
		if filename.endswith('.json'):
			filename_no_ext = filename[:-5]
			with open('./Data/ancestries/%s' % filename) as f:
				if verbose: print('   %s' % filename)
				ALL_DATA['ancestries'][filename_no_ext] = json.load(f)
				ALL_FEATURES.update(ALL_DATA['ancestries'][filename_no_ext]['features'])

	# load cultures
	if verbose: print(' Data/build-a-culture')
	ALL_DATA['culture'] = {}
	directory = os.fsencode('./Data/build-a-culture')
	for file in os.listdir(directory):
		filename = os.fsdecode(file)
		if filename.endswith('.json'):
			filename_no_ext = filename[:-5]
			with open('./Data/build-a-culture/%s' % filename) as f:
				if verbose: print('   %s' % filename)
				ALL_DATA['culture'][filename_no_ext] = json.load(f)
				# no features in culture, just scripts (skills)

	# load careers	
	if verbose: print(' Data/careers')
	ALL_DATA['careers'] = {}
	directory = os.fsencode('./Data/careers')
	for file in os.listdir(directory):
		filename = os.fsdecode(file)
		if filename.endswith('.json'):
			filename_no_ext = filename[:-5]
			with open('./Data/careers/%s' % filename) as f:
				if verbose: print('   %s' % filename)
				ALL_DATA['careers'][filename_no_ext] = json.load(f)
				ALL_FEATURES.update(ALL_DATA['careers'][filename_no_ext]['features'])

	# load complications
	if verbose: print(' Data/complications')
	ALL_DATA['complications'] = {}
	directory = os.fsencode('./Data/complications')
	for file in os.listdir(directory):
		filename = os.fsdecode(file)
		if filename.endswith('.json'):
			filename_no_ext = filename[:-5]
			with open('./Data/complications/%s' % filename) as f:
				if verbose: print('   %s' % filename)
				if filename_no_ext == 'no complication':
					ALL_DATA['no complication'] = json.load(f)
				else:
					ALL_DATA['complications'][filename_no_ext] = json.load(f)
					ALL_FEATURES.update(ALL_DATA['complications'][filename_no_ext]['features'])

	# load classes
	if verbose: print(' Data/classes')
	ALL_DATA['classes'] = {}
	ALL_DATA['subclasses'] = {}
	directory = os.fsencode('./Data/classes')
	for folder in os.listdir(directory):
		class_name = os.fsdecode(folder)
		if verbose: print('   %s' % class_name)
		with open('./Data/classes/%s/class.json' % class_name) as f:
			ALL_DATA['classes'][class_name] = json.load(f)
			ALL_FEATURES.update(ALL_DATA['classes'][class_name]['features'])

		# load subclasses
		ALL_DATA['subclasses'][class_name] = {}
		subclass_dir_path = './Data/classes/%s/subclasses' % class_name
		subclass_dir = os.fsencode(subclass_dir_path)
		for file in os.listdir(subclass_dir):
			filename = os.fsdecode(file)
			if filename.endswith('.json'):
				filename_no_ext = filename[:-5]
				with open('%s/%s' % (subclass_dir_path, filename)) as f:
					if verbose: print('       %s' % filename)
					ALL_DATA['subclasses'][class_name][filename_no_ext] = json.load(f)
					ALL_FEATURES.update(ALL_DATA['subclasses'][class_name][filename_no_ext]['features'])

	# load characteristic choices
	if verbose: print(' Data/allocate-stats')
	ALL_DATA['characteristics'] = {}
	with open('./Data/allocate-stats/stats.json') as f:
		ALL_DATA['characteristics'] = json.load(f)
		# no features in characteristics, just scripts and followups

	# load kits
	if verbose: print(' Data/kits')
	ALL_DATA['kits'] = {}
	ALL_DATA['allkits'] = {}
	directory = os.fsencode('./Data/kits')
	for folder in os.listdir(directory):
		kit_type = os.fsdecode(folder)
		if verbose: print('   %s' % kit_type)
		ALL_DATA['kits'][kit_type] = {}
		kit_dir_path = './Data/kits/%s' % kit_type
		kit_type_dir = os.fsencode(kit_dir_path)
		for file in os.listdir(kit_type_dir):
			filename = os.fsdecode(file)
			if filename.endswith('.json'):
				filename_no_ext = filename[:-5]
				with open('%s/%s' % (kit_dir_path, filename)) as f:
					if verbose: print('       %s' % filename)
					ALL_DATA['kits'][kit_type][filename_no_ext] = json.load(f)
					ALL_DATA['allkits'][filename_no_ext] = ALL_DATA['kits'][kit_type][filename_no_ext]
					ALL_DATA['allkits'][filename_no_ext]['kit_type'] = kit_type
					ALL_FEATURES.update(ALL_DATA['kits'][kit_type][filename_no_ext]['features'])

	# load skills
	if verbose: print(' Data/skills')
	ALL_DATA['skills'] = {}
	ALL_DATA['skills']['allskills'] = {}
	directory = os.fsencode('./Data/skills')
	for file in os.listdir(directory):
		filename = os.fsdecode(file)
		if filename.endswith('.json'):
			filename_no_ext = filename[:-5]
			with open('./Data/skills/%s' % filename) as f:
				if verbose: print('   %s' % filename)
				ALL_DATA['skills'][filename_no_ext] = json.load(f)
			group_name = ALL_DATA['skills'][filename_no_ext]['name']
			for skill_dict in ALL_DATA['skills'][filename_no_ext]['choices'][group_name]['choose']['options']:
				ALL_DATA['skills']['allskills'][skill_dict['name']] = skill_dict.copy()

	# load languages
	if verbose: print(' Data/language')
	ALL_DATA['language'] = {}
	directory = os.fsencode('./Data/language')
	#assert len(os.listdir(directory)) != 1, 'only one language json file allowed in top level of Data/language folder. %d found.' % len(os.listdir(directory))
	if len(os.listdir(directory)) > 1:
		print('More than one language file found in top level of Data/language folder. Only using the first one.')
	for file in os.listdir(directory):
		filename = os.fsdecode(file)
		if filename.endswith('.json'):
			filename_no_ext = filename[:-5]
			with open('./Data/language/%s' % filename) as f:
				if verbose: print('   %s' % filename)
				ALL_DATA['language'] = json.load(f)
				# no features in culture, just scripts (skills)
			break

	######## LOAD GENERAL FEATURES ###################
	# load all general features direct into json, no manipulation
	if verbose: print(' Data/general_features')
	directory = os.fsencode('./Data/general_features')
	for file in os.listdir(directory):
		filename = os.fsdecode(file)
		if filename.endswith('.json'):
			with open('./Data/general_features/%s' % filename) as f:
				if verbose: print('   %s' % filename)
				ALL_FEATURES.update(json.load(f))

	######### SETUP CHOICES ###########################
	# setup ancestry choice
	ALL_CHOICES['ancestry'] = ChoiceSelector()
	ALL_CHOICES['ancestry'].choice_name = 'Ancestry'
	ALL_CHOICES['ancestry'].prompt = 'Choose an ancestry for your character.\n'
	ALL_CHOICES['ancestry'].budget = '1'
	ALL_CHOICES['ancestry'].number_of_options = len(ALL_DATA['ancestries'])
	ALL_CHOICES['ancestry'].costs = [1] * len(ALL_DATA['ancestries'])
	ALL_CHOICES['ancestry'].names = [
		ALL_DATA['ancestries'][val]['name'] for val in ALL_DATA['ancestries']
	]
	ALL_CHOICES['ancestry'].scripts = [
		ALL_DATA['ancestries'][val]['script'] for val in ALL_DATA['ancestries']
	]
	ALL_CHOICES['ancestry'].has_description = True

	# setup career choice
	ALL_CHOICES['career'] = ChoiceSelector()
	ALL_CHOICES['career'].choice_name = 'Career'
	ALL_CHOICES['career'].prompt = 'Before your character was an adventurer, they had a career.\n'
	ALL_CHOICES['career'].budget = '1'
	ALL_CHOICES['career'].number_of_options = len(ALL_DATA['careers'])
	ALL_CHOICES['career'].costs = [1] * len(ALL_DATA['careers'])
	ALL_CHOICES['career'].names = [
		ALL_DATA['careers'][val]['name'] for val in ALL_DATA['careers']
	]
	ALL_CHOICES['career'].scripts = [
		ALL_DATA['careers'][val]['script'] for val in ALL_DATA['careers']
	]
	ALL_CHOICES['career'].has_description = True

	# setup complication choice
	ALL_CHOICES['complication'] = ChoiceSelector()
	ALL_CHOICES['complication'].choice_name = 'Complication'
	ALL_CHOICES['complication'].prompt = 'Your character might have had a complicating factor foisted upon them.\n'
	ALL_CHOICES['complication'].budget = '1'
	ALL_CHOICES['complication'].number_of_options = len(ALL_DATA['complications'])+1
	ALL_CHOICES['complication'].costs = [1] * (len(ALL_DATA['complications'])+1)
	ALL_CHOICES['complication'].names = [
		ALL_DATA['complications'][val]['name'] for val in ALL_DATA['complications']
	]
	ALL_CHOICES['complication'].names.insert(0, ALL_DATA['no complication']['name'])
	ALL_CHOICES['complication'].descriptions = [
		ALL_DATA['complications'][val]['description'] for val in ALL_DATA['complications']
	]
	ALL_CHOICES['complication'].descriptions.insert(0, ALL_DATA['no complication']['description'])
	ALL_CHOICES['complication'].scripts = [
		ALL_DATA['complications'][val]['script'] for val in ALL_DATA['complications']
	]
	ALL_CHOICES['complication'].scripts.insert(0, '')
	#ALL_CHOICES['complication'].has_description = True

	# setup class choice
	ALL_CHOICES['class'] = ChoiceSelector()
	ALL_CHOICES['class'].choice_name = 'Class'
	ALL_CHOICES['class'].prompt = 'Choose a class for your character.\n'
	ALL_CHOICES['class'].budget = '1'
	ALL_CHOICES['class'].number_of_options = len(ALL_DATA['classes'])
	ALL_CHOICES['class'].costs = [1] * len(ALL_DATA['classes'])
	ALL_CHOICES['class'].names = [
		ALL_DATA['classes'][val]['name'] for val in ALL_DATA['classes']
	]
	ALL_CHOICES['class'].scripts = [
		ALL_DATA['classes'][val]['script'] for val in ALL_DATA['classes']
	]
	ALL_CHOICES['class'].has_description = True

	# setup subclass choice
	for class_name in ALL_DATA['classes']:
		choice_name = 'subclass-%s' % class_name
		ALL_CHOICES[choice_name] = ChoiceSelector()
		ALL_CHOICES[choice_name].choice_name = ALL_DATA['classes'][class_name]['subclass_name']
		ALL_CHOICES[choice_name].budget = ALL_DATA['classes'][class_name]['subclass_budget']
		ALL_CHOICES[choice_name].prompt = '%s\n' % ALL_DATA['classes'][class_name]['subclass_prompt']
		ALL_CHOICES[choice_name].number_of_options = len(ALL_DATA['subclasses'][class_name])
		ALL_CHOICES[choice_name].costs = [1] * len(ALL_DATA['subclasses'][class_name])
		ALL_CHOICES[choice_name].names = [
			ALL_DATA['subclasses'][class_name][val]['name'] for val in ALL_DATA['subclasses'][class_name]
		]
		ALL_CHOICES[choice_name].scripts = [
			ALL_DATA['subclasses'][class_name][val]['script'] for val in ALL_DATA['subclasses'][class_name]
		]
		ALL_CHOICES[choice_name].has_description = True

	# setup kits choice later, when we know which kits we can pick from

	# setup skill choices first, so later choices can reference them with "options_skills"
	for key in ALL_DATA['skills']:
		if key == 'allskills':
			continue
		choices_dict = ALL_DATA['skills'][key]['choices']
		for choice_name in choices_dict:
			choice_data = choices_dict[choice_name]
			ALL_CHOICES[choice_name] = ChoiceSelector(choice_name, choice_data['choose'])
			ALL_CHOICES[choice_name].set_description(choice_data['description'])

	# setup features choices in ancestries
	index_counter = 0
	for key in ALL_DATA['ancestries']:
		ALL_CHOICES['ancestry'].followup_choices.append([])
		choices_dict = ALL_DATA['ancestries'][key]['choices']
		for choice_name in choices_dict:
			choice_data = choices_dict[choice_name]
			choice_key = '%s_%s' % (key, choice_name)
			ALL_CHOICES[choice_key] = ChoiceSelector(choice_name, choice_data['choose'])
			ALL_CHOICES['ancestry'].followup_choices[index_counter].append(choice_key)
		index_counter += 1

	# setup feature choices in classes
	for key in ALL_DATA['classes']:
		choices_dict = ALL_DATA['classes'][key]['choices']
		for choice_name in choices_dict:
			choice_data = choices_dict[choice_name]
			choice_key = '%s_%s' % (key, choice_name)
			#print(choice_name, choice_data.keys())
			if 'choose_dynamic' in choice_data.keys() and choice_data['choose_dynamic'] != '':
				choice_data['choose_dynamic'] = '{%s}' % choice_data['choose_dynamic']
				# setup these choices later
				ALL_CHOICES[choice_key] = 'dynamic'
			elif choice_data['choose']:
				ALL_CHOICES[choice_key] = ChoiceSelector(choice_name, choice_data['choose'])

	# setup characteristic allocate choices
	for choice_name in ALL_DATA['characteristics']['choices']:
		choice_data = ALL_DATA['characteristics']['choices'][choice_name]
		ALL_CHOICES[choice_name] = ChoiceSelector(choice_name, choice_data['choose'])
		ALL_CHOICES[choice_name].set_description(choice_data['description'])

	# setup culture choices
	for key in ALL_DATA['culture']:
		choices_dict = ALL_DATA['culture'][key]['choices']
		for choice_name in choices_dict:
			choice_data = choices_dict[choice_name]
			ALL_CHOICES[choice_name] = ChoiceSelector(choice_name, choice_data['choose'])
			ALL_CHOICES[choice_name].set_description(choice_data['description'])

	# setup language choice later

	if verbose: 
		print('Done.')
		print()