from domains.solver.engine import TABLE_HEIGHT, TABLE_WIDTH, find_runout
from domains.solver.geometry import DEFAULT_BALL_RADIUS


def _expect_value_error(fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
        assert False, "expected a ValueError"
    except ValueError:
        pass


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


def test_cue_rest_position_never_ends_up_off_the_table():
    # regression: for a ball near the top rail, the stun-shot tangent line can
    # point past y=0; the cue ball must not be reported as resting off-table
    cue = {"x": 30, "y": 20}
    ball = {"number": 1, "x": 60, "y": 3}

    result = find_runout(cue, [ball])

    assert result["possible"] is True
    rest = result["order"][0]["cue_rest_position"]
    assert DEFAULT_BALL_RADIUS <= rest["x"] <= TABLE_WIDTH - DEFAULT_BALL_RADIUS
    assert DEFAULT_BALL_RADIUS <= rest["y"] <= TABLE_HEIGHT - DEFAULT_BALL_RADIUS


def test_search_backtracks_when_the_easiest_ball_leads_to_a_dead_end():
    # Ball 1 has the easiest angle of the three when checked on its own
    # (~13.0°, versus ~26.8° for ball 2 and ~40.0° for ball 3), so a greedy
    # search with no backtracking would shoot it first. But shooting ball 1
    # first leaves the cue in a position from which neither ball 2 nor ball 3
    # has a valid shot, for any of the three shot types (verified directly:
    # _search from each of those rest positions returns None). A correct
    # search must notice that dead end and fall back to ball 2 instead,
    # which does lead to a full run-out.
    cue = {"x": 50, "y": 25}
    ball1 = {"number": 1, "x": 69.2, "y": 37.6}
    ball2 = {"number": 2, "x": 29.3, "y": 29.4}
    ball3 = {"number": 3, "x": 25.9, "y": 27.4}

    result = find_runout(cue, [ball1, ball2, ball3])

    assert result["possible"] is True
    assert [step["ball"] for step in result["order"]] == [2, 3, 1]


def test_search_tries_other_shot_types_before_giving_up_on_a_ball():
    # for this ball and pocket, "follow" (tried first) and "draw" both leave
    # the cue ball unable to reach the other ball afterward, but "stun" does
    # work (verified directly for all three). The search must try all three
    # shot types for the same ball before moving on to a different ball.
    cue = {"x": 50, "y": 25}
    ball1 = {"number": 1, "x": 85.4, "y": 17.0}
    ball2 = {"number": 2, "x": 37.5, "y": 11.6}

    result = find_runout(cue, [ball1, ball2])

    assert result["possible"] is True
    assert result["order"][0]["ball"] == 2
    assert result["order"][0]["shot_type"] == "stun"


def test_nine_ball_mode_forces_the_lowest_numbered_ball_first():
    # ball 5 has a much easier angle (~11.5°) than ball 2 (~41.8°), so
    # freeform shoots 5 first, but nine-ball rules require contacting the
    # lowest remaining number first regardless of how hard it is
    cue = {"x": 50, "y": 25}
    ball_low = {"number": 2, "x": 26.4, "y": 26.8}
    ball_high = {"number": 5, "x": 38.3, "y": 29.2}

    freeform = find_runout(cue, [ball_low, ball_high], game_mode="freeform")
    nine_ball = find_runout(cue, [ball_low, ball_high], game_mode="nine_ball")

    assert [s["ball"] for s in freeform["order"]] == [5, 2]
    assert [s["ball"] for s in nine_ball["order"]] == [2, 5]


def test_eight_ball_mode_forces_the_8_to_be_potted_last():
    # the 8-ball has a much easier angle (~1.7°) than ball 3 (~29.7°), so
    # freeform shoots the 8 first, but 8-ball rules require it to be the
    # very last ball pocketed
    cue = {"x": 50, "y": 25}
    ball_other = {"number": 3, "x": 15.6, "y": 14.9}
    ball_eight = {"number": 8, "x": 14.1, "y": 7.4}

    freeform = find_runout(cue, [ball_other, ball_eight], game_mode="freeform")
    eight_ball = find_runout(cue, [ball_other, ball_eight], game_mode="eight_ball")

    assert [s["ball"] for s in freeform["order"]] == [8, 3]
    assert [s["ball"] for s in eight_ball["order"]] == [3, 8]


def test_unknown_game_mode_is_rejected():
    cue = {"x": 50, "y": 25}
    ball = {"number": 1, "x": 20, "y": 10}
    _expect_value_error(find_runout, cue, [ball], game_mode="rotation")


def test_eight_ball_mode_requires_exactly_one_8():
    cue = {"x": 50, "y": 25}
    balls = [{"number": 1, "x": 20, "y": 10}, {"number": 2, "x": 40, "y": 15}]
    _expect_value_error(find_runout, cue, balls, game_mode="eight_ball")


def test_nine_ball_mode_requires_distinct_numbers():
    cue = {"x": 50, "y": 25}
    balls = [{"number": 1, "x": 20, "y": 10}, {"number": 1, "x": 40, "y": 15}]
    _expect_value_error(find_runout, cue, balls, game_mode="nine_ball")


def test_nine_ball_mode_allows_more_balls_than_the_freeform_cap():
    # nine_ball only ever considers the single lowest-numbered ball per
    # level, so it's allowed up to MAX_BALLS_NINE_BALL (9), well above the
    # freeform/eight_ball cap of MAX_BALLS (6)
    cue = {"x": 50, "y": 25}
    balls = [{"number": i, "x": 10 + i * 8, "y": 10} for i in range(1, 8)]

    result = find_runout(cue, balls, game_mode="nine_ball")

    assert result["possible"] in (True, False)  # just needs not to raise


def test_my_group_only_plans_the_players_own_balls_plus_the_eight():
    # two of mine (solids 1, 2), two of the opponent's (stripes 9, 10), none
    # of them blocking each other; without my_group the planner clears all
    # five, with my_group="solids" it should stop at just mine plus the 8
    cue = {"x": 50, "y": 25}
    mine_a = {"number": 1, "x": 20, "y": 10}   # collinear cue -> pocket (0, 0)
    mine_b = {"number": 2, "x": 80, "y": 40}   # collinear cue -> pocket (100, 50)
    eight = {"number": 8, "x": 50, "y": 45}
    opponent_a = {"number": 9, "x": 95, "y": 5}
    opponent_b = {"number": 10, "x": 5, "y": 45}
    balls = [mine_a, mine_b, eight, opponent_a, opponent_b]

    whole_table = find_runout(cue, balls, game_mode="eight_ball")
    mine_only = find_runout(cue, balls, game_mode="eight_ball", my_group="solids")

    assert sorted(step["ball"] for step in whole_table["order"]) == [1, 2, 8, 9, 10]
    assert [step["ball"] for step in mine_only["order"]] == [1, 2, 8]
    assert mine_only["possible"] is True


def test_my_group_opponent_balls_still_block_shots():
    # same blocking geometry as the freeform/nine_ball blocking test, but the
    # ball sitting on the cue's path to ball 1 is now the opponent's (a
    # stripe), not mine; it must still block the shot even though it's
    # excluded from what the sequence tries to pot
    cue = {"x": 10, "y": 5}
    mine = {"number": 1, "x": 40, "y": 20}
    opponent_blocker = {"number": 9, "x": 23.66, "y": 11.83}
    eight = {"number": 8, "x": 90, "y": 45}

    result = find_runout(cue, [mine, opponent_blocker, eight], game_mode="eight_ball", my_group="solids")

    assert result["possible"] is False
    assert result["failed_at"] == 1


def test_my_group_is_rejected_outside_eight_ball_mode():
    cue = {"x": 50, "y": 25}
    ball = {"number": 1, "x": 20, "y": 10}
    _expect_value_error(find_runout, cue, [ball], game_mode="freeform", my_group="solids")
    _expect_value_error(find_runout, cue, [ball], game_mode="nine_ball", my_group="solids")


def test_my_group_must_be_solids_or_stripes():
    cue = {"x": 50, "y": 25}
    ball_other = {"number": 1, "x": 20, "y": 10}
    ball_eight = {"number": 8, "x": 60, "y": 30}
    _expect_value_error(
        find_runout, cue, [ball_other, ball_eight], game_mode="eight_ball", my_group="green"
    )
