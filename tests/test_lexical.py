from api.lexical import LexicalRetriever, tokenize
from tests.conftest import assert_excluded_ranked_last


def test_tokenize_basic_punctuation_and_case():
    assert tokenize("Hello, World! 123") == ["hello", "world", "123"]


def test_tokenize_empty_string():
    assert tokenize("") == []


def test_tokenize_lowercases():
    assert tokenize("ABC def") == ["abc", "def"]


def test_tokenize_treats_whitespace_and_punctuation_as_separators():
    # Underscore is not an ASCII letter or digit, so it separates tokens too.
    assert tokenize("foo-bar_baz.qux") == ["foo", "bar", "baz", "qux"]


def test_tokenize_mixed_alphanumeric_runs():
    assert tokenize("abc123 456def") == ["abc123", "456def"]


def test_tokenize_only_punctuation_yields_no_tokens():
    assert tokenize("!!! ... ,,,") == []


def _corpus():
    return [
        {"id": 0, "long_description": "We build software for veterinarians to manage appointments."},
        {"id": 1, "long_description": "A marketplace connecting freelance photographers with clients."},
        {"id": 2, "long_description": "An accounting tool for small restaurants and cafes."},
    ]


def test_lexical_retriever_stores_companies():
    companies = _corpus()
    retriever = LexicalRetriever(companies)
    assert retriever.companies == companies


def test_lexical_retriever_ranks_matching_document_first():
    companies = _corpus()
    retriever = LexicalRetriever(companies)

    results = retriever.rank("veterinarians appointments")

    scores = {idx: score for idx, score in results}
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]
    # Ranked list should put index 0 first.
    assert results[0][0] == 0


def test_lexical_retriever_distinctive_keyword_wins():
    companies = _corpus()
    retriever = LexicalRetriever(companies)

    results = retriever.rank("photographers")

    scores = {idx: score for idx, score in results}
    assert scores[1] > scores[0]
    assert scores[1] > scores[2]


def test_lexical_retriever_exclude_index_pushes_to_end():
    companies = _corpus()
    retriever = LexicalRetriever(companies)

    results = retriever.rank("photographers", exclude_index=1)

    indices = [idx for idx, _ in results]
    assert_excluded_ranked_last(indices, excluded=1, others=(0, 2))
