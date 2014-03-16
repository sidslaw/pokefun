
from urllib import urlopen, urlencode

from xml.etree import ElementTree
from bs4 import BeautifulSoup
from plib import XmlListConfig, XmlDictConfig
from models import Effect

#========================================================================
def convert_effect_str_to_effect(effect_str):

	def _process_dict(effects_list, effect, keyword):
		# Flip a coin. If heads, do 40 damage to each of your opponent's pokemon.
		# Expected string format: "heads__is_all__is_opp__damage__:40__end_heads"
		# Expected output format: {'heads': Effect({'is_all': True, 'is_opp': True, 'damage': 40})}

		end_key = 'end_%s' % keyword
		arg_set = []
		while effects_list and effects_list[0] != end_key:
			key = effects_list.pop(0)
			arg_set.append(key)

		if effects_list and effects_list[0] == end_key:
			effects_list.pop(0)

		sub_effect = process_effects('__'.join(arg_set))
		effect.set_attr(keyword, sub_effect)

		return effects_list, effect

	def _process_list(effects_list, effect, keyword):
		end_key = 'end_%s' % keyword
		effect_vals = []
		while effects_list and effects_list[0] != end_key:
			effect_vals.append(effects_list.pop(0).lstrip(':'))

		if effects_list and effects_list[0] == end_key:
			effects_list.pop(0)

		effect.set_attr(keyword, effect_vals)
		return effects_list, effect

	def _process_effect_list(effects_list, effect, keyword):
		# Expected string format: "chain_effects__chain_effects_1__is_opp__is_all__end_chain_effects_1__chain_effects_2__is_opp__is_all__end_chain_effects_2__end_chain_effects"
		# Expected output format: {'chain_effects': [Effect({'is_opp':True, 'is_all':True}), Effect({'is_self':True, 'is_all':True})]}

		# list_data is a dictionary containing the different start/end
		# indices for each list item
		list_data = {}
		i = 1
		arg_sets = []
		while effects_list and effects_list[0] != 'end_%s' % keyword:
			if effects_list[0] == '%s_%s' % (keyword, i):
				arg_sets.append([])
				effects_list.pop(0)
			if effects_list[0] == 'end_%s_%s' % (keyword, i):
				effects_list.pop(0)
				i += 1
			elif effects_list[0] != 'end_%s' % keyword:
				arg_sets[-1].append(effects_list.pop(0))

		if effects_list and effects_list[0] == 'end_%s' % keyword:
			effects_list.pop(0)

		new_effects = []
		for arg_set in arg_sets:
			new_effects.append(process_effects('__'.join(arg_set)))

		effect.set_attr(keyword, new_effects)

		return effects_list, effect

	def _simple_effects(effects_list, effect, effect_str):
		effects_with_args = [
			'base_damage', 'damage',
			'damage_for_energies', 'damage_for_evolved',
			'num_coin_flips', 'num_card_per_type',
			'num_damage_mod', 'evolves_from', 'num_cards',
		]
		arg = True
		if effect_str in effects_with_args and effects_list \
		   and isinstance(effects_list[0], basestring) \
		   and effects_list[0].strip().startswith(':'):

			# All arg values start with a colon
			arg = effects_list.pop(0).strip()[1:]
			try:
				arg = int(arg)
			except:
				pass

		effect.set_attr(effect_str, arg)

		return effects_list, effect

	def process_effects(effects_str, effect=None):
		if not effect:
			effect = Effect()
		dict_types = ['damage_conds', 'heads', 'tails', ]
		list_types = ['energy_types', 'card_types_to_move', ]
		effect_list_types = ['choice', 'chain_effects', 'move', ]

		effects_list = effects_str.split('__')
		while effects_list:
			effect_str = effects_list.pop(0)

			if effect_str in effect_list_types:
				effects_list, effect = _process_effect_list(effects_list, effect, effect_str)
			elif effect_str in list_types:
				effects_list, effect = _process_list(effects_list, effect, effect_str)
			elif effect_str in dict_types:
				effects_list, effect = _process_dict(effects_list, effect, effect_str)
			else:
				effects_list, effect = _simple_effects(effects_list, effect, effect_str)

		return effect

	return process_effects(effect_str)

#========================================================================
#================= process_effect() HELPER FUNCTIONS ====================
#========================================================================
def damage(x='[damage]', conds=[]):
	return_li = ['damage', ':%s' % x] + conds
	return _filter(*return_li)

#========================================================================
def damage_conds(conds):
	if not conds:
		return ''
	return_li = ['damage_conds'] + conds + ['end_damage_conds']
	return _filter(*return_li)

#========================================================================
def num_cards(x='[num_cards]'):
	return _filter('num_cards', ':%s' % x)

#========================================================================
def move(src, dest, card_types_list=[], nc='', et='', is_max=False):
	# Acceptable values for src and dest include: is_opp, is_self,
	#	this_pokemon, discard, lost_zone
    # card_types_list is expected to be a value acceptable for the
    #   card_types() function
    # nc is a string containing the num_cards regex variable name
    # et is a string containing the energy_types regex_variable name
    # is_max is a bool; if true then "is_max" is added to the filter str

	# src and dest are expected to be lists of strings
	if not isinstance(src, list) or not isinstance(dest, list):
		return ''

	# src and dest are expected to have values
	if not src or not dest:
		return ''

	return_li = []
	return_li += ['move']
	return_li += ['move_1__%s__end_move_1' % src]
	return_li += ['move_2__%s__end_move_2' % dest]
	if card_types: return_li += card_types(card_types_list)
    if nc: return_li += num_cards(nc)
    if et: return_li += energy_types(et)
    if is_max: return_li += ['is_max']
	return_li += ['end_move']
	return _filter(*return_li)

#========================================================================
def card_types(card_types_list=[]):
	# Acceptable values are energy, pokemon, damage, random, all
	# When the "all" or "random" type is used, the "damage" type is ignored
	if not card_types_list:
		return ''
	return_li = ['card_types'] + card_types_list + ['end_card_types']
	return _filter(*return_li)

#========================================================================
def chain_effects(effects=[]):
	if not effects:
		return ''

	return_li = ['chain_effects']
	for i, effect in enumerate(effects):
		cei = i + 1
		return_li += [_filter('chain_effects_%s' % cei, effect, 'end_chain_effects_%s' % cei)]
	return_li += ['end_chain_effects']
	return _filter(*return_li)

#========================================================================
def cond_chain_effects(conds=[]):
	# In the event that this filter is used, then a chain effect or choice
	# will not be able to happen until all these effects are met

	if not conds:
		return ''

	return_li = ['cond_chain_effects'] + conds + ['end_cond_chain_effects']
	return _filter(*return_li)

#========================================================================
def energy_types(energy_types_list='[energy_types]'):
	if not energy_types_list:
		return ''
	return_li = ['energy_types'] + energy_types_list + ['end_energy_types']
	return _filter(*return_li)

#========================================================================
def damage_for_energies(x='[damage_for_energies]', conds=[]):
	if x == '':
		return ''
	return _filter('damage_for_energies', x, damage_conds(conds), 'end_damage_for_energies')

#========================================================================
def switch(target='', chooser='is_self'):
	# target and chooser are both one of the following: is_opp, is_self
	if not target or not chooser:
		return ''
	return _filter('switch', target, chooser, 'end_switch')

#========================================================================
def heads(effects=[]):
	return_li = ['heads'] + effects + ['end_heads']
	return _filter(*return_li)

#========================================================================
def tails(effects=[]):
	return_li = ['tails'] + effects + ['end_tails']
	return _filter(*return_li)

#========================================================================
def choices(ic='[is_choice]', conds=[], choices=[]):
	# If ic is True then the player may choose to opt out of
	# making any choices. Acceptable values for ic include:
	#	* True
	#	* False
	#	* string used in the regex

	return_li = ['choices']
	for i, choice in enumerate(choices):
		ci = i + 1
		return_li += ['choices_%s__%s__end_choices_%s'] % (ci, choice, ci)

	cce = cond_chain_effects(conds)
	if cce: return_li += [cce]

	ic = is_choice(ic)
	if ic: return_li += [ic]

	return_li += ['end_choices']
	return _filter(*return_li)

#========================================================================
def heal(src, dest='discard', hp=0, heal_for_damage=0):
	# Setting dest to discard just removes the damage

	# At least one of these is required
	if not hp and not heal_for_damage:
		return ''

	# src is required
	if not src:
		return ''

	return_li = ['heal']
	if hp: return_li += ['hp__:%s' % hp]
	if heal_for_damage: return_li += ['heal_for_damage__:%s' % heal_for_damage]
	return_li += [move(src, dest, ['damage'])]
	return_li += ['end_heal']
	return _filter(*return_li)

#========================================================================
def rearrange(rearranger, target):
	# -> rearranger - required list of strings
	# -> target     - required list of strings

	if not rearranger or not target:
		return ''

	return_li = ['rearrange']
	return_li += ['rearranger__%s__end_rearranger' % '__'.join(rearranger)]
	return_li += ['target__%s__end_target' % '__'.join(target)]
	return_li += ['end_rearrange']
	return _filter(*return_li)

#========================================================================
def damage_counters(x, conds=[]):
	# x is a required value that must be able to be an int
	if not x:
		return ''

	try:
		x = int(x)
	except:
		return ''

	return damage(x * 10, conds)

#========================================================================
def is_choice(x):
	if not x:
		return ''
	elif x == True:
		x = '1'

	x = ':%s' % x

	return _filter('is_choice', x)

#========================================================================
def draw(target, cards = '[num_cards]'):
    return _filter('draw', target, num_cards(cards), 'end_draw')

#========================================================================
def _filter(*xs):
	return '__'.join(xs)

#========================================================================
#========================================================================
def process_effect(base_damage, effect):
	"""
	This function accepts an effect string from a card and processes it
	into a format that the program can understand. There are many helper
	functions and strings to make writing these formats easier.

	Functions:
		* damage(x, conds)
		* num_cards(x)
		* move(x, y, card_types_list, num_cards, energy_types, others)
		* card_types(card_types_list)
		* chain_effects(effects)
		* cond_chain_effects(conds) -- must be in a chain_effects or choices group
		* energy_types(energy_types)
		* damage_for_energies(x, conds)
		* damage_conds(conds)
		* switch(target, chooser) -- target and chooser are either "is_opp" or "is_self"
		* heads(effects)
		* tails(effects)
		* choices(is_choice, conds, choices)
		* heal(src, dest, hp, heal_for_damage) -- dest is set to discard to just remove the counters
		* rearrange(rearranger, target) -- rearranger is the player that gets to rearrange the cards
		* damage_counters(x) -- Multiplied by 10
		* is_choice(x) -- x is either a string or bool, if string and empty then x is False
        * draw(target) -- target is the player that gets to draw; either "is_opp" or "is_self"

	Strings:
		* ignore_resistance
		* ignore_weakness
		* ignore_pokebody
		* ignore_pokepower
		* is_opp
		* is_all
        * is_active -- similar to "this_pokemon" but can be used with is_opp too
		* this_pokemon
		* discard
		* energy
		* parent_card
		* bench
		* is_evolved
		* is_basic
		* apply_next_turn
		* is_self
		* is_max
		* hand
		* shuffle
		* show
		* draw
		* paralyzed
		* poisoned
		* confused
		* cannot_attack
		* no_retreat
        * no_damage -- removes the base attack damage, used when an attack adds to the base damage or similar actions
		* mirror
		* top		-- refers to the deck location
		* bottom	-- refers to the deck location

	-> effect is a string that we will regex
	<- a dict of effect key/value pairs related to the effect string param
	"""
	effect_dict = {}

	if not effect:
		# TODO: Return only effect_dict
		return effect_dict or 0

	energy_types = 'pdrwgflm'

	effect_regexes = {
		# Misc Damage
		_filter('ignore_resistance'): [
			'this attack\'s damage isn\'t affected by resistance.'
		],
		_filter('ignore_resistance', 'ignore_weakness'): [
			'this attack\'s damage isn\'t affected by weakness or resistance.'
		],
		_filter('ignore__resistance', 'ignore_weakness', 'ignore_pokepower', 'ignore_pokebody'): [
			'this attack\'s damage isn\'t affected by weakness, resistance,(?: poke-powers,)*(?: poke-bodies,)*(?: pokemon powers,)* or any other effects on the defending pokemon.'
		],

		# Opponent Damage
		_filter(damage(), 'is_opp', 'is_all'): ['put (?P<damage>\d+) damage counters* on each of your opponent\'s pokemon'],
		_filter(damage(), 'is_opp', 'is_all', num_cards()): [
			'this attack does (?P<damage>\d+) damage to (?P<num_cards>\d) of your opponent\'s pokemon.$',
			'choose (\d) of your opponent\'s pokemon. this attack does (\d+) damage to that pokemon.$',
		],
		_filter(damage(), num_cards(), 'is_opp', 'is_all', 'ignore_weakness', 'ignore_resistance'): [
			'choose (?P<num_cards>\d) of your opponent\'s pokemon. this attack does (?P<damage>\d+) damage to (?:that|each) pokemon. don\'t apply weakness and resistance.'
		],
		chain_effects([
			_filter(num_cards(), move('this_pokemon', 'discard', ['energy']), energy_types()),
			_filter(damage(), num_cards('[num_cards2]'), 'is_opp', 'is_all'),
		]): [
			'discard (?P<num_cards>all|\d+) (?P<energy_types>\w)*\s*energy attached to this pokemon. this attack does (?P<damage>\d+) damage to (?P<num_cards2>\d) of your opponent\'s pokemon.'
		],
		_filter('is_opp', 'is_all', num_cards(), damage_for_energies('[damage_for_energies]', ['parent_card'])): [
			'choose (?P<num_cards>\d) of your opponent\'s pokemon. this attack does \d+ damage plus (?P<damage_for_energies>\d+) more damage for each energy attached to that pokemon.',
		],
        _filter(damage(), 'bench', 'is_opp', num_cards()): [
			'choose (?P<num_cards>\d+) of your opponent\'s benched pokemon. this attack does (?P<damage>\d+) damage to each of them.',
			'does (?P<damage>\d+) damage to (?P<num_cards>\d|each|all) of your opponent\'s benched pokemon.',
		],
        chain_effects([_filter('no_damage'), _filter(damage()), _filter(damage('damage2'), damage_conds('is_opp', 'is_evolved'))]): [
			'if the defending pokemon is an evolved pokemon, this attack does (?P<base_damage>\d+) damage plus (?P<damage_for_evolved>\d+) more damage.',
		],
        chain_effects([_filter(switch('is_opp', 'is_self')), _filter('is_opp', damage())]): [
			'switch the defending pokemon with 1 of your opponent\'s benched pokemon. this attack does (?P<damage>\d+) damage to the new defending pokemon.',
		],

		# Self Damage
		_filter(damage(), 'is_self'): [
			'this pokemon does (?P<damage>\d+) damage to itself.',
		],
		_filter(damage(), 'is_self', 'is_all', 'ignore_weakness', 'ignore_resistance', num_cards()): [
			'does (?P<damage>\d+) damage to (?P<num_cards>\d) of your pokemon, and don\'t apply weakness and resistance to this damage.',
		],
		_filter('apply_next_turn', chain_effects([_filter('no_damage'), _filter(damage())])): [
			'during your next turn, .+? base damage is (?P<damage>\d+).',
		],

		# Energy cards
		heads(move(_filter('is_opp'), _filter('is_opp', 'discard'), card_types_list=['energy'], nc='[num_cards]', et='[energy_types]')): [
			'flip a coin. if heads, discard (?P<num_cards>an|all|\d+) (?P<energy_types>[%s]){0,1}\s*energy\s*(?:card){0,1}\s*attached to the defending pokemon.' % energy_types,
		],
		heads(move(_filter('is_opp'), _filter('is_opp', 'bench'), num_cards('[num_cards2]')), card_types_list=['energy'], nc='[num_cards]')): [
			'flip a coin. if heads, choose (?P<num_cards>\d+) energy cards* attached to the defending pokemon and (?P<num_cards2>\d+) of your opponent\'s benched pokemon. attach that energy card to that pokemon.',
		],
		tails(move(_filter('is_self', 'is_active'), _filter('is_self', 'discard'), card_types_list=['energy'], nc='[num_cards]', et='[energy_types]')): [
			'flip a coin. if tails, discard (?P<num_cards>an|all|\d+) (?P<energy_types>[%s]){0,1}\s*energy\s*(?:card){0,1}\s*attached to (?:yanma|this pokemon).' % energy_types,
		],
		heads(_filter('is_self', 'discard'), _filter('is_self', 'is_active'), ['energy'], '1'): [
			'flip a coin. if heads, search your discard pile for an energy card and attach it to (?:[^.]+).',
		],
        heads(move(_filter('is_self', 'discard'), _filter('is_self', 'is_active'), ['energy'], '[num_cards]', '[energy_types]', True)): [
			'if there are any (?P<energy_types>[%s]+) energy cards in your discard pile, flip a coin. if heads attach (?P<num_cards>\d+) of those energy cards to (?:[^.]+).' % energy_types,
		],
        choices('[is_choice]', [], [move(_filter('is_self', 'this_pokemon'), _filter('is_self', 'discard'), ['energy'], '[num_cards]', '[energy_types]')]): [
			'(?P<is_choice>you may )*discard (?P<num_cards>all|\d+)\s*(?P<energy_types>[%s]){0,1} energy (?:attached to this pokemon|cards to use this attack).' % energy_types,
		],
		choices(
				'[is_choice]',
				[chain_effects([_filter('no_damage'), _filter(damage())])],
				[move(_filter(), _filter(), ['energy'], '[num_cards]', '[energy_types]')]
		): [
			'(?P<is_choice>you may )*discard (?P<num_cards>all|\d+)\s*(?P<energy_types>[%s]){0,1} energy attached to (?:[^.]+). if you do, this attack\'s base damage is (?P<damage>\d+) instead of \d+.' % energy_types,
		],
		move(_filter('is_self', 'discard'), _filter('is_self', 'this_pokemon'), ['energy'], '[num_cards]', '[energy_types]'): [
			'attach (?P<num_cards>\d+) (?P<energy_types>[%s]){0,1}\s*energy from your discard pile to this pokemon.' % energy_types,
		],
        chain_effects([move(_filter('is_self', 'deck'), _filter('is_self', 'hand'), ['energy'], '[num_cards]'), _filter('shuffle')]): [
			'search your deck for up to (?P<num_cards>\d+) different types of basic energy cards, show them to your opponent, and put them into your hand. shuffle your deck afterward.',
		],
		'choices__' \
		'choices_1__' \
		'chain_effects__' \
		'chain_effects_1__' \
		'switch__' \
		'switch_1__is_self__end_switch_1__' \
		'switch_2__is_self__end_switch_2__' \
		'end_switch__' \
		'cond_chain_effects__' \
		'num_cards__:-1__' \
		'is_max__' \
		'card_types_to_move__:energy__end_card_types_to_move__' \
		'move__move_1__this_pokemon__end_move_1__' \
		'move_2__is_self__end_move_2__end_move__' \
		'end_cond_chain_effects__' \
		'end_chain_effects_1__' \
		'end_chain_effects__' \
		'end_choices_1__' \
		'[is_choice]end_choices': [
			'you (?P<is_choice>may) switch yanma with 1 of your benched pokemon. if you do, move as many energy cards attached to yanma as you like to the new active pokemon',
		],

		# Search deck
		'num_cards__:1__' \
		'move__' \
		'move_1__is_self__deck__end_move_1__' \
		'move_2__is_self__hand__end_move_2__' \
		'end_move__' \
		'card_types_to_move__:all__end_card_types_to_move': [
			'search your deck for a card and put it into your hand.',
		],
		'is_max__num_cards__:[num_cards]__move__move_1__deck__is_self__end_move_1__move_2__is_self__bench__end_move_2__end_move__card_types_to_move__:basic__:pokemon__end_card_types_to_move': [
			'search your deck for up to (?P<num_cards>\d+) basic pokemon and put (?:it|them) onto your bench.',
		],
		'num_cards__:1__' \
		'evolves_from__:this_pokemon__' \
		'card_types_to_move__:pokemon__:evolution__end_card_types_to_move__' \
		'move__' \
		'move_1__is_self__deck__end_move_1__' \
		'move_2__this_pokemon__end_move_2__' \
		'end_move': [
			'search your deck for a card that evolves from this pokemon and put it onto this pokemon.',
		],
		'num_cards__:1__' \
		'energy_types__:[energy_types]__end_energy_types__' \
		'card_types_to_move__:energy__end_card_types_to_move__' \
		'move__' \
		'move_1__deck__is_self__end_move_1__' \
		'move_2__this_pokemon__end_move_2__' \
		'end_move': [
			'^search your deck for an* (?P<energy_types>[%s])\s*energy card and attach it to this pokemon' % energy_types,
		],

		# Search discard pile
		'show__num_cards__:[num_cards]__' \
		'move__' \
		'move_1__discard_pile__is_self__end_move_1__' \
		'move_2__is_self__deck__end_move_2__' \
		'end_move__' \
		'card_types_to_move__:all__end_card_types_to_move': [
			'search your discard pile for any (?P<num_cards>\d+) cards*, show (?:it|them) to your opponent, and put (?:it|them) on top of your deck.',
		],

		# Draw card
        draw('is_self'): [
			'^draw a card.'
		],

		# Flip statuses
		'heads__paralyzed__is_opp__end_heads': [
			'flip a coin. if heads, the defending pokemon is now paralyzed.',
			'flip a coin. if heads, each defending pokemon is now paralyzed.',
		],
		'heads__confused__is_opp__end_heads': [
			'flip a coin. if heads, the defending pokemon is now confused.',
			'flip a coin. if heads, each defending pokemon is now confused.',
		],
		'heads__poisoned__is_opp__end_heads': [
			'flip a coin. if heads, the defending pokemon is now poisoned.',
			'flip a coin. if heads, each defending pokemon is now poisoned.',
		],

		# Flip damage
		'tails__cannot_attack__end_tails': [
			'if tails, this attack does nothing.',
		],
		'tails__damage__:[damage]__this_pokemon__end_tails': [
			'if tails, (?:zapdos|this pokemon) does (?P<damage>\d+) damage to (?:it)*self.',
			'if tails, put (?P<damage_counters>\d+) damage counters on ([^.]+).',
		],
		'heads__damage__opp__bench__end_heads': [
			'if heads, this attack does (\d+) damage to (\d) of your opponent\'s benched pokemon.'
		],
		'tails__damage__opp__bench__end_tails': [
			'if tails, this attack does (\d+) damage to (\d) of your opponent\'s benched pokemon.'
		],
		'heads__damage__opp__all__end_heads': [
			'if (heads|tails), this attack does (\d+) damage to each of your opponent\'s pokemon.'
		],
		'tails__damage__opp__all__end_tails': [
			'if (heads|tails), this attack does (\d+) damage to each of your opponent\'s pokemon.'
		],
		# TODO: Fix these two effects
		'heads__damage__opp__self__end_heads': [
			'for each of your opponent\'s benched pokemon, flip a coin. if heads, this attack does (\d+) damage to that pokemon. .+? then, .+? does (\d+) damage times the number of (heads|tails) to itself.'
		],
		'tails__damage__opp__self__end_tails': [
			'for each of your opponent\'s benched pokemon, flip a coin. if tails, this attack does (\d+) damage to that pokemon. .+? then, .+? does (\d+) damage times the number of (heads|tails) to itself.'
		],
		'heads__opp__cannot_attack__end_heads': [
			'flip a coin. if heads,(?: during your opponent\'s next turn)* prevent all effects of (?:an attack|attacks), including damage, done to (?:yanma|this pokemon)(?: during your opponent\'s next turn)*.'
		],
		'tails__opp__cannot_attack__end_tails': [
			'flip a coin. if tails,(?: during your opponent\'s next turn)* prevent all effects of (?:an attack|attacks), including damage, done to (?:yanma|this pokemon)(?: during your opponent\'s next turn)*.'
		],

		# Status changes
		_filter('confused', 'is_opp'): [
			'defending pokemon is now confused.'
		],
		_filter('poisoned', 'is_opp'): [
			'the defending pokemon is now poisoned.'
		],
        _filter('no_retreat', 'is_opp'): [
			'the defending pokemon can\'t retreat during (?:your )*opponent\'s next turn.'
		],
        _filter('mirror'): [
			'choose (\d+) of the defending pokemon\'s attacks and use it as this attack.'
		],
        switch('is_opp', 'is_opp'): [
			'your opponent switches the defending pokemon with 1 of his or her benched pokemon.'
		],
        switch('is_self', 'is_self'): [
			'switch (?:yanmega |yanma )*with 1 of your benched pokemon.'
		],

		# Heal
        heal('is_self', hp = 'hp'): [
			'heal (?P<hp>\d+) damage from this pokemon.',
		],
        heal('is_self', heal_for_damage = '1'): [
			'remove a number of damage counters from [a-z ]+? equal to the damage done to the defending pokemon.',
		],
        heal('is_self', 'is_opp__is_all', 'hp'): [
			'move (?P<hp>\d+) damage counters* from any of your pokemon to any of your opponent\'s pokemon.'
		],

		# Hand
		'heads__' \
		'chain_effects__' \
		'chain_effects_1__' \
		'num_cards__:[num_cards]__show__' \
		'move__' \
		'move_1__is_opp__hand__end_move_1__' \
		'move_2__is_opp__deck__end_move_2__' \
		'end_move__' \
		'card_types_to_move__:random__end_card_types_to_move__' \
		'end_chain_effects_1__' \
		'chain_effects_2__' \
		'shuffle__is_opp__' \
		'end_chain_effects_2__' \
		'end_heads': [
			'if heads, choose (?P<num_cards>a|any|\d+) cards* at random from your opponent\'s hand. your opponent reveals that card and shuffles it into his or her deck.',
		],
		'num_cards__:[num_cards]__show__' \
		'move__' \
		'move_1__is_opp__hand__end_move_1__' \
		'move_2__is_opp__hand__end_move_2__' \
		'end_move__' \
		'card_types_to_move__:random__end_card_types_to_move__': [
			'choose (?P<num_cards>\d+) cards* from your opponent\'s hand without looking. look at the card you chose',
		],
		'num_cards__:[num_cards]__show__' \
		'move__' \
		'move_1__is_opp__hand__end_move_1__' \
		'move_2__lost_zone__end_move_2__' \
		'end_move__' \
		'card_types_to_move__:random__end_card_types_to_move': [
			'choose (?P<num_cards>\d+) cards* from your opponent\'s hand without looking and put (?:it|them) in the lost zone.',
		],

		# TODO: Finish this one
		'hand__opp__no__items': ['your* opponent can\'t play any item cards from his or her hand next turn.'],

		# Deck
		# TODO: Add a filter for deck_loc where it will add in "deck_top" or "deck_bottom"
		'choices__' \
		'choices_1__' \
		'[deck_loc]__ ' \
		'num_cards__:[num_cards]__' \
		'rearrange__' \
		'rearrange_1__is_self__end_rearrange_1__' \
		'rearrange_2__is_self__end_rearrange_2__' \
		'end_rearrange__' \
		'end_choices__1__' \
		'choices_2__' \
		'[deck_loc]__ ' \
		'num_cards__:[num_cards]__' \
		'rearrange__' \
		'rearrange_1__is_self__end_rearrange_1__' \
		'rearrange_2__is_opp__end_rearrange_2__' \
		'end_rearrange__' \
		'end_choices__2__' \
		'end_choices': [
			'look at the (?P<deck_loc>top|bottom) (?P<num_cards>\d+) cards* of either player\'s deck and rearrange them as you like.',
		],
	}

	effect_regexes_reversed = {v:k for k,vs in effect_regexes.items() for v in vs}

	# 3845

	regex = ''
	try:
		import re
		effect = effect.replace('  ', ' ')
		matches = 0
		regex_matches = []
		for regex, key in effect_regexes_reversed.items():
			query = None
			if 'flip a coin' not in effect or 'flip a coin' in regex:
				query = re.search(regex, effect)
			if query:
				matches += 1
				regex_matches.append(regex)
				if matches > 1:
					print
					print '---------------------------------------------------------'
					print 'Found %s matches for effect: %s' % (matches, effect)
					print '\t* %s' % ('\n\t* '.join(regex_matches))
					print '---------------------------------------------------------'
					print

		if not matches and 'o-wisp' not in effect:
			print ' * %s' % effect
			return 1
		# TODO: Return effect_dict not 0
		return 0
	except Exception, e:
		print 'REGEX:', regex
		print 'EFFECT:', effect
		raise Exception(e)

#========================================================================
def process_cards(cards, evolutions):
	# cards is a list of dicts
	# evolutions is a dict of lists containnig names of pokemon that
	#            evolve from the one in the key
	import re
	keys = ['setName', 'cardname', 'attack3', 'weakness', 'hp', 'resistance', 'rarity', 'cardnumber', 'attack2',
			'pokemonpower', 'attack1', 'attack4', 'type', 'retreatcost', 'stage']
	series_ignores = ['trainer kit', 'op series', 'promo']

	major_text_changed_str = ' (Major text change. Requires reference.)'
	energy_conversion_keys = {'p':'psychic', 'd':'dark', 'r':'fire',
							  'w':'water', 'g':'grass', 'f':'fighting',
							  'l':'lightning', 'm':'metal'}
	attack_conversion_keys = ['attack1', 'attack2', 'attack3', 'attack4']
	key_conversions = {'setName': 'series', 'cardname': 'name', 'type': 'energy_type_key', 'retreatcost': 'retreat', }
	card_attack_parts = '\[([0-9A-Z]+)\] ([^(]+)((?:-|\(\d+\)))(.*)'
	valid_cards = []
	for card in cards:
		card_set = card['setName']

		# Don't process any cards that aren't in valid sets
		if any([(si in card_set.lower()) for si in series_ignores]):
			continue

		# Normalize the field names
		for old_key, new_key in key_conversions.items():
			card[new_key] = card[old_key]
			del card[old_key]

		# If a reference is required, mark the card as outdated
		card['is_outdated'] = False
		if major_text_changed_str in card['name']:
			card['name'] = card['name'].strip(major_text_changed_str)
			card['is_outdated'] = True


		# Convert the attacks to a list of attacks
		card.setdefault('attacks', [])
		for key in attack_conversion_keys:
			attack_str = card[key]
			if attack_str:
				row_reg_results = re.findall(card_attack_parts, attack_str)

				if not row_reg_results:
					continue

				ec = row_reg_results[0][0].strip()
				name = row_reg_results[0][1].strip()
				damage = int(row_reg_results[0][2].strip('- ()') or 0)
				# TODO: Don't make the effect text lowercase
				effects = row_reg_results[0][3].strip().lower()

				# Process the energy cost
				energy_cost = []
				if ec:
					if ec.lower() in energy_conversion_keys.keys():
						energy_cost.append(energy_conversion_keys[ec.lower()])
					elif ec.isdigit():
						energy_cost += (['normal'] * int(ec))

				# TODO: Process Weakness and Resistance

				# TODO: Process the effects
				effects = process_effect(damage, effects)

				# Make attack into a dict and add the
				# name, energy_cost, damage and effects to it
				attack = {
					'energy_cost': energy_cost,
					'name': name,
					'damage': damage,
					'effects': effects,
				}

				card['attacks'].append(attack)
			del card[key]

		card['evolutions'] = evolutions.get(card['name'], [])

		valid_cards.append(card)

	print len(valid_cards), 'VALID CARDS PROCESSED!'
	save_cards(valid_cards)

	return valid_cards



#========================================================================
def save_obj(fname='card_data.txt', obj=[]):
	try:
		import simplejson as json
	except ImportError:
		import json
	f = open(fname, 'w')
	f.write(json.dumps(obj))
	f.close()

#========================================================================
def read_obj(fname='card_data.txt'):
	try:
		import simplejson as json
	except ImportError:
		import json
	f = open(fname, 'r')
	obj = json.loads(f.read())
	f.close()
	return obj

#========================================================================
def save_cards(cards):
	save_obj('card_data.txt', cards)

#========================================================================
def get_all_pokemon():
	resp = urlopen('http://www.pokepedia.net/species.php','format=X&outputformat=XML').read()
	parsed_html = BeautifulSoup(resp)
	rows = parsed_html.find('table', attrs={'class': 'sortable'}).find_all('tr')

	pokemon_list = []
	for row in rows[1:-1]:
		pokemon_list.append(row.find_all('td')[1].get_text().strip().lower())

	return pokemon_list


#========================================================================
def get_evolution_data(pokemon_list):

	evolutions = {}
	resp = urlopen('http://www.pokepedia.net/fullevo.php','format=X&outputformat=XML').read()
	parsed_html = BeautifulSoup(resp)
	rows = parsed_html.find('table', attrs={'class': 'sortable'}).find_all('tr')

	def check_for_fuzzy_duplicate_key(key, d, val, valid_list):
		if not val:
			return d

		valid_key = ''
		for word in key.split():
			if word in valid_list and not valid_key:
				valid_key = word

		valid_val = ''
		for word in val.split():
			if word in valid_list and not valid_val:
				valid_val = word

		d.setdefault(valid_key, [])
		if valid_val not in d[valid_key]:
			d[valid_key].append(valid_val)

		return d

	for row in rows:
		basic, stage1, stage2 = row.find_all('td')

		stage2 = stage2.a
		if stage2:
			stage2 = stage2.get_text().lower()

		stage1 = stage1.a
		if stage1:
			stage1 = stage1.get_text().lower()
			evolutions = check_for_fuzzy_duplicate_key(stage1, evolutions, stage2, pokemon_list)

		basic = basic.a
		if basic:
			basic = basic.get_text().lower()
			evolutions = check_for_fuzzy_duplicate_key(basic, evolutions, stage1, pokemon_list)

	return evolutions

#========================================================================
def get_card_data():
	s = 'format=X&hpComparator=%3D&hp=&rarity=A&stageComparator=%3D&stage=Any&resistance=&weakness=A&type=A&dualtype=A&retreatComparator=%3D&retreatCost=&CondCond=AND&flipOptions=either&pokName=&freeText=&powerattack=PWRATK&textsrch=PHR&excludeText=&textexcl=EPHR&pokemonandtrainers=AL&pokType=ALLPOK&energyReqComparator=%3D&energyReq=&damageType=MIN&damageComparator=%3D&damageDealt=&sort1=&sort2=&sort3=&sort1dir=ASC&sort2dir=ASC&sort3dir=ASC&outputformat=XML'
	resp = urlopen('http://www.pokepedia.net/xmlgenerator.php', s).read()

	resp = ElementTree.XML(resp)
	resp_dict = XmlDictConfig(resp)
	return resp_dict['cards']['card']

#========================================================================
def main():
	'''
	pokemon = get_all_pokemon()
	evolutions = get_evolution_data(pokemon)
	cards = get_card_data()
	return process_cards(cards, evolutions)
	'''

	total_effects_remaining = 0
	total_effects = 0
	cards_by_series = {}
	for card in read_obj():
		cards_by_series.setdefault(card['series'].lower(), []).append(card)
		for attack in card.get('attacks', []):
			effects = attack.get('effects', '')
			if effects:
				total_effects += 1
				total_effects_remaining += process_effect(0, effects)

	for key, cards in cards_by_series.items():
		save_obj('series_%s_list.txt'%key, cards)

	print
	print 'TOTAL EFFECTS REMAINING TO BE PROCESSED:', total_effects_remaining, '/', total_effects

if __name__ == '__main__':
	main()


