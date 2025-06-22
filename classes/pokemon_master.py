import json

class PokemonMaster:
    def __init__(self, id, name, base_experience, height, weight, is_default, abilities_names, held_items_names, types_names, front_default_sprite, back_default_sprite, back_shiny_sprite, front_shiny_sprite, official_artwork_front_default_sprite, official_artwork_front_shiny_sprite, base_stats_json, species_color_name, evolves_from_species_name, evolves_from_species_url, flavor_text_entry, generation_name, growth_rate_name, is_legendary, is_mythical, shape_name, region, tier):
        self.id = id
        self.name = name
        self.base_experience = base_experience
        self.height = height
        self.weight = weight
        self.is_default = is_default
        self.abilities_names = abilities_names
        self.held_items_names = held_items_names
        self.types_names = types_names
        self.front_default_sprite = front_default_sprite
        self.back_default_sprite = back_default_sprite
        self.back_shiny_sprite = back_shiny_sprite
        self.front_shiny_sprite = front_shiny_sprite
        self.official_artwork_front_default_sprite = official_artwork_front_default_sprite
        self.official_artwork_front_shiny_sprite = official_artwork_front_shiny_sprite
        self.base_stats_json = base_stats_json
        self.species_color_name = species_color_name
        self.evolves_from_species_name = evolves_from_species_name
        self.evolves_from_species_url = evolves_from_species_url
        self.flavor_text_entry = flavor_text_entry
        self.generation_name = generation_name
        self.growth_rate_name = growth_rate_name
        self.is_legendary = is_legendary
        self.is_mythical = is_mythical
        self.shape_name = shape_name
        self.region = region
        self.tier = tier

    def __str__(self):
        return (
            f"ID: {self.id}\n"
            f"Name: {self.name}\n"
            f"Tier: {self.tier}\n"
            f"Growth Rate: {self.growth_rate_name}\n"
        )

    def to_dict(self):
        # Serialize lists and dictionaries to JSON strings for database storage
        return {
            "id": self.id,
            "name": self.name,
            "base_experience": self.base_experience,
            "height": self.height,
            "weight": self.weight,
            "is_default": self.is_default,
            "abilities_names": json.dumps(self.abilities_names),
            "held_items_names": json.dumps(self.held_items_names),
            "types_names": json.dumps(self.types_names),
            "front_default_sprite": self.front_default_sprite,
            "back_default_sprite": self.back_default_sprite,
            "back_shiny_sprite": self.back_shiny_sprite,
            "front_shiny_sprite": self.front_shiny_sprite,
            "official_artwork_front_default_sprite": self.official_artwork_front_default_sprite,
            "official_artwork_front_shiny_sprite": self.official_artwork_front_shiny_sprite,
            "base_stats_json": json.dumps(self.base_stats_json),
            "species_color_name": self.species_color_name,
            "evolves_from_species_name": self.evolves_from_species_name,
            "evolves_from_species_url": self.evolves_from_species_url,
            "flavor_text_entry": self.flavor_text_entry,
            "generation_name": self.generation_name,
            "growth_rate_name": self.growth_rate_name,
            "is_legendary": self.is_legendary,
            "is_mythical": self.is_mythical,
            "shape_name": self.shape_name,
            "region": self.region,
            "tier": self.tier
        }

    @staticmethod
    def from_dict(data):
        """
        Creates a PokemonMaster object from a dictionary.

        Args:
            data (dict): A dictionary containing Pokemon data.
                         Keys should match the constructor arguments.
                         Assumes JSON string fields are parsed back to Python objects.

        Returns:
            PokemonMaster: A new PokemonMaster object.
        """
        # Helper function to safely load JSON or return the value directly
        def load_json_if_str(value, default_value):
            if isinstance(value, (str, bytes, bytearray)):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    # Handle cases where the string might not be valid JSON
                    return default_value
            elif value is None:
                return default_value
            else:
                return value # Already a list or dict

        return PokemonMaster(
            id=data.get("id"),
            name=data.get("name"),
            base_experience=data.get("base_experience"),
            height=data.get("height"),
            weight=data.get("weight"),
            is_default=data.get("is_default"),
            abilities_names=load_json_if_str(data.get("abilities_names"), []),
            held_items_names=load_json_if_str(data.get("held_items_names"), []),
            types_names=load_json_if_str(data.get("types_names"), []),
            front_default_sprite=data.get("front_default_sprite"),
            back_default_sprite=data.get("back_default_sprite"),
            back_shiny_sprite=data.get("back_shiny_sprite"),
            front_shiny_sprite=data.get("front_shiny_sprite"),
            official_artwork_front_default_sprite=data.get("official_artwork_front_default_sprite"),
            official_artwork_front_shiny_sprite=data.get("official_artwork_front_shiny_sprite"),
            base_stats_json=load_json_if_str(data.get("base_stats_json"), {}),
            species_color_name=data.get("species_color_name"),
            evolves_from_species_name=data.get("evolves_from_species_name"),
            evolves_from_species_url=data.get("evolves_from_species_url"),
            flavor_text_entry=data.get("flavor_text_entry"),
            generation_name=data.get("generation_name"),
            growth_rate_name=data.get("growth_rate_name"),
            is_legendary=data.get("is_legendary"),
            is_mythical=data.get("is_mythical"),
            shape_name=data.get("shape_name"),
            region=data.get("region"),
            tier = int(data.get("tier"))
        )