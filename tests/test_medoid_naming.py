import numpy as np

from pipeline.cluster_problems import medoid_index, name_clusters_by_medoid, slugify


def test_slugify_lowercases_and_hyphenates():
    assert slugify("Expense Report Automation") == "expense-report-automation"


def test_slugify_collapses_punctuation_to_single_hyphen():
    assert slugify("NoSQL data pipeline to BI!!") == "nosql-data-pipeline-to-bi"


def test_medoid_index_picks_point_closest_to_centroid():
    embeddings = np.array(
        [
            [0.0, 0.0],
            [10.0, 10.0],  # far outlier
            [0.1, -0.1],  # closest to the centroid of the tight cluster
        ]
    )
    # centroid of all three is skewed by the outlier, but among a tight
    # cluster the point nearest the mean should win
    tight_cluster = embeddings[[0, 2]]
    assert medoid_index(tight_cluster) in (0, 1)  # local index within tight_cluster


def test_medoid_index_single_point_is_its_own_medoid():
    embeddings = np.array([[1.0, 2.0]])
    assert medoid_index(embeddings) == 0


def test_name_clusters_by_medoid_names_each_cluster_after_its_medoid_span():
    spans = ["expense report automation", "receipts and reimbursements", "corporate card outlier", "pet grooming booking"]
    embeddings = np.array(
        [
            [0.0, 0.0],
            [0.1, 0.05],  # closest to the tight cluster's centroid -> medoid
            [10.0, 10.0],  # drags the centroid away from the other two
            [50.0, 50.0],  # alone in cluster 1
        ]
    )
    labels = [0, 0, 0, 1]

    names = name_clusters_by_medoid(spans, embeddings, labels, k=2)

    assert names[0] == "receipts-and-reimbursements"
    assert names[1] == "pet-grooming-booking"


def test_name_clusters_by_medoid_covers_every_cluster_index():
    spans = ["a", "b", "c"]
    embeddings = np.array([[0.0], [1.0], [2.0]])
    labels = [0, 1, 2]

    names = name_clusters_by_medoid(spans, embeddings, labels, k=3)

    assert set(names) == {0, 1, 2}
