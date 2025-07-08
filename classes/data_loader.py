import uuid
import requests
import json
from classes.learned_by import LearnedBy
from classes.move import Move
from classes.pokemon_master import PokemonMaster
import time

from classes.raid_pokemon_master import RaidPokemonMaster

class DataLoader:

    def __init__(self):
        self.base_url = 'https://pokeapi.co/api/v2/'

    def get_all_pokemon(self):
        pokemon_regions = {
            "generation-i": "Kanto",
            "generation-ii": "Johto",
            "generation-iii": "Hoenn",
            "generation-iv": "Sinnoh",
            "generation-v": "Unova",
            "generation-vi": "Kalos",
            "generation-vii": "Alola",
            "generation-viii": "Galar",
            "generation-ix": "Paldea"
        }
        pokemon_full_url = self.base_url + 'pokemon?limit=100000&offset=0'
        species_full_url = self.base_url + 'pokemon-species?limit=100000&offset=0'
        pokemon_response = json.loads(requests.get(pokemon_full_url).text) 
        species_response = json.loads(requests.get(species_full_url).text) 
        result = []
        for pokemon, species in zip(pokemon_response['results'],species_response['results']):
            #print(pokemon)
            #print(species)
            print(f'Getting data for: {species['name']}')
            species_json = json.loads(requests.get(species['url']).text)  
            color = species_json['color']['name']
            evolves_from = species_json['evolves_from_species']
            flavor_text = species_json['flavor_text_entries'][0]['flavor_text']
            generation = species_json['generation']['name']
            region = pokemon_regions[generation]
            growth_rate = species_json['growth_rate']['name']
            is_legendary = species_json['is_legendary']
            is_mythical = species_json['is_mythical']
            shape = species_json['shape']['name']
            pokemon_json = json.loads(requests.get(pokemon['url']).text)
            abilities = [ability['ability']['name'] for ability in pokemon_json['abilities']]
            base_experience = pokemon_json['base_experience']
            height = pokemon_json['height']
            held_items = [item['item']['name'] for item in pokemon_json['held_items']] if pokemon_json['held_items'] else []
            pokemon_id = pokemon_json['id']
            pokemon_name = pokemon_json['name']
            sprites = {
                'front_default': pokemon_json['sprites']['front_default'],
                'back_default': pokemon_json['sprites']['back_default'],
                'back_shiny': pokemon_json['sprites']['back_shiny'],
                'front_shiny': pokemon_json['sprites']['front_shiny'],
                'official_artwork_front_default': pokemon_json['sprites']['other']['official-artwork']['front_default'],
                'official_artwork_front_shiny': pokemon_json['sprites']['other']['official-artwork']['front_shiny']
            }
            base_stats = {
                stat['stat']['name']: stat['base_stat']
                for stat in pokemon_json['stats']
            }
            types = [pokemon_type['type']['name'] for pokemon_type in pokemon_json['types']]
            weight = pokemon_json['weight']
            if is_legendary or is_mythical:
                tier = 4
            elif base_experience >= 180:
                tier = 3
            elif base_experience < 180 and base_experience >= 100:
                tier = 2
            else:
                tier = 1

            final_pokemon = PokemonMaster(
                id=pokemon_id,
                name=pokemon_name,
                base_experience=base_experience,
                height=height,
                weight=weight,
                is_default=True,
                abilities_names=abilities,
                held_items_names=held_items,
                types_names=types,
                front_default_sprite=sprites.get('front_default'),
                back_default_sprite=sprites.get('back_default'),
                back_shiny_sprite=sprites.get('back_shiny'),
                front_shiny_sprite=sprites.get('front_shiny'),
                official_artwork_front_default_sprite=sprites.get('official-artwork_front_default'),
                official_artwork_front_shiny_sprite=sprites.get('official-artwork_front_shiny'),
                base_stats_json=base_stats,
                species_color_name=color,
                evolves_from_species_name=evolves_from.get('name') if evolves_from else None,
                evolves_from_species_url=evolves_from.get('url') if evolves_from else None,
                flavor_text_entry=flavor_text,
                generation_name=generation,
                growth_rate_name=growth_rate,
                is_legendary= is_legendary,
                is_mythical= is_mythical,
                shape_name= shape,
                region=region,
                tier = tier
            )
            result.append(final_pokemon)
        return result
    
    def get_all_raid_pokemon(self):
        pokemon_regions = {
            "generation-i": "Kanto",
            "generation-ii": "Johto",
            "generation-iii": "Hoenn",
            "generation-iv": "Sinnoh",
            "generation-v": "Unova",
            "generation-vi": "Kalos",
            "generation-vii": "Alola",
            "generation-viii": "Galar",
            "generation-ix": "Paldea"
        }
        pokemon_full_url = self.base_url + 'pokemon?limit=100000&offset=1025'
        pokemon_response = json.loads(requests.get(pokemon_full_url).text)
        print(pokemon_full_url)
        print(pokemon_response) 
        result = []
        for pokemon in pokemon_response['results']:
            pokemon_json = json.loads(requests.get(pokemon['url']).text)
            species_json = json.loads(requests.get(pokemon_json['species']['url']).text) 
            print(f'Getting data for: {pokemon_json['name']}') 
            color = species_json['color']['name']
            evolves_from = species_json['evolves_from_species']
            flavor_text = species_json['flavor_text_entries'][0]['flavor_text']
            generation = species_json['generation']['name']
            region = pokemon_regions[generation]
            growth_rate = species_json['growth_rate']['name']
            is_legendary = species_json['is_legendary']
            is_mythical = species_json['is_mythical']
            shape = species_json['shape']['name']
            abilities = [ability['ability']['name'] for ability in pokemon_json['abilities']]
            base_experience = pokemon_json['base_experience']
            height = pokemon_json['height']
            held_items = [item['item']['name'] for item in pokemon_json['held_items']] if pokemon_json['held_items'] else []
            pokemon_id = pokemon_json['id']
            pokemon_name = pokemon_json['name']
            sprites = {
                'front_default': pokemon_json['sprites']['front_default'],
                'back_default': pokemon_json['sprites']['back_default'],
                'back_shiny': pokemon_json['sprites']['back_shiny'],
                'front_shiny': pokemon_json['sprites']['front_shiny'],
                'official_artwork_front_default': pokemon_json['sprites']['other']['official-artwork']['front_default'],
                'official_artwork_front_shiny': pokemon_json['sprites']['other']['official-artwork']['front_shiny']
            }
            base_stats = {
                stat['stat']['name']: stat['base_stat']
                for stat in pokemon_json['stats']
            }
            types = [pokemon_type['type']['name'] for pokemon_type in pokemon_json['types']]
            weight = pokemon_json['weight']
            if is_legendary or is_mythical:
                tier = 4
            elif base_experience >= 180:
                tier = 3
            elif base_experience < 180 and base_experience >= 100:
                tier = 2
            else:
                tier = 1

            final_pokemon = RaidPokemonMaster(
                id=pokemon_id,
                name=pokemon_name,
                base_experience=base_experience,
                height=height,
                weight=weight,
                is_default=True,
                abilities_names=abilities,
                held_items_names=held_items,
                types_names=types,
                front_default_sprite=sprites.get('front_default'),
                back_default_sprite=sprites.get('back_default'),
                back_shiny_sprite=sprites.get('back_shiny'),
                front_shiny_sprite=sprites.get('front_shiny'),
                official_artwork_front_default_sprite=sprites.get('official-artwork_front_default'),
                official_artwork_front_shiny_sprite=sprites.get('official-artwork_front_shiny'),
                base_stats_json=base_stats,
                species_color_name=color,
                evolves_from_species_name=evolves_from.get('name') if evolves_from else None,
                evolves_from_species_url=evolves_from.get('url') if evolves_from else None,
                flavor_text_entry=flavor_text,
                generation_name=generation,
                growth_rate_name=growth_rate,
                is_legendary= is_legendary,
                is_mythical= is_mythical,
                shape_name= shape,
                region=region,
                tier = tier
            )
            result.append(final_pokemon)
        return result
    

    """
    result = data_loader.get_all_pokemon()

    for entry in result:
       await storage_manager.save_object(obj=entry, cache_key=f"pokemon_master:{entry.id}", table_name="pokemon_master", unique_columns=['id'])

    """
    @staticmethod
    def load_moves(move_id):
        move_full_url = r"https://pokeapi.co/api/v2/move/"        
        move_response = json.loads(requests.get(move_full_url + str(move_id)).text)
        id = move_response['id']
        accuracy = move_response['accuracy']
        damage_class = move_response['damage_class']['name'] 
        name = move_response['name']
        power = move_response['power']
        pp = move_response['pp']
        priority = move_response['priority']
        type_name = move_response['type']['name']
        contest_type = None
        if move_response['contest_type']:
            contest_type = move_response['contest_type']['name']
        stat_changes = []
        for change in move_response['stat_changes']:
            change_name = change['stat']['name']
            change_value = change['change']
            stat_changes.append({"name": change_name, "value": change_value})

        learned_by_ids = []
        for learned_by in move_response['learned_by_pokemon']:
            parts = learned_by['url'].split('/')
            pokemon_id = parts[-2]
            learned_by_ids.append(LearnedBy(id= uuid.uuid4(), pokemon_id=pokemon_id, move_id=id))
        move = Move(id=id, name=name, accuracy=accuracy, damage_class=damage_class, power=power, pp=pp, priority=priority, type_name=type_name, stat_changes=stat_changes, contest_type=contest_type)
        return move, learned_by_ids
