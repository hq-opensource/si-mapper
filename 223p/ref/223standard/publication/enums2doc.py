#!/usr/bin/python3

"""
Enumerations
"""

import sys
import argparse

from rdflib import Graph, Namespace, BNode, RDF, RDFS, URIRef, Literal

# globals
gin = Graph()
gout = Graph()

S223 = Namespace("http://data.ashrae.org/standard223#")

# build a parser for the command line arguments
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

# parameter for input Turtle files and output Markdown file
parser.add_argument(
    "outfile",
    type=str,
    help="output markdown file",
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
    gin.parse(fname, format="turtle")

# make a reverse namespace
namespace_map = {}
prefix_definitions = []
for prefix, uriref in gin.namespaces():
    namespace_map[prefix] = Namespace(uriref)
    prefix_definitions.append("PREFIX %s: <%s>" % (prefix, uriref))
prefix_header = "\n".join(prefix_definitions)

# use whatever was bound to doc prefix
if "doc" not in namespace_map:
    sys.stderr.write("error: 'doc' namespace not found\n")
    sys.exit(1)

# documentation uses a special prefix
DOC = namespace_map["doc"]
gout.namespace_manager.bind("doc", str(DOC))
gout.namespace_manager.bind("s223", str(S223))

def walk_tree(node, indent):
    subclauses = []
    for subclass_node in gin.subjects(RDFS.subClassOf, node):
        subclauses.append(subclass_node)
        walk_tree(subclass_node, indent + 1)

    if subclauses:
        subject: URIRef = node
        predicate: URIRef = DOC.subclauses

        for subclass_node in subclauses:
            # create a blank node referencing the thing
            list_node = BNode()
            gout.add((list_node, RDF.first, subclass_node))

            # chain along this list node
            gout.add((subject, predicate, list_node))
            subject = list_node
            predicate = RDF.rest

        # end of the list
        gout.add((subject, predicate, RDF.nil))

    else:
        comment = ""
        for instance_node in gin.subjects(RDF.type, node):
            if not comment:
                comment += "\n: Enumerations\n"
                comment += "\n| Enumeration |\n| ----- |\n"
            if instance_node != node:
                comment += "| " + instance_node.n3(gout.namespace_manager) + " |\n"
        if comment:
            gout.add((node, RDFS.comment, Literal(comment)))


walk_tree(S223.EnumerationKind, 0)

# save the document
with open(args.outfile, "w") as f:
    gout.serialize(f.buffer, format="turtle")
