
from classes.pokemon import Pokemon


class Types:
    @staticmethod
    def check_effectiveness(pokemon: Pokemon):
        """
        Calculates the combined type effectiveness for a given Pokémon against all
        possible attacking types, considering the Pokémon's one or two types.

        Args:
            pokemon: An instance of the Pokemon class with a 'types' attribute
                     (list of strings).

        Returns:
            A dictionary containing four lists:
            - "no_effect": Types that have 0.0x effectiveness.
            - "normal": Types that have 1.0x effectiveness.
            - "super_effective": Types that have >1.0x effectiveness.
            - "not_very_effective": Types that have <1.0x and >0.0x effectiveness.
        """
        chart = Types.get_types()

        # Initialize a dictionary to store the cumulative effectiveness for each attacking type.
        # Start all attacking types at 1.0 (normal effectiveness).
        final_effectiveness = {
            attacking_type: 1.0 for attacking_type in chart.keys()
        }

        # Iterate through each of the Pokémon's types (usually one or two)
        for pokemon_type in pokemon.types:
            # Ensure the Pokémon's type exists in the chart
            if pokemon_type not in chart:
                print(f"Warning: Pokémon type '{pokemon_type}' not found in chart.")
                continue

            # Get the effectiveness multipliers for the current Pokémon type
            type_multipliers = chart[pokemon_type]

            # Multiply the current final effectiveness by the multipliers for this Pokémon type
            for attacking_type, multiplier in type_multipliers.items():
                if attacking_type in final_effectiveness:
                    final_effectiveness[attacking_type] *= multiplier
                else:
                    # If an attacking type is not in the initial final_effectiveness,
                    # it means it's a new type from the chart (shouldn't happen if chart is complete)
                    final_effectiveness[attacking_type] = multiplier


        # Now, categorize the attacking types based on their final effectiveness
        pokemon_no_effect = []
        pokemon_normal = []
        pokemon_super = []
        pokemon_not_very_effective = [] # Renamed from pokemon_weak for clarity

        for attacking_type, total_multiplier in final_effectiveness.items():
            if total_multiplier == 0.0:
                pokemon_no_effect.append(attacking_type)
            elif total_multiplier > 1.0:
                pokemon_super.append(attacking_type)
            elif total_multiplier < 1.0 and total_multiplier > 0.0:
                pokemon_not_very_effective.append(attacking_type)
            else: # total_multiplier == 1.0
                pokemon_normal.append(attacking_type)

        return {
            "no_effect": pokemon_no_effect,
            "normal": pokemon_normal,
            "super_effective": pokemon_super,
            "not_very_effective": pokemon_not_very_effective,
        }

    @staticmethod
    def get_types():
        """
        Returns the comprehensive Pokémon type effectiveness chart.
        The values represent the multiplier for damage from an attacking type
        against a defending type.
        e.g., chart["Fire"]["Grass"] = 2.0 means Fire attacks are 2x effective against Grass.
        """
        return {
            "Normal": {
                "Rock": 0.5, "Ghost": 0.0, "Steel": 0.5,
                "Normal": 1.0, "Fire": 1.0, "Water": 1.0, "Grass": 1.0,
                "Electric": 1.0, "Ice": 1.0, "Fighting": 1.0, "Poison": 1.0,
                "Ground": 1.0, "Flying": 1.0, "Psychic": 1.0, "Bug": 1.0,
                "Dragon": 1.0, "Dark": 1.0, "Fairy": 1.0,
            },
            "Fire": {
                "Grass": 2.0, "Ice": 2.0, "Bug": 2.0, "Steel": 2.0,
                "Fire": 0.5, "Water": 0.5, "Dragon": 0.5, "Rock": 0.5,
                "Normal": 1.0, "Electric": 1.0, "Fighting": 1.0, "Poison": 1.0,
                "Ground": 1.0, "Flying": 1.0, "Psychic": 1.0, "Ghost": 1.0,
                "Dark": 1.0, "Fairy": 1.0,
            },
            "Water": {
                "Fire": 2.0, "Ground": 2.0, "Rock": 2.0,
                "Water": 0.5, "Grass": 0.5, "Dragon": 0.5, "Electric": 0.5,
                "Normal": 1.0, "Ice": 1.0, "Fighting": 1.0, "Poison": 1.0,
                "Flying": 1.0, "Psychic": 1.0, "Bug": 1.0, "Ghost": 1.0,
                "Steel": 1.0, "Dark": 1.0, "Fairy": 1.0,
            },
            "Grass": {
                "Water": 2.0, "Ground": 2.0, "Rock": 2.0,
                "Fire": 0.5, "Grass": 0.5, "Poison": 0.5, "Flying": 0.5,
                "Bug": 0.5, "Dragon": 0.5, "Steel": 0.5,
                "Normal": 1.0, "Electric": 1.0, "Ice": 1.0, "Fighting": 1.0,
                "Psychic": 1.0, "Ghost": 1.0, "Dark": 1.0, "Fairy": 1.0,
            },
            "Electric": {
                "Water": 2.0, "Flying": 2.0,
                "Grass": 0.5, "Electric": 0.5, "Dragon": 0.5, "Ground": 0.0,
                "Normal": 1.0, "Fire": 1.0, "Ice": 1.0, "Fighting": 1.0,
                "Poison": 1.0, "Psychic": 1.0, "Bug": 1.0, "Rock": 1.0,
                "Ghost": 1.0, "Steel": 1.0, "Dark": 1.0, "Fairy": 1.0,
            },
            "Ice": {
                "Grass": 2.0, "Ground": 2.0, "Flying": 2.0, "Dragon": 2.0,
                "Fire": 0.5, "Water": 0.5, "Ice": 0.5, "Steel": 0.5,
                "Normal": 1.0, "Electric": 1.0, "Fighting": 1.0, "Poison": 1.0,
                "Psychic": 1.0, "Bug": 1.0, "Rock": 1.0, "Ghost": 1.0,
                "Dark": 1.0, "Fairy": 1.0,
            },
            "Fighting": {
                "Normal": 2.0, "Ice": 2.0, "Rock": 2.0, "Dark": 2.0, "Steel": 2.0,
                "Poison": 0.5, "Flying": 0.5, "Psychic": 0.5, "Bug": 0.5, "Fairy": 0.5,
                "Ghost": 0.0,
                "Normal": 1.0, "Fire": 1.0, "Water": 1.0, "Grass": 1.0,
                "Electric": 1.0, "Ground": 1.0, "Dragon": 1.0,
            },
            "Poison": {
                "Grass": 2.0, "Fairy": 2.0,
                "Poison": 0.5, "Ground": 0.5, "Rock": 0.5, "Ghost": 0.5,
                "Steel": 0.0,
                "Normal": 1.0, "Fire": 1.0, "Water": 1.0, "Electric": 1.0,
                "Ice": 1.0, "Fighting": 1.0, "Flying": 1.0, "Psychic": 1.0,
                "Bug": 1.0, "Dragon": 1.0, "Dark": 1.0,
            },
            "Ground": {
                "Fire": 2.0, "Electric": 2.0, "Poison": 2.0, "Rock": 2.0, "Steel": 2.0,
                "Grass": 0.5, "Bug": 0.5,
                "Flying": 0.0,
                "Normal": 1.0, "Water": 1.0, "Ice": 1.0, "Fighting": 1.0,
                "Ground": 1.0, "Psychic": 1.0, "Ghost": 1.0, "Dragon": 1.0,
                "Dark": 1.0, "Fairy": 1.0,
            },
            "Flying": {
                "Grass": 2.0, "Fighting": 2.0, "Bug": 2.0,
                "Electric": 0.5, "Rock": 0.5, "Steel": 0.5,
                "Normal": 1.0, "Fire": 1.0, "Water": 1.0, "Ice": 1.0,
                "Poison": 1.0, "Ground": 1.0, "Flying": 1.0, "Psychic": 1.0,
                "Ghost": 1.0, "Dragon": 1.0, "Dark": 1.0, "Fairy": 1.0,
            },
            "Psychic": {
                "Fighting": 2.0, "Poison": 2.0,
                "Psychic": 0.5, "Steel": 0.5,
                "Dark": 0.0,
                "Normal": 1.0, "Fire": 1.0, "Water": 1.0, "Grass": 1.0,
                "Electric": 1.0, "Ice": 1.0, "Ground": 1.0, "Flying": 1.0,
                "Bug": 1.0, "Rock": 1.0, "Ghost": 1.0, "Dragon": 1.0,
                "Fairy": 1.0,
            },
            "Bug": {
                "Grass": 2.0, "Psychic": 2.0, "Dark": 2.0,
                "Fire": 0.5, "Fighting": 0.5, "Flying": 0.5, "Ghost": 0.5,
                "Poison": 0.5, "Steel": 0.5, "Fairy": 0.5,
                "Normal": 1.0, "Water": 1.0, "Electric": 1.0, "Ice": 1.0,
                "Ground": 1.0, "Bug": 1.0, "Rock": 1.0, "Dragon": 1.0,
            },
            "Rock": {
                "Fire": 2.0, "Ice": 2.0, "Flying": 2.0, "Bug": 2.0,
                "Fighting": 0.5, "Ground": 0.5, "Steel": 0.5,
                "Normal": 1.0, "Water": 1.0, "Grass": 1.0, "Electric": 1.0,
                "Poison": 1.0, "Psychic": 1.0, "Rock": 1.0, "Ghost": 1.0,
                "Dragon": 1.0, "Dark": 1.0, "Fairy": 1.0,
            },
            "Ghost": {
                "Psychic": 2.0, "Ghost": 2.0,
                "Normal": 0.0, "Fighting": 0.0,
                "Dark": 0.5,
                "Normal": 1.0, "Fire": 1.0, "Water": 1.0, "Grass": 1.0,
                "Electric": 1.0, "Ice": 1.0, "Poison": 1.0, "Ground": 1.0,
                "Flying": 1.0, "Bug": 1.0, "Rock": 1.0, "Dragon": 1.0,
                "Steel": 1.0, "Fairy": 1.0,
            },
            "Dragon": {
                "Dragon": 2.0,
                "Steel": 0.5,
                "Fairy": 0.0,
                "Normal": 1.0, "Fire": 1.0, "Water": 1.0, "Grass": 1.0,
                "Electric": 1.0, "Ice": 1.0, "Fighting": 1.0, "Poison": 1.0,
                "Ground": 1.0, "Flying": 1.0, "Psychic": 1.0, "Bug": 1.0,
                "Rock": 1.0, "Ghost": 1.0, "Dark": 1.0,
            },
            "Steel": {
                "Ice": 2.0, "Rock": 2.0, "Fairy": 2.0,
                "Fire": 0.5, "Water": 0.5, "Electric": 0.5, "Steel": 0.5,
                "Normal": 1.0, "Grass": 1.0, "Fighting": 1.0, "Poison": 1.0,
                "Ground": 1.0, "Flying": 1.0, "Psychic": 1.0, "Bug": 1.0,
                "Ghost": 1.0, "Dragon": 1.0, "Dark": 1.0,
            },
            "Dark": {
                "Psychic": 2.0, "Ghost": 2.0,
                "Fighting": 0.5, "Dark": 0.5, "Fairy": 0.5,
                "Normal": 1.0, "Fire": 1.0, "Water": 1.0, "Grass": 1.0,
                "Electric": 1.0, "Ice": 1.0, "Poison": 1.0, "Ground": 1.0,
                "Flying": 1.0, "Bug": 1.0, "Rock": 1.0, "Dragon": 1.0,
                "Steel": 1.0,
            },
            "Fairy": {
                "Fighting": 2.0, "Dragon": 2.0, "Dark": 2.0,
                "Fire": 0.5, "Poison": 0.5, "Steel": 0.5,
                "Normal": 1.0, "Water": 1.0, "Grass": 1.0, "Electric": 1.0,
                "Ice": 1.0, "Ground": 1.0, "Flying": 1.0, "Psychic": 1.0,
                "Bug": 1.0, "Rock": 1.0, "Ghost": 1.0, "Fairy": 1.0,
            },
        }
