import os
import pytest
from django.conf import settings
from cartographer.Node import GraphBuilder, PathFinder


LE_PATH = os.path.join(
    settings.BASE_DIR,
    "cartographer/static/buildings/LE.json"
)

def load_graphs(n):
    graphs = []
    for _ in range(n):
        graphs.append(GraphBuilder.from_file(LE_PATH))
    return graphs


def pick_nodes(graph):
    ids = list(graph.get_id_to_index().keys())
    return ids[0], ids[1]

@pytest.mark.parametrize("graph_count", [1, 10, 100])
def test_search_speed(benchmark, graph_count):
    graphs = load_graphs(graph_count)
    sample_graph = graphs[0]

    node, _ = pick_nodes(sample_graph)
    query = node[:3]

    def run():
        return sample_graph.search_for_targetables(query)

    result = benchmark(run)
    assert len(result) > 0, "Invalid identifier"


@pytest.mark.parametrize("graph_count", [1, 10, 100])
def test_dijkstra_speed_under_load(benchmark, graph_count):
    graphs = load_graphs(graph_count)
    choosen_graph = graphs[0]

    node1, node2 = pick_nodes(choosen_graph)

    def run():
        return PathFinder.find_path(
            choosen_graph,
            node1,
            node2,
            accessible=False,
            use_closed_corridors=True,
            algorithm="dijkstra",
        )

    path = benchmark(run)
    assert isinstance(path, list), "The result is not a List"


@pytest.mark.parametrize("graph_count", [1, 10, 100])
def test_astar_speed_under_load(benchmark, graph_count):
    graphs = load_graphs(graph_count)
    sample_graph = graphs[0]

    node1, node2 = pick_nodes(sample_graph)

    def run():
        return PathFinder.find_path(
            sample_graph,
            node1,
            node2,
            accessible=False,
            use_closed_corridors=True,
            algorithm="astar",
        )

    path = benchmark(run)
    assert isinstance(path, list), "The result is not a List"
