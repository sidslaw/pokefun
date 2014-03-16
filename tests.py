
import models
import plib
from unittest import TestCase
import unittest

print '''
#==============================================================================
#=========================== MODEL TESTS ======================================
#==============================================================================
'''

def build_trainer_card(effects={}):
	return models.TrainerCard('Gust', build_effects(effects))

def build_attack(effects={}):
	return models.Attack('Roar', build_pokemon_card(), build_effects(effects))

def build_effects(effects={}):
	return [models.Effect(effects)]

def build_energy_card():
	return models.EnergyCard('fire')

def build_energy_type():
	return models.EnergyType('fire')

def build_pokemon():
	return models.Pokemon('Chimi')

def build_pokemon_card():
	return models.PokemonCard(build_pokemon(), hp=10, energy_type_key='fire')

#==============================================================================
class EnergyTypeTests(TestCase):
	# TODO: Add more testing for model changes
	def setUp(self):
		return

	def test_energy_type_invalids(self):
		self.assertEqual(models.EnergyType(1).get_currentid(), 1)

		with self.assertRaises(plib.InvalidIDException):
			invalid_str_type = models.EnergyType('red')

		with self.assertRaises(plib.InvalidIDException):
			invalid_null_type = models.EnergyType(None)


#==============================================================================
class AttackTests(TestCase):
	# TODO: Add testing
	def setUp(self):
		pass


#==============================================================================
class CardTests(TestCase):
	def setUp(self):
		self.card = models.Card()

	def get_card_display_lines(self):
		return self.card.get_card_display_lines()

	def test_card_display_height(self):
		display_output = self.get_card_display_lines()
		self.assertEqual(len(display_output), self.card.height)

	def test_card_display_width(self):
		display_output = self.get_card_display_lines()
		self.assertGreater(len(display_output), 1)
		self.assertEqual(len(display_output[0]), self.card.width)


#==============================================================================
class EnergyCardTests(TestCase):

	def test_valid_energy(self):
		card = models.EnergyCard('fire')
		self.assertEqual(card.energy_type.currentkey, 'fire')
		ineffective_type = 'water'
		effective_type = 'grass'

		# Test adding energy cards by their ID
		card = models.EnergyCard(card.get_currentid())

	def test_invalid_energy(self):
		with self.assertRaises(plib.InvalidIDException):
			card = models.EnergyCard('fluffles')
		with self.assertRaises(plib.InvalidIDException):
			card = models.EnergyCard(None)


#==============================================================================
class PokemonCardTests(TestCase):
	# TODO: Add testing for new fields
	# TODO: Add testing for attacks
	# TODO: Add testing for rarity
	def setUp(self):
		self.name = 'Harold'
		self.energy_type = 'fire'
		self.hp = 10
		pokemon = models.Pokemon(self.name)
		self.pokemon = models.PokemonCard(pokemon, self.hp, energy_type_key=self.energy_type)
		return

	def test_pokemon_card_init(self):
		self.assertEqual(self.pokemon.name, self.name)
		self.assertEqual(self.pokemon.energy_type.currentkey, self.energy_type)
		self.assertEqual(self.pokemon.hp, self.hp)

#==============================================================================
class TrainerCardTests(TestCase):
	# TODO: Finish testing
	def setUp(self):
		return

	def test_(self):
		return

#==============================================================================
class EffectTests(TestCase):
	# TODO: Add testing for this
	def setUp(self):
		return

	def test_(self):
		return

#==============================================================================
class PokemonTests(TestCase):
	# TODO: Add testing for this
	def setUp(self):
		return

	def test_(self):
		return

#==============================================================================
tests = [EnergyTypeTests, AttackTests, CardTests, EnergyCardTests,
		 PokemonCardTests, TrainerCardTests, EffectTests, PokemonTests]

suite = unittest.TestSuite()
for test in tests:
	suite.addTest(unittest.TestLoader().loadTestsFromTestCase(test))
unittest.TextTestRunner(verbosity=2).run(suite)


print '''
#==============================================================================
#=========================== DATA MINING TESTS ================================
#==============================================================================
'''
import get_card_info
class DataMiningTests(TestCase):
	def setUp(self):
		self.addTypeEqualityFunc(models.Effect, self.check_effects_are_equal)
		return

	def test_effect_simple(self):
		expected_effect = models.Effect({'is_self': True, 'is_all': True})
		effect_str = 'is_self__is_all'
		effect = get_card_info.convert_effect_str_to_effect(effect_str)
		return

	def test_effect_with_arg(self):
		expected_effect = models.Effect({'is_self': True, 'is_all': True, 'damage': 10})
		effect_str = 'is_self__is_all__damage__:10'
		effect = get_card_info.convert_effect_str_to_effect(effect_str)
		return

	def test_effect_effect_list(self):
		# Discard upto 4 energy cards attached to the defending pokemon.
		# Then do 20 damage to one of your opponent's benched pokemon.
		expected_effect = models.Effect({'chain_effects': [
			models.Effect({
				'card_types_to_move': ['energy'],
				'move': [models.Effect({'is_opp': True}), models.Effect({'discard_pile': True})],
				'num_cards': 4,
				'is_max': True,
			}),
			models.Effect({
				'damage': 20,
				'is_opp': True,
				'bench': True,
				'num_cards': 1,
			}),
		]})

		effect_str = '''
chain_effects
chain_effects_1
card_types_to_move
:energy
end_card_types_to_move
move
move_1
is_opp
end_move_1
move_2
discard_pile
end_move_2
end_move
num_cards
:4
is_max
end_chain_effects_1
chain_effects_2
damage
:20
is_opp
bench
num_cards
:1
end_chain_effects_2
end_chain_effects
'''.strip().replace('\n', '__')
		effect = get_card_info.convert_effect_str_to_effect(effect_str)
		self.assertEqual(expected_effect, effect)
		return

	def test_effect_list(self):
		# Do 40 damage to all pokemon with types grass and fire.
		expected_effect = models.Effect({
			'is_all': True,
			'is_opp': True,
			'is_self': True,
			'num_cards': -1,
			'damage': 40,
			'energy_types': ['grass', 'fire'],
		})
		effect_str = 'is_all__is_opp__is_self__num_cards__:-1__damage__:40__energy_types__:grass__:fire__end_energy_types'
		effect = get_card_info.convert_effect_str_to_effect(effect_str)
		self.assertEqual(expected_effect, effect)
		return

	def test_effect_dict(self):
		# Flip a coin. If heads, do 40 damage to each of your opponent's pokemon.
		expected_effect = models.Effect({
			'num_coin_flips': 1,
			'heads': models.Effect({
				'is_opp': True,
				'is_all': True,
				'damage': 50,
			})
		})
		effect_str = 'num_coin_flips__:1__heads__is_all__is_opp__damage__:50__end_heads'
		effect = get_card_info.convert_effect_str_to_effect(effect_str)
		self.assertEqual(expected_effect, effect)
		return

	def test_complicated_effect(self):
		expected_effect = models.Effect({
			'chain_effects': [
				models.Effect({
					'num_cards': 2,
					'move': [models.Effect({'this_pokemon': True}), models.Effect({'discard_pile': True})],
					'card_types_to_move': ['energy'],
					'energy_types': ['grass'],
				}),
				models.Effect({'damage': 40, 'is_opp': True, 'is_all': True, 'num_cards': 2}),
			]
		})
		effect_str = 'chain_effects__chain_effects_1__num_cards__:2__move__move_1__this_pokemon__end_move_1__move_2__discard_pile__end_move_2__end_move__card_types_to_move__energy__end_card_types_to_move__energy_types__:grass__end_energy_types__end_chain_effects_1__chain_effects_2__damage__:40__is_opp__is_all__num_cards__:2__end_chain_effects_2__end_chain_effects'
		effect = get_card_info.convert_effect_str_to_effect(effect_str)
		self.assertEqual(expected_effect, effect)

	def check_effects_are_equal(self, effect1, effect2, *args, **kwargs):
		if effect1 != effect2:
			raise self.failureException('The two Effect objects are not equal!')

#==============================================================================
data_mining_tests = [DataMiningTests]
suite = unittest.TestSuite()
for test in data_mining_tests:
	suite.addTest(unittest.TestLoader().loadTestsFromTestCase(test))
unittest.TextTestRunner(verbosity=2).run(suite)

"""

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
		* choices(ic, conds, choices)
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
        * is_active
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
"""





































