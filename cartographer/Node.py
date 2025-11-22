import json
import math
import heapq
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional, Any


class Node(ABC):
    def __init__(self, x_coordinate, y_coordinate, identifier, closed_corridor, accessibility, level):
        self._x_coordinate = x_coordinate
        self._y_coordinate = y_coordinate
        self._identifier = identifier
        self._closed_corridor = closed_corridor
        self._accessibility = accessibility
        self._level = level

    def get_x_coordinate(self):
        return self._x_coordinate

    def get_y_coordinate(self):
        return self._y_coordinate

    def get_identifier(self):
        return self._identifier

    def is_closed_corridor(self):
        return self._closed_corridor

    def is_accessible(self):
        return self._accessibility

    def get_level(self):
        return self._level

    @staticmethod
    def get_level_difference(node1, node2):
        difference = node1.get_level() - node2.get_level()
        if difference > 0:
            return -1
        elif difference < 0:
            return 1
        else:
            return 0

    @abstractmethod
    #Gives back True if the fronted can see the Node during search.
    def is_visible_to_client(self) -> bool:
        pass

    def is_text_in_identifier(self, text):
        if text == "":
            return False
        if text.lower() in self._identifier.lower():
            return True
        return False

    def __str__(self):
        return ("[x: " + str(self._x_coordinate) +
        ", y: " + str(self._y_coordinate) +
        ", identifier: " + self._identifier +
        ", closed_corridor: " + str(self._closed_corridor) +
        ", accessibility: " + str(self._accessibility) +
        ", level: " + str(self._level))


#This class contains nodes that can be searched, and have specific name/names too.
class Targetable(Node):
    def __init__(self, x_coordinate, y_coordinate, identifier, closed_corridor, accessibility, level, *aliases):
        super().__init__(x_coordinate, y_coordinate, identifier, closed_corridor, accessibility, level)
        self.__aliases = aliases

    def is_text_in_aliases(self, text):
        if text == "":
            return False
        for alias in self.__aliases:
            if text.lower() in alias.lower():
                return True
        return False

    def get_aliases(self):
        return self.__aliases

    def is_visible_to_client(self) -> bool:
        return True

#This class containes leading Nodes, that helps connect Targetable nodes.
class NotTargetable(Node):
    def __init__(self, x_coordinate, y_coordinate, identifier, closed_corridor, accessibility, level):
        super().__init__(x_coordinate, y_coordinate, identifier, closed_corridor, accessibility, level)
        self.__closed_corridor = closed_corridor
        self.__accessibility = accessibility

    def is_visible_to_client(self) -> bool:
        return False

#Graph class contains a building's nodes in a list, and edges in a adjacency list witch will help faster search results.
class Graph:
    def __init__(self):
        self._nodes: List[Node] = []
        self._name_to_index: Dict[str, int] = {}
        self._adjacency_list: List[List[Tuple[int, float]]] = []
        self.levels: Dict[int, Dict[str, float]] = {}
        self.floor_height_cm = 1000

    #This function search for targetables by the search_text in the identifier and aliases attribute, so more result
    #will be genereated.
    def search_for_targetables(self, search_text):
        targetable_list = []
        for node in self._nodes:
            appended = False
            if len(targetable_list) > 9:
                break
            if node.is_visible_to_client() and node.is_text_in_identifier(search_text):
                appended = True
                targetable_list.append(node)

            if node.is_visible_to_client() and node.is_text_in_aliases(search_text) and not appended:
                targetable_list.append(node)
        return targetable_list

    def get_id_to_index(self):
        return self._name_to_index

    def add_level_metadata(self, level: int, origin_x: float, origin_y: float, pixel_to_cm: float):
        self.levels[int(level)] = {"x": origin_x, "y": origin_y, "pixel_to_cm": float(pixel_to_cm)}

    def add_node(self, node: Node):
        index = len(self._nodes)
        self._nodes.append(node)
        self._name_to_index[node.get_identifier()] = index
        self._adjacency_list.append([])

    def add_edge_by_indices(self, sourceIndex: int, goalIndex: int, weight: float):
        self._adjacency_list[sourceIndex].append((goalIndex, weight))
        self._adjacency_list[goalIndex].append((sourceIndex, weight))

    def add_edge_by_name(self, name1: str, name2: str, weight: float):
        sourceIndex = self._name_to_index[name1]
        goalIndex = self._name_to_index[name2]
        self.add_edge_by_indices(sourceIndex, goalIndex, weight)

    def get_node(self, index: int) -> Node:
        return self._nodes[index]

    def get_index(self, identifier: str) -> int:
        return self._name_to_index[identifier]

    #Gives back true if the Node can be used as a part of a route.
    def is_usable_index(self, index: int, accessibility: bool, use_closed_corridors: bool) -> bool:
        node = self._nodes[index]
        return (
                (not accessibility or node.is_accessible()) and
                (use_closed_corridors or not node.is_closed_corridor())
        )

    #Calculates the shortest path in a graph between two points
    def dijkstra(self, source_id: str, goal_id: str, accessible=True, use_closed_corridors=False):
        source_index = self.get_index(source_id)
        goal_index = self.get_index(goal_id)
        node_quantity = len(self._nodes)
        distance = [math.inf]*node_quantity
        previous_list: List[Optional[int]] = [None]*node_quantity
        distance[source_index] = 0
        heap = [(0, source_index)]
        visited = [False]*node_quantity

        while heap:
            popped_distance, popped_node_index = heapq.heappop(heap)
            if visited[popped_node_index]:
                continue
            visited[popped_node_index] = True
            if popped_node_index == goal_index:
                break
            for adjacent_node_index, adjacent_weight in self._adjacency_list[popped_node_index]:
                if not self.is_usable_index(adjacent_node_index, accessible, use_closed_corridors):
                    continue
                new_distance = popped_distance + adjacent_weight
                if new_distance < distance[adjacent_node_index]:
                    distance[adjacent_node_index] = new_distance
                    previous_list[adjacent_node_index] = popped_node_index
                    heapq.heappush(heap, (new_distance, adjacent_node_index))
        return self._reconstruct_path(previous_list, source_index, goal_index)

    #Recalculates a Node coordinates, so during a route finding process the nodes in different levels can be compared.
    def node_real_coords_cm(self, node_index: int) -> Tuple[float, float]:
        node = self._nodes[node_index]
        level_number = int(node.get_level())
        level_data = self.levels.get(level_number)
        if level_data:
            global_origin_x = level_data.get("x", 0)
            global_origin_y = level_data.get("y", 0)
            scale = level_data.get("pixel_to_cm", 1.0)
        else:
            global_origin_x = 0
            global_origin_y = 0
            scale = 1.0
        real_x_coordinate = node.get_x_coordinate() - global_origin_x
        real_y_coordinate = node.get_y_coordinate() - global_origin_y
        return real_x_coordinate * scale, real_y_coordinate * scale

    #Caluclates the estimated distnace between two Node
    def heuristic(self, node_a_index: int, node_b_index: int) -> float:
        node_a_real_x, node_a_real_y = self.node_real_coords_cm(node_a_index)
        node_b_real_x, node_b_real_y = self.node_real_coords_cm(node_b_index)
        z_axis_difference = self.floor_height_cm * abs(self._nodes[node_a_index].get_level() - self._nodes[node_b_index].get_level())
        return math.hypot(node_a_real_x - node_b_real_x, node_a_real_y - node_b_real_y, z_axis_difference)

    # Calculates a short path between two nodes if the heuristic is good.
    # If the graph contains many more edges than nodes, this algorithm may be faster,
    # but the resulting path will not necessarily be the shortest.
    def astar(self, source_name: str, goal_name: str, accessible=True, use_closed_corridors=False):
        source_index = self._name_to_index[source_name]
        goal_index = self._name_to_index[goal_name]
        node_quantity = len(self._nodes)
        route_cost = [math.inf] * node_quantity
        total_estimated_cost = [math.inf] * node_quantity
        previous_indexes: List[Optional[int]] = [None] * node_quantity
        route_cost[source_index] = 0.0
        total_estimated_cost[source_index] = self.heuristic(source_index, goal_index)
        heap = [(total_estimated_cost[source_index], source_index)]
        closed_nodes = [False] * node_quantity

        while heap:
            _, popped_index = heapq.heappop(heap)
            if closed_nodes[popped_index]:
                continue
            if popped_index == goal_index:
                break
            closed_nodes[popped_index] = True
            for node_index, weight in self._adjacency_list[popped_index]:
                if not self.is_usable_index(node_index, accessible, use_closed_corridors):
                    continue

                new_cost = route_cost[popped_index] + weight
                if new_cost < route_cost[node_index]:
                    previous_indexes[node_index] = popped_index
                    route_cost[node_index] = new_cost
                    total_estimated_cost[node_index] = new_cost + self.heuristic(node_index, goal_index)
                    heapq.heappush(heap, (total_estimated_cost[node_index], node_index))
        return self._reconstruct_path(previous_indexes, source_index, goal_index)

    #This function gives back the node list by the gives Node indexes
    def _reconstruct_path(self, previous_indexes: List[Optional[int]], source: int, goal: int):
        if previous_indexes[goal] is None and source != goal:
            return []
        path_index = []
        current = goal
        while current is not None:
            path_index.insert(0, current)
            current = previous_indexes[current]

        return [self._nodes[i] for i in path_index]

    def count_edges(self):
        edges = 0
        for neighbors in self._adjacency_list:
            edges += len(neighbors)

        return edges

#Graphbuilder can make a Graph out of JSON datafiles
class GraphBuilder:
    @staticmethod
    def from_json(data: Dict[str, Any], floor_height_cm: float = 1000) -> Graph:
        graph = Graph()
        graph.floor_height_cm = float(floor_height_cm)

        for level_key, level_value in data.get("levels", {}).items():
            graph.add_level_metadata(int(level_key), level_value.get("x", 0), level_value.get("y", 0),
            level_value.get("pixel_to_cm", 1.0))

        for node in data.get("points", []):
            level = int(node.get("level", 0))
            if node.get("targetable", False):
                node = Targetable(
                    node["x"], node["y"], node["identifier"],
                    node.get("closedCorridor", False),
                    node.get("accessible", True),
                    level,
                    *node.get("aliases", [])
                )
            else:
                node = NotTargetable(
                    node["x"], node["y"], node["identifier"],
                    node.get("closedCorridor", False),
                    node.get("accessible", True),
                    level
                )
            graph.add_node(node)

        for edge in data.get("edges", []):
            source_name = edge["from"]
            goal_name = edge["to"]
            if source_name not in graph.get_id_to_index() or goal_name not in graph.get_id_to_index():
                continue
            distance = edge.get("distance", None)
            if distance is None:
                continue
            else:
                graph.add_edge_by_name(source_name, goal_name, float(distance))
        return graph

    @staticmethod
    def from_file(path: str, floor_height_cm: float = 1000):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GraphBuilder.from_json(data, floor_height_cm=floor_height_cm)


#Pathfinder can search for routes in a Graph and gives back the coordinates to the client
class PathFinder:
    @staticmethod
    def path_nodes_to_list(nodes):
        if not nodes:
            return  []

        list = []
        for node in nodes:
            list.append(
                {
                    "x": node.get_x_coordinate(),
                    "y": node.get_y_coordinate(),
                    "level": node.get_level()
                }
            )
        return list

    @staticmethod
    def find_path(graph: Graph,
                  source_id: str,
                  goal_id: str,
                  accessible: bool = True,
                  use_closed_corridors: bool = False,
                  algorithm: str = "dijkstra",
                  ):

        algorithm = algorithm.lower()

        try:
            _ = graph.get_index(source_id)
            _ = graph.get_index(goal_id)
        except Exception as e:
            return False

        if algorithm == "astar":
            path_nodes = graph.astar(source_id, goal_id, accessible, use_closed_corridors)
        else:
            path_nodes = graph.dijkstra(source_id, goal_id, accessible, use_closed_corridors)

        path_list = PathFinder.path_nodes_to_list(path_nodes)

        if path_list is None:
            path_list = []

        return path_list
