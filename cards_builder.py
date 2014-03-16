
import models

# TODO: ADD TESTING FOR THE BUILDER
# TODO: FINISH POKEMON DATA
POKEMON_DATA = {
		'bulbasaur': {'name': 'Bulbasaur', 'type': 'grass', 'card_data': [
			{'hp':40, 'series':None, 'attacks':[], 'rarity': 'C'},
		]},
		'ivysaur': {'name': 'Ivysaur', 'type': 'grass', 'card_data': [
			{'hp':60, 'series':None, 'attacks':[], 'rarity': 'C'},
		]},
		'venasaur': {'name': 'Venasaur', 'type': 'grass', 'card_data': [
			{'hp':100, 'series':None, 'attacks':[], 'rarity': 'R'},
		]},
		'charmander': {'name': 'Charmander', 'type': 'fire', 'card_data': [
			{'hp':50, 'series':None, 'attacks':[], 'rarity': 'C'},
		]},
		'charmeleon': {'name': 'Charmeleon', 'type': 'fire', 'card_data': [
			{'hp':70, 'series':None, 'attacks':[], 'rarity': 'C'},
		]},
		'charizard': {'name': 'Charizard', 'type': 'fire', 'card_data': [
			{'hp':120, 'series':None, 'attacks':[], 'rarity': 'R'},
		]},
		'squirtle': {'name': 'Squirtle', 'type': 'water', 'card_data': [
			{'hp':50, 'series':None, 'attacks':[], 'rarity': 'C'},
		]},
		'wartortle': {'name': 'Wartortle', 'type': 'water', 'card_data': [
			{'hp':60, 'series':None, 'attacks':[], 'rarity': 'C'},
		]},
		'blastoise': {'name': 'Blastoise', 'type': 'water', 'card_data': [
			{'hp':110, 'series':None, 'attacks':[], 'rarity': 'R'},
		]},
}

# TODO: FINISH TRAINER CARD DATA
TRAINER_DATA = [
	{'name': 'Gust', 'effects': []},
]

#==============================================================================
class Builder(object):
	def __init__(self):
		super(Builder, self).__init__()
		self.pokemon_by_name = {}
		self.pokemon_cards_list = []
		self.pokemon_cards_by_name = {}
		self.energy_cards = {}
		self.trainer_cards_list = []
		self.build_all_pokemon()
		self.build_all_cards()

	def build_all_pokemon(self):
		for key, pokemon_data in POKEMON_DATA:
			self.pokemon_by_name[key] = models.Pokemon(
					pokemon_data['name'], pokemon_data['type'])

	def build_all_cards(self):
		for key, pokemon_data in POKEMON_DATA.items():
			for card in pokemon_data.get('card_data', []):
				self.pokemon_cards_by_name.setdefault(key, []).append(models.PokemonCard(
					self.pokemon_by_name(key), pokemon_data['hp'], rarity=pokemon_data['rarity']))

	def build_all_energy_cards(self):
		for energy in models.EnergyType.energy_choices:
			self.energy_cards[energy] = models.EnergyCard(energy)

	def build_all_trainer_cards(self):
		for trainer in TRAINER_DATA:
			self.trainer_cards_list.append(models.TrainerCard(**trainer))

	def __str__(self):
		return '\n\n'.join([str(_) for _ in self.cards_by_name.values()])
		

#==============================================================================
