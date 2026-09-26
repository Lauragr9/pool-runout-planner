import math

DEFAULT_BALL_RADIUS = 1.5


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

    def norm(v):
        length = math.hypot(*v)
        return (v[0] / length, v[1] / length) if length else (0.0, 0.0)

    cue_n, obj_n = norm(cue_vec), norm(obj_vec)
    dot = max(-1.0, min(1.0, cue_n[0] * obj_n[0] + cue_n[1] * obj_n[1]))
    return math.degrees(math.acos(dot))
