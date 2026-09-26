from . import geometry

MAX_CUT_ANGLE = 80  # degrees; beyond this a shot is treated as unrealistic to attempt
MAX_BALLS = 8  # keeps the backtracking search fast enough for a single HTTP request

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


def _best_pocket_shot(cue_pos, object_ball, other_balls):
    """Return the easiest makeable shot for this ball (lowest cut angle), or None."""
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
        candidates.append((angle, pocket, ghost))
    if not candidates:
        return None
    candidates.sort(key=lambda c: c[0])
    angle, pocket, ghost = candidates[0]
    return {"pocket": pocket, "cue_rest_position": ghost, "cut_angle": angle}


def _search(cue_pos, remaining):
    """Depth-first search over shot orderings, trying easier shots first and
    backtracking whenever a choice leaves no valid continuation."""
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
        rest = [b for b in remaining if b["number"] != ball["number"]]
        continuation = _search(shot["cue_rest_position"], rest)
        if continuation is not None:
            step = {"ball": ball["number"], "pocket": shot["pocket"], "cut_angle": shot["cut_angle"]}
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
