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
        self.tier_2_ids = [2, 5, 8, 12, 15, 17, 20, 22, 24, 25, 28, 30, 33, 35, 38, 42, 44, 47, 49, 51, 53, 55, 57, 61, 64, 67, 70, 75, 78, 80, 82, 83, 85, 87, 89, 93, 97, 99, 101, 105, 106, 107, 110, 112, 115, 117, 119, 122, 123, 124, 125, 126, 127, 128, 132, 139, 141, 148, 153, 156, 159, 162, 164, 166, 168, 171, 176, 178, 180, 185, 188, 192, 195, 199, 201, 202, 203, 205, 206, 208, 210, 212, 213, 214, 217, 219, 221, 222, 224, 225, 226, 227, 229, 232, 234, 237, 241, 247, 253, 256, 259, 262, 264, 267, 269, 271, 274, 277, 279, 284, 286, 288, 291, 294, 297, 301, 302, 303, 305, 308, 310, 311, 312, 313, 314, 315, 317, 319, 321, 323, 324, 326, 327, 329, 332, 334, 335, 336, 337, 338, 340, 342, 344, 346, 348, 351, 352, 354, 356, 357, 358, 359, 362, 364, 367, 368, 369, 370, 372, 375, 388, 391, 394, 397, 400, 402, 404, 409, 411, 413, 414, 416, 417, 419, 421, 423, 424, 426, 428, 429, 430, 432, 435, 437, 440, 441, 442, 444, 452, 454, 455, 457, 460, 461, 472, 478, 479, 496, 499, 502, 505, 507, 510, 512, 514, 516, 518, 520, 523, 525, 528, 530, 533, 536, 538, 539, 541, 544, 547, 549, 550, 552, 555, 556, 558, 560, 561, 563, 565, 567, 569, 571, 573, 575, 578, 581, 583, 586, 587, 589, 591, 593, 594, 596, 598, 600, 603, 606, 608, 611, 614, 617, 618, 620, 621, 623, 625, 626, 628, 630, 631, 632, 634, 651, 654, 657, 660, 662, 663, 668, 670, 675, 676, 678, 680, 683, 685, 687, 689, 691, 693, 695, 699, 701, 702, 703, 705, 707, 709, 711, 723, 726, 729, 732, 735, 737, 740, 741, 743, 745, 748, 750, 752, 754, 756, 758, 760, 762, 764, 765, 766, 770, 771, 774, 775, 776, 777, 778, 779, 780, 783, 811, 814, 817, 820, 822, 825, 828, 830, 831, 832, 834, 836, 838, 841, 842, 844, 845, 847, 849, 853, 855, 857, 860, 863, 864, 865, 867, 869, 870, 871, 873, 874, 875, 876, 877, 879, 880, 881, 882, 883, 886, 900, 903, 904, 907, 910, 913, 916, 918, 920, 922, 925, 927, 929, 931, 933, 939, 941, 943, 945, 947, 950, 952, 954, 956, 958, 961, 964, 966, 967, 972, 973, 976, 978, 980, 997, 1011, 1013]
        self.tier_3_ids = [6, 3, 9, 26, 31, 40, 59, 68, 76, 94, 103, 113, 130, 136, 149, 157, 181, 186, 196, 230, 242, 248, 257, 275, 282, 295, 306, 330, 350, 365, 373, 389, 392, 407, 445, 462, 470, 497, 500, 666, 521, 908, 526, 537, 545, 553, 576, 584, 601, 609, 700, 635, 652, 658, 671, 673, 681, 697, 706, 713, 724, 733, 763, 781, 815, 826, 839, 851, 861, 884, 887, 899, 914, 930, 937, 949, 962, 975, 990, 1005, 1018, 992, 34, 36, 45, 62, 73, 131, 134, 142, 143, 154, 160, 182, 901, 189, 197, 233, 260, 289, 376, 395, 398, 448, 463, 464, 465, 466, 467, 468, 471, 473, 474, 475, 476, 477, 503, 531, 542, 986, 987, 579, 604, 612, 615, 655, 988, 715, 727, 730, 738, 784, 812, 818, 858, 862, 866, 902, 934, 968, 970, 977, 979, 981, 982, 983, 984, 985, 991, 993, 994, 995, 998, 1000, 1006, 1010, 1019, 1020, 1021, 1022, 1023, 18, 65, 71, 91, 121, 135, 169, 184, 254, 272, 923, 405, 450, 936, 469, 508, 534, 637, 768, 823, 911, 959, 989, 1009]
        self.tier_4_ids = [794, 798, 799, 803, 806, 796, 804, 905, 144, 146, 150, 151, 243, 245, 249, 250, 251, 377, 378, 379, 381, 382, 383, 385, 386, 480, 481, 482, 483, 484, 485, 486, 487, 489, 490, 491, 492, 493, 494, 638, 639, 640, 641, 642, 643, 644, 645, 646, 648, 649, 716, 717, 718, 719, 720, 721, 772, 773, 785, 793, 787, 788, 789, 791, 792, 797, 800, 801, 802, 805, 807, 808, 809, 888, 889, 890, 891, 892, 893, 894, 896, 897, 898, 1002, 1003, 1004, 1007, 1008, 1015, 1016, 1017, 1024, 1025, 145, 244, 380, 384, 488, 647, 786, 790, 895, 1001, 1014, 795]

        self.event_ids = [704]

        self.raid_tier_1_ids = [10029, 10027, 10028, 10091, 10101, 10103, 10105, 10107, 10109, 10112, 10231, 10151, 10161, 10162, 10164, 10174, 10176, 10179, 10200, 10205, 10229, 10234, 10235, 10238, 10253, 10263]
        self.raid_tier_2_ids = [10004, 10005, 10013, 10014, 10015, 10016, 10030, 10025, 10031, 10032, 10052, 10054, 10066, 10080, 10081, 10082, 10083, 10084, 10085, 10092, 10093, 10094, 10095, 10096, 10097, 10098, 10099, 10102, 10104, 10106, 10108, 10110, 10113, 10115, 10121, 10123, 10124, 10125, 10126, 10130, 10131, 10132, 10133, 10134, 10135, 10136, 10137, 10138, 10139, 10140, 10141, 10142, 10143, 10144, 10145, 10148, 10149, 10150, 10152, 10160, 10163, 10165, 10166, 10167, 10168, 10232, 10172, 10173, 10175, 10177, 10180, 10184, 10185, 10186, 10187, 10198, 10199, 10203, 10207, 10214, 10216, 10217, 10218, 10219, 10223, 10224, 10228, 10237, 10239, 10240, 10241, 10247, 10250, 10251, 10252, 10254, 10256, 10257, 10258, 10259, 10260, 10261, 10262]
        self.raid_tier_3_ids = [10008, 10009, 10010, 10011, 10012, 10017, 10026, 10033, 10034, 10035, 10036, 10037, 10038, 10039, 10040, 10041, 10042, 10045, 10046, 10047, 10048, 10049, 10050, 10051, 10053, 10055, 10056, 10057, 10058, 10059, 10060, 10061, 10064, 10065, 10067, 10068, 10069, 10070, 10071, 10072, 10073, 10074, 10076, 10087, 10088, 10089, 10090, 10100, 10111, 10114, 10116, 10117, 10122, 10127, 10178, 10195, 10196, 10197, 10201, 10202, 10204, 10206, 10209, 10210, 10211, 10212, 10213, 10215, 10220, 10221, 10222, 10225, 10230, 10233, 10236, 10242, 10243, 10244, 10248, 10255, 10272]
        self.raid_tier_4_ids = [10001, 10002, 10003, 10006, 10007, 10018, 10019, 10020, 10021, 10022, 10023, 10024, 10043, 10044, 10075, 10062, 10063, 10077, 10078, 10079, 10086, 10118, 10119, 10120, 10147, 10155, 10156, 10157, 10169, 10170, 10171, 10188, 10189, 10190, 10191, 10192, 10193, 10194, 10276, 10208, 10226, 10227, 10277, 10245, 10246, 10249, 10273, 10274, 10275]



    def get_outcome_for_frame(self, frame: int, user):
        # === Reseed RNGs deterministically per frame ===
        self.tier_rng.seed(self.original_tier_int_seed + frame)
        self.shiny_rng.seed(self.original_shiny_int_seed + frame)
        self.pokemon_rng.seed(self.original_pokemon_int_seed + frame)
        self.type_rng.seed(self.original_type_int_seed + frame)
        self.item_rng.seed(self.original_item_int_seed + frame)

        # === 1) Determine Tier ===
        tier_roll = self.tier_rng.random()
        tier_sum = self.odds.tier1_rate + self.odds.tier2_rate + self.odds.tier3_rate + self.odds.tier4_rate

        t1 = self.odds.tier1_rate / tier_sum
        t2 = (self.odds.tier1_rate + self.odds.tier2_rate) / tier_sum
        t3 = (self.odds.tier1_rate + self.odds.tier2_rate + self.odds.tier3_rate) / tier_sum

        if tier_roll < t1:
            chosen_tier = 1
            pool_size = self.odds.tier1_pool_size
            tier_pool = self.tier_1_ids
        elif tier_roll < t2:
            chosen_tier = 2
            pool_size = self.odds.tier2_pool_size
            tier_pool = self.tier_2_ids
        elif tier_roll < t3:
            chosen_tier = 3
            pool_size = self.odds.tier3_pool_size
            tier_pool = self.tier_3_ids
        else:
            chosen_tier = 4
            pool_size = self.odds.tier4_pool_size
            tier_pool = self.tier_4_ids

        # === 2) Pick Pokémon using fixed pool size ===
        pokemon_index_roll = self.pokemon_rng.random()
        pokemon_index = math.floor(pokemon_index_roll * pool_size)
        pokemon_index = max(0, min(pokemon_index, pool_size - 1))
        # Map index to actual list with modulus to avoid index errors if list is smaller than pool_size
        pokemon_id = tier_pool[pokemon_index % len(tier_pool)]

        # === 3) Determine Shininess ===
        shiny_rate = self.odds.shiny_rate
        shiny_roll = self.shiny_rng.random()
        is_shiny = (shiny_roll < shiny_rate)

        event = False
        # === 4) Attempt event override if NOT shiny ===
        if not is_shiny and user.event  and chosen_tier != 4:
            if  self.item_rng.random() < self.odds.event_rate:
                event = True
                shiny_rate = self.odds.event_shiny_rate
                is_shiny = (shiny_roll < shiny_rate)
                pokemon_id = self.tier_rng.choice(self.event_ids)

        # === 5) Pack result ===
        result = {
            "frame": frame,
            "tier": chosen_tier,
            "is_shiny": is_shiny,
            "pokemon_index_in_tier": pokemon_index,
            "tier_pool_size": pool_size,
            "pokemon_id": pokemon_id,
            "event": event
        }
        return result

    
    def find_shiny_frame(self, user, start_frame: int = 0, max_frames_to_check: int = 100000):
        """
        Searches for a frame number that would result in a shiny Pokémon.
        This iterates through frames and checks the shiny outcome for each.

        Args:
            user: The user object, containing 'event' status.
            start_frame (int): The frame number to start searching from.
            max_frames_to_check (int): The maximum number of frames to check.

        Returns:
            int or None: The first frame number found that yields a shiny Pokémon,
                        or None if no such frame is found within the specified range.
        """
        #print(f"Searching for a non-event shiny frame between {start_frame} and {start_frame + max_frames_to_check - 1}...")
        for frame in range(start_frame, start_frame + max_frames_to_check):
           result = self.get_outcome_for_frame(frame = frame, user = user)
           if result['event']: 
               continue
           elif result['is_shiny']:
               print(result)
               return frame                
        return None

    def find_event_shiny_frame(self, user, start_frame: int = 0, max_frames_to_check: int = 100000):
        """
        Searches for a frame number that would result in a shiny Pokémon.
        This iterates through frames and checks the shiny outcome for each.

        Args:
            user: The user object, containing 'event' status.
            start_frame (int): The frame number to start searching from.
            max_frames_to_check (int): The maximum number of frames to check.

        Returns:
            int or None: The first frame number found that yields a shiny Pokémon,
                        or None if no such frame is found within the specified range.
        """
        #print(f"Searching for a non-event shiny frame between {start_frame} and {start_frame + max_frames_to_check - 1}...")
        for frame in range(start_frame, start_frame + max_frames_to_check):
           result = self.get_outcome_for_frame(frame = frame, user = user)
           if result['event'] and result['is_shiny']:
               print(result)
               return frame        
        return None
    
    def get_outcome_for_raid_frame(self, frame: int):
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
        tier_sum_of_rates = self.odds.raid_tier1_rate + self.odds.raid_tier2_rate + self.odds.raid_tier3_rate + self.odds.raid_tier4_rate
        
        normalized_tier1_cutoff = self.odds.raid_tier1_rate / tier_sum_of_rates
        normalized_tier2_cutoff = (self.odds.raid_tier1_rate + self.odds.raid_tier2_rate) / tier_sum_of_rates
        normalized_tier3_cutoff = (self.odds.raid_tier1_rate + self.odds.raid_tier2_rate + self.odds.raid_tier3_rate) / tier_sum_of_rates
        
        chosen_tier = None
        tier_pool_size = 0
        chosen_pokemon_index = 0 # Initialize to avoid UnboundLocalError
        pokemon_id = None # Initialize to avoid UnboundLocalError

        if tier_roll < normalized_tier1_cutoff:
            chosen_tier = 1
            tier_pool_size = self.odds.raid_tier1_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.raid_tier_1_ids[chosen_pokemon_index]
        elif tier_roll < normalized_tier2_cutoff:
            chosen_tier = 2
            tier_pool_size = self.odds.raid_tier2_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.raid_tier_2_ids[chosen_pokemon_index]
        elif tier_roll < normalized_tier3_cutoff:
            chosen_tier = 3
            tier_pool_size = self.odds.raid_tier3_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.raid_tier_3_ids[chosen_pokemon_index]
        else:
            chosen_tier = 4
            tier_pool_size = self.odds.raid_tier4_pool_size
            pokemon_index_roll = self.pokemon_rng.random() # Roll AFTER tier_pool_size is set
            chosen_pokemon_index = math.floor(pokemon_index_roll * tier_pool_size)
            chosen_pokemon_index = max(0, min(chosen_pokemon_index, tier_pool_size - 1))
            pokemon_id = self.raid_tier_4_ids[chosen_pokemon_index]

        # 2. Determine Shininess
        shiny_roll = self.shiny_rng.random() # Uses the re-seeded RNG
        is_shiny = shiny_roll < self.odds.raid_shiny_rate
        
        result = {
            "frame": frame,
            "tier": chosen_tier,
            "is_shiny": is_shiny,
            "pokemon_index_in_tier": chosen_pokemon_index,
            "tier_pool_size": tier_pool_size,
            "pokemon_id": pokemon_id
        }
        print(result)
        return result
    
    def find_shiny_raid_frame(self, start_frame: int = 0, max_frames_to_check: int = 100000):
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
            if shiny_roll < self.odds.raid_shiny_rate:
                print(f"Found shiny frame: {frame} (Shiny roll: {shiny_roll:.4f} < Shiny rate: {self.odds.raid_shiny_rate})")
                return frame
        print(f"No shiny frame found within {max_frames_to_check} frames starting from {start_frame}.")
        return None