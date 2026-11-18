# Table bounds mirror services/solver/engine.py's TABLE_WIDTH/TABLE_HEIGHT.
# The two services can't share a module across the seam, and the bound
# belongs here too: layouts is the one storing coordinates, so it's the one
# that must refuse to store a cue or ball sitting off the table.
TABLE_WIDTH = 100
TABLE_HEIGHT = 50


class ValidationError(ValueError):
    pass


def _require_number(value, field):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{field} must be a number")
    return float(value)


def _validate_point(point, field):
    if not isinstance(point, dict):
        raise ValidationError(f"{field} must be an object with x and y")
    x = _require_number(point.get("x"), f"{field}.x")
    y = _require_number(point.get("y"), f"{field}.y")
    if not (0 <= x <= TABLE_WIDTH) or not (0 <= y <= TABLE_HEIGHT):
        raise ValidationError(f"{field} is outside the table bounds")
    return x, y


def validate_layout_payload(data):
    if not isinstance(data, dict):
        raise ValidationError("request body must be a JSON object")
    if "cue" not in data:
        raise ValidationError("cue is required")
    cue_x, cue_y = _validate_point(data["cue"], "cue")

    if "balls" not in data:
        raise ValidationError("balls is required")
    balls = data["balls"]
    if not isinstance(balls, list):
        raise ValidationError("balls must be a list")

    validated_balls = []
    for i, ball in enumerate(balls):
        if not isinstance(ball, dict):
            raise ValidationError(f"balls[{i}] must be an object")
        number = ball.get("number")
        if not isinstance(number, int) or isinstance(number, bool):
            raise ValidationError(f"balls[{i}].number must be an integer")
        x, y = _validate_point(ball, f"balls[{i}]")
        validated_balls.append({"number": number, "x": x, "y": y})

    return {"x": cue_x, "y": cue_y}, validated_balls


def validate_attempt_payload(data):
    if not isinstance(data, dict):
        raise ValidationError("request body must be a JSON object")
    succeeded = data.get("succeeded")
    if not isinstance(succeeded, bool):
        raise ValidationError("succeeded is required and must be true or false")
    notes = data.get("notes", "")
    if not isinstance(notes, str):
        raise ValidationError("notes must be a string")
    return succeeded, notes
