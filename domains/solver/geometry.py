import math

DEFAULT_BALL_RADIUS = 1.5
STUN_TANGENT_TRAVEL = 15.0  # arbitrary fixed distance; we don't model shot speed


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


def stun_rest_position(cue_pos, object_ball, pocket, ball_radius=DEFAULT_BALL_RADIUS,
                        travel_distance=STUN_TANGENT_TRAVEL):
    """Where the cue ball ends up after a stun shot (no spin): As in 
    real-life pool, it does not stop dead at the contact point, it keeps 
    sliding along the tangent line: perpendicular to the direction the 
    object ball just went. That tangent direction is exactly the part of 
    the cue ball's incoming velocity left over once the component along 
    the line of centers is transferred to the object ball, so we get it by
    projecting the incoming direction off the impact direction. For a 
    straight-in shot there is no leftover component and the cue ball genuinely 
    does stop at the contact point.
    """
    ghost = ghost_ball_position(object_ball, pocket, ball_radius)

    incoming = _normalize((ghost["x"] - cue_pos["x"], ghost["y"] - cue_pos["y"]))
    impact = _normalize((pocket["x"] - object_ball["x"], pocket["y"] - object_ball["y"]))

    dot = incoming[0] * impact[0] + incoming[1] * impact[1]
    tangent = (incoming[0] - impact[0] * dot, incoming[1] - impact[1] * dot)
    tangent_length = math.hypot(*tangent)
    if tangent_length < 1e-9:
        return ghost

    tangent_n = (tangent[0] / tangent_length, tangent[1] / tangent_length)
    return {
        "x": ghost["x"] + tangent_n[0] * travel_distance,
        "y": ghost["y"] + tangent_n[1] * travel_distance,
    }
