from api.alignment import build_alignment_grid
from api.facets import FACET_NAMES


def test_matching_facet_value_is_marked_same():
    idea_facets = {"customer": {"value": "SMB", "span": "small businesses"}}
    company_facets = {"customer": {"value": "SMB", "span": "small companies"}}

    grid = build_alignment_grid(idea_facets, company_facets)

    assert grid["customer"]["same"] is True


def test_differing_facet_value_is_marked_not_same():
    idea_facets = {"customer": {"value": "SMB", "span": "small businesses"}}
    company_facets = {"customer": {"value": "enterprise", "span": "large enterprises"}}

    grid = build_alignment_grid(idea_facets, company_facets)

    assert grid["customer"]["same"] is False


def test_grid_cell_carries_both_display_values():
    idea_facets = {"wedge": {"value": "faster", "span": "same-day"}}
    company_facets = {"wedge": {"value": "cheaper", "span": "half price"}}

    grid = build_alignment_grid(idea_facets, company_facets)

    assert grid["wedge"]["idea_value"] == "faster"
    assert grid["wedge"]["company_value"] == "cheaper"


def test_grid_covers_every_bilateral_facet():
    idea_facets = {name: {"value": "x", "span": "s"} for name in FACET_NAMES}
    company_facets = {name: {"value": "x", "span": "s"} for name in FACET_NAMES}

    grid = build_alignment_grid(idea_facets, company_facets)

    assert set(grid) == set(FACET_NAMES)
