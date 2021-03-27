import itertools
import collections
import sys
from multiprocessing import Process, Queue
from sim import simulate_zaps, simulate_squirts, simulate_drops, num_gags, level_to_hp
from programGlobals import *

# Seems to allow the script to work in both Py2 and Py3
if sys.version_info < (3, 0):
    input = raw_input

POINTS = ((0, 1, 5, 10), (0, 3, 9, 40), (0, 1, 5, 10))
NAMES = (('Seltzer', 'Hose', 'Storm', 'Geyser'),
         ('Taser', 'TV', 'Tesla', 'Lightning'),
         ('Weight', 'Safe', 'Boulder', 'Piano'))
MAX_LEVEL = 20  # Anything above this will be treated as hp, anything equal/below is treated as a level

solutions = Queue()

# Loops reading/executing calculator commands until the user quits
def main():
    print("------------------------------------------")
    print("Chris's TTCC Zap Calculator v1.1")
    print("Last updated: 8/6/2020")
    while True:
        print("------------------------------------------\n")

        # Take input
        command = input("Enter command (q to quit): ")
        if command == 'q':
            return

        # Parse and run the command, if possible
        print('')
        try:
            pick_gag_tracks(*parse_command(command))
            print_solutions()
        except ValueError:
            print("Invalid command - format as [r]HP/LVL[s][pl][l] and optionally [-] [Xp] [Xs] [Xz] [Xd]")
        print('')


# Parses the line inputted by the user
# Could be updated to give the user a little bit more feedback on invalid commands, but oh well
def parse_command(command):
    # If the user starts the command with r, the cogs they enter will be reversed
    want_reversed = False
    if command[0] == 'r':
        want_reversed = True
        command = command[1:]

    arguments = command.lower().split()

    # Split up args into required and optional
    try:
        dash_index = arguments.index('-')
        cogs = arguments[0:dash_index]
        rest = arguments[dash_index + 1:]
    except ValueError:
        cogs = arguments[0:]
        rest = []

    if len(cogs) == 0:
        raise ValueError

    # Parse the cog info
    cog_info = [[], [], [], []]
    for cog in cogs:
        # Find where the HP stops and the extra stuff begins
        cur_index = 0
        while cur_index < len(cog) and cog[cur_index].isdigit():
            cur_index += 1

        # Check for extra info
        extra_info = cog[cur_index:]
        is_executive = 'e' in extra_info
        cog_info[IS_SOAKED_INDEX].append('s' in extra_info)
        cog_info[IS_LURED_INDEX].append('l' in extra_info)
        cog_info[IS_P_LURED_INDEX].append('l' in extra_info and 'p' in extra_info)

        # Process the level/hp part, must be above 0
        hp = int(cog[:cur_index])
        if hp > 0:
            if hp <= MAX_LEVEL:
                hp = level_to_hp(hp, is_executive)
            cog_info[HP_INDEX].append(hp)
        else:
            raise ValueError

    # Parse and execute the optional commands
    num_toons = 4
    want_gags = [None] * NUM_TRACKS
    for item in rest:
        command = item[-1:]

        # Non-int value will trigger the ValueError
        value = int(item[:-1])
        if command == 'p':
            num_toons = value
        elif command == 's':
            want_gags[SQUIRT_INDEX] = value
        elif command == 'z':
            want_gags[ZAP_INDEX] = value
        elif command == 'd':
            want_gags[DROP_INDEX] = value

    # Reverse the list at the end, once it's finalized, if the user requested it
    if want_reversed:
        for sub_list in cog_info:
            sub_list.reverse()

    return num_toons, want_gags, cog_info


# Returns the minimum number of squirt gags to soak every cog in soaked
def min_squirt(soaked):
    cur_soaked = list(soaked)
    squirts = 0
    # If the entire set isn't soaked, soak the next 3 and check again
    while not all(cur_soaked):
        first_non_soaked = cur_soaked.index(False)
        for i in range(first_non_soaked, min(first_non_soaked + 3, len(cur_soaked))):
            cur_soaked[i] = True

        squirts += 1

    return squirts


# Loop through every possible combination of gag tracks based on user input
def pick_gag_tracks(num_toons, want_gags, cog_info):
    # Setup ranges
    combinations = []
    for i in range(0, NUM_TRACKS):
        if want_gags[i] is None:
            combinations.append(range(0, num_toons + 1))
        else:
            combinations.append((want_gags[i],))

    # Replace the default 0 to num_toons range with min_squirt to num_toons if a squirt gag number wasn't requested
    if want_gags[SQUIRT_INDEX] is None:
        combinations[SQUIRT_INDEX] = range(min_squirt(cog_info[IS_SOAKED_INDEX]), num_toons + 1)

    # Use each gag range; filter out ones that don't add up to num_toons
    processes = []
    for gag_choice in filter(lambda x: sum(x) == num_toons, itertools.product(*combinations)):
        p = Process(target=pick_gags, args=(gag_choice, cog_info, solutions))
        processes.append(p)
        p.start()

    for process in processes:
        process.join()


# Loop through every gag combo, skip redundant or obsoleted ones
def pick_gags(gag_tracks, cog_info, solution_queue):
    # Generate all possible gag combinations with no duplicates, order is not important
    components = []
    for i in range(0, NUM_TRACKS):
        components.append(make_nondecreasing_tuples(gag_tracks[i], num_gags[i]))

    gag_combos = list(itertools.product(*components))
    for gag_combo in gag_combos:
        # If the gag combination can destroy all the cogs, get rid of the combinations it obsoletes
        if pick_targets(gag_combo, cog_info, solution_queue):
            # Generate the list of now-obsoleted combos and remove them
            obsolete_components = []
            for j in range(0, NUM_TRACKS):
                obsolete_components.append(make_nondecreasing_tuples(gag_tracks[j], num_gags[j], gag_combo[j]))

            obsolete_combos = list(itertools.product(*obsolete_components))[1:]
            for obsolete_combo in obsolete_combos:
                try:
                    gag_combos.remove(obsolete_combo)
                except ValueError:
                    pass


# Pick every possible non-redundant target selection, add valid solutions to the global array
# Returns True if these gags are able to destroy these cogs
def pick_targets(gags, cog_info, solution_queue):
    num_targets = len(cog_info[0])
    found_solution = False

    # Apply squirt gag combinations, eliminate duplicate target permutations since order doesn't matter
    squirt_components = []
    for num_each_squirt in collections.Counter(gags[SQUIRT_INDEX]).values():
        squirt_components.append(make_nondecreasing_tuples(num_each_squirt, num_targets))
    for squirt_targets in itertools.product(*squirt_components):
        squirt_targets = sum(squirt_targets, ())
        squirt_info, squirt_stuns, all_soaked = simulate_squirts(gags[SQUIRT_INDEX], squirt_targets, cog_info)
        if not all_soaked:
            continue

        # Apply zap gag combinations, order is important
        num_zap = len(gags[ZAP_INDEX])
        for zap_targets in itertools.product(range(num_targets), repeat=num_zap):
            zap_targets = zap_targets
            zap_info, zap_stuns = simulate_zaps(gags[ZAP_INDEX], zap_targets, squirt_info)

            # Apply drop combinations, order not important
            drop_components = []
            for num_each_drop in collections.Counter(gags[DROP_INDEX]).values():
                drop_components.append(make_nondecreasing_tuples(num_each_drop, num_targets))
            for drop_targets in itertools.product(*drop_components):
                drop_targets = sum(drop_targets, ())
                drop_info = simulate_drops(gags[DROP_INDEX], drop_targets, zap_info)

                # Check if all cogs are dead
                if all(k <= 0 for k in drop_info[HP_INDEX]):
                    # Calculate no-stun drops penalty and add the solution to the global list
                    bad_drops = 0
                    for drop_target in drop_targets:
                        if drop_target not in squirt_stuns and drop_target not in zap_stuns:
                            bad_drops += 1

                    # Solutions queue is in no particular order, only used in printing
                    solution_queue.put((gags, (squirt_targets, zap_targets, drop_targets), bad_drops))
                    found_solution = True

    return found_solution


# Generator for the set of nondecreasing tuples from start-n with length depth
def make_nondecreasing_tuples(depth, n, start=None):
    # Only possible that start == None in the first iteration if no argument is given
    if start is None:
        start = [0] * depth
    else:
        start = list(start)

    # Recursive base case
    if depth == 0:
        yield ()
    else:
        # Recursively construct the next depth worth of elements
        for x in range(start[-depth], n):
            # Start is used and updated to make sure the child elements are nondecreasing
            if depth > 1:
                start[-(depth - 1)] = max(x, start[-(depth - 1)])
            for t in make_nondecreasing_tuples(depth - 1, n, start):
                yield (x,) + t


# Scores a set of gags using POINTS
def score_solutions(gags):
    total = 0
    for i in range(0, NUM_TRACKS):
        for j in range(0, len(gags[i])):
            total += POINTS[i][gags[i][j]]

    return total


# Prints the solutions array in a human-readable format
def print_solutions():
    string_length = 17
    gag_index = 0
    target_index = 1
    bad_drop_index = 2

    # Convert the asynchronous queue to a list
    solutions_list = []
    while solutions.qsize() > 0:
        solutions_list.append(solutions.get())

    if len(solutions_list) == 0:
        print('No solutions found :(')
        return

    # Sort by points and bad drops
    solutions_list.sort(key=lambda s: (score_solutions(s[gag_index]), s[bad_drop_index]), reverse=True)

    # Print the gags used in the combo and the cogs they target
    for solution in solutions_list:
        print_string = ''
        for i in range(0, NUM_TRACKS):
            for j in range(0, len(solution[gag_index][i])):
                gag_string = NAMES[i][solution[gag_index][i][j]] + ' ' + str(solution[target_index][i][j] + 1) + ' '
                padding = max(0, string_length - len(gag_string))
                print_string += gag_string + ' ' * padding

        print_string = print_string
        print(print_string)


if __name__ == "__main__":
    main()
