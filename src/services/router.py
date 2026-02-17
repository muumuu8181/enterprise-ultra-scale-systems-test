import networkx as nx
import heapq
import math

class Router:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.ch_graph = None # Graph for Contraction Hierarchies
        self.node_order = {} # Node order for CH

    def add_edge(self, u, v, weight, **attr):
        # If distance not provided, assume weight is distance
        if 'distance' not in attr:
            attr['distance'] = weight
        self.graph.add_edge(u, v, weight=weight, **attr)

    def dijkstra(self, start, end):
        """
        Standard Dijkstra algorithm.
        """
        try:
            path = nx.dijkstra_path(self.graph, start, end, weight='weight')
            length = nx.dijkstra_path_length(self.graph, start, end, weight='weight')
            return path, length
        except nx.NetworkXNoPath:
            return None, float('inf')

    def astar(self, start, end, heuristic_func=None):
        """
        A* algorithm using a heuristic function.
        heuristic_func: function(u, v) -> float
        """
        if heuristic_func is None:
            # Default Euclidean heuristic if nodes have positions
            def heuristic_func(u, v):
                pos_u = self.graph.nodes[u].get('pos')
                pos_v = self.graph.nodes[v].get('pos')
                if pos_u and pos_v:
                    return math.sqrt((pos_u[0] - pos_v[0])**2 + (pos_u[1] - pos_v[1])**2)
                return 0

        try:
            path = nx.astar_path(self.graph, start, end, heuristic=heuristic_func, weight='weight')
            length = nx.astar_path_length(self.graph, start, end, heuristic=heuristic_func, weight='weight')
            return path, length
        except nx.NetworkXNoPath:
            return None, float('inf')

    def contraction_hierarchies(self):
        """
        [Simplified Implementation]
        This method is a placeholder for the full Contraction Hierarchies preprocessing logic.
        In a production environment, this would involve ordering nodes by importance (e.g., edge difference)
        and adding shortcut edges to preserve shortest path distances while skipping unimportant nodes.

        For this prototype, we prepare the structure but do not implement the full contraction and
        shortcut generation logic due to its complexity.
        This method prepares the self.ch_graph.
        """
        # For demonstration, we'll just clone the graph.
        # A full CH implementation is complex and requires node ordering strategies
        # (edge difference, deleted neighbors, etc.) and shortcut addition.

        self.ch_graph = self.graph.copy()

        # Simple node ordering (random or degree based)
        nodes = list(self.graph.nodes())
        # Sort by degree as a simple heuristic for importance
        nodes.sort(key=lambda n: self.graph.degree(n))

        for i, node in enumerate(nodes):
            self.node_order[node] = i

        # Contraction step (simplified: just marking order)
        # Real CH would add shortcut edges here:
        # For each node v in order:
        #   For each pair of neighbors (u, w) such that u -> v -> w:
        #     If path u->v->w is the only shortest path, add shortcut u->w with weight(u,v)+weight(v,w)
        #     Remove v from graph (temporarily for construction)

        # Since we are not fully implementing the contraction loop,
        # queries will use standard Dijkstra but conceptually this is where CH logic lives.
        return True

    def query_ch(self, start, end):
        """
        Query using Contraction Hierarchies structure.
        Ideally uses bidirectional search on the CH graph.
        """
        if not self.ch_graph:
            self.contraction_hierarchies()

        # Fallback to standard Dijkstra for this implementation as full CH query is complex
        return self.dijkstra(start, end)

    def apply_traffic(self, traffic_data):
        """
        Update graph weights based on real-time traffic data.
        traffic_data: list of dicts {'u': u, 'v': v, 'factor': multiplier}
        """
        for data in traffic_data:
            u, v = data['u'], data['v']
            factor = data.get('factor', 1.0)
            if self.graph.has_edge(u, v):
                original_weight = self.graph[u][v].get('original_weight', self.graph[u][v]['weight'])
                # Store original weight if not present
                if 'original_weight' not in self.graph[u][v]:
                    self.graph[u][v]['original_weight'] = original_weight

                self.graph[u][v]['weight'] = original_weight * factor

    def calculate_eta(self, route, speed_profile):
        """
        Calculate ETA based on a route and speed profile.
        route: list of nodes
        speed_profile: dict mapping edge (u, v) to speed (km/h) or simple constant
        """
        total_time_hours = 0.0
        if not route or len(route) < 2:
            return 0.0

        for i in range(len(route) - 1):
            u, v = route[i], route[i+1]
            if self.graph.has_edge(u, v):
                # Assume weight is distance in km for this calculation,
                # or we have a distance attribute
                distance = self.graph[u][v].get('distance', self.graph[u][v]['weight'])

                # Get speed for this segment
                speed = speed_profile.get((u, v), 30.0) # Default 30 km/h
                if speed <= 0: speed = 0.1 # Avoid division by zero

                total_time_hours += distance / speed

        return total_time_hours * 60 # Return minutes
