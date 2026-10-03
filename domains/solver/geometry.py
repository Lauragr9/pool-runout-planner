import math

DEFAULT_BALL_RADIUS = 1.5
DEFAULT_SHOT_SPEED = 30.0  # arbitrary table-units/second; a "medium-firm" shot
SLIDE_FRICTION = 30.0  # arbitrary deceleration constant (folds in mu and g)
FOLLOW_BLEND = 0.65  # how far the exit direction rotates toward "incoming" for follow
DRAW_BLEND = 0.65  # how far it rotates toward "-incoming" for draw


def _normalize(v):
    length = math.hypot(*v)
    return (v[0] / length, v[1] / length) if length else (0.0, 0.0)


def point_segment_distance(point, seg_start, seg_end):
    """Shortest distance from `point` to the segment seg_start -> seg_end."""
    sx, sy = seg_start["x"], seg_start["y"]
    ex, ey = seg_end["x"], seg_end["y"]
    px, py = point["x"], point["y"]

    dx, dy = ex - sx, ey - sy
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return math.hypot(px - sx, py - sy)

    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / length_sq))
    proj_x, proj_y = sx + t * dx, sy + t * dy
    return math.hypot(px - proj_x, py - proj_y)


def is_path_blocked(seg_start, seg_end, obstacles, ball_radius=DEFAULT_BALL_RADIUS):
    """True if any obstacle ball sits close enough to the segment to intercept it."""
    for obstacle in obstacles:
        if point_segment_distance(obstacle, seg_start, seg_end) < ball_radius * 2:
            return True
    return False


def ghost_ball_position(object_ball, pocket, ball_radius=DEFAULT_BALL_RADIUS):
    """Cue-ball center position needed to send object_ball straight toward pocket."""
    dx = object_ball["x"] - pocket["x"]
    dy = object_ball["y"] - pocket["y"]
    dist = math.hypot(dx, dy)
    if dist == 0:
        return dict(object_ball)
    scale = (ball_radius * 2) / dist
    return {"x": object_ball["x"] + dx * scale, "y": object_ball["y"] + dy * scale}


def cut_angle_degrees(cue_pos, object_ball, pocket):
    """Angle between the cue ball's travel direction and the object ball's travel direction."""
    ghost = ghost_ball_position(object_ball, pocket)
    cue_vec = (ghost["x"] - cue_pos["x"], ghost["y"] - cue_pos["y"])
    obj_vec = (pocket["x"] - object_ball["x"], pocket["y"] - object_ball["y"])

    cue_n, obj_n = _normalize(cue_vec), _normalize(obj_vec)
    dot = max(-1.0, min(1.0, cue_n[0] * obj_n[0] + cue_n[1] * obj_n[1]))
    return math.degrees(math.acos(dot))


def _ray_circle_hit_distance(origin, direction, center, radius):
    """How far along the ray from `origin` in unit `direction` the point
    first comes within `radius` of `center`, or None if it never does.
    If `origin` already starts inside that radius, returns 0 (the ball
    can't move any closer than it already started)."""
    ox, oy = origin["x"] - center["x"], origin["y"] - center["y"]
    dx, dy = direction
    b = 2 * (ox * dx + oy * dy)
    c = ox * ox + oy * oy - radius * radius
    if c < 0:
        return 0.0
    discriminant = b * b - 4 * c
    if discriminant < 0:
        return None
    nearest = (-b - math.sqrt(discriminant)) / 2
    return nearest if nearest >= 0 else None


def cue_rest_position(cue_pos, object_ball, pocket, shot_type="stun",
                       ball_radius=DEFAULT_BALL_RADIUS, speed=DEFAULT_SHOT_SPEED,
                       blockers=None):
    """Where the cue ball ends up after the shot: an approximation that
    involves both translation and rotation, not just the instant-of-contact
    geometry.

    Translation: the cue ball does not stop dead at the contact point, it
    keeps sliding along the tangent line (perpendicular to the direction the
    object ball just went, since that's the part of the cue ball's incoming
    velocity left over once the component along the line of centers is
    transferred to the object ball). How far it slides is a real kinematics
    question, not a fixed number: distance = speed^2 / (2 * SLIDE_FRICTION).

    Rotation: a collision only transfers linear velocity, not spin, so
    whatever spin the cue ball already had keeps pointing along its own
    original approach direction ("incoming"), not toward the object ball's
    direction. A rolling cue ball (shot_type="follow") therefore doesn't
    just add a bit of forward motion on top of the tangent kick, its exit
    direction actually rotates partway from the tangent toward "incoming"
    (by FOLLOW_BLEND), and a backspun one (shot_type="draw") rotates the
    other way, toward "-incoming" (by DRAW_BLEND), while keeping the same
    overall slide distance. A pure "stun" shot carries no spin, so the exit
    direction stays exactly the tangent line.

    This is a simplified, qualitative model (fixed FOLLOW_BLEND/DRAW_BLEND,
    one assumed shot speed, no cushions) rather than a full rigid-body
    simulation. For a straight-in shot there is no tangent component left
    at all, so "stun" genuinely stops dead at the contact point, while
    "follow"/"draw" still roll straight through forward or backward along
    the original line.

    If `blockers` is given (every other ball still on the table, including
    ones the solver has no intention of potting), the slide stops early at
    the first one it would actually run into, instead of reporting a rest
    position that would have the cue ball pass straight through it.
    """
    ghost = ghost_ball_position(object_ball, pocket, ball_radius)

    incoming = _normalize((ghost["x"] - cue_pos["x"], ghost["y"] - cue_pos["y"]))
    impact = _normalize((pocket["x"] - object_ball["x"], pocket["y"] - object_ball["y"]))

    dot = incoming[0] * impact[0] + incoming[1] * impact[1]
    tangent = _normalize((incoming[0] - impact[0] * dot, incoming[1] - impact[1] * dot))

    if shot_type == "follow":
        blended = (
            tangent[0] * (1 - FOLLOW_BLEND) + incoming[0] * FOLLOW_BLEND,
            tangent[1] * (1 - FOLLOW_BLEND) + incoming[1] * FOLLOW_BLEND,
        )
    elif shot_type == "draw":
        blended = (
            tangent[0] * (1 - DRAW_BLEND) - incoming[0] * DRAW_BLEND,
            tangent[1] * (1 - DRAW_BLEND) - incoming[1] * DRAW_BLEND,
        )
    elif shot_type == "stun":
        blended = tangent
    else:
        raise ValueError("shot_type must be 'stun', 'follow', or 'draw'")

    exit_direction = _normalize(blended)
    slide_distance = speed ** 2 / (2 * SLIDE_FRICTION)

    for blocker in blockers or []:
        hit = _ray_circle_hit_distance(ghost, exit_direction, blocker, ball_radius * 2)
        if hit is not None and hit < slide_distance:
            slide_distance = hit

    return {
        "x": ghost["x"] + exit_direction[0] * slide_distance,
        "y": ghost["y"] + exit_direction[1] * slide_distance,
    }
