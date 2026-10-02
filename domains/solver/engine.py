from . import geometry

MAX_CUT_ANGLE = 50  # degrees; beyond this a shot is treated as unrealistic to attempt
MAX_BALLS = 6  # keeps the backtracking search fast enough for a single HTTP request
MAX_BALLS_NINE_BALL = 9  # nine_ball only ever considers one ball per level (the
# lowest remaining), so the search is far cheaper and a real rack (up to 9
# balls) stays well under 25ms even at this size, measured directly
SHOT_TYPE_PREFERENCE = ("follow", "stun", "draw")  # tried in this order per shot
GAME_MODES = ("freeform", "nine_ball", "eight_ball")
EIGHT_BALL_NUMBER = 8

TABLE_WIDTH = 100
TABLE_HEIGHT = 50
POCKETS = [
    {"x": 0, "y": 0},
    {"x": TABLE_WIDTH / 2, "y": 0},
    {"x": TABLE_WIDTH, "y": 0},
    {"x": 0, "y": TABLE_HEIGHT},
    {"x": TABLE_WIDTH / 2, "y": TABLE_HEIGHT},
    {"x": TABLE_WIDTH, "y": TABLE_HEIGHT},
]


def _clamp_to_table(pos, ball_radius=geometry.DEFAULT_BALL_RADIUS):
    """Cushions stop the cue ball rather than letting it slide off the table;
    we don't model the bounce, just treat the rail as a hard limit. The
    ball's center can only get within one radius of a rail, same as a real
    ball resting against the cushion."""
    return {
        "x": max(ball_radius, min(TABLE_WIDTH - ball_radius, pos["x"])),
        "y": max(ball_radius, min(TABLE_HEIGHT - ball_radius, pos["y"])),
    }


def _best_pocket_shot(cue_pos, object_ball, other_balls):
    """Return the easiest makeable shot for this ball (lowest cut angle), or
    None. This only decides which pocket to aim for; it says nothing about
    shot_type, since the best shot_type depends on what the rest of the
    table needs afterward, not on the shot itself."""
    candidates = []
    for pocket in POCKETS:
        angle = geometry.cut_angle_degrees(cue_pos, object_ball, pocket)
        if angle > MAX_CUT_ANGLE:
            continue
        ghost = geometry.ghost_ball_position(object_ball, pocket)
        if geometry.is_path_blocked(cue_pos, ghost, other_balls):
            continue
        if geometry.is_path_blocked(object_ball, pocket, other_balls):
            continue
        candidates.append((angle, pocket))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    angle, pocket = candidates[0]
    return {"pocket": pocket, "cut_angle": angle}


def _legal_candidates(remaining, game_mode):
    """Which balls from `remaining` the rules even allow attempting next.
    Doesn't decide which one is best, only which ones are legal to try."""
    if game_mode == "nine_ball":
        lowest = min(b["number"] for b in remaining)
        return [b for b in remaining if b["number"] == lowest]
    if game_mode == "eight_ball":
        if len(remaining) == 1:
            return remaining
        return [b for b in remaining if b["number"] != EIGHT_BALL_NUMBER]
    return remaining


def _search(cue_pos, remaining, game_mode):
    """Depth-first search over shot orderings, trying easier shots first and
    backtracking whenever a choice leaves no valid continuation. For each
    ball it also tries each shot_type in SHOT_TYPE_PREFERENCE, since the
    right spin to use depends on where it leaves the cue ball for the rest
    of the balls, not just on the shot being taken. `game_mode` restricts
    which ball is even allowed to be attempted next (nine-ball: must be the
    lowest remaining number; eight-ball: the 8 only once it's the last ball
    left); it doesn't change which balls can block a path."""
    if not remaining:
        return []

    scored = []
    for ball in _legal_candidates(remaining, game_mode):
        others = [b for b in remaining if b["number"] != ball["number"]]
        shot = _best_pocket_shot(cue_pos, ball, others)
        if shot is not None:
            scored.append((shot["cut_angle"], ball, shot))
    scored.sort(key=lambda s: s[0])

    for _, ball, shot in scored:
        rest_of_balls = [b for b in remaining if b["number"] != ball["number"]]
        for shot_type in SHOT_TYPE_PREFERENCE:
            rest = _clamp_to_table(
                geometry.cue_rest_position(cue_pos, ball, shot["pocket"], shot_type=shot_type)
            )
            continuation = _search(rest, rest_of_balls, game_mode)
            if continuation is not None:
                step = {
                    "ball": ball["number"],
                    "pocket": shot["pocket"],
                    "cut_angle": shot["cut_angle"],
                    "cue_rest_position": rest,
                    "shot_type": shot_type,
                }
                return [step] + continuation

    return None


def _first_unmakeable_ball(cue_pos, balls, game_mode):
    """Best-effort explanation for an impossible layout: the first legal-to-
    attempt ball that has no shot at all from the starting position. Does
    not catch deeper sequencing conflicts where every ball is individually
    makeable but no order works."""
    for ball in _legal_candidates(balls, game_mode):
        others = [b for b in balls if b["number"] != ball["number"]]
        if _best_pocket_shot(cue_pos, ball, others) is None:
            return ball["number"]
    return None


def find_runout(cue_pos, balls, game_mode="freeform"):
    if game_mode not in GAME_MODES:
        raise ValueError(f"game_mode must be one of {GAME_MODES}")
    ball_cap = MAX_BALLS_NINE_BALL if game_mode == "nine_ball" else MAX_BALLS
    if len(balls) > ball_cap:
        raise ValueError(f"layout has more than {ball_cap} balls; solver is not designed for that")
    if game_mode == "eight_ball":
        eight_balls = [b for b in balls if b["number"] == EIGHT_BALL_NUMBER]
        if len(eight_balls) != 1:
            raise ValueError("eight_ball mode requires exactly one ball numbered 8")
    if game_mode == "nine_ball":
        numbers = [b["number"] for b in balls]
        if len(set(numbers)) != len(numbers):
            raise ValueError("nine_ball mode requires every ball to have a distinct number")

    order = _search(cue_pos, balls, game_mode)
    if order is None:
        return {"possible": False, "order": None, "failed_at": _first_unmakeable_ball(cue_pos, balls, game_mode)}
    return {"possible": True, "order": order, "failed_at": None}
