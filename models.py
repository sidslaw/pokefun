
import plib

# C = Common, U = Uncommon, R = Rare
RARITY_CHOICES = ['C', 'U', 'R']


#==============================================================================
class Card(plib.Model):
	def __init__(self, rarity=None, *args, **kwargs):
		self.width = 35
		self.height = 40
		self.rows = self.height
		self.rarity = rarity
		
	def display(self):
		print str(self)

	def get_border(self):
		self.rows -= 1
		return '*' * self.width

	def get_row(self, text_list=[]):
		num_words = len(text_list) or 1
		width_to_fill = self.width - 4   # Takes the edges out of consideration
		total_chars = 0
		for t in text_list:
			total_chars += len(str(t).strip())
		total_spacing = width_to_fill - total_chars
		spacing_locations = ((num_words - 1) or 1)
		spacing = int(total_spacing / spacing_locations)
		spacings = [' ' * spacing for _ in range(spacing_locations)]
		spacings[0] += (' ' * (total_spacing - (spacing_locations * spacing)))
		
		text = []
		for i, t in enumerate(text_list):
			text.append(str(t).strip())
			if i < len(spacings):
				text.append(spacings[i])

		if not text_list:
			text = [spacings[0]]

		self.rows -= 1
		return '* %s *' % ''.join(text)

	def get_image(self):
		img_width, img_height = self.width - 6, int(self.height / 3)
		output = []
		add = output.append
		add(self.get_row(['', ' %s ' % ('-' * (img_width-2)), '']))
		for _ in range(img_height - 2):
			add(self.get_row(['|', '|']))
		add(self.get_row(['', ' %s ' % ('-' * (img_width-2)), '']))
		return output

	def get_remainder(self):
		output = []
		add = output.append
		while (self.rows > 1):
			add(self.get_row())
		add(self.get_border())
		return output

	def get_card_display_lines(self):
		# Override this function in the subclass
		return [self.get_border()] + self.get_remainder()

	def __str__(self):
		return '\n'.join(self.get_card_display_lines())

#==============================================================================
class TrainerCard(Card):
	def __init__(self, name, effects=[], *args, **kwargs):
		super(TrainerCard, self).__init__(*args, **kwargs)
		self.name = name
		self.effects = effects

#==============================================================================
class Attack(plib.Model):
	# TODO: Add energy cost
	# TODO: Add testing for energy cost
	def __init__(self, name, pokemon_card, effects=[], energy_cost=[]):
		# energy_costs is a list of strings
		# effects is a list of Effect objects
		super(Attack, self).__init__()
		self.pokemon_card = pokemon_card
		self.name = name
		self.effects_list = effects

	def get_effects(self, keyword=''):
		# Takes an optional keyword. If a keyword is passed, then it returns
		# a list of all the effects' values for the given keyword.
		# If no keyword is given, it returns the full effects_list.
		# TODO: Test this
		if not keyword:
			return self.effects_list

		effect_list = []
		for effect in self.effects_list:
			effect = effect_list.append(effect.get_attr(keyword))
		return effect_list

	@property
	def damage(self):
		return self.get_effects('damage')

	@property
	def burn(self):
		return self.get_effects('burn')

	@property
	def confused(self):
		return self.get_effects('confused')

	@property
	def paralyze(self):
		return self.get_effects('paralyze')

	@property
	def sleep(self):
		return self.get_effects('sleep')

#==============================================================================
class Effect(plib.Model):
	# TODO: Add testing for all the new fields
	def __init__(self, effects={}):
		super(Effect, self).__init__()
		# This will be the text that is displayed
		self.description = ''

		# Both you and opponent: is_self = is_opp = True
		# All a player's pokemon (active/benched): is_all = True
		# Only active: bench_only = is_all = False
		# Only benched: bench_only = True and is_all = False
		self.is_self = False
		self.is_opp = False
		self.is_all = False # Refers to both bench and active
		self.this_pokemon = False
		self.bench = False
		self.hand = False
		self.deck_top = False
		self.deck_bottom = False
		self.deck = False
		self.lost_zone = False
		self.draw = False
		self.discard_pile = False
		self.show = False
		self.shuffle = False
		self.asleep = False
		self.burned = False
		self.paralyzed = False
		self.poisoned = False
		self.confused = False
		self.flip_until_heads = False
		self.flip_until_tails = False
		self.ignore_weakness = False
		self.ignore_resistance = False
		self.ignore_pokepower = False
		self.ignore_pokebody = False
		self.is_max = False # If true, then "num_cards" is the maximum
		self.apply_next_turn = False
		self.cannot_attack = False # if true, usually need to meet a condition
		# This is only used in the damage_conds variable. It designates that
		# damage will effect the card selected in the parent effect
		self.parent_card = False

		# --- DICT TYPES --- these get turned into Effect() objects
		# Only does extra damage if conditions are met. Doesn't do normal damage
		# if "damage" is on of the conditions and is less than 0.
		# valid conditions are Effect properties (is_self, deck, hand, etc...)
		self.damage_conds = {}
		# Only do these if the main effect is in a chain and completed
		# TODO: Add testing for this
		self.cond_chain_effects = {}
		self.heads = {}
		self.tails = {}
		self.heal = {}

		# --- EFFECT LIST TYPES ---
		# A list of Effects you can choose to do. To denote a "do nothing" effect
		# make an empty choice
		self.choices = []
		self.move = [] # [move_from, move_to]
		self.chain_effects = [] # similar to heads/tails but will always happen
		self.switch = [] # [player_to_move, player_who_gets_to_choose]
		self.rearrange = [] # [player_to_rearrange, player_who_rearranges]
		
		# --- LIST TYPES ---
		self.energy_types = [] # energy type keywords
		# valid card types: all, energy, pokemon, basic, evolution, trainer, 
		# 					random
		self.card_types_to_move = []

		# --- ARGUMENT TYPES ---
		self.num_card_per_type = 0
		self.base_damage = None       # If None, then use the pokemon's damage
		self.damage = 0               # In addition to the pokemon's damage
		self.damage_for_energies = 0
		self.damage_for_evolved = 0
		self.heal_for_damage = 0 # Normally, this will be 1 (heal 1 for 1 damage)
		self.num_coin_flips = 0
		self.num_damage_mod = 0
		self.num_cards = 0 # -1 = all
		self.evolves_from = None # pokemon name or this_pokemon

		# Caveats:
		# 1)	If card_types_to_move = [pokemon, evolution] and evolves_from is
		# 		set, then only move a pokemon that evolves from the given pokemon
		# 2)	If card_types_to_move = [random] and move1 = [is_opp, hand], then
		# 		player chooses num_cards amount to randomly pick from their hand
		# 3)	If show=True, then the move order goes move1 -> show -> move2
		# 4)	If heal has an effect, then the given pokemon is/are healed for
		# 		the value set in the damage field
		# 5)	If the heal_for_damage field has a value > 0, then the heal field
		# 		must have an effect designating who will get healed

		for effect, val in effects.items():
			self.set_attr(effect, val)

	def set_attr(self, effect, val):
		setattr(self, effect, val)

	def get_attr(self, effect):
		val = getattr(self, effect)
		if not val:
			return {}
		return val

	def __eq__(self, other):
		if not isinstance(other, self.__class__):
			return False

		is_equal = True
		self_dict = self.__dict__.copy()
		self_keys = self_dict.keys()
		other_dict = other.__dict__.copy()

		while self_keys:
			key = self_keys.pop(0)
			if key in other_dict:
				if isinstance(self_dict[key], list) and isinstance(other_dict[key], list) and (
						len(self_dict[key]) == len(other_dict[key])
				):
					if len(self_dict[key]) != len(other_dict[key]):
						# The lists do not have the same length and so are not equal
						print 'SELF %s: Length of list %s != length of list %s' % (key, self_dict[key], other_dict[key])
						is_equal = False
					else:
						# Iterate through and check all items in the lists
						for i, item in enumerate(self_dict[key]):
							if self_dict[key][i] != other_dict[key][i]:
								print 'SELF LIST %s: %s != %s' % (key, self_dict[key][i], other_dict[key][i])
								is_equal = False
				elif self_dict[key] != other_dict[key]:
					# Effect values are not equal
					print 'SELF %s: %s != %s' % (key, self_dict[key], other_dict[key])
					is_equal = False
				del other_dict[key]
			else:
				print 'KEY [%s] WAS NOT FOUND IN OTHER' % key
				is_equal = False
			del self_dict[key]

		other_keys = other_dict.keys()
		while other_keys:
			key = other_keys.pop(0)
			if key in self_dict:
				if isinstance(self_dict[key], list) and isinstance(other_dict[key], list) and (
						len(self_dict[key]) == len(other_dict[key])
				):
					if len(self_dict[key]) != len(other_dict[key]):
						# The lists do not have the same length and so are not equal
						print 'OTHER %s: Length of list %s != length of list %s' % (key, self_dict[key], other_dict[key])
						is_equal = False
					else:
						# Iterate through and check all items in the lists
						for i, item in enumerate(self_dict[key]):
							if self_dict[key][i] != other_dict[key][i]:
								print 'OTHER LIST %s: %s != %s' % (key, self_dict[key][i], other_dict[key][i])
								is_equal = False
				elif other_dict[key] != self_dict[key]:
					# Check if values are equal
					print 'OTHER %s: %s != %s' % (key, self_dict[key], other_dict[key])
					is_equal = False
				del self_dict[key]
			else:
				print 'KEY [%s] WAS NOT FOUND IN SELF' % key
				is_equal = False
			del other_dict[key]

		if not is_equal:
			print
			print 'SELF:', self.__dict__.keys()
			print
			print 'OTHER:', other.__dict__.keys()
			print 'DAMAGE:', other.get_attr(':50')
			print

		return is_equal

	def __ne__(self, other):
		return not self.__eq__(other)

	def __str__(self):
		str_dict = {}
		for k, v in self.__dict__.items():
			if isinstance(v, list):
				val = []
				for item in v:
					if isinstance(item, self.__class__):
						val.append(item.__dict__)
					else:
						val.append(str(item))
			else:
				val = str(v)
			str_dict[k] = val
		return str(str_dict)
		


#==============================================================================
class EnergyCard(Card):
	def __init__(self, energy_type_key, value = 1, *args, **kwargs):
		super(EnergyCard, self).__init__(*args, **kwargs)
		self.energy_type = EnergyType(energy_type_key)
		self.value = value or 1

	def get_currentid(self):
		return self.energy_type.get_currentid()

	def get_currentkey(self):
		return self.energy_type.get_currentkey()

	def is_ineffective(self, *args, **kwargs):
		return self.energy_type.is_ineffective(*args, **kwargs)

	def is_effective(self, *args, **kwargs):
		return self.energy_type.is_effective(*args, **kwargs)
	
#==============================================================================
class EnergyType(plib.ChoiceTable):
	# TODO: REMOVE RESISTANCE/STRENGTH STUFF FROM TESTS
	
	energy_choices = ['fire', 'grass', 'water', 'fighting', 'lightning', 'psychic', 'darkness', 'metal', 'normal',]

	def __init__(self, current_key_or_id):
		super(EnergyType, self).__init__('energy_types', self.energy_choices, current_key_or_id)

	def __str__(self):
		return self.currentkey.title()
		

#==============================================================================
class Pokemon(plib.Model):
	# TODO: Changed energy type to pokemon card, change this elsewhere
	# TODO: Add in evolutions here
	def __init__(self, name):
		self.name = name

#==============================================================================
class PokemonCard(Card):
	# TODO: ADD WEAKNESS AND RESISTANCE TO CARD DISPLAY
	# TODO: ALLOW ADDING ENERGY TO CARDS
	# TODO: ADD RETREAT COST
	def __init__(self, pokemon, hp=0, resistance=None, weakness=None, series_key='', energy_type_key='', *args, **kwargs):
		super(PokemonCard, self).__init__(*args, **kwargs)
		self.pokemon = pokemon
		self.name = pokemon.name
		self.hp = self.current_hp = hp
		self.attacks = []
		self.resistance = resistance
		self.weakness = weakness
		self.series = series_key
		self.energy_type = EnergyType(energy_type_key)

		if isinstance(resistance, basestring):
			self.resistance = EnergyType(resistance)

		if isinstance(weakness, basestring):
			self.weakness = EnergyType(weakness)

	def add_attack(self, attack):
		# attack is expected to be an Attack() model
		self.attacks.append(attack)

	def get_card_display_lines(self):
		self.rows = self.height
		output = []
		output.append(self.get_border())
		# Add the name and hp
		output.append(self.get_row([self.name, 'HP %s' % self.current_hp]))
		# Add the elements
		output.append(self.get_row(['', str(self.energy_type)]))
		output += self.get_image()
		output += self.get_remainder()
		return output
		
#==============================================================================
