PLAYER_COLORS = ["red", "blue", "green", "yellow"]

BOARD_SIZE = 15

# Main path: 52 cells going clockwise starting from Red's entry
# Red enters at bottom arm, Blue at left arm (from Red's perspective it's right),
# Green at top arm, Yellow at left arm
MAIN_PATH = [
    (13, 6), (12, 6), (11, 6), (10, 6), (9, 6),           # 0-4   bottom arm up
    (8, 6), (8, 5), (8, 4), (8, 3), (8, 2), (8, 1), (8, 0), # 5-11  left arm left
    (7, 0), (6, 0),                                         # 12-13 left edge
    (6, 1), (6, 2), (6, 3), (6, 4), (6, 5),                 # 14-18 top arm right (from left)
    (5, 6), (4, 6), (3, 6), (2, 6), (1, 6), (0, 6),         # 19-24 top arm up
    (0, 7), (0, 8),                                         # 25-26 top edge
    (1, 8), (2, 8), (3, 8), (4, 8), (5, 8),                 # 27-31 top arm down
    (6, 9), (6, 10), (6, 11), (6, 12), (6, 13), (6, 14),    # 32-37 right arm right
    (7, 14), (8, 14),                                       # 38-39 right edge
    (8, 13), (8, 12), (8, 11), (8, 10), (8, 9),             # 40-44 bottom arm down
    (9, 8), (10, 8), (11, 8), (12, 8), (13, 8),             # 45-49 bottom arm down right
    (13, 7),                                                # 50     bottom edge (cell before entry)
]

assert len(MAIN_PATH) == 51, f"MAIN_PATH must have 51 cells, got {len(MAIN_PATH)}"

# Entry offset for each player on the main path
PLAYER_ENTRY = [0, 13, 26, 39]  # Red, Blue, Green, Yellow

# Home stretch: 5 cells + finish (last cell = finish position)
HOME_STRETCH = {
    0: [(13, 7), (12, 7), (11, 7), (10, 7), (9, 7), (8, 7)],     # Red
    1: [(7, 1), (7, 2), (7, 3), (7, 4), (7, 5), (7, 6)],        # Blue
    2: [(1, 7), (2, 7), (3, 7), (4, 7), (5, 7), (6, 7)],        # Green
    3: [(7, 13), (7, 12), (7, 11), (7, 10), (7, 9), (7, 8)],    # Yellow
}

# Starting zones where pieces wait to enter
START_ZONES = {
    0: [(9, 11), (9, 12), (10, 11), (10, 12)],    # Red bottom-right
    1: [(2, 11), (2, 12), (3, 11), (3, 12)],      # Blue top-right
    2: [(2, 2), (2, 3), (3, 2), (3, 3)],          # Green top-left
    3: [(9, 2), (9, 3), (10, 2), (10, 3)],        # Yellow bottom-left
}

PIECES_PER_PLAYER = 4
HOME_STRETCH_LEN = 6  # 5 steps + finish
STEPS_TO_FINISH = 51 + 5  # full path (51 steps from entry) + 5 home stretch steps = 56 total

def create_board_state():
    return {
        "pieces": {p: [{"state": "home", "pos": -1, "steps": 0} for _ in range(PIECES_PER_PLAYER)]
                   for p in range(4)},
        "current_turn": 0,
        "dice_value": None,
        "game_over": False,
        "winner": None,
        "rolled_this_turn": False,
        "consecutive_sixes": 0,
    }

def roll_dice():
    import random
    return random.randint(1, 6)

def is_valid_roll(state, player):
    if state["game_over"]:
        return False, "游戏已结束"
    if state["current_turn"] != player:
        return False, "还没轮到你"
    if state["rolled_this_turn"]:
        return False, "本回合已掷过骰子"
    return True, None

def get_playable_pieces(state, player, dice_value):
    pieces = state["pieces"][player]
    playable = []
    for i, p in enumerate(pieces):
        if p["state"] == "home":
            if dice_value == 6:
                playable.append(i)
        elif p["state"] == "active":
            new_steps = p["steps"] + dice_value
            if new_steps <= STEPS_TO_FINISH:
                playable.append(i)
        elif p["state"] == "finished":
            pass
    return playable

def execute_move(state, player, piece_idx):
    pieces = state["pieces"][player]
    piece = pieces[piece_idx]
    dice = state["dice_value"]

    result = {"captured": None, "entered": False, "finished": False}

    if piece["state"] == "home":
        piece["state"] = "active"
        piece["steps"] = 0
        piece["pos"] = MAIN_PATH[PLAYER_ENTRY[player]]
        result["entered"] = True
        result["new_pos"] = piece["pos"]
    elif piece["state"] == "active":
        new_steps = piece["steps"] + dice
        if new_steps >= STEPS_TO_FINISH:
            piece["state"] = "finished"
            piece["steps"] = new_steps
            result["finished"] = True
            result["new_pos"] = HOME_STRETCH[player][-1]
        elif new_steps >= 51:
            home_idx = new_steps - 51
            piece["steps"] = new_steps
            piece["pos"] = HOME_STRETCH[player][home_idx]
            result["new_pos"] = piece["pos"]
        else:
            new_path_idx = (PLAYER_ENTRY[player] + new_steps) % 51
            piece["steps"] = new_steps
            piece["pos"] = MAIN_PATH[new_path_idx]
            result["new_pos"] = piece["pos"]

            # Check capture: if another player has a piece at the same MAIN_PATH cell
            if piece["state"] == "active":
                pos = piece["pos"]
                for op in range(4):
                    if op == player:
                        continue
                    for opi, opp in enumerate(state["pieces"][op]):
                        if opp["state"] == "active" and opp["pos"] == pos:
                            if get_path_index(opp["pos"]) is not None and is_same_position(pos, opp["pos"]):
                                opp["state"] = "home"
                                opp["steps"] = 0
                                opp["pos"] = -1
                                result["captured"] = {"player": op, "piece": opi}
                                break

    if result["finished"]:
        if all(p["state"] == "finished" for p in pieces):
            state["game_over"] = True
            state["winner"] = player

    return result

def get_path_index(pos):
    try:
        return MAIN_PATH.index(pos)
    except ValueError:
        return None

def is_same_position(a, b):
    return a[0] == b[0] and a[1] == b[1]

def get_home_stretch_pos(player, step):
    if 0 <= step < HOME_STRETCH_LEN:
        return HOME_STRETCH[player][step]
    return None

def get_entry_pos(player):
    return MAIN_PATH[PLAYER_ENTRY[player]]

def absolute_to_view(coord, player_view):
    r, c = coord
    if player_view == 1:      # Blue: rotate 90° CW
        return (c, 14 - r)
    elif player_view == 2:    # Green: rotate 180°
        return (14 - r, 14 - c)
    elif player_view == 3:    # Yellow: rotate 270° CW (90° CCW)
        return (14 - c, r)
    return (r, c)             # Red: no rotation

def view_to_absolute(coord, player_view):
    r, c = coord
    if player_view == 1:      # Blue: rotate 90° CCW
        return (14 - c, r)
    elif player_view == 2:    # Green: rotate 180°
        return (14 - r, 14 - c)
    elif player_view == 3:    # Yellow: rotate 90° CW
        return (c, 14 - r)
    return (r, c)             # Red: no rotation
