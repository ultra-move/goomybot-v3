import requests
import json
from classes.pokemon_master import PokemonMaster
import time

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
            elif base_experience >= 200:
                tier = 3
            elif base_experience < 200 and base_experience >= 100:
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
    

    """
    result = data_loader.get_all_pokemon()

    for entry in result:
       await storage_manager.save_object(obj=entry, cache_key=f"pokemon_master:{entry.id}", table_name="pokemon_master", unique_columns=['id'])

    """