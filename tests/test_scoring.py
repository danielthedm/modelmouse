"""Tests for scoring algorithms."""
import pytest
from modelmouse.services.scoring import (
    score_value,
    compare_outputs,
    compare_text_outputs,
    _score_string,
    _score_number,
    _score_array,
    _score_object,
)


class TestScoreString:
    def test_exact_match(self):
        assert _score_string("hello", "hello") == 100.0

    def test_case_insensitive(self):
        assert _score_string("Hello", "hello") == 95.0

    def test_trimmed_match(self):
        assert _score_string("  hello  ", "hello") == 90.0

    def test_substring_match(self):
        score = _score_string("hello world", "hello")
        assert 60 < score < 80

    def test_no_match(self):
        assert _score_string("foo", "bar") == 0.0


class TestScoreNumber:
    def test_exact_match(self):
        assert _score_number(100, 100) == 100.0

    def test_within_1_percent(self):
        assert _score_number(100, 101) == 100.0

    def test_within_5_percent(self):
        score = _score_number(100, 105)
        assert 90 <= score <= 95

    def test_zero_expected(self):
        assert _score_number(0, 0) == 100.0
        assert _score_number(1, 0) < 100

    def test_confidence_scoring(self):
        score = _score_number(0.85, 0.9, is_confidence=True)
        assert 80 <= score <= 100


class TestScoreArray:
    def test_exact_match(self):
        assert _score_array(["a", "b"], ["a", "b"]) == 100.0

    def test_partial_match(self):
        score = _score_array(["a", "b"], ["a", "b", "c"])
        assert 75 <= score <= 85

    def test_extra_items(self):
        score = _score_array(["a", "b", "c"], ["a", "b"])
        assert score < 100

    def test_empty_arrays(self):
        assert _score_array([], []) == 100.0
        assert _score_array(["a"], []) == 0.0


class TestScoreObject:
    def test_exact_match(self):
        obj = {"a": 1, "b": "hello"}
        assert _score_object(obj, obj) == 100.0

    def test_partial_match(self):
        actual = {"a": 1, "b": "hello"}
        expected = {"a": 1, "b": "world"}
        score = _score_object(actual, expected)
        assert 40 <= score <= 60

    def test_missing_field(self):
        actual = {"a": 1}
        expected = {"a": 1, "b": 2}
        score = _score_object(actual, expected)
        assert score < 100

    def test_extra_field(self):
        actual = {"a": 1, "b": 2, "c": 3}
        expected = {"a": 1, "b": 2}
        score = _score_object(actual, expected)
        assert score < 100


class TestCompareOutputs:
    def test_exact_match(self):
        result = compare_outputs({"a": 1}, {"a": 1})
        assert result["exact_match"] is True
        assert result["overall_score"] == 100.0

    def test_partial_match(self):
        result = compare_outputs({"a": 1, "b": 2}, {"a": 1, "b": 3})
        assert result["exact_match"] is False
        assert 75 <= result["overall_score"] <= 85

    def test_attribute_scores(self):
        result = compare_outputs(
            {"a": "hello", "b": 100},
            {"a": "hello", "b": 100}
        )
        assert result["attribute_scores"]["a"] == 100.0
        assert result["attribute_scores"]["b"] == 100.0

    def test_missing_attribute(self):
        result = compare_outputs({"a": 1}, {"a": 1, "b": 2})
        assert result["attribute_scores"]["b"] == 0.0
        assert result["attribute_matches"]["b"] is False


class TestCompareTextOutputs:
    def test_exact_match(self):
        result = compare_text_outputs("hello world", "hello world")
        assert result["exact_match"] is True
        assert result["overall_score"] == 100.0

    def test_case_difference(self):
        result = compare_text_outputs("Hello World", "hello world")
        assert result["exact_match"] is False
        assert result["overall_score"] == 95.0

    def test_no_expected(self):
        result = compare_text_outputs("hello", None)
        assert result["overall_score"] == 0.0
