#!/usr/bin/python3

"""
Turtle To Markdown

This application loads Turtle files together into a graph.  It looks for a
doc:Document node as the root clause and doc:subclauses property for
each node for children, recursive descent.  For each node it generates
markdown content.

Because running the deductive closure with both RDFS and OWLRL semantics can
expanded graph.
"""

import sys
import argparse

from rdflib import Graph, Namespace, BNode, RDF
import owlrl

# globals
g = Graph()
doc_nodes = set()

S223 = Namespace("http://data.ashrae.org/standard223#")
SH = Namespace("http://www.w3.org/ns/shacl#")


def walk_list(node):
    """Given the head of an RDF list, yield each of the nodes."""
    while node != RDF.nil:
        yield g.value(node, RDF.first)
        node = g.value(node, RDF.rest)


def do_clause(node, clauses, document_node):
    """Generate the documentation for a given node."""
    global document, namespace_map

    # add this as a visited node
    doc_nodes.add(node)

    # get the node name and simplify it
    node_name = str(node)
    for prefix, namespace in namespace_map.items():
        if node_name.startswith(namespace):
            node_name = prefix + ":" + node_name[len(namespace) :]
            break

    # extract the clause title
    title_value = g.value(node, DOC.title)
    if title_value:
        header_text = title_value.value
    elif isinstance(node, BNode):
        header_text = "Untitled " + node_name
    else:
        header_text = node_name

    # build a clause number
    clause_number = ".".join(str(sect) for sect in clauses)

    # generate the clause name
    clause_name = clause_number + " " + header_text
    print(clause_name)

    document_child_node = {"name": clause_name}
    if "children" not in document_node:
        document_node["children"] = []
    document_node["children"].append(document_child_node)

    # recursively do subclauses
    child_subclauses = g.value(node, DOC.subclauses)
    if child_subclauses:
        for i, child in enumerate(walk_list(child_subclauses)):
            do_clause(child, clauses + [i + 1], document_child_node)


# build a parser for the command line arguments
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)

# parameter for input Turtle files and output Markdown file
parser.add_argument(
    "md",
    type=str,
    help="output markdown file",
)
parser.add_argument(
    "ttl",
    type=str,
    nargs="+",
    help="turtle files to load",
)

# add an option to run RDFS semantics
parser.add_argument(
    "--rdfs",
    action="store_true",
    help="run RDFS semantics",
)

# add an option to run OWLRL semantics
parser.add_argument(
    "--owlrl",
    action="store_true",
    help="run OWLRL semantics",
)

# add an option to run both RDFS and OWLRL semantics
parser.add_argument(
    "--both",
    action="store_true",
    help="run both RDFS and OWLRL semantics",
)

# sample additional option to store the expanded graph
parser.add_argument(
    "--expanded",
    type=str,
    help="store the expanded graph",
)

# parse the command line arguments
args = parser.parse_args()

# load the files
for fname in args.ttl:
    g.parse(fname, format="turtle")

# expand the graph
if args.rdfs or args.owlrl or args.both:
    if (args.rdfs and args.owlrl) or args.both:
        inferencer = owlrl.DeductiveClosure(owlrl.RDFS_OWLRL_Semantics)
    elif args.rdfs and not args.owlrl:
        inferencer = owlrl.DeductiveClosure(owlrl.RDFS_Semantics)
    elif not args.rdfs and args.owlrl:
        inferencer = owlrl.DeductiveClosure(owlrl.OWLRL_Semantics)
    inferencer.expand(g)

# make a reverse namespace
namespace_map = {}
for prefix, uriref in g.namespaces():
    namespace_map[prefix] = Namespace(uriref)

# use whatever was bound to doc prefix
if "doc" not in namespace_map:
    sys.stderr.write("error: 'doc' namespace not found\n")
    sys.exit(1)

# documentation uses a special prefix
DOC = namespace_map["doc"]

document_root = {"name": "Root"}

# look for all of the root documents (warning: unordered)
for root in g.subjects(RDF.type, DOC.Document):
    for i, child in enumerate(walk_list(g.value(root, DOC.subclauses))):
        do_clause(child, [i + 1], document_root)

html = """
<!DOCTYPE html>
<div id="container"></div>
<script src="d3.v7.min.js"></script>
<script type="module">

// Declare the chart dimensions and margins.
const width = 928;
// const height = 400;

const data = {data};
const root = d3.hierarchy(data);

const dx = 15;
const dy = width / (root.height + 1);

// Create a tree layout.
const tree = d3.tree().nodeSize([dx, dy]);

// Sort the tree and apply the layout.
// root.sort((a, b) => d3.ascending(a.data.name, b.data.name));
tree(root);

// Compute the extent of the tree. Note that x and y are swapped here
// because in the tree layout, x is the breadth, but when displayed, the
// tree extends right rather than down.
let x0 = Infinity;
let x1 = -x0;
root.each(d => {
    if (d.x > x1) x1 = d.x;
    if (d.x < x0) x0 = d.x;
    });

// Compute the adjusted height of the tree.
const height = x1 - x0 + dx * 2;

const svg = d3.create("svg")
  .attr("width", width)
  .attr("height", height)
  .attr("viewBox", [-dy / 3, x0 - dx, width, height])
  .attr("style", "max-width: 100%; height: auto; font: 10px sans-serif;");

const link = svg.append("g")
  .attr("fill", "none")
  .attr("stroke", "#555")
  .attr("stroke-opacity", 0.4)
  .attr("stroke-width", 1.5)
  .selectAll()
  .data(root.links())
  .join("path")
  .attr("d",
    d3.linkHorizontal()
      .x(d => d.y)
      .y(d => d.x)
    );

const node = svg.append("g")
  .attr("stroke-linejoin", "round")
  .attr("stroke-width", 3)
  .selectAll()
  .data(root.descendants())
  .join("g")
  .attr("transform",
    d => `translate(${d.y},${d.x})`
    );

node.append("circle")
  .attr("fill", d => d.children ? "#555" : "#999")
  .attr("r", 2.5);

node.append("text")
  .attr("dy", "0.31em")
  .attr("x", d => d.children ? -6 : 6)
  .attr("text-anchor", d => d.children ? "end" : "start")
  .text(d => d.data.name)
  .clone(true).lower()
  .attr("stroke", "white");

// Append the SVG element.
container.append(svg.node());

</script>
"""

with open("ttl-outline.html", "w") as f:
    f.write(html.replace("{data}", str(document_root)))  # document_root))
