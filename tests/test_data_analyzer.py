"""Tests for the pure functions of data_analyzer: get_emoji and calculate_missing_pct.

Source stays ASCII (rule 4.1), so the emoji are written as escape sequences.
Each test names the failure it prevents.
"""

import numpy as np
import pandas as pd
import pytest

from data_analyzer import calculate_missing_pct, get_emoji

HAPPY = "\U0001F60A"    # smiling face, pct < 5
SLIGHT = "\U0001F642"   # slightly smiling face, 5 <= pct < 15
NEUTRAL = "\U0001F610"  # neutral face, 15 <= pct < 30
WORRIED = "\U0001F61F"  # worried face, 30 <= pct <= 50
CRYING = "\U0001F622"   # crying face, pct > 50


# --- get_emoji -------------------------------------------------------------

@pytest.mark.parametrize("pct,expected", [
    (0.0, HAPPY),
    (4.9, HAPPY),
    (5.0, SLIGHT),
    (14.9, SLIGHT),
    (15.0, NEUTRAL),
    (29.9, NEUTRAL),
    (30.0, WORRIED),
    (50.0, WORRIED),
    (50.1, CRYING),
    (100.0, CRYING),
])
def test_get_emoji_thresholds(pct, expected):
    """Prevents a shifted or inverted threshold: a value exactly on 5/15/30/50
    landing in the neighbouring bucket (e.g. `<=` written where `<` belongs),
    which would silently mislabel file quality in the HTML report."""
    assert get_emoji(pct) == expected


def test_get_emoji_upper_bound_is_inclusive_at_50():
    """Prevents the asymmetry at the last threshold from being 'fixed' into
    `< 50`: 50.0% missing must still be WORRIED, not CRYING, otherwise a file
    exactly at the limit changes verdict without any data change."""
    assert get_emoji(50.0) == WORRIED
    assert get_emoji(49.999) == WORRIED
    assert get_emoji(50.001) == CRYING


def test_get_emoji_returns_one_of_five_values():
    """Prevents a missing return branch (a path falling through to None), which
    would render the literal 'None' next to the file name in the report."""
    allowed = {HAPPY, SLIGHT, NEUTRAL, WORRIED, CRYING}
    for pct in [i * 0.5 for i in range(0, 201)]:
        assert get_emoji(pct) in allowed


# --- calculate_missing_pct -------------------------------------------------

def test_calculate_missing_pct_no_missing_is_zero():
    """Prevents an inverted count (counting present values instead of NaN),
    which would report a complete file as 100% missing."""
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    assert calculate_missing_pct(df) == 0.0


def test_calculate_missing_pct_all_missing_is_hundred():
    """Prevents the ratio being taken over rows or columns instead of cells:
    a frame of only NaN must give exactly 100.0."""
    df = pd.DataFrame({"a": [np.nan, np.nan], "b": [np.nan, np.nan]})
    assert calculate_missing_pct(df) == 100.0


def test_calculate_missing_pct_counts_cells_not_rows():
    """Prevents dividing by len(df) (rows) instead of df.size (cells): with
    1 NaN out of 2 rows x 2 columns the answer is 25.0, not 50.0."""
    df = pd.DataFrame({"a": [1, np.nan], "b": [3, 4]})
    assert calculate_missing_pct(df) == pytest.approx(25.0)


def test_calculate_missing_pct_is_not_scaled_as_fraction():
    """Prevents the *100 being dropped: the function returns percent, and the
    report prints the value straight after '% brakow'."""
    df = pd.DataFrame({"a": [1, np.nan, np.nan, np.nan]})
    assert calculate_missing_pct(df) == pytest.approx(75.0)


def test_calculate_missing_pct_empty_dataframe_is_hundred():
    """Prevents ZeroDivisionError on an empty file: df.size == 0 must short
    circuit to 100.0 instead of crashing the whole report generation."""
    assert calculate_missing_pct(pd.DataFrame()) == 100.0


def test_calculate_missing_pct_columns_without_rows_is_hundred():
    """Prevents the empty guard from checking only df.empty/columns: a frame
    with declared columns but zero rows still has size 0 and must give 100.0."""
    df = pd.DataFrame({"a": [], "b": []})
    assert df.size == 0
    assert calculate_missing_pct(df) == 100.0
