"""Tests for the two pure functions of data_analyzer.py.

get_emoji           - threshold ladder 5 / 15 / 30 / 50
calculate_missing_pct - percent of NaN cells, including the empty DataFrame

ASCII only in the source (rule 4.1): the emoji are written as \\U escapes,
which are the exact strings data_analyzer.get_emoji returns.
"""

import pandas as pd
import pytest

from data_analyzer import calculate_missing_pct, get_emoji

HAPPY = "\U0001F60A"    # smiling face with smiling eyes, < 5%
SLIGHT = "\U0001F642"   # slightly smiling face, < 15%
NEUTRAL = "\U0001F610"  # neutral face, < 30%
WORRIED = "\U0001F61F"  # worried face, <= 50%
CRYING = "\U0001F622"   # crying face, > 50%

ALL_EMOJI = (HAPPY, SLIGHT, NEUTRAL, WORRIED, CRYING)


# --------------------------------------------------------------------------
# get_emoji
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "pct, expected",
    [
        (0.0, HAPPY),
        (4.9, HAPPY),
        (5.0, SLIGHT),     # threshold is "< 5", so 5.0 already falls through
        (14.9, SLIGHT),
        (15.0, NEUTRAL),   # "< 15"
        (29.9, NEUTRAL),
        (30.0, WORRIED),   # "< 30"
        (49.9, WORRIED),
        (50.0, WORRIED),   # "<= 50" - inclusive, unlike the three above
        (50.1, CRYING),
        (100.0, CRYING),
    ],
)
def test_get_emoji_thresholds(pct, expected):
    """Names the failure: an off-by-one-bucket emoji at a threshold value.

    Each threshold is probed from both sides (4.9/5.0, 14.9/15.0, 29.9/30.0,
    50.0/50.1), so turning any "<" into "<=" (or back), or reordering the
    branches, flips at least one case. Without the paired values a wrong
    comparison operator is invisible: mid-bucket inputs like 10% or 40%
    classify identically under both.
    """
    assert get_emoji(pct) == expected


def test_get_emoji_last_threshold_is_inclusive_at_50():
    """Names the failure: silently making the 50% boundary exclusive.

    The ladder is deliberately asymmetric - 5/15/30 are exclusive ("< 5") but
    the last one is inclusive ("<= 50"), so exactly 50.0% missing is still the
    worried face, not the crying one. A "consistency" cleanup that rewrote the
    last branch to "< 50" would pass every mid-bucket test and only break here.
    """
    assert get_emoji(50.0) == WORRIED
    assert get_emoji(50.0) != CRYING


def test_get_emoji_covers_the_range_with_five_distinct_values():
    """Names the failure: an unreachable bucket after editing the ladder.

    If two branches return the same emoji, or a threshold is written out of
    order (e.g. 30 before 15), the function still returns a string for every
    input and every single-value assertion may still pass - but one bucket is
    dead. Walking the range in 0.1 steps has to yield all five faces.
    """
    seen = {get_emoji(i / 10.0) for i in range(0, 1001)}
    assert seen == set(ALL_EMOJI)


# --------------------------------------------------------------------------
# calculate_missing_pct
# --------------------------------------------------------------------------

def test_calculate_missing_pct_empty_dataframe_is_100():
    """Names the failure: ZeroDivisionError (or 0.0) on an empty DataFrame.

    df.size is 0 for an empty frame, so the division must be guarded. The
    guard must return 100.0, not 0.0 - a file with nothing in it is the worst
    possible data quality, and 0.0 would report it as the happy face.
    """
    assert calculate_missing_pct(pd.DataFrame()) == 100.0


def test_calculate_missing_pct_columns_without_rows_is_100():
    """Names the failure: the empty guard keyed on len(df) instead of df.size.

    A frame with declared columns but zero rows has len(df) == 0 and
    df.size == 0, yet isnull().sum().sum() is also 0 - so an unguarded or
    wrongly guarded version returns 0.0 (happy face) for a file with no data.
    """
    assert calculate_missing_pct(pd.DataFrame(columns=["a", "b"])) == 100.0


def test_calculate_missing_pct_no_missing_is_zero():
    """Names the failure: an inverted count (notnull instead of isnull).

    On a fully populated frame a version counting present cells returns 100.0
    instead of 0.0. This is the anchor that makes the inversion visible; a
    half-missing frame would return 50.0 either way.
    """
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    assert calculate_missing_pct(df) == 0.0


def test_calculate_missing_pct_all_missing_is_100():
    """Names the failure: an inverted count, seen from the other end.

    Together with the no-missing case this pins the direction: all-NaN must be
    100.0, not 0.0.
    """
    df = pd.DataFrame({"a": [None, None], "b": [None, None]})
    assert calculate_missing_pct(df) == 100.0


def test_calculate_missing_pct_counts_cells_not_rows():
    """Names the failure: dividing by len(df) or by the column count.

    6 cells, 2 of them NaN -> 33.3%. Dividing by the 3 rows gives 66.7% and
    dividing by the 2 columns gives 100.0%, so the wrong denominator cannot
    hide. The frame is deliberately non-square (3 x 2) - with a square one all
    three denominators agree.
    """
    df = pd.DataFrame({"a": [1, None, 3], "b": [None, 5, 6]})
    assert calculate_missing_pct(df) == pytest.approx(2 / 6 * 100)


def test_calculate_missing_pct_returns_percent_not_fraction():
    """Names the failure: a missing "* 100", i.e. returning 0.5 for 50%.

    The value is fed straight into get_emoji, whose thresholds are in percent,
    so a fraction would classify a half-empty file (50.0 -> worried face) as
    0.5 -> happy face. The assertion is on the scale, not just the ratio.
    """
    df = pd.DataFrame({"a": [1, None], "b": [None, 4]})
    pct = calculate_missing_pct(df)
    assert pct == pytest.approx(50.0)
    assert get_emoji(pct) == WORRIED


def test_calculate_missing_pct_treats_nan_and_none_alike():
    """Names the failure: counting only float NaN and missing None/NaT.

    csv_merger reads mixed dtypes, so missing values arrive as NaN in numeric
    columns and as None in object columns. A check like "x != x" over the raw
    values catches the first and skips the second, halving the reported
    percentage for object columns.
    """
    df = pd.DataFrame({"num": [1.0, float("nan")], "txt": ["x", None]})
    assert calculate_missing_pct(df) == pytest.approx(50.0)
