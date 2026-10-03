import math

import pytest

from domains.solver import geometry


def test_point_segment_distance_point_on_segment_is_zero():
    p = {"x": 5, "y": 0}
    start = {"x": 0, "y": 0}
    end = {"x": 10, "y": 0}
    assert geometry.point_segment_distance(p, start, end) == 0


def test_point_segment_distance_perpendicular_offset():
    p = {"x": 5, "y": 3}
    start = {"x": 0, "y": 0}
    end = {"x": 10, "y": 0}
    assert geometry.point_segment_distance(p, start, end) == 3


def test_is_path_blocked_true_when_ball_sits_on_the_line():
    start = {"x": 0, "y": 0}
    end = {"x": 10, "y": 0}
    obstacles = [{"x": 5, "y": 0}]
    assert geometry.is_path_blocked(start, end, obstacles) is True


def test_is_path_blocked_false_when_ball_is_far_from_the_line():
    start = {"x": 0, "y": 0}
    end = {"x": 10, "y": 0}
    obstacles = [{"x": 5, "y": 20}]
    assert geometry.is_path_blocked(start, end, obstacles) is False


def test_ghost_ball_position_sits_on_the_object_to_pocket_line():
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}
    ghost = geometry.ghost_ball_position(object_ball, pocket)
    # the ghost ball must be on the opposite side of the object ball from the pocket
    assert ghost["x"] < object_ball["x"]
    assert ghost["y"] == object_ball["y"]


def test_cut_angle_is_zero_for_a_straight_in_shot():
    cue_pos = {"x": 0, "y": 25}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}
    angle = geometry.cut_angle_degrees(cue_pos, object_ball, pocket)
    assert angle < 0.01


def test_cut_angle_is_large_for_a_sharp_cut():
    cue_pos = {"x": 50, "y": 0}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}
    angle = geometry.cut_angle_degrees(cue_pos, object_ball, pocket)
    assert angle > 60


def _expected_slide_distance(speed=geometry.DEFAULT_SHOT_SPEED):
    return speed ** 2 / (2 * geometry.SLIDE_FRICTION)


def test_stun_shot_is_the_contact_point_for_a_straight_in_shot():
    # a straight-in shot has no tangent component at all, so a spin-free
    # stun shot genuinely stops dead at the ghost-ball point
    cue_pos = {"x": 0, "y": 25}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}

    ghost = geometry.ghost_ball_position(object_ball, pocket)
    rest = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="stun")

    assert rest["x"] == pytest.approx(ghost["x"])
    assert rest["y"] == pytest.approx(ghost["y"])


def test_follow_rolls_straight_through_a_straight_in_shot():
    # with no tangent component to blend with, a rolling cue ball just keeps
    # rolling straight through in its own original direction, the full
    # slide distance ("follow-through")
    cue_pos = {"x": 0, "y": 25}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}

    ghost = geometry.ghost_ball_position(object_ball, pocket)
    incoming = geometry._normalize((ghost["x"] - cue_pos["x"], ghost["y"] - cue_pos["y"]))
    rest = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="follow")

    expected = _expected_slide_distance()
    assert rest["x"] == pytest.approx(ghost["x"] + incoming[0] * expected)
    assert rest["y"] == pytest.approx(ghost["y"] + incoming[1] * expected)


def test_draw_rolls_straight_back_on_a_straight_in_shot():
    # same situation, but backspin sends it the full slide distance back
    # toward the shooter instead
    cue_pos = {"x": 0, "y": 25}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}

    ghost = geometry.ghost_ball_position(object_ball, pocket)
    incoming = geometry._normalize((ghost["x"] - cue_pos["x"], ghost["y"] - cue_pos["y"]))
    rest = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="draw")

    expected = _expected_slide_distance()
    assert rest["x"] == pytest.approx(ghost["x"] - incoming[0] * expected)
    assert rest["y"] == pytest.approx(ghost["y"] - incoming[1] * expected)


def test_stun_shot_travels_along_the_tangent_by_the_friction_based_distance():
    # for anything but a straight-in shot, a stun (no-spin) cue ball keeps
    # sliding past the contact point along the tangent line, by a distance
    # derived from speed and friction (speed^2 / (2 * SLIDE_FRICTION)), not a
    # fixed made-up number
    cue_pos = {"x": 50, "y": 0}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}

    ghost = geometry.ghost_ball_position(object_ball, pocket)
    rest = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="stun")

    traveled = math.hypot(rest["x"] - ghost["x"], rest["y"] - ghost["y"])
    assert traveled == pytest.approx(_expected_slide_distance())


def test_follow_rotates_the_exit_direction_toward_incoming():
    # the cue ball's spin isn't changed by the collision, so a rolling
    # ("follow") cue ball's exit direction rotates (partway) from the plain
    # tangent toward its own original approach direction, covering the same
    # total slide distance either way, not just toward where the object
    # ball went
    cue_pos = {"x": 30, "y": 20}
    object_ball = {"x": 70, "y": 27}
    pocket = {"x": 100, "y": 50}

    ghost = geometry.ghost_ball_position(object_ball, pocket)
    incoming = geometry._normalize((ghost["x"] - cue_pos["x"], ghost["y"] - cue_pos["y"]))

    def along_incoming(rest):
        disp = (rest["x"] - ghost["x"], rest["y"] - ghost["y"])
        return disp[0] * incoming[0] + disp[1] * incoming[1]

    stun_rest = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="stun")
    follow_rest = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="follow")

    assert along_incoming(follow_rest) > along_incoming(stun_rest)
    traveled = math.hypot(follow_rest["x"] - ghost["x"], follow_rest["y"] - ghost["y"])
    assert traveled == pytest.approx(_expected_slide_distance())


def test_draw_rotates_the_exit_direction_away_from_incoming():
    # same shot, but backspin rotates the exit direction the other way,
    # back toward the shooter, still covering the same slide distance
    cue_pos = {"x": 30, "y": 20}
    object_ball = {"x": 70, "y": 27}
    pocket = {"x": 100, "y": 50}

    ghost = geometry.ghost_ball_position(object_ball, pocket)
    incoming = geometry._normalize((ghost["x"] - cue_pos["x"], ghost["y"] - cue_pos["y"]))

    def along_incoming(rest):
        disp = (rest["x"] - ghost["x"], rest["y"] - ghost["y"])
        return disp[0] * incoming[0] + disp[1] * incoming[1]

    stun_rest = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="stun")
    draw_rest = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="draw")

    assert along_incoming(draw_rest) < along_incoming(stun_rest)
    traveled = math.hypot(draw_rest["x"] - ghost["x"], draw_rest["y"] - ghost["y"])
    assert traveled == pytest.approx(_expected_slide_distance())


def test_cue_rest_position_stops_short_of_a_blocker_in_its_path():
    # same straight-in shot as test_follow_rolls_straight_through_a_straight_in_shot,
    # but with another ball sitting directly on the cue ball's follow-through
    # path: the real cue ball would collide with it, not glide straight past
    cue_pos = {"x": 0, "y": 25}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}
    blocker = {"x": 55, "y": 25}

    unobstructed = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="follow")
    rest = geometry.cue_rest_position(
        cue_pos, object_ball, pocket, shot_type="follow", blockers=[blocker]
    )

    assert rest["x"] < unobstructed["x"]
    # exactly two ball radii short of the blocker's center, since that's
    # where the two balls' surfaces would actually touch
    distance_to_blocker = math.hypot(blocker["x"] - rest["x"], blocker["y"] - rest["y"])
    assert distance_to_blocker == pytest.approx(geometry.DEFAULT_BALL_RADIUS * 2)


def test_cue_rest_position_cant_move_at_all_if_already_touching_a_blocker():
    # edge case: a blocker sits essentially right at the contact point itself,
    # so the cue ball can't slide anywhere at all, not even a little
    cue_pos = {"x": 0, "y": 25}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}
    ghost = geometry.ghost_ball_position(object_ball, pocket)
    blocker_at_ghost = dict(ghost)

    rest = geometry.cue_rest_position(
        cue_pos, object_ball, pocket, shot_type="follow", blockers=[blocker_at_ghost]
    )

    assert rest["x"] == pytest.approx(ghost["x"])
    assert rest["y"] == pytest.approx(ghost["y"])


def test_cue_rest_position_ignores_a_blocker_off_to_the_side():
    cue_pos = {"x": 0, "y": 25}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}
    far_blocker = {"x": 55, "y": 45}  # nowhere near the straight path along y=25

    unobstructed = geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="follow")
    rest = geometry.cue_rest_position(
        cue_pos, object_ball, pocket, shot_type="follow", blockers=[far_blocker]
    )

    assert rest == unobstructed


def test_cue_rest_position_rejects_an_unknown_shot_type():
    cue_pos = {"x": 50, "y": 0}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}

    try:
        geometry.cue_rest_position(cue_pos, object_ball, pocket, shot_type="spin")
        assert False, "expected a ValueError for an unknown shot_type"
    except ValueError:
        pass
