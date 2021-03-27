import math
import copy
from programGlobals import *

EXE_HP_MULT = 1.5
GAG_DAMAGE = ((30, 56, 80, 115), (24, 40, 66, 80), (80, 125, 180, 220))

MAX_JUMPS = 2
JUMP_DAMAGE = (3, 2.5, 2)

YELLOW_MULT = (0, 0, 0.2)
YELLOW_MULT_DROP = (0, 0, 0.3, 0.4, 0.5)

ORANGE_MULT_LURE = 0.5
ORANGE_MULT_P_LURE = 0.65

num_gags = len(GAG_DAMAGE[0]), len(GAG_DAMAGE[1]), len(GAG_DAMAGE[2])


# Converts a cog's level to its hp
def level_to_hp(level, is_executive):
    if is_executive:
        return int((level + 1) * (level + 2) * EXE_HP_MULT)
    else:
        return (level + 1) * (level + 2)


# Simulates the chosen squirt gags on the chosen cogs
# Returns the new hps, stuns, and whether all cogs are soaked or not
def simulate_squirts(squirts, targets, cog_info):
    new_info = copy.deepcopy(cog_info)
    num_cogs = len(new_info[0])

    # Update soaked
    new_soaked = new_info[IS_SOAKED_INDEX]
    for target in targets:
        left_cog = max(0, target - 1)
        right_cog = min(num_cogs - 1, target + 1)
        new_soaked[target] = True
        new_soaked[left_cog] = True
        new_soaked[right_cog] = True

    # Quit if a cog isn't soaked
    if False in new_soaked:
        return None, targets, False

    # Initialize damage
    red_damage = [0] * num_cogs
    yellow_mults = [0] * num_cogs
    orange_mults = [0] * num_cogs

    # Calculate orange multipliers based on if cog is lured/p lured
    for i in range(0, num_cogs):
        if new_info[IS_P_LURED_INDEX][i]:
            orange_mults[i] = ORANGE_MULT_P_LURE
        elif new_info[IS_LURED_INDEX][i]:
            orange_mults[i] = ORANGE_MULT_LURE

    # Calculate yellow multipliers and unlure cogs
    num_targeted = [0] * num_cogs
    for target in targets:
        num_targeted[target] += 1
        new_info[IS_P_LURED_INDEX][target] = False
        new_info[IS_LURED_INDEX][target] = False
    for i in range(0, num_cogs):
        yellow_mults[i] = YELLOW_MULT[min(num_targeted[i], len(YELLOW_MULT) - 1)]

    # Total up all red damage
    for i in range(0, len(squirts)):
        red_damage[targets[i]] += GAG_DAMAGE[SQUIRT_INDEX][squirts[i]]

    # Subtract damage
    new_hps = new_info[HP_INDEX]
    for i in range(0, num_cogs):
        total_damage = red_damage[i] +\
                       math.ceil(red_damage[i] * yellow_mults[i]) +\
                       math.ceil(red_damage[i] * orange_mults[i])
        new_hps[i] -= int(total_damage)

    return new_info, targets, True


# Simulates the chosen zaps and returns the new HPs and stuns
# Executes the gags in the order they're listed in zaps, doesn't check if the combo is valid or not
def simulate_zaps(zaps, targets, cog_info):
    new_info = copy.deepcopy(cog_info)
    num_cogs = len(new_info[0])

    jumped = [False] * num_cogs
    stuns = []

    for i in range(0, len(zaps)):
        target = targets[i]

        gag = zaps[i]
        damage = GAG_DAMAGE[ZAP_INDEX][gag]

        # Hit the main cog. If it's already dead, skip calculating the bounces
        new_info[IS_P_LURED_INDEX][target] = False
        new_info[IS_LURED_INDEX][target] = False
        if not new_info[IS_SOAKED_INDEX][target]:  # Shouldn't happen since we're assuming all cogs soaked
            continue
        elif new_info[HP_INDEX][target] <= 0:
            stuns.append(target)
            new_info[HP_INDEX][target] -= int(math.ceil(damage * JUMP_DAMAGE[0]))
            continue
        else:
            stuns.append(target)
            new_info[HP_INDEX][target] -= int(math.ceil(damage * JUMP_DAMAGE[0]))

        # Calculate the bounce damage/stuns
        current_cog = target
        for j in range(0, MAX_JUMPS):
            jump_targets = [current_cog - 1, current_cog - 2, current_cog + 1, current_cog + 2]
            for jump_target in jump_targets:
                if 0 <= jump_target < num_cogs and not jump_target == target and new_info[IS_SOAKED_INDEX][jump_target]\
                        and not jumped[jump_target] and new_info[HP_INDEX][jump_target] > 0:
                    new_info[IS_P_LURED_INDEX][jump_target] = False
                    new_info[IS_LURED_INDEX][jump_target] = False
                    stuns.append(jump_target)
                    jumped[jump_target] = True
                    new_info[HP_INDEX][jump_target] -= int(math.ceil(damage * JUMP_DAMAGE[j + 1]))
                    current_cog = jump_target
                    break

    return new_info, stuns


# Simulates the given drop gags and returns an updated cog_info
def simulate_drops(drops, targets, cog_info):
    new_info = copy.deepcopy(cog_info)
    num_cogs = len(new_info[0])

    # Initialize damage
    red_damage = [0] * num_cogs
    yellow_mults = [0] * num_cogs

    # Calculate yellow multipliers
    nam_targeted = [0] * num_cogs
    for target in targets:
        nam_targeted[target] += 1
    for i in range(0, num_cogs):
        yellow_mults[i] = YELLOW_MULT_DROP[min(nam_targeted[i], len(YELLOW_MULT_DROP) - 1)]

    # Total up all red damage
    for i in range(0, len(drops)):
        red_damage[targets[i]] += GAG_DAMAGE[DROP_INDEX][drops[i]]

    # Subtract damage
    new_hps = new_info[HP_INDEX]
    for i in range(0, num_cogs):
        is_lured = new_info[IS_P_LURED_INDEX][i] or new_info[IS_LURED_INDEX][i]
        if not is_lured:
            total_damage = red_damage[i] + math.ceil(red_damage[i] * yellow_mults[i])
            new_hps[i] -= int(total_damage)

    return new_info
