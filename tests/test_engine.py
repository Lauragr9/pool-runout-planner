from domains.solver.engine import find_runout


def test_single_ball_with_clear_shot_is_a_runout():
    cue = {"x": 50, "y": 25}
    ball = {"number": 1, "x": 20, "y": 10}  # collinear with cue and pocket (0, 0)

    result = find_runout(cue, [ball])

    assert result["possible"] is True
    assert result["failed_at"] is None
    assert [step["ball"] for step in result["order"]] == [1]


def test_two_independent_balls_can_both_be_potted():
    cue = {"x": 50, "y": 25}
    ball_a = {"number": 1, "x": 20, "y": 10}   # collinear with cue and pocket (0, 0)
    ball_b = {"number": 2, "x": 80, "y": 40}   # collinear with cue and pocket (100, 50)

    result = find_runout(cue, [ball_a, ball_b])

    assert result["possible"] is True
    assert [step["ball"] for step in result["order"]] == [1, 2]


def test_blocked_ball_is_shot_after_the_ball_blocking_it():
    # A sits on a clean line to pocket (100, 50); B sits directly on the cue's
    # path to A, so A cannot be shot first. B must go first, clearing the way.
    cue = {"x": 10, "y": 5}
    ball_a = {"number": 1, "x": 40, "y": 20}
    ball_b = {"number": 2, "x": 23.66, "y": 11.83}

    result = find_runout(cue, [ball_a, ball_b])

    assert result["possible"] is True
    assert [step["ball"] for step in result["order"]] == [2, 1]


def test_ball_with_no_viable_angle_to_any_pocket_is_impossible():
    # the cue sits on the same side as every pocket relative to this ball, so
    # there is no direction it could realistically be cut into any pocket from
    cue = {"x": 50, "y": 25}
    ball = {"number": 7, "x": 48, "y": 25}

    result = find_runout(cue, [ball])

    assert result["possible"] is False
    assert result["order"] is None
    assert result["failed_at"] == 7


def test_more_than_max_balls_is_rejected():
    cue = {"x": 50, "y": 25}
    balls = [{"number": i, "x": i * 5, "y": 10} for i in range(1, 10)]

    try:
        find_runout(cue, balls)
        assert False, "expected a ValueError for a layout above MAX_BALLS"
    except ValueError:
        pass
