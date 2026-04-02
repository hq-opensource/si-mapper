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

import re
import sys
import textwrap
import argparse
from copy import copy
from hashlib import blake2b
import os
from constraints import ConstraintExtractor

from typing import Dict, List, Tuple

from rdflib import Graph, Namespace, BNode, RDF, RDFS, URIRef
import owlrl

# globals
g = Graph()
document = ""
extractor = None
doc_nodes = set()
clause_reference: Dict[str, str]
figure_count: Dict[int, int]
full_doc_tree: List[Tuple[URIRef, List[str], int]] = []
# Maps full clause path to node and vice versa for BFS numbering
path_by_node: Dict[URIRef, Tuple[str, ...]] = {}
node_by_path: Dict[Tuple[str, ...], URIRef] = {}
# Precomputed depth-first display index for nodes deeper than CUTOFF_DEPTH
dfs_display_index: Dict[Tuple[str, ...], int] = {}
# DFS-based display path (enumerated) for each node
display_path_by_node: Dict[URIRef, Tuple[str, ...]] = {}
# Parent/child relationships for clause tree
children_by_node: Dict[URIRef, List[URIRef]] = {}
parent_by_node: Dict[URIRef, URIRef] = {}

DCTERMS = Namespace("http://purl.org/dc/terms#")
S223 = Namespace("http://data.ashrae.org/standard223#")
SH = Namespace("http://www.w3.org/ns/shacl#")
g.bind("s223", S223)
g.bind("sh", SH)
g.bind("dcterms", DCTERMS)

# generate links to HTML documentation
S223_DOC_HOST = os.getenv("S223_DOC_HOST", "https://defs.open223.info")
S223_EXPLORE_HOST = "https://explore.open223.info"
CUTOFF_DEPTH = 5


def compute_display_clauses(full):
    """
    Compute the display clauses, using DFS numbering if deeper than CUTOFF_DEPTH
    """
    path_tuple = tuple(full)
    if len(path_tuple) < CUTOFF_DEPTH:
        return list(path_tuple)
    idx = dfs_display_index.get(path_tuple)
    if idx is None:
        return list(path_tuple[: CUTOFF_DEPTH - 1]) + ["?"]
    return list(path_tuple[: CUTOFF_DEPTH - 1]) + [str(idx)]


def collect_paths():
    """Build the clause tree (parent/child relationships) and enumerate DFS display paths."""
    global path_by_node, node_by_path, display_path_by_node, children_by_node, parent_by_node
    path_by_node = {}
    node_by_path = {}
    display_path_by_node = {}
    children_by_node = {}
    parent_by_node = {}

    def build_tree(node):
        """Populate children_by_node and parent_by_node starting at node."""
        subclauses = g.value(node, DOC.subclauses)
        children = []
        if subclauses:
            for child in walk_list(subclauses):
                children.append(child)
                parent_by_node[child] = node
                build_tree(child)
        children_by_node[node] = children

    # Build trees starting from each Document root
    for root in g.subjects(RDF.type, DOC.Document):
        build_tree(root)

    # Enumerate DFS paths ignoring clause labels
    def enumerate_paths(parent, parent_path):
        children = children_by_node.get(parent, [])
        for idx, child in enumerate(children, start=1):
            path = parent_path + [str(idx)]
            display_path_by_node[child] = tuple(path)
            path_by_node[child] = tuple(path)
            node_by_path[tuple(path)] = child
            enumerate_paths(child, path)

    for root in g.subjects(RDF.type, DOC.Document):
        enumerate_paths(root, [])


def build_dfs_display_index():
    """Precompute depth-aware DFS display indices for nodes at or beyond CUTOFF_DEPTH."""
    global dfs_display_index
    dfs_display_index = {}

    # collect unique base prefixes that will be flattened
    bases = set()
    for path in node_by_path.keys():
        if len(path) >= CUTOFF_DEPTH:
            bases.add(tuple(path[: CUTOFF_DEPTH - 1]))

    for base in bases:
        base_node = node_by_path.get(base)
        if base_node is None:
            continue

        # Visit all descendants in DFS order collecting their display paths
        order: List[Tuple[str, ...]] = []

        def dfs_from(n):
            for child in children_by_node.get(n, []):
                fp = display_path_by_node.get(child)
                if fp and len(fp) > len(base):
                    order.append(fp)
                dfs_from(child)

        dfs_from(base_node)

        # Assign indices using pure DFS visitation order. Immediate children occupy
        # the first positions; deeper descendants continue the sequence.
        visit_idx = 0
        for fp in order:
            visit_idx += 1
            if len(fp) < CUTOFF_DEPTH:
                continue
            dfs_display_index[fp] = visit_idx


def stable_id(bnode):
    """
    Returns a stable hex key for the given bnode
    """
    local_graph = g.cbd(bnode)
    h = blake2b()
    for _, p, o in sorted(local_graph.triples((None, None, None))):
        if isinstance(o, BNode):
            continue
        h.update(f"{p}{o}".encode("utf-8"))
    return h.digest().hex()


def simplify_node(node):
    if isinstance(node, BNode):
        return f"{S223_DOC_HOST}#{stable_id(node)}"
    return f"{S223_DOC_HOST}#{g.namespace_manager.qname(node)}"


def get_explore_link(node):
    ns, _, value = g.namespace_manager.compute_qname(node)
    return f"{S223_EXPLORE_HOST}/{ns}/{value}"


def get_meaningful_nodes(node):
    """Return a list of rules, shapes and other nodes in the graph
    that relate to the given node"""
    meaningful = set()
    for constraint in _get_all_constraints():
        if constraint == node:
            continue
        other_subgraph = g.cbd(constraint)
        if _node_is_meaningful(other_subgraph, node):
            meaningful.add(constraint)
    return list(meaningful)


def _node_is_meaningful(sg, node):
    g = copy(sg)
    g.remove((None, SH["class"], node))
    g.remove((None, RDFS["subClassOf"], node))
    abbr = g.namespace_manager.qname(node)
    strg = g.serialize(format="turtle")
    return node in g.all_nodes() or abbr in strg


def _get_all_constraints():
    for node_shape in g.subjects(RDF["type"], SH["NodeShape"]):
        if node_shape in S223:
            yield node_shape
    for property_shape in g.subjects(RDF["type"], SH["PropertyShape"]):
        if property_shape in S223:
            yield property_shape


def walk_list(node):
    """Given the head of an RDF list, yield each of the nodes."""
    while node != RDF.nil:
        yield g.value(node, RDF.first)
        node = g.value(node, RDF.rest)


def do_clause(node):
    """Generate the documentation for a given node using DFS-based numbering."""
    global document, namespace_map, extractor

    # add this as a visited node
    doc_nodes.add(node)

    # compute DFS-based display path and visible clause number
    display_path = list(display_path_by_node[node])
    display_clauses = compute_display_clauses(display_path)

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
    clause_number = ".".join(str(sect) for sect in display_clauses)
    clause_reference[node_name] = clause_number

    # generate the heading
    document += (
        "\n" + " ".join(("#" * len(display_clauses), clause_number, header_text)) + "\n"
    )

    # add the comments as descriptive text (warning: unordered)
    for comment in g.objects(node, RDFS.comment):
        text = textwrap.dedent(comment.value)

        # look for figure references
        def find_figure_reference(matchobj):
            figure_caption = matchobj.group(0)[2:-1]

            top_level = display_path[0]
            if top_level not in figure_count:
                figure_count[top_level] = 0

            figure_count[top_level] += 1
            figure_caption = (
                "!["
                + "Figure {}-{}.".format(top_level, figure_count[top_level])
                + " "
                + figure_caption
                + "]"
            )

            return figure_caption

        # swap out figure references
        text = re.sub(r"[!]\[.*\]", find_figure_reference, text)

        document += f"\n{text}\n"

    extracted_constraints = extractor.get_constraints(node)

    # Related Rules and Constraints
    # We first look for all related "constraints" on this particular concept.
    # These are:
    # - the PropertyShapes which have the concept as a subject
    # - the Nodeshapes which have the concept as a targetClass (but aren't SHACL Rules)
    constraints = g.query(
        f"""SELECT ?shape WHERE {{
        {{ <{node}> sh:property ?shape }}
        UNION
        {{ ?shape sh:targetClass <{node}> .
           FILTER NOT EXISTS {{ ?shape sh:rule ?rule }}
        }}
    }}"""
    )
    constraints = {res[0] for res in constraints}

    # TODO: use consistent hashing to generate a link to the property shape definition so that we can link to it
    # want to lnink to instances of these rules and constraints. This can be done for those that are
    # named as a URI as this is a stable identifier. However, if the rule/constraint is identified as
    # a blank node, it therefore does *not* have a stable identifier and we need to define one.

    tmp = ""
    seen = set()
    for shape in constraints:
        # get the name or label or message or path
        name_or_label = (
            g.value(shape, SH["name"])
            or g.value(shape, RDFS["label"])
            or g.value(shape, SH["message"])
        )
        maybe_path = g.value(shape, SH["path"])
        # to get the description, we first look for the rdfs:comment on the shape
        desc = g.value(shape, RDFS.comment) or (
            " Name/Label:" + str(name_or_label) + " Path:" + maybe_path.rsplit("#")[-1]
            if maybe_path
            else None
        )
        # if desc is None, then pull all of the rdfs:comment from its children
        # and append them together
        if desc is None:
            desc = ""
            # search sh:property, sh:sparql
            for child in g.objects(shape, SH["property"] | SH["sparql"]):
                desc += str(g.value(child, RDFS.comment)) or ""
        # if desc is still empty, then use the qname of the shape
        if desc is None or desc == "":
            desc = g.namespace_manager.qname(shape)

        if desc or name_or_label:
            # name = name_or_label or "Anonymous"
            abbr = simplify_node(shape)
            if abbr in seen:
                continue
            seen.add(abbr)

            link = f"[Link]({abbr})"
            tmp += f"| {desc} | {link} |\n"

    # handle sh:or, sh:and, sh:xone
    document += extracted_constraints.related_constraints_as_markdown_table(
        S223_DOC_HOST
    )
    document += extracted_constraints.related_rules_as_markdown_table(S223_DOC_HOST)

    # recursively do subclauses
    children = children_by_node.get(node, [])
    for child in children:
        child_display = compute_display_clauses(list(display_path_by_node[child]))
        print(f"Generating clause {'.'.join(child_display)} from full clause {'.'.join(display_path_by_node[child])}")
        full_doc_tree.append((child, tuple(child_display), len(display_path_by_node[child])))
        do_clause(child)


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

# add option to override clause depth cutoff
parser.add_argument(
    "--cutoff",
    type=int,
    default=5,
    help="maximum clause depth before truncation with DFS index (default: 5)",
)

# sample additional option to store the expanded graph
parser.add_argument(
    "--expanded",
    type=str,
    help="store the expanded graph",
)

# parse the command line arguments
args = parser.parse_args()

# update clause depth cutoff from argument
CUTOFF_DEPTH = max(1, args.cutoff)

# load the files
for fname in args.ttl:
    g.parse(fname, format="turtle")
g.serialize("/tmp/ttl2md.ttl", format="turtle")
extractor = ConstraintExtractor(g)

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

# no clause references to start
clause_reference = {}
figure_count = {}

# precompute DFS display indices
collect_paths()
build_dfs_display_index()

# look for all of the root documents (warning: unordered)
for root in g.subjects(RDF.type, DOC.Document):
    for comment in g.objects(root, RDFS.comment):
        text = textwrap.dedent(comment.value)

        document += f"\n{text}\n"
    for child in children_by_node.get(root, []):
        do_clause(child)


# find the missing classes
missing_class_query = """%s
    SELECT DISTINCT ?cls
    WHERE {
        ?cls rdf:type s223:Class .
    }
    """ % (prefix_header,)
missing_class_nodes = list(
    node for (node,) in g.query(missing_class_query) if node not in doc_nodes
)

# find the missing properties
missing_property_query = """%s
    SELECT ?prop
    WHERE {
        ?prop rdf:type rdf:Property .
        }
    """ % (prefix_header,)
missing_property_nodes = list(
    node for (node,) in g.query(missing_property_query) if node not in doc_nodes
)

# look for general references to s223 things
for qname in re.findall(r"`(s223:[A-Za-z0-9-.]+)`", document):
    node_ref = g.namespace_manager.expand_curie(qname)
    if node_ref in missing_class_nodes:
        missing_class_nodes.remove(node_ref)
    if node_ref in missing_property_nodes:
        missing_property_nodes.remove(node_ref)

# look for general references to s223 things without the s223: prefix
for qname in re.findall(r"`([A-Za-z0-9-.]+)`", document):
    node_ref = g.namespace_manager.expand_curie("s223:" + qname)
    if node_ref in missing_class_nodes:
        missing_class_nodes.remove(node_ref)
    if node_ref in missing_property_nodes:
        missing_property_nodes.remove(node_ref)

# add the missing pieces up front
if missing_class_nodes:
    missing_classes = "**Missing Classes**\n\n"
    missing_classes += "| Class |\n"
    missing_classes += "|:------|\n"
    for node in missing_class_nodes:
        missing_classes += f"| {node} |\n"
    missing_classes += "\n\n"
else:
    missing_classes = ""

if missing_property_nodes:
    missing_properties = "**Missing Properties**\n\n"
    missing_properties += "| Property |\n"
    missing_properties += "|:---------|\n"
    for node in missing_property_nodes:
        missing_properties += f"| {node} |\n"
    missing_properties += "\n\n"
else:
    missing_properties = ""

# prefix the document with these sections
document = missing_classes + missing_properties + document

# look for comment references
for node, _, comment in g.triples((None, RDFS.comment, None)):
    if isinstance(node, BNode):
        continue

    # get the node name and simplify it
    node_name = str(node)
    for prefix, namespace in namespace_map.items():
        if node_name.startswith(namespace):
            node_name = prefix + ":" + node_name[len(namespace) :]
            break

    comment = " ".join(comment.split())
    document = document.replace("{" + node_name + "/rdfs:comment}", comment)


# look for clause references
def find_clause_reference(matchobj):
    node_name = matchobj.group(0)[1:-1]
    if node_name in clause_reference:
        return "Clause " + clause_reference[node_name]
    else:
        return "?"


# swap out node names with clause references
document = re.sub("{[a-z0-9]+:[A-Za-z0-9-]+}", find_clause_reference, document)

# add appendix with the full document tree
document += "\n\n# Appendix: Full Document Tree\n\n"
for node, clauses, depth in full_doc_tree:
    # get the node name and simplify it
    node_name = str(node)
    for prefix, namespace in namespace_map.items():
        if node_name.startswith(namespace):
            node_name = prefix + ":" + node_name[len(namespace) :]
            break

    clause_number = ".".join(str(sect) for sect in clauses)
    title_value = g.value(node, DOC.title)
    if title_value:
        header_text = title_value.value
    elif isinstance(node, BNode):
        header_text = "Untitled " + node_name
    else:
        header_text = node_name

    indent = "  " * (depth - 1)
    document += f"{indent}* {clause_number} {header_text}\n"

# save the document
with open(args.md, "w") as f:
    f.write(document)

# this file gets used to generate the defs.open223.info site
extractor.to_json("constraints.json")

# save the exloded graph for debugging
if args.expanded:
    with open(args.expanded, "wb") as f:
        g.serialize(f, format="turtle")
