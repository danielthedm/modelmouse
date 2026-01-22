from typing import Any, Dict

CONFIDENCE_ATTRIBUTES = {"confidence", "score", "probability", "certainty"}
CONFIDENCE_TOLERANCE = 0.15


def score_value(actual: Any, expected: Any, attr_name: str = "") -> float:
    """
    Score how well actual matches expected (0-100).
    """
    if expected is None:
        return 100.0 if actual is None else 0.0
    if actual is None:
        return 0.0

    if type(actual) != type(expected):
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            pass
        else:
            return 0.0

    if isinstance(expected, str):
        return _score_string(actual, expected)

    if isinstance(expected, (int, float)):
        is_confidence = attr_name.lower() in CONFIDENCE_ATTRIBUTES
        return _score_number(actual, expected, is_confidence=is_confidence)

    if isinstance(expected, bool):
        return 100.0 if actual == expected else 0.0

    if isinstance(expected, list):
        return _score_array(actual, expected)

    if isinstance(expected, dict):
        return _score_object(actual, expected)

    return 100.0 if actual == expected else 0.0


def _score_string(actual: str, expected: str) -> float:
    if actual == expected:
        return 100.0

    if actual.lower() == expected.lower():
        return 95.0

    if actual.strip().lower() == expected.strip().lower():
        return 90.0

    if len(expected) <= 20:
        if expected.lower() in actual.lower():
            return 70.0
        if actual.lower() in expected.lower():
            return 60.0

    actual_lower = actual.lower()
    expected_lower = expected.lower()

    if len(expected_lower) >= 3 and len(actual_lower) >= 3:
        expected_ngrams = set(_get_ngrams(expected_lower, 3))
        actual_ngrams = set(_get_ngrams(actual_lower, 3))
        if expected_ngrams and actual_ngrams:
            intersection = len(expected_ngrams & actual_ngrams)
            union = len(expected_ngrams | actual_ngrams)
            if union > 0:
                similarity = intersection / union
                return similarity * 50

    return 0.0


def _get_ngrams(s: str, n: int) -> list:
    return [s[i:i+n] for i in range(len(s) - n + 1)]


def _score_number(actual: float, expected: float, is_confidence: bool = False) -> float:
    if actual == expected:
        return 100.0

    if expected == 0:
        if actual == 0:
            return 100.0
        return max(0, 100 - abs(actual) * 100)

    relative_diff = abs(actual - expected) / abs(expected)

    if is_confidence:
        absolute_diff = abs(actual - expected)
        if absolute_diff <= CONFIDENCE_TOLERANCE:
            return 100.0 - (absolute_diff / CONFIDENCE_TOLERANCE) * 20
        else:
            return max(0, 80 - (absolute_diff - CONFIDENCE_TOLERANCE) * 200)

    if relative_diff <= 0.01:
        return 100.0
    elif relative_diff <= 0.05:
        return 95.0 - (relative_diff - 0.01) * 125
    elif relative_diff <= 0.10:
        return 90.0 - (relative_diff - 0.05) * 100
    elif relative_diff <= 0.25:
        return 85.0 - (relative_diff - 0.10) * 100
    elif relative_diff <= 0.50:
        return 70.0 - (relative_diff - 0.25) * 80
    else:
        return max(0, 50 - relative_diff * 50)


def _score_array(actual: list, expected: list) -> float:
    """
    Score array similarity using precision and recall (F1-score approach).
    """
    if not expected:
        return 100.0 if not actual else 0.0

    if not actual:
        return 0.0

    if all(isinstance(x, (str, int, float, bool)) for x in expected):
        def normalize(x):
            if isinstance(x, str):
                return x.lower().strip()
            return x

        expected_set = set(normalize(x) for x in expected)
        actual_set = set(normalize(x) for x in actual)

        true_positives = len(expected_set & actual_set)
        false_positives = len(actual_set - expected_set)
        false_negatives = len(expected_set - actual_set)

        if true_positives == 0:
            return 0.0

        precision = true_positives / len(actual_set) if actual_set else 0.0
        recall = true_positives / len(expected_set) if expected_set else 0.0

        if precision + recall == 0:
            return 0.0

        f1 = 2 * (precision * recall) / (precision + recall)

        return round(f1 * 100, 2)

    if all(isinstance(x, dict) for x in expected) and all(isinstance(x, dict) for x in actual):
        return _score_object_arrays(actual, expected)

    total_score = 0.0

    for i, exp_item in enumerate(expected):
        if i < len(actual):
            item_score = score_value(actual[i], exp_item)
            total_score += item_score

    avg_score = total_score / len(expected) if expected else 100.0

    extra_items = len(actual) - len(expected)
    if extra_items > 0:
        extra_ratio = extra_items / max(len(actual), 1)
        penalty = extra_ratio * 50
        avg_score = max(0, avg_score * (1 - penalty / 100))

    return round(avg_score, 2)


def _score_object_arrays(actual: list, expected: list) -> float:
    if not expected:
        return 100.0 if not actual else 50.0
    if not actual:
        return 0.0

    used_actual = set()
    total_score = 0.0

    for exp_item in expected:
        best_score = 0.0
        best_idx = -1

        for i, act_item in enumerate(actual):
            if i in used_actual:
                continue
            item_score = _score_object(act_item, exp_item)
            if item_score > best_score:
                best_score = item_score
                best_idx = i

        if best_idx >= 0:
            used_actual.add(best_idx)
        total_score += best_score

    return round(total_score / len(expected), 2)


def _score_object(actual: dict, expected: dict) -> float:
    if not expected:
        return 100.0 if not actual else 50.0
    if not actual:
        return 0.0

    scores = []

    for key, exp_value in expected.items():
        if key in actual:
            attr_score = score_value(actual[key], exp_value, attr_name=key)
        else:
            attr_score = 0.0
        scores.append(attr_score)

    extra_keys = set(actual.keys()) - set(expected.keys())
    if extra_keys and scores:
        penalty = min(len(extra_keys) * 5, 15)
        avg_score = sum(scores) / len(scores)
        return round(max(0, avg_score - penalty), 2)

    return round(sum(scores) / len(scores), 2) if scores else 100.0


def compare_outputs(actual: Any, expected: Any) -> Dict[str, Any]:
    """
    Compare actual output to expected output and return detailed scoring.
    """
    exact_match = _deep_equals(actual, expected)
    overall_score = score_value(actual, expected)

    attribute_scores = {}
    attribute_matches = {}

    if isinstance(expected, dict) and isinstance(actual, dict):
        for key, exp_value in expected.items():
            if key in actual:
                score = score_value(actual[key], exp_value, attr_name=key)
                attribute_scores[key] = round(score, 2)
                attribute_matches[key] = score >= 90
            else:
                attribute_scores[key] = 0.0
                attribute_matches[key] = False

        for key in actual:
            if key not in expected:
                attribute_scores[key] = 0.0
                attribute_matches[key] = False

    return {
        "exact_match": exact_match,
        "overall_score": round(overall_score, 2),
        "attribute_scores": attribute_scores,
        "attribute_matches": attribute_matches,
    }


def _deep_equals(a: Any, b: Any) -> bool:
    if type(a) != type(b):
        if isinstance(a, (int, float)) and isinstance(b, (int, float)):
            return a == b
        return False

    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_deep_equals(a[k], b[k]) for k in a)

    if isinstance(a, list):
        if len(a) != len(b):
            return False
        return all(_deep_equals(x, y) for x, y in zip(a, b))

    return a == b


def compare_text_outputs(actual: str, expected: str) -> Dict[str, Any]:
    """
    Compare text outputs for unschematized benchmarks.
    """
    if expected is None:
        return {
            "exact_match": False,
            "overall_score": 0.0,
            "attribute_scores": {},
            "attribute_matches": {},
        }

    if actual is None:
        return {
            "exact_match": False,
            "overall_score": 0.0,
            "attribute_scores": {},
            "attribute_matches": {},
        }

    exact_match = actual == expected

    overall_score = _score_string(actual, expected) if isinstance(actual, str) and isinstance(expected, str) else 0.0

    return {
        "exact_match": exact_match,
        "overall_score": round(overall_score, 2),
        "attribute_scores": {},
        "attribute_matches": {},
    }
