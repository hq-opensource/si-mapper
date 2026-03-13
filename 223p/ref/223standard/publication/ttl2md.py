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

from typing import Dict

from rdflib import Graph, Namespace, BNode, RDF, RDFS
import owlrl

# globals
g = Graph()
document = ""
extractor = None
doc_nodes = set()
clause_reference: Dict[str, str]
figure_count: Dict[int, int]

DCTERMS = Namespace("http://purl.org/dc/terms#")
S223 = Namespace("http://data.ashrae.org/standard223#")
SH = Namespace("http://www.w3.org/ns/shacl#")
g.bind("s223", S223)
g.bind("sh", SH)
g.bind("dcterms", DCTERMS)

# generate links to HTML documentation
S223_DOC_HOST = os.getenv("S223_DOC_HOST", "https://defs.open223.info")
S223_EXPLORE_HOST = "https://explore.open223.info"


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
    # for sproperty in g.subjects(RDF["type"], RDF["Property"]):
    #     if sproperty in S223:
    #         yield sproperty
    # for rule in g.subjects(SH["rule"]):
    #     if rule in S223:
    #         yield rule


def walk_list(node):
    """Given the head of an RDF list, yield each of the nodes."""
    while node != RDF.nil:
        yield g.value(node, RDF.first)
        node = g.value(node, RDF.rest)


def do_clause(node, clauses):
    """Generate the documentation for a given node."""
    global document, namespace_map, extractor

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
    clause_reference[node_name] = clause_number

    # generate the heading
    document += "\n" + " ".join(("#" * len(clauses), clause_number, header_text)) + "\n"

    # uncomment this to add explore.open223.info links to the documentation
    # document += f"[Online documentation link]({get_explore_link(node)}). "

    # add the comments as descriptive text (warning: unordered)
    for comment in g.objects(node, RDFS.comment):
        text = textwrap.dedent(comment.value)

        # look for figure references
        def find_figure_reference(matchobj):
            figure_caption = matchobj.group(0)[2:-1]

            if clauses[0] not in figure_count:
                figure_count[clauses[0]] = 0

            figure_count[clauses[0]] += 1
            figure_caption = (
                "!["
                + "Figure {}-{}.".format(clauses[0], figure_count[clauses[0]])
                + " "
                + figure_caption
                + "]"
            )

            return figure_caption

        # swap out figure references
        text = re.sub(r"[!]\[.*\]", find_figure_reference, text)

        document += f"\n{text}\n"

    # GABE NEW STUFF HERE
    extracted_constraints = extractor.get_constraints(node)
    # print(node)
    # print(constraints.related_constraints_as_markdown_table(S223_DOC_HOST))
    # print(constraints.related_rules_as_markdown_table(S223_DOC_HOST))

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
            # tmp += f"| {name} | {desc} | {link} |\n"
            tmp += f"| {desc} | {link} |\n"
            # tmp += f"| {desc} uri:{shape.title()} stable_id {abbr}| {link} |\n"

    # handle sh:or, sh:and, sh:xone
    document += extracted_constraints.related_constraints_as_markdown_table(
        S223_DOC_HOST
    )
    document += extracted_constraints.related_rules_as_markdown_table(S223_DOC_HOST)
    # constraints = g.objects(node, SH["or"] | SH["and"] | SH["xone"])
    # # each 'compound_shape' is a list of shapes
    # for compound_shape in constraints:
    #    # get the rdfs:comment from each shape in the list.
    #    desc = {g.value(s, SH.property / RDFS.comment) for s in walk_list(compound_shape)}
    #    if len(desc) > 1:
    #        # boolean_condition = next(g.predicates(node, compound_shape))
    #        # clean up the boolean condition to make it more readable (sh:and -> AND, etc)
    #        # boolean_condition = boolean_condition.split("#")[-1].upper()
    #        # if there is more than one unique description, then stitch them together with
    #        # the boolean condition
    #        # desc = f"{boolean_condition} ".join(desc)
    #        desc = " ".join(desc)
    #    elif len(desc) == 1:
    #        desc = desc.pop()
    #    else:
    #        desc = g.namespace_manager.qname(shape)
    #    abbr = simplify_node(compound_shape)
    #    if abbr in seen:
    #        continue
    #    link = f"[Link]({abbr})"
    #    tmp += f"| {desc} | {link} |\n"

    # if len(tmp) > 0:
    #    document += "\n: Related Constraints\n"
    #    # document += "\n| Name | Description | Link |\n"
    #    # document += "| ----- | ---------- | -- |\n"
    #    document += "\n| Description | Link |\n"
    #    document += "| ---------- | -- |\n"
    #    document += tmp
    #    document += "\n\n"

    # pull in related rules
    # tmp = ""
    # seen = set()
    # for rule_shape in set(g.objects(node, SH["rule"])):
    #    name_or_label = g.value(rule_shape, SH["name"]) or g.value(
    #        rule_shape, RDFS["label"]
    #    )
    #    message_or_comment = g.value(rule_shape, RDFS.comment) or (
    #        " Name/Label:" + str(name_or_label)
    #    )
    #    if message_or_comment or name_or_label:
    #        desc = message_or_comment
    #        # name = name_or_label or "Anonymous"
    #        abbr = simplify_node(rule_shape)
    #        if abbr in seen:
    #            continue
    #        seen.add(abbr)
    #        link = f"[Link]({abbr})"
    #        # tmp += f"| {name} | {desc} | {link} |\n"
    #        tmp += f"| {desc} | {link} |\n"

    # if len(tmp) > 0:
    #    document += "\n: Related Inference Rules\n"
    #    # document += "\n| Name | Description | Link |\n"
    #    # document += "| ----- | ---------- | -- |\n"
    #    document += "\n| Description | Link |\n"
    #    document += "|  ---------- | -- |\n"
    #    document += tmp
    #    document += "\n\n"

    # document += "\n\n"

    # constraints = get_meaningful_nodes(node)
    # if len(constraints) > 0:
    #     document += "\n| Related Constraints | Doc Link | \n"
    #     document += "| ---------- | -------- |\n"
    #     for constraint in constraints:
    #         abbr = simplify_node(constraint)
    #         link = f"[https://223p.gtf.fyi#{abbr}](https://223p.gtf.fyi#{abbr})"
    #         document += f"| {constraint} | {link} | \n"
    #     document += "\n\n"

    # recursively do subclauses
    child_subclauses = g.value(node, DOC.subclauses)
    if child_subclauses:
        for i, child in enumerate(walk_list(child_subclauses)):
            clause_value = g.value(child, DOC.clause)
            if clause_value:
                clause_label = clause_value.value
            else:
                clause_label = str(i + 1)
            do_clause(child, clauses + [clause_label])


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

# look for all of the root documents (warning: unordered)
for root in g.subjects(RDF.type, DOC.Document):
    for comment in g.objects(root, RDFS.comment):
        text = textwrap.dedent(comment.value)

        document += f"\n{text}\n"
    for i, child in enumerate(walk_list(g.value(root, DOC.subclauses))):
        clause_value = g.value(child, DOC.clause)
        if clause_value:
            clause_label = clause_value.value
        else:
            clause_label = str(i + 1)
        do_clause(child, [clause_label])

# find the missing classes
missing_class_query = """%s
    SELECT DISTINCT ?cls
    WHERE {
        ?cls rdf:type s223:Class .
    }
    """ % (
    prefix_header,
)
missing_class_nodes = list(
    node for (node,) in g.query(missing_class_query) if node not in doc_nodes
)

# find the missing properties
missing_property_query = """%s
    SELECT ?prop
    WHERE {
        ?prop rdf:type rdf:Property .
        }
    """ % (
    prefix_header,
)
missing_property_nodes = list(
    node for (node,) in g.query(missing_property_query) if node not in doc_nodes
)

# look for general references to s223 things
for qname in re.findall(r"`(s223:[A-Za-z0-9-.+]+)`", document):
    node_ref = g.namespace_manager.expand_curie(qname)
    if node_ref in missing_class_nodes:
        missing_class_nodes.remove(node_ref)
    if node_ref in missing_property_nodes:
        missing_property_nodes.remove(node_ref)

# look for general references to s223 things without the s223: prefix
for qname in re.findall(r"`([A-Za-z0-9-.+]+)`", document):
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

# save the document
with open(args.md, "w") as f:
    f.write(document)

# this file gets used to generate the defs.open223.info site
extractor.to_json("constraints.json")

# save the exloded graph for debugging
if args.expanded:
    with open(args.expanded, "wb") as f:
        g.serialize(f, format="turtle")
