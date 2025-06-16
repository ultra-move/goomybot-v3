class Odds:

    def __init__(self):
        self.shiny_rate = 1/4096
        
        self.tier1_rate = 1
        self.tier2_rate = 1/2
        self.tier3_rate = 1/4
        self.tier4_rate = 1/100
        
        self.tier1_pool_size = 336
        self.tier2_pool_size = 399
        self.tier3_pool_size = 185
        self.tier4_pool_size = 105

    def __str__(self):
        return (
                f"Shiny Rate: 1 in {1/self.shiny_rate:.0f}\n"
                f"\n"
                f"Tier 1 Rate: {self.tier1_rate:.0%} (Pool Size: {self.tier1_pool_size})\n"
                f"Tier 2 Rate: {self.tier2_rate:.0%} (Pool Size: {self.tier2_pool_size})\n"
                f"Tier 3 Rate: {self.tier3_rate:.0%} (Pool Size: {self.tier3_pool_size})\n"
                f"Tier 4 Rate: {self.tier4_rate:.0%} (Pool Size: {self.tier4_pool_size})\n"
                )
