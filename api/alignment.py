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
