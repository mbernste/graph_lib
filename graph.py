import sys
import collections
from collections import defaultdict, deque

DEBUG = False

def main():
    source_to_targets = {
        'A': set(['B', 'C', 'D']),
        'B': set(['C', 'D', 'E']),
        'C': set(['E']),
        'D': set(['E']),
        'E': set()
    }
    graph = DirectedAcyclicGraph(source_to_targets)
    reduced_graph = transitive_reduction_on_dag(graph)
    #print reduced_graph.source_to_targets
    print topological_sort(reduced_graph)


class DirectedAcyclicGraph:
    """
    Implements a directed graph
    """
    def __init__(self, source_to_targets, target_to_sources=None):
        self.source_to_targets = source_to_targets
        if not target_to_sources:
            self.target_to_sources = defaultdict(lambda: set())
            for source, targets in source_to_targets.iteritems():
                for target in targets:
                    self.target_to_sources[target].add(source)
        else:
            self.target_to_sources = target_to_sources
        self.target_to_sources = dict(self.target_to_sources)
        self.source_to_targets = dict(self.source_to_targets)
        for node in source_to_targets:
            if node not in self.target_to_sources:
                self.target_to_sources[node] = set()
        for node in self.target_to_sources:
            if node not in self.source_to_targets:
                self.source_to_targets[node] = set()

    def add_edge(self, source, target):
        if source not in self.source_to_targets:
            self.source_to_targets[source] = set()
        if target not in self.target_to_sources:
            self.target_to_sources[target] = set()
        self.source_to_targets[source].add(target)
        self.target_to_sources[target].add(source)

    def descendent_nodes(self, node):
        return self._downstream_nodes(
            node,
            self.source_to_targets
        )

    def ancestor_nodes(self, node):
        return self._downstream_nodes(
            node,
            self.target_to_sources
        )

    def most_specific_nodes(self, nodes):
        most_specific_nodes = set()
        # Map terms to superterms
        node_to_supernodes = {}
        for node in nodes:
            node_to_supernodes[node] = self.ancestor_nodes(node)

        # Create "more-general-than" tree

        # The compliment of this set are the nodes that 
        # do not have an ancestor in the given  set of 
        # nodes
        have_relations = set() 
        more_general_than = defaultdict(lambda: set())
        for node_a in node_to_supernodes.keys():
            for node_b, b_supernodes in node_to_supernodes.iteritems():
                if node_a == node_b:
                    continue
                if node_a in b_supernodes:
                    more_general_than[node_a].add(node_b)
                    have_relations.update([node_a, node_b])
        more_general_than = dict(more_general_than)

        # Collect leaves of the tree
        for subs in more_general_than.values():
            for s in subs:
                if not s in more_general_than.keys():
                    most_specific_nodes.add(s)

        loner_nodes = set(nodes) - have_relations
        return most_specific_nodes | loner_nodes

    def _downstream_nodes(self, node, orig_to_dests):
        visited = set([node])
        q = deque([node])
        while len(q) > 0:
            orig = q.popleft()
            if orig not in orig_to_dests:
                continue
            for dest in orig_to_dests[orig]:
                if dest not in visited:
                    visited.add(dest)
                    q.append(dest)
        return visited

    def get_all_nodes(self):
        all_nodes = set(self.source_to_targets.keys())
        for target, sources in self.target_to_sources.iteritems():
            all_nodes.update(sources)
            all_nodes.add(target)
        return all_nodes

    def copy(self):
        return DirectedAcyclicGraph(self.source_to_targets.copy())

    def __eq__(self, other):
        if not isinstance(other, DirectedAcyclicGraph):
            return False
        self_all_nodes = frozenset(self.get_all_nodes())
        other_all_nodes = frozenset(other.get_all_nodes())
        if self_all_nodes != other_all_nodes:
            return False
        # TODO FINSIH THIS
    

class UndirectedGraph:
    """
    Implements a general undirected graph without edge weights
    using hash tables. Thus, this object is better for sparse
    graphs, which most graphs are.
    """
    def __init__(edges):
        self.node_to_neighbors = defaultdict(lambda: set())
        for edge in edges:
            node_a = edge[0]
            node_b = edge[1]
            self.node_to_neighbors[node_a].add(node_b)
            self.node_to_neighbors[node_b].add(node_a)

    def get_all_nodes(self):
        return set(self.node_to_neighbors.keys())


def transitive_reduction_on_dag(dag):
    """
    Compute the transitive reduction on a DAG. This function will not 
    work on a graph with cycles.
    """    
    # Set of (source, target) node pairs representing edges 
    # that should be removed in order to form the transitive 
    # reduction
    remove_edges = set()

    # For each node u, for each child v of u, for each descendant
    # v' of v, if v' is a child of u, then remove (u, v')
    for parent, children in dag.source_to_targets.iteritems():
        for child in children:
            descendants = set(dag.descendent_nodes(child)) - set([child])
            for remove_target in descendants & children:
                remove_edges.add((parent, remove_target))
    
    reduced_source_to_targets = dag.source_to_targets.copy()
    for edge in remove_edges:
        source = edge[0]
        target = edge[1]
        reduced_source_to_targets[source].remove(target)
    reduced_graph = DirectedAcyclicGraph(reduced_source_to_targets)
    return reduced_graph


def topological_sort(dag):
    """
    Perform a topological sort of nodes on a DAG
    """
    # Initialize the removed nodes to those with no incoming 
    # edges
    removed_nodes = set([
        node 
        for node in dag.get_all_nodes()
        if len(dag.target_to_sources[node]) == 0
    ])
    sorted_nodes = sorted(removed_nodes)
    remaining_nodes = dag.get_all_nodes() - removed_nodes
    while removed_nodes < dag.get_all_nodes():
        next_removed = set()
        for node in remaining_nodes:
            incoming_nodes = set(dag.target_to_sources[node]) - removed_nodes
            if len(incoming_nodes) == 0:
                next_removed.add(node)
        removed_nodes.update(next_removed)
        sorted_nodes += sorted(next_removed)
        remaining_nodes = dag.get_all_nodes() - removed_nodes
    return sorted_nodes


def moralize(graph):
    # Add edges between all nodes that have a common child
    for node_a in graph.get_all_nodes():
        children_a = set(graph.source_to_targets[node_a])
        for node_b in graph.get_all_nodes():
            children_b = set(graph.source_to_targets[node_b])
            if len(children_a & children_b) > 0:
                add_edges.append((node_a, node_b))
    undir_edges = set(add_edges)
    # Convert to an undirected graph
    for source, targets in graph.source_to_targets:
        for target in targets:
            undir_edges.add((source, target))
    return UndirectedGraph(edges)        
        

if __name__ == "__main__":
    main()
