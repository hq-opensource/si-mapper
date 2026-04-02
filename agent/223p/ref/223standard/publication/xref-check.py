"""
This application loads Turtle files together into a graph.  It looks for a
doc:Document node as the root clause and doc:subclauses property for
each node for children, recursive descent.  For each node it generates
the expanded clause name and comment text.
"""

import sys
import argparse

from typing import Dict

from rdflib import Graph, Namespace, URIRef, RDF

# globals
g = Graph()
doc_nodes: Dict[URIRef, str] = {}

DCTERMS = Namespace("http://purl.org/dc/terms#")
S223 = Namespace("http://data.ashrae.org/standard223#")
SH = Namespace("http://www.w3.org/ns/shacl#")


def walk_list(node):
    """Given the head of an RDF list, yield each of the nodes."""
    while node != RDF.nil:
        yield g.value(node, RDF.first)
        node = g.value(node, RDF.rest)


def do_clause(node, clauses):
    """Generate the reference for a given node."""
    global namespace_map

    # get the node name and simplify it
    node_name = str(node)
    for prefix, namespace in namespace_map.items():
        if node_name.startswith(namespace):
            node_name = prefix + ":" + node_name[len(namespace) :]
            break

    # build a clause number
    clause_number = ".".join(str(sect) for sect in clauses)

    # check for existing reference
    if node in doc_nodes:
        print(f"{node_name}: {doc_nodes[node]} -> {clause_number}")

    # save it
    doc_nodes[node] = clause_number

    # recursively do subclauses
    child_subclauses = g.value(node, DOC.subclauses)
    if child_subclauses:
        for i, child in enumerate(walk_list(child_subclauses)):
            do_clause(child, clauses + [i + 1])


# build a parser for the command line arguments
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument(
    "ttl",
    type=str,
    nargs="+",
    help="turtle files to load",
)

# parse the command line arguments
args = parser.parse_args()

# load the files
for fname in args.ttl:
    g.parse(fname, format="turtle")

# make a reverse namespace
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

# documentation uses a special prefix
DOC = namespace_map["doc"]

# look for all of the root documents (warning: unordered)
for root in g.subjects(RDF.type, DOC.Document):
    # for comment in g.objects(root, RDFS.comment):
    #     text = textwrap.dedent(comment.value)
    #     document += f"\n{text}\n"
    for i, child in enumerate(walk_list(g.value(root, DOC.subclauses))):
        do_clause(child, [i + 1])

if 0:
    for node_shape in g.subjects(RDF.type, SH.NodeShape):
        if node_shape in S223:
            if node_shape in doc_nodes:
                print(f"{node_shape} in document")
            doc_nodes[node_shape] = "node shape"

    for property_shape in g.subjects(RDF.type, SH.PropertyShape):
        if property_shape in S223:
            if node_shape in doc_nodes:
                print(f"{property_shape} in document")
            doc_nodes[property_shape] = "property shape"
