from . import geometry

MAX_CUT_ANGLE = 50  # degrees; beyond this a shot is treated as unrealistic to attempt
MAX_BALLS = 6  # keeps the backtracking search fast enough for a single HTTP request
SHOT_TYPE_PREFERENCE = ("follow", "stun", "draw")  # tried in this order per shot

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


def _search(cue_pos, remaining):
    """Depth-first search over shot orderings, trying easier shots first and
    backtracking whenever a choice leaves no valid continuation. For each
    ball it also tries each shot_type in SHOT_TYPE_PREFERENCE, since the
    right spin to use depends on where it leaves the cue ball for the rest
    of the balls, not just on the shot being taken."""
    if not remaining:
        return []

    scored = []
    for ball in remaining:
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
            continuation = _search(rest, rest_of_balls)
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


def _first_unmakeable_ball(cue_pos, balls):
    """Best-effort explanation for an impossible layout: the first ball that has
    no shot at all from the starting position. Does not catch deeper sequencing
    conflicts where every ball is individually makeable but no order works."""
    for ball in balls:
        others = [b for b in balls if b["number"] != ball["number"]]
        if _best_pocket_shot(cue_pos, ball, others) is None:
            return ball["number"]
    return None


def find_runout(cue_pos, balls):
    if len(balls) > MAX_BALLS:
        raise ValueError(f"layout has more than {MAX_BALLS} balls; solver is not designed for that")

    order = _search(cue_pos, balls)
    if order is None:
        return {"possible": False, "order": None, "failed_at": _first_unmakeable_ball(cue_pos, balls)}
    return {"possible": True, "order": order, "failed_at": None}
