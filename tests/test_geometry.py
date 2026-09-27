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


def test_stun_rest_position_is_the_contact_point_for_a_straight_in_shot():
    # a straight-in shot has no sideways speed left after contact: the cue
    # ball really does stop dead at the ghost-ball point
    cue_pos = {"x": 0, "y": 25}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}

    ghost = geometry.ghost_ball_position(object_ball, pocket)
    rest = geometry.stun_rest_position(cue_pos, object_ball, pocket)

    assert rest["x"] == pytest.approx(ghost["x"])
    assert rest["y"] == pytest.approx(ghost["y"])


def test_stun_rest_position_travels_along_the_tangent_for_a_cut_shot():
    # for anything but a straight-in shot, the cue ball keeps sliding past the
    # contact point by exactly STUN_TANGENT_TRAVEL, along the tangent line
    cue_pos = {"x": 50, "y": 0}
    object_ball = {"x": 50, "y": 25}
    pocket = {"x": 100, "y": 25}

    ghost = geometry.ghost_ball_position(object_ball, pocket)
    rest = geometry.stun_rest_position(cue_pos, object_ball, pocket)

    traveled = math.hypot(rest["x"] - ghost["x"], rest["y"] - ghost["y"])
    assert traveled == pytest.approx(geometry.STUN_TANGENT_TRAVEL)
