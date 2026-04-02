"""
Find the classes defined in the model that are not referenced in the document
tree.
"""

import sys
import glob
from rdflib import Graph, Namespace, RDF

g = Graph()

g.parse("223standard.ttl", format="turtle")

for fname in glob.glob("../models/*.ttl"):
    g.parse(fname, format="turtle")
for fname in glob.glob("../vocab/*.ttl"):
    g.parse(fname, format="turtle")
for fname in glob.glob("../inference/*.ttl"):
    g.parse(fname, format="turtle")
for fname in glob.glob("../validation/*.ttl"):
    g.parse(fname, format="turtle")

# find the definitions
namespace_map = {}
prefix_definitions = []
for prefix, uriref in g.namespaces():
    namespace_map[prefix] = Namespace(uriref)
    prefix_definitions.append("PREFIX %s: <%s>" % (prefix, uriref))
prefix_header = "\n".join(prefix_definitions)

# use whatever was bound to doc prefix
if "doc" not in namespace_map:
    sys.stderr.write("error: 'doc' namespace not found\n")
    sys.exit(1)

DOC = namespace_map["doc"]
S223 = namespace_map["s223"]

doc_nodes = set()


def walk_list(node):
    """Given the head of an RDF list, yield each of the nodes."""
    while node != RDF.nil:
        yield g.value(node, RDF.first)
        node = g.value(node, RDF.rest)


def do_clause(node):
    """Generate the documentation for a given node."""
    doc_nodes.add(node)

    # recursively do subclauses
    child_subclauses = g.value(node, DOC.subclauses)
    if child_subclauses:
        for i, child in enumerate(walk_list(child_subclauses)):
            do_clause(child)


# look for all of the root documents (warning: unordered)
for root in g.subjects(RDF.type, DOC.Document):
    for i, child in enumerate(walk_list(g.value(root, DOC.subclauses))):
        do_clause(child)

# find the missing classes
query_string = """%s
    SELECT ?sub ?cls
    WHERE {
        ?cls rdf:type s223:Class ;
        FILTER NOT EXISTS {
            ?cls rdf:type ?cls }
        }
    """ % (
    prefix_header,
)
query_results = list(g.query(query_string))
if query_results:
    print("= Classes")
    print()
    for sub, node in query_results:
        if node not in doc_nodes:
            print(sub, node)
    print()

# find the missing properties
query_string = """%s
    SELECT ?prop
    WHERE {
        ?prop rdf:type rdf:Property .
        }
    """ % (
    prefix_header,
)
query_results = list(g.query(query_string))
if query_results:
    print("= Properties")
    print()
    for (node,) in g.query(query_string):
        if node not in doc_nodes:
            print(node)
    print()
