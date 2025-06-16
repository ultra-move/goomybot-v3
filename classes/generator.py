import math
import random
import os
from classes.odds import Odds

class Generator:
    def __init__(self, tier_seed: float, type_seed: float, pokemon_seed: float, shiny_seed: float, item_seed: float):
        self.odds = Odds()
        
        # Store the original integer seeds derived from the float seeds
        # This is crucial for deterministic re-seeding per frame.
        # Multiply by a large number to ensure diverse integer seeds from floats.
        self.original_tier_int_seed = int(tier_seed * 1_000_000_000)
        self.original_type_int_seed = int(type_seed * 1_000_000_000)
        self.original_pokemon_int_seed = int(pokemon_seed * 1_000_000_000)
        self.original_shiny_int_seed = int(shiny_seed * 1_000_000_000)
        self.original_item_int_seed = int(item_seed * 1_000_000_000)

        # Initialize RNGs with their original seeds (though they will be re-seeded per frame)
        self.tier_rng = random.Random(self.original_tier_int_seed)
        self.type_rng = random.Random(self.original_type_int_seed)
        self.pokemon_rng = random.Random(self.original_pokemon_int_seed)
        self.shiny_rng = random.Random(self.original_shiny_int_seed)
        self.item_rng = random.Random(self.original_item_int_seed)

        self.tier_1_ids = [1, 4, 7, 10, 11, 13, 14, 16, 19, 21, 23, 27, 29, 32, 37, 39, 41, 43, 46, 48, 50, 52, 54, 56, 58, 60, 63, 66, 69, 72, 74, 77, 79, 81, 84, 86, 88, 90, 92, 95, 96, 98, 100, 102, 104, 108, 109, 111, 114, 116, 118, 120, 129, 133, 137, 138, 140, 147, 152, 155, 158, 161, 163, 165, 167, 170, 172, 173, 174, 175, 177, 179, 183, 187, 190, 191, 193, 194, 198, 200, 204, 207, 209, 211, 215, 216, 218, 220, 223, 228, 231, 235, 236, 238, 239, 240, 246, 252, 255, 258, 261, 263, 265, 266, 268, 270, 273, 276, 278, 280, 281, 283, 285, 287, 290, 292, 293, 296, 298, 299, 300, 304, 307, 309, 316, 318, 320, 322, 325, 328, 331, 333, 339, 341, 343, 345, 347, 349, 353, 355, 360, 361, 363, 366, 371, 374, 387, 390, 393, 396, 399, 401, 403, 406, 408, 410, 412, 415, 418, 420, 422, 425, 427, 431, 433, 434, 436, 438, 439, 443, 446, 447, 449, 451, 453, 456, 458, 459, 495, 498, 501, 504, 506, 509, 511, 513, 515, 517, 519, 522, 524, 527, 529, 532, 535, 540, 543, 546, 548, 551, 554, 557, 559, 562, 564, 566, 568, 570, 572, 574, 577, 580, 582, 585, 588, 590, 592, 595, 597, 599, 602, 605, 607, 610, 613, 616, 619, 622, 624, 627, 629, 633, 636, 650, 653, 656, 659, 661, 664, 665, 667, 669, 672, 674, 677, 679, 682, 684, 686, 688, 690, 692, 694, 696, 698, 704, 708, 710, 712, 714, 722, 725, 728, 731, 734, 736, 739, 742, 744, 746, 747, 749, 751, 753, 755, 757, 759, 761, 767, 769, 782, 810, 813, 816, 819, 821, 824, 827, 829, 833, 835, 837, 840, 843, 846, 848, 850, 852, 854, 856, 859, 868, 872, 878, 885, 906, 909, 912, 915, 917, 919, 921, 924, 926, 928, 932, 935, 938, 940, 942, 944, 946, 948, 951, 953, 955, 957, 960, 963, 965, 969, 971, 974, 996, 999, 1012]
        self.tier_2_ids = [2, 5, 8, 12, 15, 17, 20, 22, 24, 25, 28, 30, 33, 35, 38, 40, 42, 44, 47, 49, 51, 53, 55, 57, 59, 61, 64, 67, 70, 73, 75, 78, 80, 82, 83, 85, 87, 89, 91, 93, 97, 99, 101, 103, 105, 106, 107, 110, 112, 115, 117, 119, 121, 122, 123, 124, 125, 126, 127, 128, 130, 131, 132, 134, 135, 136, 139, 141, 142, 143, 148, 153, 156, 159, 162, 164, 166, 168, 171, 176, 178, 180, 184, 185, 188, 192, 195, 196, 197, 199, 201, 202, 203, 205, 206, 208, 210, 212, 213, 214, 217, 219, 221, 222, 224, 225, 226, 227, 229, 232, 233, 234, 237, 241, 247, 253, 256, 259, 262, 264, 267, 269, 271, 274, 277, 279, 284, 286, 288, 291, 294, 297, 301, 302, 303, 305, 308, 310, 311, 312, 313, 314, 315, 317, 319, 321, 323, 324, 326, 327, 329, 332, 334, 335, 336, 337, 338, 340, 342, 344, 346, 348, 350, 351, 352, 354, 356, 357, 358, 359, 362, 364, 367, 368, 369, 370, 372, 375, 388, 391, 394, 397, 400, 402, 404, 409, 411, 413, 414, 416, 417, 419, 421, 423, 424, 426, 428, 429, 430, 432, 435, 437, 440, 441, 442, 444, 448, 450, 452, 454, 455, 457, 460, 461, 463, 465, 469, 470, 471, 472, 476, 478, 479, 496, 499, 502, 505, 507, 510, 512, 514, 516, 518, 520, 523, 525, 528, 530, 533, 536, 538, 539, 541, 544, 547, 549, 550, 552, 555, 556, 558, 560, 561, 563, 565, 567, 569, 571, 573, 575, 578, 581, 583, 586, 587, 589, 591, 593, 594, 596, 598, 600, 603, 606, 608, 611, 614, 615, 617, 618, 620, 621, 623, 625, 626, 628, 630, 631, 632, 634, 651, 654, 657, 660, 662, 663, 666, 668, 670, 673, 675, 676, 678, 680, 683, 685, 687, 689, 691, 693, 695, 697, 699, 700, 701, 702, 703, 705, 707, 709, 711, 713, 715, 723, 726, 729, 732, 735, 737, 740, 741, 743, 745, 748, 750, 752, 754, 756, 758, 760, 762, 764, 765, 766, 768, 770, 771, 774, 775, 776, 777, 778, 779, 780, 781, 783, 803, 811, 814, 817, 820, 822, 825, 828, 830, 831, 832, 834, 836, 838, 841, 842, 844, 845, 847, 849, 851, 853, 855, 857, 860, 863, 864, 865, 866, 867, 869, 870, 871, 873, 874, 875, 876, 877, 879, 880, 881, 882, 883, 884, 886, 900, 903, 904, 907, 910, 913, 916, 918, 920, 922, 925, 927, 929, 931, 933, 939, 941, 943, 945, 947, 949, 950, 952, 954, 956, 958, 961, 964, 966, 967, 970, 972, 973, 975, 976, 978, 980, 982, 997, 1011, 1013]
        self.tier_3_ids = [3, 6, 9, 18, 26, 31, 34, 36, 45, 62, 65, 68, 71, 76, 94, 113, 149, 154, 157, 160, 169, 181, 182, 186, 189, 230, 242, 248, 254, 257, 260, 272, 275, 282, 289, 295, 306, 330, 365, 373, 376, 389, 392, 395, 398, 405, 407, 445, 462, 464, 466, 467, 468, 473, 474, 475, 477, 497, 500, 503, 508, 521, 526, 531, 534, 537, 542, 545, 553, 576, 579, 584, 601, 604, 609, 612, 635, 637, 652, 655, 658, 671, 681, 706, 724, 727, 730, 733, 738, 763, 784, 793, 794, 795, 796, 797, 798, 799, 804, 805, 806, 812, 815, 818, 823, 826, 839, 858, 861, 862, 887, 899, 901, 902, 908, 911, 914, 923, 930, 934, 936, 937, 959, 962, 968, 977, 979, 981, 983, 984, 985, 986, 987, 988, 989, 990, 991, 992, 993, 994, 995, 998, 1000, 1005, 1006, 1009, 1010, 1018, 1019, 1020, 1021, 1022, 1023]
        self.tier_4_ids = [144, 145, 146, 150, 151, 243, 244, 245, 249, 250, 251, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 638, 639, 640, 641, 642, 643, 644, 645, 646, 647, 648, 649, 716, 717, 718, 719, 720, 721, 772, 773, 785, 786, 787, 788, 789, 790, 791, 792, 800, 801, 802, 807, 808, 809, 888, 889, 890, 891, 892, 893, 894, 895, 896, 897, 898, 905, 1001, 1002, 1003, 1004, 1007, 1008, 1014, 1015, 1016, 1017, 1024, 1025]



    def get_outcome_for_frame(self, frame: int):
        # The key to determinism per frame:
        # Re-seed each RNG for *every frame* using a combination of its original, immutable seed
        # and the current frame number. This ensures that the sequence of "random"
        # numbers generated for a specific type of roll (e.g., tier) at a specific frame
        # is always the same, regardless of previous calls to this method or different Python runs.

        # We combine the original integer seed with the frame number using a simple sum.
        # This is deterministic across all Python runs and for all frame numbers.
        tier_frame_seed = self.original_tier_int_seed + int(frame)
        self.tier_rng.seed(tier_frame_seed)

        shiny_frame_seed = self.original_shiny_int_seed + int(frame)
        self.shiny_rng.seed(shiny_frame_seed)

        pokemon_frame_seed = self.original_pokemon_int_seed + int(frame)
        self.pokemon_rng.seed(pokemon_frame_seed)
        
        # Also re-seed type_rng and item_rng, even if not used in this specific outcome calculation
        type_frame_seed = self.original_type_int_seed + int(frame)
        self.type_rng.seed(type_frame_seed)

        item_frame_seed = self.original_item_int_seed + int(frame)
        self.item_rng.seed(item_frame_seed)


        # 1. Determine Tier
        tier_roll = self.tier_rng.random() # Uses the re-seeded RNG
        tier_sum_of_rates = self.odds.tier1_rate + self.odds.tier2_rate + self.odds.tier3_rate + self.odds.tier4_rate
        
        normalized_tier1_cutoff = self.odds.tier1_rate / tier_sum_of_rates
        normalized_tier2_cutoff = (self.odds.tier1_rate + self.odds.tier2_rate) / tier_sum_of_rates
        normalized_tier3_cutoff = (self.odds.tier1_rate + self.odds.tier2_rate + self.odds.tier3_rate) / tier_sum_of_rates
        
        chosen_tier = None
        tier_pool_size = 0
        chosen_pokemon_index = 0 # Initialize to avoid UnboundLocalError
        pokemon_id = None # Initialize to avoid UnboundLocalError

        if tier_roll < normalized_tier1_cutoff:
            chosen_tier = 1
            tier_pool_size = self.odds.tier1_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.tier_1_ids[chosen_pokemon_index]
        elif tier_roll < normalized_tier2_cutoff:
            chosen_tier = 2
            tier_pool_size = self.odds.tier2_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.tier_2_ids[chosen_pokemon_index]
        elif tier_roll < normalized_tier3_cutoff:
            chosen_tier = 3
            tier_pool_size = self.odds.tier3_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.tier_3_ids[chosen_pokemon_index]
        else:
            chosen_tier = 4
            tier_pool_size = self.odds.tier4_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.tier_4_ids[chosen_pokemon_index]

        # 2. Determine Shininess
        shiny_roll = self.shiny_rng.random() # Uses the re-seeded RNG
        is_shiny = shiny_roll < self.odds.shiny_rate
        
        return {
            "frame": frame,
            "tier": chosen_tier,
            "is_shiny": is_shiny,
            "pokemon_index_in_tier": chosen_pokemon_index,
            "tier_pool_size": tier_pool_size,
            "pokemon_id": pokemon_id
        }
    
    def find_shiny_frame(self, start_frame: int = 0, max_frames_to_check: int = 100000):
        """
        Searches for a frame number that would result in a shiny Pokémon.
        This iterates through frames and checks the shiny outcome for each.

        Args:
            start_frame (int): The frame number to start searching from.
            max_frames_to_check (int): The maximum number of frames to check.

        Returns:
            int or None: The first frame number found that yields a shiny Pokémon,
                         or None if no such frame is found within the specified range.
        """
        print(f"Searching for a shiny frame between {start_frame} and {start_frame + max_frames_to_check - 1}...")
        for frame in range(start_frame, start_frame + max_frames_to_check):
            # Re-seed the shiny RNG specifically for this frame check
            shiny_frame_seed = self.original_shiny_int_seed + int(frame)
            self.shiny_rng.seed(shiny_frame_seed)
            
            shiny_roll = self.shiny_rng.random()
            if shiny_roll < self.odds.shiny_rate:
                print(f"Found shiny frame: {frame} (Shiny roll: {shiny_roll:.4f} < Shiny rate: {self.odds.shiny_rate})")
                return frame
        print(f"No shiny frame found within {max_frames_to_check} frames starting from {start_frame}.")
        return None