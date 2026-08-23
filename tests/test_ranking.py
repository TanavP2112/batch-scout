import numpy as np

from api.ranking import rank_from_scores
from tests.conftest import assert_excluded_ranked_last


def test_rank_from_scores_descending_order_no_exclusion():
    scores = np.array([0.1, 0.9, 0.5, 0.3])

    result = rank_from_scores(scores, None)

    indices = [idx for idx, _ in result]
    assert indices == [1, 2, 3, 0]


def test_rank_from_scores_covers_full_corpus_when_no_exclusion():
    scores = np.array([0.1, 0.9, 0.5, 0.3])

    result = rank_from_scores(scores, None)

    assert sorted(idx for idx, _ in result) == [0, 1, 2, 3]
    assert len(result) == 4


def test_rank_from_scores_exact_score_passthrough():
    scores = np.array([0.1, 0.9, 0.5, 0.3])

    result = rank_from_scores(scores, None)

    for idx, score in result:
        assert score == scores[idx]


def test_rank_from_scores_exclusion_pushes_index_to_end():
    # Index 1 would be ranked first if not excluded.
    scores = np.array([0.2, 0.99, 0.5, 0.3])

    result = rank_from_scores(scores, 1)

    indices = [idx for idx, _ in result]
    assert_excluded_ranked_last(indices, excluded=1, others=(0, 2, 3))


def test_rank_from_scores_exclusion_with_none_is_unaffected():
    scores = np.array([0.5, 0.1, 0.9])

    result = rank_from_scores(scores, None)

    indices = [idx for idx, _ in result]
    assert indices == [2, 0, 1]


def test_rank_from_scores_does_not_mutate_input_array():
    scores = np.array([0.2, 0.99, 0.5, 0.3])
    original = scores.copy()

    rank_from_scores(scores, 1)

    assert np.array_equal(scores, original)


def test_rank_from_scores_does_not_mutate_input_array_no_exclusion():
    scores = np.array([0.2, 0.99, 0.5, 0.3])
    original = scores.copy()

    rank_from_scores(scores, None)

    assert np.array_equal(scores, original)
