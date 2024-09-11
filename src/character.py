from textwrap import wrap 	# for printing descriptions
from src.dataloader import *


CHARC_INDEX = {
	'Might' : 0,
	'Agility' : 1,
	'Reason' : 2,
	'Intuition' : 3,
	'Presence' : 4
}

INDEX_CHARC 	= ['Might', 	'Agility', 	'Reason', 	'Intuition', 	'Presence']
INDEX_CHARAB 	= ['MGT',		'AGL',		'REA',		'INU',			'PRS']

SKILL_INDEX = {
	'crafting' : 0,
	'exploration' : 1,
	'interpersonal' : 2,
	'intrigue' : 3,
	'lore' : 4
}

class Vec:
	def __init__(self, vals):
		self.values = vals[:]
		self.length = len(self.values)

	def __add__(self, newval):
		assert(len(newval) == self.length)
		result = self.values[:]
		for i in range(self.length):
			result[i] += newval[i]
		return result

	def __str__(self):
		return str(self.values)

	def __len__(self):
		return self.length

	def __getitem__(self, idx):
		return self.values[idx]

	def __setitem__(self, idx, value):
		self.values[idx] = value
		return value

	def to_list(self):
		return self.values[:]

class CharacterData:
	def __init__(self):
		self.name = 'Nemo'
		self.ancestry = 'Thing'
		self.environment = ''
		self.organization = ''
		self.upbringing = ''
		self.career = ''
		self.complication = ''

		self.char_class = 'Ne\'er-do-well'
		self.char_subclass = []
		self.hr_feature = None

		# characteristics		  CHAR1, CHAR2, CHAR3, ...
		self.charposition 		= Vec([0, 0, 0, 0, 0]) # each value = CHARC_INDEX[CHAR<index>]
		self.charvalue 			= Vec([2, 2, 0, 0, 0])
		self.characteristics 	= Vec([0, 0, 0, 0, 0])
		self.charcs_chosen 		= 'False'

		'''
		# used to set and manipulate data inside json for printing later
		# keys are always surrounded by curly brackets, e.g. {CHAR1} or {FIRE_DISCOUNT}
		'''
		self.otherdata_dict = {}

		# stats
		self.stamina = 0
		self.winded = 0
		self.recoveries = 0
		self.recover_value_bonus = 0

		self.size = '1M'
		self.speed = 5
		self.stability = 0

		self.reach_bonus = 0
		self.weapon_distance = 0
		self.magic_distance = 0
		self.psionic_distance = 0

		self.magic_area = 0
		self.psionic_area = 0
		self.weapon_area = 0

		# damage bonuses
		self.melee_bonus = Vec([0, 0, 0])
		self.ranged_bonus = Vec([0, 0, 0])
		self.magic_bonus = Vec([0, 0, 0])
		self.psionic_bonus = Vec([0, 0, 0])

		self.renown = 0
		self.projectpoints = 0

		self.num_languages = 2 # common is free and you always get one from culture
		self.languages = []

		# compilations of stuff
		self.num_skill_picks = Vec([0, 0, 0, 0, 0]) # crft, expl, intp, intg, lore
		self.crafting_skills = []
		self.exploration_skills = []
		self.interpersonal_skills = []
		self.intrigue_skills = []
		self.lore_skills = []
		
		self.immunities = []
		self.weaknesses = []

		# kit stuff (mostly for tactician's field arsenal)
		self.first_kit_options = ['Martial', 'Caster', 'Psionic'] # stormwight appends(*) 'Stormwight' to this
		self.second_kit_options = [] # with field arsenal, this will just contain 'Martial'
		self.kits = []
		self.kit_bonuses = {}
		self.kit_equipment = []
		self.kit_wear = []
		self.kit_wield = []

		# feature ids
		self.hr_name = ''
		self.hr_feature = None # only set by class selection
		self.free_strikes = ['melee_weapon_free_strike', 'ranged_weapon_free_strike']
		self.triggers = ['opportunity_attacks']
		self.maneuvers = [] # does not include heroic ability maneuvers
		self.signatures = []
		self.heroic3maneuvers = []
		self.heroic3actions = []
		self.heroic5maneuvers = []
		self.heroic5actions = []
		self.actions = [] # does not include heroic actions or signature attacks
		self.misc_features = []
		self.feature_choices = {}

		self.gen_maneuvers = ['aid_attack', 'drink_potion', 'escape_grab', 'grab', 'hide', 'knockback', 'make_assist_test', 'search_for_hidden_creatures', 'stand_up']
		self.gen_actions = ['catch_breath', 'charge', 'defend', 'heal']

	# script <=,keyword,value>
	def set_value(self, keyword, value, otherdata):
		result = value
		if ':' in value:
			result = Vec(value.split(':'))

		if value == '[]': # for Null setting first_kit_options to empty
			result = []
		
		if otherdata:
			bracket_kw = '{%s}' % keyword
			self.otherdata_dict[bracket_kw] = value
		else:
			setattr(self, keyword, result)

	# script <*,keyword,value>
	def append_value(self, keyword, value, otherdata, insert_at_start_of_list):
		if otherdata:
			keyword = '{%s}' % keyword
			if not keyword in self.otherdata_dict:
				self.otherdata_dict[keyword] = []
			if insert_at_start_of_list:
				self.otherdata_dict[keyword].insert(0, value)
			else:
				self.otherdata_dict[keyword].append(value)
		else:
			if insert_at_start_of_list:
				getattr(self, keyword).insert(0, value)
			else:
				getattr(self, keyword).append(value)

	# script <+,keyword,value> or <+,keyword,value m minimum>, for when value is negative
	#                                              ^ delineator is "m"
	def add_value(self, keyword, value, otherdata, minimum=None):
		result = None

		index = None
		if '@' in keyword:
			keyword, index = keyword.split('@')
			index = int(index)

		# check if keyword is a key into otherdata (uses curly brackets)
		if otherdata:
			result = self.otherdata_dict[keyword]
		else:
			result = getattr(self, keyword)

		if index:
			valuevec = [0] * len(result)
			valuevec[index] = value
			value = Vec(valuevec)
		
		# if value is an integer, add ints, otherwise add Vecs
		if isinstance(value, int):
			result = int(result) + value
			# clip to minimum if there is one
			if minimum != None:
				result = max(minimum, result)
		else:
			value[0] # test that value is subscriptable
			result = Vec(result) + value

		if otherdata:
			self.otherdata_dict[keyword] = value
		else:
			setattr(self, keyword, result)
			

	def add_kit_bonus(self, bonus_keyword, feature_id):
		if not bonus_keyword in self.kit_bonuses.keys():
			self.kit_bonuses[bonus_keyword] = []
		self.kit_bonuses[bonus_keyword].append(feature_id)

	def add_feature_choice(self, feature, choice):
		self.feature_choices[feature] = choice

	def string_replace_with_otherdata(self, str_value):
		result = str_value
		for key in self.otherdata_dict:
			result = result.replace(key, str(self.otherdata_dict[key]))
		return result

	def set_characteristic_names(self):
		assert not 'CHAR1' in self.otherdata_dict.keys(), 'assigned CHAR2 but not CHAR1 in class json'
		assert not 'CHAR2' in self.otherdata_dict.keys(), 'assigned CHAR1 but not CHAR2 in class json'

		major_idxs = [CHARC_INDEX[self.otherdata_dict['{CHAR1}']], CHARC_INDEX[self.otherdata_dict['{CHAR2}']]]
		charnum = 3
		for i in range(5):
			if not i in major_idxs:
				self.otherdata_dict['{CHAR%d}'%charnum] = INDEX_CHARC[i]
				self.otherdata_dict['{CHARAB%d}'%charnum] = INDEX_CHARAB[i]
				charnum += 1

		for i in range(5):
			self.charposition[i] = CHARC_INDEX[self.otherdata_dict['{CHAR%d}' % (i+1)]]

	def set_characteristics(self):
		'''							CHAR1, CHAR2, ...
		self.charposition 		= Vec([0, 0, 0, 0, 0]) # each value = CHARC_INDEX[CHAR<index>]
		self.charvalue 			= Vec([2, 2, 0, 0, 0])
		'''
		#print(self.charposition)
		#print(self.charvalue)
		#print()
		# NOTE: this took forever to debug for some reason, 
		# and I ultimately don't know how I got it to work
		# it just did, at some point.
		charcs = [None]*5

		for i in range(5):
			#print(self.charposition[i], int(self.charvalue[i]))
			charcs[int(self.charposition[i])] = int(self.charvalue[i])

		for i in range(5):
			dict_index = '{%sVAL}' % INDEX_CHARAB[i]
			self.otherdata_dict[dict_index] = charcs[i]

		self.characteristics = Vec(charcs)

		#print()
		#print(charcs)

	def get_all_skills(self):
		result = []
		result.extend(self.crafting_skills)
		result.extend(self.exploration_skills)
		result.extend(self.interpersonal_skills)
		result.extend(self.intrigue_skills)
		result.extend(self.lore_skills)
		return result

	# customize how features are presented in the output file and summary in console
	def print_feature(self, fid, verbose=False):
		result = ''
		feature = ALL_FEATURES[fid]
		feature_name = self.string_replace_with_otherdata(ALL_FEATURES[fid]['name'])
		section_start = '      >'
		section_start_len = len(section_start)+1
		space_between = 38

		ability_keywords = ''
		feature_has_keywords = False
		if 'keywords' in feature and feature['keywords'].strip() != '':
			ability_keywords = feature['keywords'].split(',')
			feature_has_keywords = True

		# is the feature free-typed?
		free = ('free' in feature and feature['free'] == 'True')

		# start with the name
		result += feature_name

		# add triggers and power roll info, if applicable
		if 'trigger' in feature and feature['trigger'] != '':
			trigger = '\n'.join(wrap(feature['trigger'], 60, subsequent_indent='\t'))
			result += '\n     >> Trigger: %s' % trigger

		feature_has_powerroll = ('powerroll' in feature and feature['powerroll'] == 'True')
		powerrolllines = ['\t   11: ', '\t12-16: ', '\t   17: ']
		if feature_has_powerroll:

			# setup powerroll data
			for i in range(3):
				powerroll = {}
				powerrollline = ''
				pr_text = feature['powerroll_tier%s' % str(i+1)]
				pr_split = pr_text.split('|')
				for item in pr_split:
					item_split = item.split(':')

					kw, val = (0, 0)
					if len(item_split) < 2:
						kw = 'effect'
						val = item_split[0].strip()
					else: # as long as the damage part always has "damage:" in front, this works good
						kw, val = item_split
						val = val.strip()

					# do damage calculation based on keywords and kit bonuses
					if kw == 'damage':
						powerroll['damage'] = {}
						val_split = val.split(',')
						if len(val_split) > 1:
							powerroll['damage']['type'] = val_split[0].strip()
							powerroll['damage']['value'] = val_split[1].strip()
						else:
							powerroll['damage']['type'] = ''
							powerroll['damage']['value'] = val_split[0].strip()

						damage = powerroll['damage']['value']
						roll_damage = 'd' in damage

						kit_damage_bonuses = {
							'melee' : self.melee_bonus[i],
							'ranged' : self.ranged_bonus[i],
							'magic' : self.magic_bonus[i],
							'psionic' : self.psionic_bonus[i]
						}

						required_keywords_per_bonus = {
							'melee' : ['weapon','melee'],
							'ranged' : ['weapon','ranged'],
							'magic' : ['magic'],
							'psionic' : ['psionic']
						}

						# add damage bonuses from kits based on matching keywords
						bonuses = []
						
						for keyword in required_keywords_per_bonus:
							requirements_met = True
							for kw in required_keywords_per_bonus[keyword]:
								if kw not in ability_keywords:
									requirements_met = False
							if requirements_met:
								if keyword in kit_damage_bonuses:
									bonuses.append(keyword)

						# attacks like Fade with more than one damage keyword (Ranged & Melee)
						if len(bonuses) > 1:
							line_list = []

							for keyword in bonuses:
								this_bonus_damage = ''

								if roll_damage: # e.g. 1d6 damage
									if '+' in damage: # e.g. 1d6+18 damage
										vals = damage.split('+')
										val_damages = []
										for val in vals: # e.g. 1d10+1d6+8 damage
											if 'd' in val:
												val_damages.append(v)
											else:
												val_damages.append(int(v) + int(kit_damage_bonuses[keyword]))
										this_bonus_damage = '+'.join(val_damages)
									else:
										this_bonus_damage = '%s+%s' % (damage, kit_damage_bonuses[keyword])
								else:
									this_bonus_damage = str(int(damage) + int(kit_damage_bonuses[keyword]))

								line_list.append('%s (%s)' % (this_bonus_damage, keyword))

							powerrollline += ' or '.join(line_list)

						# attacks with only one damage keyword
						elif bonuses:
							this_bonus_damage = ''

							if roll_damage: # e.g. 1d6 damage
								if '+' in damage: # e.g. 1d6+18 damage
									vals = damage.split('+')
									val_damages = []
									for val in vals: # e.g. 1d10+1d6+8 damage
										if 'd' in val:
											val_damages.append(val)
										else:
											val_damages.append(str(int(val) + int(kit_damage_bonuses[bonuses[0]])))
									this_bonus_damage = '+'.join(val_damages)
								else:
									this_bonus_damage = '%s+%s' % (damage, kit_damage_bonuses[bonuses[0]])
							else:
								this_bonus_damage = str(int(damage) + int(kit_damage_bonuses[bonuses[0]]))

							powerrollline += this_bonus_damage

						# no bonuses at all, can just copy the string!
						else:
							powerrollline += str(damage)

						if powerroll['damage']['type'] != '':
							powerroll['damage']['type'] = ' %s' % powerroll['damage']['type']
						powerrollline += '%s damage' % powerroll['damage']['type']

						if len(pr_split) > 1:
							powerrollline += '; '
						
					# effects don't get auto-calculated changes, so we can just print them as is
					elif kw == 'effect':
						powerrollline += val

				powerrolllines[i] += powerrollline

		### end if power rolls ###############################################

		### print keywords, distance and target (and powerrolls if any)

		# apply kit bonuses to distance
		distances = []
		if 'distance' in feature and feature['distance'].strip() != '':
			# first split on | for attacks with multiple ranges (e.g. Fade)
			distance_split = feature['distance'].lower().split('|') 

			# add non-self distances, implement kit bonuses
			for i in range(len(distance_split)):
				dist = distance_split[i]
				dist_added = False
				if dist == 'self':
					distances.append('self')
					dist_added = True
				else:
					#if len(dist.split(',')) != 2:
					#	print(dist)

					dist_bonuses = {
						'magic' : self.magic_distance,
						'psionic' : self.psionic_distance,
						'weapon' : self.weapon_distance
					}

					kw, val = dist.split(',')

					if kw == 'reach':
						# reach
						if 'melee' in ability_keywords and 'weapon' in ability_keywords:
							distances.append('reach %s' % str(int(val) + int(self.reach_bonus)))
							dist_added = True

					if kw == 'ranged':

						applicable_ranged_bonuses = [range_kw for range_kw in ['weapon', 'magic'] if range_kw in ability_keywords]
						multiple_ranged_bonuses = (len(applicable_ranged_bonuses) > 1)

						# ranged
						if 'ranged' in ability_keywords:
							for applicable_ranged_bonus in applicable_ranged_bonuses:
								dist_print_line = 'ranged %s' % str(int(val) + int(dist_bonuses[applicable_ranged_bonus]))

								if multiple_ranged_bonuses:
									dist_print_line += ' (%s)' % applicable_ranged_bonus

								distances.append(dist_print_line)
								dist_added = True
						else:
							distances.append('ranged %s' % str(int(val)))
							dist_added = True	

					# all magic areas
					area_kws = ['aura', 'burst', 'cube', 'line', 'wall'] # TODO: ignoring special

					area_bonuses = {
						'magic' : self.magic_area,
						'psionic' : self.psionic_area,
						'weapon' : self.weapon_area
					}
					applicable_area_dist_bonuses = [d for d in dist_bonuses.keys() if d in ability_keywords]
					nonzero_bonuses_num = 0
					for bonus in applicable_area_dist_bonuses:
						if area_bonuses[bonus] > 0:
							nonzero_bonuses_num += 1
						elif dist_bonuses[bonus] > 0:
							nonzero_bonuses_num += 1

					if 'area' in ability_keywords and kw in area_kws:

						if applicable_area_dist_bonuses:

							for bonus in applicable_area_dist_bonuses:

								if kw == 'aura':
									distance_print_line = 'aura %s' % str(int(val) + int(area_bonuses[bonus]))
									if nonzero_bonuses_num:
										distance_print_line += ' (%s)' % bonus
									distances.append(distance_print_line)
									dist_added = True
								elif kw == 'burst':
									distance_print_line = 'burst %s' % str(int(val) + int(area_bonuses[bonus]))
									if nonzero_bonuses_num:
										distance_print_line += ' (%s)' % bonus
									distances.append(distance_print_line)
									dist_added = True
								elif kw == 'cube':
									cube_size, cube_dist = val.split(':')
									cube_size = str(int(cube_size) + int(area_bonuses[bonus]))
									cube_dist = str(int(cube_dist) + int(dist_bonuses[bonus]))
									distance_print_line = '%s cube in %s' % (cube_size, cube_dist)
									if nonzero_bonuses_num:
										distance_print_line += ' (%s)' % bonus
									distances.append(distance_print_line)
									dist_added = True
								elif kw == 'line':
									line_A, line_B, line_dist = val.split(':')
									line_A = str(int(line_A) + int(area_bonuses[bonus]))
									line_B = str(int(line_B) + int(area_bonuses[bonus]))
									line_dist = str(int(line_dist) + int(dist_bonuses[bonus]))
									distance_print_line = '%s x %s line in %s' % (line_A, line_B, line_dist)
									if nonzero_bonuses_num:
										distance_print_line += ' (%s)' % bonus
									distances.append(distance_print_line)
									dist_added = True
								elif kw == 'wall':
									wall_size, wall_dist = val.split(':')
									wall_size = str(int(wall_size) + int(area_bonuses[bonus]))
									wall_dist = str(int(wall_dist) + int(dist_bonuses[bonus]))
									distance_print_line = '%s wall in %s' % (wall_size, wall_dist)
									if nonzero_bonuses_num:
										distance_print_line += ' (%s)' % bonus
									distances.append(distance_print_line)
									dist_added = True
						
						# NOTE: if no Area keyword, then any distance like "aura X" simply won't print. Hm.
						else:
							# no bonuses, just print
							if kw == 'aura':
								distances.append('aura %s' % str(val))
								dist_added = True
							elif kw == 'burst':
								distances.append('burst %s' % str(val))
								dist_added = True
							elif kw == 'cube':
								cube_size, cube_dist = val.split(':')
								distances.append('cube %s within %s' % (cube_size, cube_dist))
								dist_added = True
							elif kw == 'line':
								line_A, line_B, line_dist = val.split(':')
								distances.append('%s x %s line within %s' % (line_A, line_B, line_dist))
								dist_added = True
							elif kw == 'wall':
								wall_size, wall_dist = val.split(':')
								distances.append('wall %s within %s' % (wall_size, wall_dist))
								dist_added = True

				if not dist_added:
					distances.append('unrecognized distance')


		# print keywords, target and distance, and print powerrolls if any
		if feature_has_keywords or feature_has_powerroll:

			header_lens = [len('Keywords: '), len('Target:   '), len('Distance: ')]
			newlineindents = [' '*section_start_len]*3
			for i in range(3):
				newlineindents[i] += ' '*header_lens[i]

			# print keywords
			print_keywords = '\tKeywords: '
			if ability_keywords:
				print_keywords += ', '.join(ability_keywords)
			else:
				print_keywords += '-'

			# print target
			targetline = ''
			if 'target' in feature:
				targetline = feature['target']
			if targetline == '':
				targetline = '-'
			print_target = '\tTarget:   ' + targetline.lower()
			
			# print distance
			distancelines = []
			if not distances:
				distancelines.append('\tDistance: -')
			else:
				distancelines.append('\tDistance: %s' % distances[0])
				for extradist in distances[1:]:
					distancelines[-1] += ' or'
					distancelines.append('\t%s%s' % (' '*header_lens[2], extradist))

			# build list of Keyword, Target, Distance (KTD) lines, using word wrap
			key_left_column_width = int(space_between*0.92)
			targ_left_column_width = int(space_between*1.0)
			dist_left_column_width = int(space_between*1.2)
			ktdlines = []

			ktdlines.extend(wrap(print_keywords, key_left_column_width, subsequent_indent=newlineindents[0]))
			ktdlines.extend(wrap(print_target, targ_left_column_width, subsequent_indent=newlineindents[1]))
			for distline in distancelines:
				ktdlines.extend(wrap(distline, dist_left_column_width, subsequent_indent=newlineindents[2]))

			if feature_has_powerroll:
				# plug power roll characteristic titleline above power roll results
				powerrolllines.insert(0, '\t[Power Roll + %s]' % feature['powerroll_char'])	
			else:
				# no power roll, don't print any power roll table
				powerrolllines = []

			wrapped_powerrolllines = []
			for line in powerrolllines:
				wrapped_powerrolllines.extend(wrap(line, 68, subsequent_indent='\t\t     '))

			maxlines = max(len(ktdlines), len(wrapped_powerrolllines))
			ktdlines.extend(['']*maxlines)
			wrapped_powerrolllines.extend(['']*maxlines)

			# iterate through lines, combining each
			for i in range(maxlines):
				result += '\n{}{}'.format(ktdlines[i].ljust(space_between), wrapped_powerrolllines[i])

		# print effects if any
		effect_split = feature['effect'].split('{N}')
		for i in range(len(effect_split)):
			effect_split[i] = '\n'.join(wrap(effect_split[i], 80, subsequent_indent='\t'))
		effect = '\n\t  '.join(effect_split)
		if effect != '':
			result += '\n%s %s' % (section_start, effect)

		# print other (e.g. "Spend Insight") if any
		if 'other' in feature and feature['other'] != '':
			other_split = feature['other'].split('{N}')
			for i in range(len(other_split)):
				other_split[i] = '\n'.join(wrap(other_split[i], 80, subsequent_indent='\t'))
			other_effect = '\n\t'.join(other_split)
			if other_effect != '':
				result += '\n%s %s  ' % (section_start, other_effect)

		# print any temporary choices made related to the feature
		if fid in self.feature_choices.keys():
			feature_choice = self.feature_choices[fid]
			feature_name = feature_choice['name']
			if feature_name.endswith('{N}'):
				feature_name = feature_name[:-3] + ':\n'
			else:
				feature_name += ':'
			result += '\n\tv\n\t[Choice] %s ' % feature_name
			effect_split_newline = feature_choice['effect'].split('{N}')
			for i in range(len(effect_split_newline)):
				effect_split_newline[i] = '\n'.join(wrap(effect_split_newline[i], 80, subsequent_indent='\t  '))
			choice_effect = '\n\t'.join(effect_split_newline)
			result += '\n%s %s  ' % (section_start, choice_effect)

		return result, free

	# customize how the data is presented at the end in the file that's outputted
	def fileoutput(self):
		pass

	# customize how the data is presented at the end in the console
	def summarize(self):
		mydata = []

		# print top line stuff
		subclass_name = ' '.join(self.char_subclass)
		epithet_detail = (self.name, subclass_name, self.char_class, self.ancestry)
		char_epithet = '%s, the %s %s %s' % epithet_detail
		titleline = '='*12 + ' ' + char_epithet + ' ' + '='*32
		titlelen = len(titleline)
		borders = '='*titlelen
		mydata.append(borders)
		mydata.append(titleline)
		mydata.append(borders)
		mydata.append(' ')

		career_complic_just = 32

		careerline = ('Career: %s' % self.career).ljust(career_complic_just)
		cultureline = ', '.join([self.environment, self.organization, self.upbringing])
		mydata.append('%s\tCulture: %s' % (careerline, cultureline))

		langs = ', '.join(self.languages)

		complication_line = 'Complication: '
		if self.complication == '':
			complication_line += '-'
		else:
			complication_line += self.complication
		complication_line = complication_line.ljust(career_complic_just)

		mydata.append('%s\tLanguages: %s' % (complication_line, langs))

		# print characteristics
		charc_abbr = ['MGT', 'AGL', 'REA', 'INU', 'PRS']
		charc_line = '/'
		for i in range(5):
			charc_space = '   %s:%d   /' % (charc_abbr[i], self.characteristics[i])
			charc_line += charc_space
		borders = '-'*len(charc_line)
		mydata.append(borders)
		mydata.append(charc_line)
		mydata.append(borders)
		mydata.append(' ')

		# NOTE: I'm not aware of any features that grant bonuses to either of these,
		#		but I can imagine one that increases your recover value
		calc_winded = self.stamina // 2
		calc_recover_value = self.stamina // 3 + self.recover_value_bonus

		# print stamina and recoveries
		mydata.append('Max Stamina %d\t\t\tMax Recoveries %d' % (self.stamina, self.recoveries))
		mydata.append('Winded @ %d\t\t\tRecover Value %d' % (calc_winded, calc_recover_value))
		mydata.append(' ')

		# size, reach (add base 1 reach to reach bonus from kits), speed, stability
		reachline = (self.reach_bonus+1, self.renown)
		speedline = (self.stability, self.projectpoints)
		mydata.append(('Size %s' % self.size).ljust(12) + 'Reach %d\t\tRenown %d' % reachline)
		mydata.append(('Speed %d' % self.speed).ljust(12) + 'Stability %d\t\tProject Points %d' % speedline)
		mydata.append(' ')

		# immunities & weaknesses
		print_immunities = self.immunities.copy()
		if not print_immunities:
			print_immunities.append('-\t')
		else:
			# trim immunities of all but highest values per damage type
			max_immus = {}
			for combo in print_immunities:
				damage_type, value = combo.split(':')
				if not damage_type in max_immus or int(value) > max_immus[damage_type]:
					max_immus[damage_type] = int(value)
			print_immunities = ['%s %d' % (dt, max_immus[dt]) for dt in max_immus.keys()]

		print_weaknesses = self.weaknesses.copy()
		if not print_weaknesses:
			print_weaknesses.append('-\t')
		else:
			# trim weaknesses of all but highest values per damage type
			max_weaks = {}
			for combo in print_weaknesses:
				damage_type, value = combo.split(':')
				if not damage_type in max_weaks or int(value) > max_weaks[damage_type]:
					max_weaks[damage_type] = int(value)
			print_weaknesses = ['%s %d' % (dt, max_weaks[dt]) for dt in max_weaks.keys()]

		# skill groups
		if not self.crafting_skills:
			self.crafting_skills.append('-')
		if not self.exploration_skills:
			self.exploration_skills.append('-')
		if not self.interpersonal_skills:
			self.interpersonal_skills.append('-')
		if not self.intrigue_skills:
			self.intrigue_skills.append('-')
		if not self.lore_skills:
			self.lore_skills.append('-')
		
		immuheader = 'Immunity: '
		weakheader = 'Weakness: '
		blankheader = ' '*len('Weakness: ')
		skillorder = [
			self.crafting_skills, 
			self.exploration_skills, 
			self.interpersonal_skills, 
			self.intrigue_skills, 
			self.lore_skills
		]
		headers = [
			'Crafting Skills:\t', 
			'Exploration Skills:\t', 
			'Interpersonal Skills:\t', 
			'Intrigue Skills:\t', 
			'Lore Skills:\t\t'
		]
		skillslen = [len(skill_list) for skill_list in skillorder]
		num_skills = sum(skillslen)
		skillperline = 3

		# build list to print for skills
		print_skills = []
		lineinskill = 0
		currskill = 0
		while currskill < len(skillorder):
			print_skill_line = ''
			if lineinskill == 0:
				print_skill_line += headers[currskill]
			else:
				print_skill_line += '\t\t\t'

			if lineinskill*skillperline < len(skillorder[currskill]):
				skillsline = ', '.join(
					skillorder[currskill][lineinskill*skillperline:(lineinskill+1)*skillperline]
				)
				print_skill_line += skillsline
				lineinskill += 1
			if (lineinskill+1)*skillperline >= len(skillorder[currskill]):
				currskill += 1
				lineinskill = 0
			print_skills.append(print_skill_line)

		# build list to print for immunities/weaknesses
		print_immuweak = []
		num_immu = len(print_immunities)
		num_immuweak = num_immu + len(print_weaknesses)
		for i in range(num_immuweak):
			print_immuweak_line = ''

			if i == 0:
				print_immuweak_line += immuheader
			elif i == num_immu:
				print_immuweak_line += weakheader
			else:
				print_immuweak_line += blankheader

			if i < num_immu:
				print_immuweak_line += print_immunities[i]
			else:
				# still in while loop, so there must be weaknesses remaining
				print_immuweak_line += print_weaknesses[i-num_immu]

			print_immuweak.append(print_immuweak_line.rstrip())

		# combine lists and print
		max_lines = max(len(print_skills), len(print_immuweak))
		if len(print_skills) < max_lines:
			print_skills.extend(['']*(max_lines-len(print_skills)))
		if len(print_immuweak) < max_lines:
			print_immuweak.extend(['']*(max_lines-len(print_immuweak)))

		for line in range(max_lines):
			mydata.append('{}{}'.format(print_immuweak[line].ljust(32), print_skills[line]))
		mydata.append('')


		# kit(s)
		kit_header = ''
		if len(self.kits) > 1:
			kit_header = 'Kits: '
		else:
			kit_header = 'Kit: '
		mydata.append(kit_header + ', '.join(self.kits))

		kit_detail = '      >'
		kitwear = ' or '.join(self.kit_wear)
		kitwield = ' or '.join(self.kit_wield)
		kit_detail += ' You wear %s and wield %s.' % (kitwear, kitwield)

		mydata.extend(wrap(kit_detail, 70, subsequent_indent=' '*len('      > ')))
		mydata.append(' ')

		# heroic resource feature
		hr_feat, _ = self.print_feature(self.hr_feature, False)
		mydata.append('Heroic Resource: %s' % hr_feat)
		# print hr feature here
		#hr_desc = '\t' + '\n'.join(wrap(self.descriptions[i], 70, subsequent_indent='\t\t\t'))
		mydata.append(' ')

		# abilities header
		abilitiesheader = '='*12 + ' ' + 'Abilities' + ' '
		fillerlen = titlelen - len(abilitiesheader)
		abilitiesheader += '='*fillerlen
		mydata.append(abilitiesheader)
		mydata.append(' ')

		# free strike actions
		for fid in self.free_strikes:
			printfeat, _ = self.print_feature(fid, False)
			mydata.append('\n[Action (FS)] %s' % printfeat)
		mydata.append(' ')

		# all triggered actions
		for fid in self.triggers:
			printfeat, free = self.print_feature(fid, False)
			freetag = ''
			if free:
				freetag = ', Free'
			mydata.append('\n[Triggered%s] %s' % (freetag, printfeat))
		if self.triggers:
			mydata.append(' ')

		# all not-heroic maneuvers
		for fid in self.maneuvers:
			printfeat, free = self.print_feature(fid, False)
			freetag = ''
			if free:
				freetag = ', Free'
			mydata.append('\n[Maneuver%s] %s' % (freetag, printfeat))
		if self.maneuvers:
			mydata.append(' ')


		# all signature actions
		for fid in self.signatures:
			printfeat, _ = self.print_feature(fid, False)
			mydata.append('\n[Action, Signature] %s' % printfeat)
		if self.signatures:
			mydata.append(' ')

		# all heroic 3-cost abilities
		for fid in self.heroic3maneuvers:
			printfeat, free = self.print_feature(fid, False)
			freetag = ''
			if free:
				freetag = ', Free'
			mydata.append('\n[Maneuver%s, Heroic] %s' % (freetag, printfeat))

		for fid in self.heroic3actions:
			printfeat, free = self.print_feature(fid, False)
			freetag = ''
			if free:
				freetag = ', Free'
			mydata.append('\n[Action, Heroic] %s' % printfeat)
		if self.heroic3maneuvers or self.heroic3actions:
			mydata.append(' ')

		# all heroic 5-cost abilities
		for fid in self.heroic5maneuvers:
			printfeat, free = self.print_feature(fid, False)
			freetag = ''
			if free:
				freetag = ', Free'
			mydata.append('\n[Maneuver%s, Heroic] %s' % (freetag, printfeat))

		for fid in self.heroic5actions:
			printfeat, free = self.print_feature(fid, False)
			freetag = ''
			if free:
				freetag = ', Free'
			mydata.append('\n[Action, Heroic] %s' % printfeat)
		if self.heroic5maneuvers or self.heroic5actions:
			mydata.append(' ')

		# all other actions
		for fid in self.actions:
			printfeat, free = self.print_feature(fid, False)
			freetag = ''
			if free:
				freetag = ', Free'
			mydata.append('\n[Action%s] %s' % (freetag, printfeat))
		if self.actions:
			mydata.append(' ')

		# all misc features
		for fid in self.misc_features:
			printfeat, _ = self.print_feature(fid, False)
			mydata.append('\n[Feature] %s' % printfeat)
		if self.misc_features:
			mydata.append(' ')

		# put it all together
		result = '\n'.join(mydata) + '\n'
		return result