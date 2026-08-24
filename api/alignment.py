"""Alignment grid: per-facet same/different comparison between an idea and one company.

See CONTEXT.md — alignment is bilateral-only (both sides have every facet)
and is what "similarity" means on screen. Never a scalar score.
"""


def build_alignment_grid(idea_facets: dict, company_facets: dict) -> dict:
    grid = {}
    for name, idea_facet in idea_facets.items():
        company_value = company_facets[name]["value"]
        grid[name] = {
            "idea_value": idea_facet["value"],
            "company_value": company_value,
            "same": idea_facet["value"] == company_value,
        }
    return grid
