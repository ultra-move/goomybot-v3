class Odds:

    def __init__(self):
        self.shiny_rate = 1/2048
        self.random_shiny_rate = 1/4096
        
        self.event_shiny_rate = 1/64
        self.event_rate = 1/8

        self.tier1_rate = 1
        self.tier2_rate = 1/2
        self.tier3_rate = 1/4
        self.tier4_rate = 1/24

        self.tier1_pool_size = 336
        self.tier2_pool_size = 399
        self.tier3_pool_size = 185
        self.tier4_pool_size = 105

        #RAID ODDS#
        self.raid_shiny_rate = 1/100 
        self.raid_tier1_rate = 1
        self.raid_tier2_rate = 1/2
        self.raid_tier3_rate = 1/3
        self.raid_tier4_rate = 1/8

        self.raid_tier1_pool_size = 26
        self.raid_tier2_pool_size = 103
        self.raid_tier3_pool_size = 81
        self.raid_tier4_pool_size = 49


    def __str__(self):
        return (
                f"Random Shiny Rate: 1 in {1/self.random_shiny_rate:.0f}\n"
                f"\nBattle rates:\n"
                f"Shiny Rate: 1 in {1/self.shiny_rate:.0f}\n"
                f"Tier 1 Rate: {self.tier1_rate:.0%} (Pool Size: {self.tier1_pool_size})\n"
                f"Tier 2 Rate: {self.tier2_rate:.0%} (Pool Size: {self.tier2_pool_size})\n"
                f"Tier 3 Rate: {self.tier3_rate:.0%} (Pool Size: {self.tier3_pool_size})\n"
                f"Tier 4 Rate: {self.tier4_rate:.0%} (Pool Size: {self.tier4_pool_size})\n"
                f"\nRaid Rates:\n"
                f"Shiny Rate: 1 in {1/self.raid_shiny_rate:.0f}\n"
                f"Tier 1 Rate: {self.raid_tier1_rate:.0%} (Pool Size: {self.raid_tier1_pool_size})\n"
                f"Tier 2 Rate: {self.raid_tier2_rate:.0%} (Pool Size: {self.raid_tier2_pool_size})\n"
                f"Tier 3 Rate: {self.raid_tier3_rate:.0%} (Pool Size: {self.raid_tier3_pool_size})\n"
                f"Tier 4 Rate: {self.raid_tier4_rate:.0%} (Pool Size: {self.raid_tier4_pool_size})\n"
                f"\nEvent Rates:\n"
                f"Shiny Rate: 1 in {1/self.event_shiny_rate:.0f}\n"
                f"Encounter Rate: {self.event_rate:.0%}\n"
                )
