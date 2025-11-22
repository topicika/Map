from django.test import TestCase
from cartographer.Node import *

class TestNode(Node):
    def is_visible_to_client(self):
        return True


class NodeGraphTests(TestCase):
    def test_node_attributes(self):
        node = TestNode(10, 20, "A", False, True, 2)
        assert node.get_x_coordinate() == 10
        assert node.get_y_coordinate() == 20
        assert node.get_identifier() == "A"
        assert node.is_closed_corridor() is False
        assert node.is_accessible() is True
        assert node.get_level() == 2
        assert node.is_text_in_identifier("a") is True
        assert node.is_text_in_identifier("") is False
        assert node.is_text_in_identifier("b") is False


    def test_level_difference(self):
        node1 = TestNode(0, 0, "node1", False, True, 2)
        node2 = TestNode(0, 0, "node2", False, True, 1)
        assert Node.get_level_difference(node1, node2) == -1
        assert Node.get_level_difference(node2, node1) == 1
        assert Node.get_level_difference(node1, TestNode(0, 0, "node3", False, True, 2)) == 0


    def test_test_in_aliases(self):
        targetable = Targetable(0, 0, "Room", False, True, 0, "Office", "Lab")
        assert targetable.is_text_in_aliases("off") is True
        assert targetable.is_text_in_aliases("lab") is True
        assert targetable.is_text_in_aliases("thing") is False
        assert targetable.is_text_in_aliases("") is False


    def test_visibility(self):
        targetable = Targetable(0,0,"A", False, True, 0)
        not_targetable = NotTargetable(0,0,"B", False, True, 0)
        assert targetable.is_visible_to_client() is True
        assert not_targetable.is_visible_to_client() is False


    def test_graph_add_node_and_edge(self):
        graph = Graph()
        node1 = Targetable(0,0,"A", False, True, 0)
        node2 = Targetable(1,1,"B", False, True, 0)
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge_by_name("A", "B", 5)
        assert graph.count_edges() == 2
        assert graph.get_node(graph.get_index("A")).get_identifier() == "A"


    def test_search_for_targetables(self):
        graph = Graph()
        targetable1 = Targetable(0,0,"RoomA", False, True, 0, "Office")
        targetable2 = Targetable(0,0,"RoomB", False, True, 0)
        targetable3 = Targetable(0,0,"Kitchen", False, True, 0, "First", "Second")
        not_targetable = NotTargetable(0,0,"Hidden", False, True, 0)
        graph.add_node(targetable1)
        graph.add_node(targetable2)
        graph.add_node(targetable3)
        graph.add_node(not_targetable)
        results = graph.search_for_targetables("room")
        result = graph.search_for_targetables("con")
        assert len(results) == 2
        assert len(result) == 1


    def test_dijkstra(self):
        graph = Graph()
        node1 = Targetable(0,0,"A", False, True, 0)
        node2 = Targetable(1,0,"B", False, True, 0)
        node3 = Targetable(2,0,"C", False, True, 0)
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_node(node3)
        graph.add_edge_by_name("A", "B", 1)
        graph.add_edge_by_name("B", "C", 1)
        path = graph.dijkstra("A", "C")
        assert [n.get_identifier() for n in path] == ["A","B","C"]


    def test_astar(self):
        graph = Graph()
        node1 = Targetable(0,0,"A", False, True, 0)
        node2 = Targetable(1,0,"B", False, True, 0)
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge_by_name("A", "B", 1)
        path = graph.astar("A", "B")
        assert [n.get_identifier() for n in path] == ["A","B"]


    def test_real_coordinates(self):
        graph = Graph()
        graph.add_level_metadata(0, 10, 10, 2.0)
        node = Targetable(20, 30, "T", False, True, 0)
        graph.add_node(node)
        x,y = graph.node_real_coords_cm(0)
        assert x == (20 - 10) * 2
        assert y == (30 - 10) * 2


    def test_from_json(self):
        data = {
            "levels": {"0": {"x": 0, "y": 0, "pixel_to_cm": 1.0}},
            "points": [
                {"x": 0, "y": 0, "identifier": "A", "targetable": True, "level": 0, "accessible": True},
                {"x": 1, "y": 1, "identifier": "B", "targetable": False, "level": 0}
            ],
            "edges": [
                {"from": "A", "to": "B", "distance": 5}
            ]
        }
        graph = GraphBuilder.from_json(data)
        assert graph.count_edges() == 2


    def test_pathfinder_success(self):
        graph = Graph()
        node1 = Targetable(0,0,"A", False, True, 0)
        node2 = Targetable(1,0,"B", False, True, 0)
        graph.add_node(node1)
        graph.add_node(node2)
        graph.add_edge_by_name("A","B",1)
        path = PathFinder.find_path(graph, "A", "B")
        assert len(path) == 2
        assert path[0]["x"] == 0
        assert path[1]["x"] == 1


    def test_pathfinder_invalid_nodes(self):
        graph = Graph()
        node = Targetable(0,0,"A", False, True, 0)
        graph.add_node(node)
        assert PathFinder.find_path(graph, "A", "Z") is False
