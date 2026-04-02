from rdflib import Graph, URIRef, Literal, BNode
import json
from rdflib.compare import to_canonical_graph
from rdflib import SH, RDFS, RDF
from functools import cached_property
import os


class FoundConstraints:
    def __init__(self, graph: Graph, simple_constraints=None, complex_constraints=None, rules=None):
        self.simple_constraints = set(simple_constraints) if simple_constraints else set()
        self.complex_constraints = set(complex_constraints) if complex_constraints else set()
        self.rules = set(rules) if rules else set()
        self.graph = graph

    def merge(self, other):
        """Merge another FoundConstraints into this one."""
        self.simple_constraints.update(other.simple_constraints)
        self.complex_constraints.update(other.complex_constraints)
        self.rules.update(other.rules)

    def copy(self):
        """Create a copy of this FoundConstraints instance."""
        return FoundConstraints(self.simple_constraints.copy(), self.complex_constraints.copy(), self.rules.copy())


class ResolvedFoundConstraints(FoundConstraints):
    def __init__(self, concept: URIRef, found: FoundConstraints):
        super().__init__(found.graph, found.simple_constraints, None, found.rules)
        self.concept = concept
        self.label = str(self.graph.value(concept, RDFS.label) or (self.graph.qname(concept) if isinstance(concept, URIRef) else None) or concept)
        self.labels = {}
        self.stable_ids = {}
        self.cbds = {}
        self.stable_id = self.get_stable_id(concept)

        self._gather_labels()
        self._gather_stable_ids()
        self._gather_cbds()

    def as_dict(self):
        return {
            "simple_constraints": list(self.simple_constraints),
            "complex_constraints": list(self.complex_constraints),
            "rules": list(self.rules),
            "label": str(self.label),
            "stable_id": self.stable_id,
            "labels": self.labels,
            "stable_ids": self.stable_ids,
            "cbd": self.graph.cbd(self.concept).serialize(format="turtle"),
            "cbds": {str(k): v.serialize(format="turtle") for k, v in self.cbds.items()},
        }

    def _gather_labels(self):
        # loop over all constraints and rules and gather their labels
        for constraint in self.simple_constraints | self.complex_constraints | self.rules:
            label = self.graph.value(constraint, RDFS.comment)
            # remove newlines
            label = str(label).replace("\n", " ") if label else None
            self.labels[constraint] = label

    def _gather_stable_ids(self):
        # loop over all constraints and rules and gather their stable IDs
        for constraint in self.simple_constraints | self.complex_constraints | self.rules:
            stable_id = self.get_stable_id(constraint)
            assert stable_id is not None
            self.stable_ids[constraint] = stable_id

    def _gather_cbds(self):
        # loop over all constraints and rules and gather their CBDS
        for constraint in self.simple_constraints | self.complex_constraints | self.rules:
            cbd_g = self.graph.cbd(constraint)
            self.cbds[constraint] = cbd_g

    def related_constraints_as_markdown_table(self, http_base):
        """Return a markdown table of the constraints.
        Formatted as:

        Related Cosntraints

        | Description | Link |
        |-------------| ---- |
        | constraint1 | [Link](<http base> + stable_id) |
        """
        if not len(self.simple_constraints):
            return ""

        if not http_base.endswith("#"):
            http_base += "#"

        # header
        table = "\n: Related Constraints\n"
        table += "\n| Description | Link |\n"
        table += "|-----------------------------|---|\n"

        # rows
        for constraint in sorted(self.simple_constraints, key=lambda c: self.labels[c]):
            label = self.labels[constraint]
            stable_id = self.stable_ids[constraint]
            table += f"| {label} | [Link]({http_base}{stable_id}) |\n"

        return table

    def related_rules_as_markdown_table(self, http_base):
        """Return a markdown table of the rules.
        Formatted as:

        Related Rules

        | Description | Link |
        |-------------|---|
        | rule1 | [Link](<http base> + stable_id) |
        """
        if not len(self.rules):
            return ""
        if not http_base.endswith("#"):
            http_base += "#"

        # header
        table = "\n: Related Inference Rules\n"
        table += "\n| Description | Link |\n"
        table += "|-----------------------------|---|\n"

        # rows
        for rule in sorted(self.rules, key=lambda c: self.labels[c]):
            label = self.labels[rule]
            stable_id = self.stable_ids[rule]
            table += f"| {label} | [Link]({http_base}{stable_id}) |\n"

        return table

    def get_stable_id(self, constraint):
        """Generate a stable ID for a constraint."""
        assert not isinstance(constraint, Literal), f"Expected URIRef or bnode, got {constraint}"
        if isinstance(constraint, URIRef):
            return self.graph.namespace_manager.qname(constraint)
        # handle bnodes
        return f"b-{hash(constraint)}"

    def dump(self):
        if self.simple_constraints or self.complex_constraints or self.rules:
            print(self.concept)
            if self.simple_constraints:
                print(f"    {len(self.simple_constraints)} simple constraints: {self.simple_constraints}")
                for simple in self.simple_constraints:
                    print(f"        label={self.labels[simple]}")
                    print(f"        stableid={self.stable_ids[simple]}")

            if self.complex_constraints:
                print(f"    {len(self.complex_constraints)} complex constraints: {self.complex_constraints}")
                for complex_s in self.complex_constraints:
                    print(f"        label={self.labels[complex_s]}")
                    print(f"        stableid={self.stable_ids[complex_s]}")

            if self.rules:
                print(f"    {len(self.rules)} rules: {self.rules}")
                for rule in self.rules:
                    print(f"        label={self.labels[rule]}")
                    print(f"        stableid={self.stable_ids[rule]}")


class ConstraintExtractor:
    def __init__(self, graph: Graph):
        if not os.path.exists("/tmp/canonical.ttl"):
            to_canonical_graph(graph).serialize("/tmp/canonical.ttl", format="turtle")
        self.graph = Graph().parse("/tmp/canonical.ttl", format="turtle")
        self.graph.namespace_manager = graph.namespace_manager
        self.constraints = {}

    def get_constraints(self, concept: URIRef) -> ResolvedFoundConstraints:
        if concept in self.constraints:
            return self.constraints[concept]

        found = self.get_nodeshape_constraints(concept)

        while True:
            # Store the original size of complex_constraints
            initial_size = len(found.complex_constraints)

            # Iterate over a copy of complex_constraints to prevent modification during iteration
            for constraint in list(found.complex_constraints):
                if self.constraint_is_list(constraint):
                    res = self.get_constraint_list(constraint)
                    found.merge(res)
                else:
                    res = self.get_nodeshape_constraints(constraint)
                    found.merge(res)

            # Break the loop if no new constraints were added
            if len(found.complex_constraints) == initial_size:
                break

        # # TODO: may need some sort of fixed-point
        # for constraint in found.complex_constraints:
        #     if self.constraint_is_list(constraint):
        #         res = self.get_constraint_list(constraint)
        #         found.merge(res)
        #     else:
        #         res = self.get_nodeshape_constraints(constraint)
        #         found.merge(res)

        # save it in the cache
        resolved = ResolvedFoundConstraints(concept, found)
        # resolved.dump()
        self.constraints[concept] = resolved

        return resolved

    def to_json(self, path: str):
        # write all constraints to a json file
        for defn in list(self.constraints.values()):
            for constraint in defn.simple_constraints:
                self.get_constraints(constraint)
            for constraint in defn.rules:
                self.get_constraints(constraint)
        json.dump({name: c.as_dict() for name, c in self.constraints.items()}, open(path, "w"), indent=2)


    def constraint_is_list(self, constraint: URIRef):
        return self.graph.value(constraint, RDF.first) is not None

    def get_constraint_list(self, constraint: URIRef) -> FoundConstraints:
        found = FoundConstraints(self.graph)
        for node in self.walk_list(constraint):
            found.merge(self.get_nodeshape_constraints(node))
        return found

    def walk_list(self, node):
        """Given the head of an RDF list, yield each of the nodes."""
        while node != RDF.nil:
            yield self.graph.value(node, RDF.first)
            node = self.graph.value(node, RDF.rest)

    def get_nodeshape_constraints(self, nodeshape: URIRef) -> FoundConstraints:
        """
        Constraints on a node shape are:
        - ?nodeshape sh:property ?constraint
        - ?nodeshape sh:sparql ?constraint
        - ?constraint sh:targetClass ?nodeshape
        - ?nodeshape sh:or|sh:and|sh:not|sh:xone ?constraint

        Do *not* include any constraint with an sh:rule.
        """
        simple_constraints = []
        complex_constraints = []
        rules = []

        # Start with property and sparql constraints on the node shape
        for constraint in self.graph.objects(nodeshape, SH.property | SH.sparql):
            if self.graph.value(constraint, RDFS.comment):
                simple_constraints.append(constraint)
            else:
                complex_constraints.append(constraint)

        # Get "external" constraints that point to our nodeshape.
        for constraint in self.graph.subjects(SH.targetClass, nodeshape):
            if self.graph.value(constraint, RDFS.comment):
                simple_constraints.append(constraint)
            else:
                complex_constraints.append(constraint)

        # Get "compound" constraints that are part of our nodeshape.
        for constraint in self.graph.objects(nodeshape, SH["or"] | SH["and"] | SH["not"] | SH.xone):
            if self.graph.value(constraint, RDFS.comment):
                simple_constraints.append(constraint)
            else:
                complex_constraints.append(constraint)

        # get rules
        for rule in self.graph.objects(nodeshape, SH.rule):
            rules.append(rule)

        return FoundConstraints(self.graph, simple_constraints, complex_constraints, rules)
