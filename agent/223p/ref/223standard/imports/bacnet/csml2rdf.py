"""
CSML to RDF
"""
import sys
import re
from functools import partial

from typing import Any, Dict, Callable, List, Tuple, TypeVar

from lxml import etree
from rdflib import Graph, Literal, URIRef, BNode
from rdflib.namespace import Namespace, RDF, RDFS, XSD

# types
DefineFn = TypeVar("DefineFn", bound=Callable[[Any, str], URIRef])
DefineDecoratorFn = TypeVar("DefineDecoratorFn", bound=Callable[[DefineFn], DefineFn])
PropertyShapeFn = TypeVar("PropertyShapeFn", bound=Callable[[Any], BNode])
PropertyShapeDecoratorFn = TypeVar(
    "PropertyShapeDecoratorFn", bound=Callable[[PropertyShapeFn], PropertyShapeFn]
)
ValueShapeFn = TypeVar("ValueShapeFn", bound=Callable[[Any], BNode])

# globals
graph = None
completed_datatypes = set()
define_fns: Dict[str, Callable[[Any], None]] = {}
property_shape_fns: Dict[str, Callable[[Any], None]] = {}
postponed_property_shapes: List[Tuple[str, Any, Any]] = []
value_shape_fns: Dict[str, Callable[[Any], None]] = {}
postponed_value_shapes: List[Tuple[str, Any]] = []

BACNET = Namespace("http://data.ashrae.org/bacnet/2020#")
SH = Namespace("http://www.w3.org/ns/shacl#")

# patterns
name_to_label_re = re.compile("([a-z])([A-Z])")


def define_fn(elem_name: str) -> Callable[[DefineFn], DefineFn]:
    def define_fn_decorator(elem_fn: DefineFn) -> DefineFn:
        define_fns[elem_name] = elem_fn
        return elem_fn

    return define_fn_decorator


def property_shape_fn(
    elem_name: str, *args
) -> Callable[[PropertyShapeFn], PropertyShapeFn]:
    def property_shape_fn_decorator(prop_fn: PropertyShapeFn) -> PropertyShapeFn:
        property_shape_fns[elem_name] = partial(prop_fn, *args)
        return prop_fn

    return property_shape_fn_decorator


def value_shape_fn(elem_name: str, *args) -> Callable[[ValueShapeFn], ValueShapeFn]:
    def value_shape_fn_decorator(prop_fn: ValueShapeFn) -> ValueShapeFn:
        value_shape_fns[elem_name] = partial(prop_fn, *args)
        return prop_fn

    return value_shape_fn_decorator


def normalize(name: str) -> str:
    """
    Simplify names.
    """
    if name.startswith("0-"):
        name = name[2:]
    # if name.startswith("BACnet-"):
    #     name = name[7:]
    if name.startswith("BACnet"):
        name = name[6:]
    name = name.replace("-", "")
    return name


def name_to_label(name: str) -> str:
    """
    Make a label.
    """
    # return Literal(name_to_label_re.sub(r"\1 \2", name))
    return Literal(name)


def common_metadata(property_elem, sh_property):
    # string metadata
    for metadata_name in (
        "displayName",
        "displayNameForWriting",
        "description",
        "documentation",
        "comment",
        "writableWhenText",
        "requiredWhenText",
        "unitsText",
        "errorText",
    ):
        metadata_value = property_elem.get(metadata_name, None)
        if metadata_value is not None:
            graph.add(
                (sh_property, BACNET[metadata_name], Literal(metadata_value, lang="en"))
            )


def common_property_metadata(property_elem, sh_property):
    # include common metadata
    common_metadata(property_elem, sh_property)

    # optional maps to min/max count
    optional = property_elem.get("optional", "false")
    if optional not in ("true", "false"):
        raise ValueError(f"{property_elem} optional value: {optional}")
    if optional == "true":
        graph.add((sh_property, SH.minCount, Literal(0)))
    else:
        graph.add((sh_property, SH.minCount, Literal(1)))
    graph.add((sh_property, SH.maxCount, Literal(1)))

    # context - ?


def constructed_data_metadata(property_elem, sh_property):
    # include common metadata
    common_metadata(property_elem, sh_property)

    # truncated - Y.13.10
    # partial - Y.13.11
    # displayOrder - Y.13.12


def simple_path_shape(sequence_uri, property_elem) -> BNode:
    global graph

    # add a property shape
    sh_property = BNode()
    graph.add((sh_property, RDF.type, SH.PropertyShape))
    graph.add((sequence_uri, SH.property, sh_property))
    common_property_metadata(property_elem, sh_property)

    # simple path
    property_name = property_elem.attrib["name"]
    property_uri = BACNET[property_name]
    graph.add((sh_property, SH.path, property_uri))

    return sh_property


def list_path_shape(sequence_uri, property_elem) -> BNode:
    # add a property shape with no hasValue/datatype or class
    sh_property = simple_path_shape(sequence_uri, property_elem)
    property_uri = graph.value(sh_property, SH.path, None)

    # make up a tag so the property path can be found
    tag_uri = URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#tag")

    property_turtle = """
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix sh: <http://www.w3.org/ns/shacl#> .

        [] a sh:NodeShape ;
            rdf:tag 0 ;
            sh:xone (
                [   sh:property [
                        sh:path (
                            <{property_uri}> [ sh:zeroOrMorePath rdf:rest ] rdf:first
                            ) ;
                        sh:minCount 1 ;
                        rdf:tag 1 ;
                    ]
                ]
                [   sh:property [
                        sh:path <{property_uri}> ;
                        sh:hasValue rdf:nil ;
                        sh:minCount 1 ;
                    ]
                ]
                [   sh:property [
                        sh:path <{property_uri}> ;
                        sh:maxCount 0;
                    ]
                ]
            ) .
        """.format(
        property_uri=property_uri
    )
    graph.parse(data=property_turtle, format="turtle")

    # find the node shape that was tagged and remove the tag
    temp_node = graph.value(None, tag_uri, Literal(0))
    graph.remove((temp_node, tag_uri, Literal(0)))

    # replace the temp node with the sequence_uri
    for s, p, o in graph.triples((temp_node, None, None)):
        graph.remove((temp_node, p, o))
        graph.add((sequence_uri, p, o))

    # find the property shape that was tagged and remove the tag
    sh_property = graph.value(None, tag_uri, Literal(1))
    graph.remove((sh_property, tag_uri, Literal(1)))

    return sh_property


#
#   Null - Y.12.1
#


@value_shape_fn("Null")
def null_value_fn(sh_property):
    graph.add((sh_property, SH.hasValue, BACNET.Null))


@property_shape_fn("Null")
def null_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    null_value_fn(sh_property)

    return sh_property


#
#   Boolean - Y.12.2
#


@value_shape_fn("Boolean")
def boolean_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.boolean))


@property_shape_fn("Boolean")
def boolean_property(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)

    # check for a static value
    value = property_elem.get("value", None)
    if value is not None:
        graph.add((sh_property, SH.hasValue, Literal(bool(value == "true"))))
    else:
        boolean_value_fn(sh_property)

    return sh_property


#
#   Unsigned - Y.12.3
#


@value_shape_fn("Unsigned", None, None)
def unsigned_value_fn(minimum, maximum, sh_property):
    graph.add((sh_property, SH.datatype, XSD.nonNegativeInteger))
    if minimum is not None:
        graph.add((sh_property, SH.minInclusive, Literal(minimum)))
    if maximum is not None:
        graph.add((sh_property, SH.maxInclusive, Literal(maximum)))


@property_shape_fn("Unsigned", None, None)
def unsigned_property(minimum, maximum, sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)

    # check for a static value
    value = property_elem.get("value", None)
    if value is not None:
        graph.add(
            (
                sh_property,
                SH.hasValue,
                Literal(int(value), datatype=XSD.nonNegativeInteger),
            )
        )
    else:
        unsigned_value_fn(minimum, maximum, sh_property)

    return sh_property


@define_fn("Unsigned")
def define_unsigned(elem, unsigned_name: str) -> URIRef:
    if not unsigned_name:
        unsigned_name = normalize(elem.attrib["name"])

    minimum = elem.get("minimum", None)
    if minimum is not None:
        minimum = int(minimum)
    maximum = elem.get("maximum", None)
    if maximum is not None:
        maximum = int(maximum)

    property_shape_fns[unsigned_name] = partial(
        unsigned_property,
        minimum,
        maximum,
    )
    value_shape_fns[unsigned_name] = partial(
        unsigned_value_fn,
        minimum,
        maximum,
    )


#
#   Integer - Y.12.4
#


@value_shape_fn("Integer", None, None)
def integer_value_fn(minimum, maximum, sh_property):
    graph.add((sh_property, SH.datatype, XSD.integer))
    if minimum is not None:
        graph.add((sh_property, SH.minInclusive, Literal(minimum)))
    if maximum is not None:
        graph.add((sh_property, SH.maxInclusive, Literal(maximum)))


@property_shape_fn("Integer", None, None)
def integer_property(minimum, maximum, sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)

    value = property_elem.get("value", None)
    if value is not None:
        graph.add((sh_property, SH.hasValue, Literal(int(value))))
    else:
        integer_value_fn(minimum, maximum, sh_property)

    return sh_property


@define_fn("Integer")
def define_integer(elem, integer_name: str) -> URIRef:
    if not integer_name:
        integer_name = normalize(elem.attrib["name"])

    minimum = elem.get("minimum", None)
    if minimum is not None:
        minimum = int(minimum)
    maximum = elem.get("maximum", None)
    if maximum is not None:
        maximum = int(maximum)

    property_shape_fns[integer_name] = partial(
        integer_property,
        minimum,
        maximum,
    )
    value_shape_fns[integer_name] = partial(
        integer_value_fn,
        minimum,
        maximum,
    )


#
#   Real - Y.12.5
#


@value_shape_fn("Real")
def real_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.float))


@property_shape_fn("Real")
def real_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)

    value = property_elem.get("value", None)
    if value is not None:
        graph.add((sh_property, SH.hasValue, Literal(float(value), datatype=XSD.float)))
    else:
        real_value_fn(sh_property)

    return sh_property


#
#   Double - Y.12.6
#


@value_shape_fn("Double")
def double_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.double))


@property_shape_fn("Double")
def double_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    double_value_fn(sh_property)

    value = property_elem.get("value", None)
    if value is not None:
        graph.add(
            (sh_property, SH.hasValue, Literal(float(value), datatype=XSD.double))
        )
    else:
        double_value_fn(sh_property)

    return sh_property


#
#   OctetString - Y.12.7
#


@value_shape_fn("OctetString", None, None)
def octetstring_value_fn(minimumLength, maximumLength, sh_property):
    graph.add((sh_property, SH.datatype, XSD.hexBinary))
    if minimumLength is not None:
        graph.add((sh_property, SH.minLength, Literal(minimumLength * 2)))
    if maximumLength is not None:
        graph.add((sh_property, SH.maxLength, Literal(maximumLength * 2)))


@property_shape_fn("OctetString", None, None)
def octetstring_property_shape(
    minimumLength, maximumLength, sequence_uri, property_elem
) -> BNode:
    # check for a minimum length in the property element, and if it's there
    # compare it to the OctetString definition if one was provided
    minimumLength_attr = property_elem.get("minimumLength", None)
    if minimumLength_attr is not None:
        minimumLength_attr = int(minimumLength_attr)
        if minimumLength is None:
            minimumLength = minimumLength_attr
        elif minimumLength != minimumLength_attr:
            raise ValueError(
                f"{property_elem} minimum length: {minimumLength_attr}, {minimumLength}"
            )

    # check for a maximum length in the property element, and if it's there
    # compare it to the OctetString definition if one was provided
    maximumLength_attr = property_elem.get("maximumLength", None)
    if maximumLength_attr is not None:
        maximumLength_attr = int(maximumLength_attr)
        if maximumLength is None:
            maximumLength = maximumLength_attr
        elif maximumLength != maximumLength_attr:
            raise ValueError(
                f"{property_elem} maximum length: {maximumLength_attr}, {maximumLength}"
            )

    sh_property = simple_path_shape(sequence_uri, property_elem)
    octetstring_value_fn(minimumLength, maximumLength, sh_property)

    return sh_property


@define_fn("OctetString")
def define_octetstring(elem, octetstring_name: str) -> URIRef:
    if not octetstring_name:
        octetstring_name = normalize(elem.attrib["name"])

    octetstring_uri = BACNET[octetstring_name]
    graph.add((octetstring_uri, RDF.type, SH.NodeShape))
    graph.add((octetstring_uri, RDFS.label, name_to_label(octetstring_name)))
    graph.add((octetstring_uri, RDFS.subClassOf, BACNET.OctetString))
    common_metadata(elem, octetstring_uri)

    minimumLength_attr = elem.get("minimumLength", None)
    if minimumLength_attr is not None:
        minimumLength_attr = int(minimumLength_attr)
        graph.add((octetstring_uri, BACNET.minimumLength, Literal(minimumLength_attr)))

    maximumLength_attr = elem.get("maximumLength", None)
    if maximumLength_attr is not None:
        maximumLength_attr = int(maximumLength_attr)
        graph.add((octetstring_uri, BACNET.maximumLength, Literal(maximumLength_attr)))

    property_shape_fns[octetstring_name] = partial(
        octetstring_property_shape,
        minimumLength_attr,
        maximumLength_attr,
    )
    value_shape_fns[octetstring_name] = partial(
        octetstring_value_fn,
        minimumLength_attr,
        maximumLength_attr,
    )


#
#   Raw - Y.12.8
#

#
#   String - Y.12.9
#


@value_shape_fn("String")
def string_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))


@property_shape_fn("String")
def string_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)

    value = property_elem.get("value", None)
    if value is not None:
        graph.add((sh_property, SH.hasValue, Literal(value)))
    else:
        string_value_fn(sh_property)

    return sh_property


#
#   StringSet - Y.12.10
#

#
#   BitString - Y.12.11
#


@value_shape_fn("BitString", None)
def bitstring_value_fn(membertype_uri, sh_property):
    if membertype_uri:
        graph.add((sh_property, SH["class"], membertype_uri))
    else:
        graph.add((sh_property, SH["class"], BACNET.NamedBits))
        # graph.add((sh_property, BACNET["x-note"], Literal("assumed generic")))


@property_shape_fn("BitString", None)
def bitstring_property_shape(membertype_uri, sequence_uri, property_elem) -> BNode:
    sh_property = list_path_shape(sequence_uri, property_elem)
    if membertype_uri:
        bitstring_value_fn(membertype_uri, sh_property)
    else:
        graph.add((sh_property, SH["class"], BACNET.NamedBits))
        # graph.add((sh_property, BACNET["x-note"], Literal("assumed generic")))

    return sh_property


@define_fn("BitString")
def define_bit_string(elem, bitstring_name: str) -> URIRef:
    if not bitstring_name:
        bitstring_name = normalize(elem.attrib["name"])

    bitstring_uri = BACNET[bitstring_name]
    graph.add((bitstring_uri, RDF.type, RDFS.Class))
    graph.add((bitstring_uri, RDF.type, SH.NodeShape))
    graph.add((bitstring_uri, RDFS.label, name_to_label(bitstring_name)))
    graph.add((bitstring_uri, RDFS.subClassOf, BACNET.Bitstring))
    common_metadata(elem, bitstring_uri)

    namedbits_uri = BACNET[bitstring_name + "NamedBits"]
    graph.add((namedbits_uri, RDF.type, RDFS.Class))
    graph.add((namedbits_uri, RDFS.label, name_to_label(bitstring_name + "NamedBits")))
    graph.add((namedbits_uri, RDFS.subClassOf, BACNET.NamedBits))
    graph.add((bitstring_uri, BACNET.memberClass, namedbits_uri))

    for child in elem.xpath("NamedBits/*"):
        bit_name = child.attrib["name"]
        bit_bit = int(child.attrib["bit"])

        bit_iri = BACNET[bitstring_name + "." + bit_name]
        graph.add((bit_iri, RDF.type, namedbits_uri))
        graph.add((bit_iri, BACNET.name, Literal(bit_name)))
        graph.add(
            (
                bit_iri,
                BACNET.bit,
                Literal(int(bit_bit), datatype=XSD.nonNegativeInteger),
            )
        )

    property_shape_fns[bitstring_name] = partial(
        bitstring_property_shape, namedbits_uri
    )
    value_shape_fns[bitstring_name] = partial(bitstring_value_fn, namedbits_uri)

    return bitstring_uri


#
#   Enumerated - Y.12.12
#


def enumerated_value_fn(member_uri, property_value, sh_property):
    if property_value is not None:
        # build a query string
        query_string = """
            PREFIX bacnet: <{bacnet}>
            PREFIX rdf: <{rdf}>

            SELECT ?member_id
            WHERE {{
                ?member_id rdf:type <{member_uri}> ;
                    bacnet:name "{name}" .
            }}
            """.format(
            bacnet=BACNET, rdf=RDF, member_uri=member_uri, name=property_value
        )

        # run the query and look for one value
        query_results = list(graph.query(query_string))
        if len(query_results) != 1:
            raise RuntimeError(
                f"unable to resolve {property_value} as a member of {member_uri}"
            )

        # add an exact match
        graph.add((sh_property, SH.hasValue, query_results[0][0]))
    else:
        graph.add((sh_property, SH["class"], member_uri))


@property_shape_fn("Enumerated", None)
def enumerated_property_shape(member_uri, sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)

    property_value = property_elem.get("value", None)
    if member_uri:
        enumerated_value_fn(member_uri, property_value, sh_property)
    else:
        graph.add((sh_property, SH["class"], BACNET.EnumerationValue))

    return sh_property


@define_fn("Enumerated")
def define_enumerated(elem, enum_name: str) -> URIRef:
    if not enum_name:
        enum_name = normalize(elem.attrib["name"])

    enum_uri = BACNET[enum_name]
    graph.add((enum_uri, RDF.type, RDFS.Class))
    graph.add((enum_uri, RDFS.label, name_to_label(enum_name)))
    graph.add((enum_uri, RDFS.subClassOf, BACNET.EnumerationKind))
    common_metadata(elem, enum_uri)

    value_uri = BACNET[enum_name + "EnumerationValue"]
    graph.add((value_uri, RDF.type, RDFS.Class))
    graph.add((value_uri, RDFS.label, name_to_label(enum_name + "EnumerationValue")))
    graph.add((value_uri, RDFS.subClassOf, BACNET.EnumerationValue))
    graph.add((enum_uri, BACNET.memberClass, value_uri))

    for child in elem.xpath("NamedValues/*"):
        child_name = child.attrib["name"]
        child_value = int(child.attrib["value"])

        child_iri = BACNET[enum_name + "." + child_name]
        graph.add((child_iri, RDF.type, value_uri))
        graph.add((child_iri, BACNET.name, Literal(child_name)))
        graph.add(
            (
                child_iri,
                BACNET.value,
                Literal(child_value, datatype=XSD.nonNegativeInteger),
            )
        )

    property_shape_fns[enum_name] = partial(enumerated_property_shape, value_uri)
    value_shape_fns[enum_name] = partial(enumerated_value_fn, value_uri, None)

    return enum_uri


#
#   Date - Y.12.13
#


@value_shape_fn("Date")
def date_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))
    graph.add(
        (
            sh_property,
            SH.pattern,
            Literal("^([0-9]{4})-([0-9]{2})-([0-9]{2}|[*])( ([0-9]|[*]))?$"),
        )
    )


@property_shape_fn("Date")
def date_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    date_value_fn(sh_property)

    return sh_property


#
#   DatePattern - Y.12.14
#


@value_shape_fn("DatePattern")
def datepattern_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))
    graph.add(
        (
            sh_property,
            SH.pattern,
            Literal("^([0-9]{4}|[*])-([0-9]{2}|[*])-([0-9]{2}|[*])( ([0-9]|[*]))?$"),
        )
    )


@property_shape_fn("DatePattern")
def datepattern_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    datepattern_value_fn(sh_property)

    return sh_property


#
#   DateTime - Y.12.15
#


@value_shape_fn("DateTime")
def datetime_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))
    graph.add(
        (
            sh_property,
            SH.pattern,
            Literal(
                "^([0-9]{4})-([0-9]{2})-([0-9]{2})( ([0-9]))? ([0-9]{2}):([0-9]{2}):([0-9]{2})[.]([0-9]{2})$"
            ),
        )
    )


@property_shape_fn("DateTime")
def datetime_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    datetime_value_fn(sh_property)

    return sh_property


#
#   DateTimePattern - Y.12.16
#


@value_shape_fn("DateTimePattern")
def datetimepattern_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))
    graph.add(
        (
            sh_property,
            SH.pattern,
            Literal(
                "^([0-9]{4}|[*])-([0-9]{2}|[*])-([0-9]{2}|[*])( ([0-9]|[*]))? ([0-9]{2}|[*]):([0-9]{2}|[*]):([0-9]{2}|[*])[.]([0-9]{2}|[*])$"
            ),
        )
    )


@property_shape_fn("DateTimePattern")
def datetimepattern_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    datetimepattern_value_fn(sh_property)

    return sh_property


#
#   Time - Y.12.17
#


@value_shape_fn("Time")
def time_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))
    graph.add(
        (
            sh_property,
            SH.pattern,
            Literal("^([0-9]{2}):([0-9]{2}):([0-9]{2})[.]([0-9]{2})$"),
        )
    )


@property_shape_fn("Time")
def time_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    time_value_fn(sh_property)

    return sh_property


#
#   TimePattern - Y.12.18
#


@value_shape_fn("TimePattern")
def timepattern_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))
    graph.add(
        (
            sh_property,
            SH.pattern,
            Literal("^([0-9]{2}|[*]):([0-9]{2}|[*]):([0-9]{2}|[*])[.]([0-9]{2}|[*])$"),
        )
    )


@property_shape_fn("TimePattern")
def timepattern_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    timepattern_value_fn(sh_property)

    return sh_property


#
#   Link - Y.12.19
#

#
#   Sequence
#


def sequence_value_fn(reference_uri, sh_property):
    graph.add((sh_property, SH["class"], reference_uri))


@property_shape_fn("Sequence", None)
def sequence_property_shape(reference_uri, sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    if reference_uri:
        sequence_value_fn(reference_uri, sh_property)

    return sh_property


@define_fn("Sequence")
def define_sequence(elem, sequence_name: str) -> URIRef:
    if not sequence_name:
        sequence_name = normalize(elem.attrib["name"])
    # sequence_type = elem.attrib.get("type", None)

    sequence_uri = BACNET[sequence_name]
    graph.add((sequence_uri, RDF.type, SH.NodeShape))
    graph.add((sequence_uri, RDFS.label, name_to_label(sequence_name)))
    graph.add((sequence_uri, RDFS.subClassOf, BACNET.Sequence))
    common_metadata(elem, sequence_uri)

    for child_elem in elem.xpath("*"):
        child_name = child_elem.attrib.get("name", None)
        child_type = child_elem.attrib.get("type", None)
        if child_type:
            child_type = normalize(child_type)

        if child_type:
            # child type explicit in 'type' attribute
            if child_type not in property_shape_fns:
                postponed_property_shapes.append((child_type, sequence_uri, child_elem))
            else:
                sh_property = property_shape_fns[child_type](sequence_uri, child_elem)

        elif child_elem.tag in ("Array", "List", "SequenceOf"):
            container_membertype = child_elem.attrib.get("memberType", None)
            if container_membertype:
                container_membertype = normalize(container_membertype)

            sh_property = list_path_shape(sequence_uri, child_elem)

            if container_membertype is None:
                if child_elem.tag in ("Array", "List"):
                    raise RuntimeError("container {child_name} memberType required")

                # make up a child type name based on the sequence name and the child name
                child_type_name = (
                    sequence_name
                    + "."
                    + "".join(
                        word[0].upper() + word[1:] for word in child_name.split("-")
                    )
                )
                define_container(child_elem, child_type_name)
                container_membertype = child_type_name

            if container_membertype in value_shape_fns:
                value_shape_fns[container_membertype](sh_property)
            else:
                postponed_value_shapes.append((container_membertype, sh_property))

        elif child_elem.tag == "Choice":
            # make up a child type name based on the choice name and the child name
            child_type_name = (
                sequence_name
                + "."
                + "".join(word[0].upper() + word[1:] for word in child_name.split("-"))
            )
            define_choice(child_elem, child_type_name)

            # now there is a shape function for it
            sh_property = property_shape_fns[child_type_name](sequence_uri, child_elem)

        elif child_elem.tag == "Sequence":
            # make up a child type name based on the choice name and the child name
            child_type_name = (
                sequence_name
                + "."
                + "".join(word[0].upper() + word[1:] for word in child_name.split("-"))
            )
            define_sequence(child_elem, child_type_name)

            # now there is a shape function for it
            sh_property = property_shape_fns[child_type_name](sequence_uri, child_elem)

        elif child_elem.tag in property_shape_fns:
            # child type describe in tag
            sh_property = property_shape_fns[child_elem.tag](sequence_uri, child_elem)

        else:
            # child type is defined here, tag determines type
            if child_elem.tag not in define_fns:
                raise RuntimeError(f"missing define_fn: {child_elem.tag}")

            # make up a child type name based on the sequence name and the child name
            child_type_name = (
                sequence_name
                + "."
                + "".join(word[0].upper() + word[1:] for word in child_name.split("-"))
            )
            define_fns[child_elem.tag](child_elem, child_type_name)

            # now there is a shape function for it
            property_shape_fns[child_type_name](sequence_uri, child_elem)

    property_shape_fns[sequence_name] = partial(sequence_property_shape, sequence_uri)
    value_shape_fns[sequence_name] = lambda sh_property: graph.add(
        (sh_property, SH.node, sequence_uri)
    )

    return sequence_uri


#
#   Choice
#


@property_shape_fn("Choice", None)
def choice_property_shape(reference_uri, sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    graph.add((sh_property, SH["class"], reference_uri))

    return sh_property


@define_fn("Choice")
def define_choice(elem, choice_name: str) -> URIRef:
    if not choice_name:
        choice_name = normalize(elem.attrib["name"])
    choice_type = elem.attrib.get("type", None)

    choice_uri = BACNET[choice_name]
    graph.add((choice_uri, RDF.type, SH.NodeShape))
    graph.add((choice_uri, RDFS.label, name_to_label(choice_name)))
    graph.add((choice_uri, RDFS.subClassOf, BACNET.Choice))
    common_metadata(elem, choice_uri)

    choices = []

    for child_elem in elem.xpath("Choices/*"):
        child_name = child_elem.attrib.get("name", None)
        child_type = child_elem.attrib.get("type", None)
        if child_type:
            child_type = normalize(child_type)

        bnode = BNode()
        choices.append(bnode)

        if child_elem.tag in ("Array", "List"):
            raise NotImplementedError(
                f"choices {choice_name} cannot be container types: {child_name}"
            )

        elif child_elem.tag == "Choice":
            choice_type = child_elem.attrib.get("type", None)
            if not choice_type:
                raise RuntimeError(f"choices {choice_name} expected type: {child_name}")
            choice_type = normalize(choice_type)

            sh_property = simple_path_shape(bnode, child_elem)

            if choice_type in value_shape_fns:
                value_shape_fns[choice_type](sh_property)
            else:
                postponed_value_shapes.append((choice_type, sh_property))

        elif child_elem.tag == "SequenceOf":
            container_type = child_elem.attrib.get("type", None)
            if container_type:
                container_type = normalize(container_type)

                sh_property = list_path_shape(bnode, child_elem)

                if container_type in value_shape_fns:
                    value_shape_fns[container_type](sh_property)
                else:
                    postponed_value_shapes.append((container_type, sh_property))
            else:
                # make up a child type name based on the choice name and the child name
                child_type_name = (
                    choice_name
                    + "."
                    + "".join(
                        word[0].upper() + word[1:] for word in child_name.split("-")
                    )
                )
                define_sequenceof(child_elem, child_type_name)

                # now there is a shape function for it
                sh_property = property_shape_fns[child_type_name](bnode, child_elem)

        elif child_type:
            # child type explicit in 'type' attribute
            if child_type not in property_shape_fns:
                postponed_property_shapes.append((child_type, bnode, child_elem))
            else:
                sh_property = property_shape_fns[child_type](bnode, child_elem)

        elif child_elem.tag == "Sequence":
            # make up a child type name based on the choice name and the child name
            child_type_name = (
                choice_name
                + "."
                + "".join(word[0].upper() + word[1:] for word in child_name.split("-"))
            )
            define_sequence(child_elem, child_type_name)

            # now there is a shape function for it
            sh_property = property_shape_fns[child_type_name](bnode, child_elem)

        elif child_elem.tag in property_shape_fns:
            # child type describe in tag
            sh_property = property_shape_fns[child_elem.tag](bnode, child_elem)

        else:
            raise RuntimeError(
                f"unknown element: {elem} {elem.items()} {child_elem} {child_elem.items()}"
            )

    subject = choice_uri
    predicate = SH.xone
    for choice in choices:
        # create a blank node referencing the thing
        list_node = BNode()
        graph.add((list_node, RDF.first, choice))

        # chain along this list node
        graph.add((subject, predicate, list_node))
        subject = list_node
        predicate = RDF.rest

    # end of the list
    graph.add((subject, predicate, RDF.nil))

    property_shape_fns[choice_name] = partial(choice_property_shape, choice_uri)
    value_shape_fns[choice_name] = lambda sh_property: graph.add(
        (sh_property, SH.node, choice_uri)
    )

    return choice_uri


#
#   Containers
#


def container_value_fn(membertype_uri, sh_property):
    graph.add((sh_property, SH.node, membertype_uri))


def container_property_shape(membertype_uri, sequence_uri, property_elem) -> BNode:
    sh_property = list_path_shape(sequence_uri, property_elem)
    if membertype_uri:
        graph.add((sh_property, SH.node, membertype_uri))

    return sh_property


def define_container(elem, container_name: str) -> URIRef:
    if not container_name:
        container_name = normalize(elem.attrib["name"])

    container_uri = BACNET[container_name]
    graph.add((container_uri, RDF.type, BACNET[elem.tag]))
    common_metadata(elem, container_uri)

    container_membertype = elem.attrib.get("memberType", None)
    if container_membertype:
        container_membertype = normalize(container_membertype)
        membertype_uri = BACNET[container_membertype]
    else:
        # get the child element of the member type definition
        member_type_elements = elem.xpath("MemberTypeDefinition/*")
        if len(member_type_elements) != 1:
            raise RuntimeError(
                f"{child_name} in {elem}, one member type definition expected"
            )
        member_type_element = member_type_elements[0]
        if member_type_element.tag == "Sequence":
            membertype_name = container_name + "Sequence"
            if membertype_name in value_shape_fns:
                raise RuntimeError(
                    f"{container_name} existing value shape function: {membertype_name}"
                )

            membertype_uri = define_sequence(member_type_element, membertype_name)
        elif member_type_element.tag == "Choice":
            membertype_name = container_name + "Choice"
            if membertype_name in value_shape_fns:
                raise RuntimeError(
                    f"{container_name} existing value shape function: {membertype_name}"
                )

            membertype_uri = define_choice(member_type_element, membertype_name)
        else:
            raise NotImplementedError(
                f"{container_name} container member type definition: {member_type_element.tag}"
            )

    graph.add((container_uri, BACNET.memberType, membertype_uri))

    property_shape_fns[container_name] = partial(
        container_property_shape, membertype_uri
    )
    value_shape_fns[container_name] = partial(container_value_fn, membertype_uri)

    return container_uri


#
#   Array - Y.13.3
#


@define_fn("Array")
def define_array(elem, array_name: str) -> URIRef:
    return define_container(elem, array_name)


#
#   Unknown - Y.13.4
#

#
#   List - Y.13.5
#


@define_fn("List")
def define_list(elem, list_name: str) -> URIRef:
    return define_container(elem, list_name)


#
#   SequenceOf - Y.13.6
#


@define_fn("SequenceOf")
def define_sequenceof(elem, sequenceof_name: str) -> URIRef:
    return define_container(elem, sequenceof_name)


#
#   Collection - Y.13.7
#

#
#   Composition - Y.13.8
#

#
#   Object - Y.13.9
#


@define_fn("Object")
def define_object(elem, object_name: str) -> URIRef:
    if not object_name:
        object_name = normalize(elem.attrib["name"])

    object_uri = BACNET[object_name]
    graph.add((object_uri, RDF.type, SH.NodeShape))
    graph.add((object_uri, RDF.type, RDFS.Class))
    graph.add((object_uri, RDFS.label, name_to_label(object_name)))
    graph.add((object_uri, RDFS.subClassOf, BACNET.Object))
    common_metadata(elem, object_uri)

    for property_elem in elem.xpath("*"):
        # property_name = property_elem.attrib.get("name", None)
        property_type = property_elem.attrib.get("type", None)
        if property_type:
            property_type = normalize(property_type)
        property_membertype = property_elem.attrib.get("memberType", None)
        if property_membertype:
            property_membertype = normalize(property_membertype)

        if property_type:
            # child type explicit in 'type' attribute
            if property_type not in property_shape_fns:
                postponed_property_shapes.append(
                    (property_type, object_uri, property_elem)
                )
            else:
                sh_property = property_shape_fns[property_type](
                    object_uri, property_elem
                )

        elif property_membertype:
            sh_property = list_path_shape(object_uri, property_elem)
            if property_membertype in value_shape_fns:
                value_shape_fns[property_membertype](sh_property)
            else:
                postponed_value_shapes.append((property_membertype, sh_property))

        elif property_elem.tag in property_shape_fns:
            # child type describe in tag
            sh_property = property_shape_fns[property_elem.tag](
                object_uri, property_elem
            )

        else:
            raise RuntimeError(f"missing property shape: {property_elem.tag}")

    # property_shape_fns[object_name] = partial(object_property_shape, object_uri)
    value_shape_fns[object_name] = lambda sh_property: graph.add(
        (sh_property, SH["class"], object_uri)
    )

    return object_uri


#
#   Any - Y.14.1
#


@value_shape_fn("Any")
def any_value_fn(sh_property):
    pass


@property_shape_fn("Any")
def any_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)

    return sh_property


#
#   ObjectIdentifier - Y.20.1
#


@value_shape_fn("ObjectIdentifier")
def objectidentifier_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))
    graph.add((sh_property, SH.pattern, Literal("^[A-Za-z0-9-]+,[1-9][0-9]*$")))


@property_shape_fn("ObjectIdentifier")
def objectidentifier_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    objectidentifier_value_fn(sh_property)

    return sh_property


@define_fn("ObjectIdentifier")
def define_objectidentifier(elem, objectidentifier_name: str) -> URIRef:
    if not objectidentifier_name:
        objectidentifier_name = normalize(elem.attrib["name"])

    objectidentifier_uri = BACNET[objectidentifier_name]
    graph.add((objectidentifier_uri, RDF.type, BACNET[elem.tag]))
    common_metadata(elem, objectidentifier_uri)

    property_shape_fns[objectidentifier_name] = objectidentifier_property_shape
    value_shape_fns[objectidentifier_name] = objectidentifier_value_fn

    return objectidentifier_uri


#
#   ObjectIdentifierPattern - Y.20.2
#


@value_shape_fn("ObjectIdentifierPattern")
def objectidentifierpattern_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))
    graph.add(
        (sh_property, SH.pattern, Literal("^([A-Za-z0-9-]+|[*]),([1-9][0-9]*|[*])$"))
    )


@property_shape_fn("ObjectIdentifierPattern")
def objectidentifierpattern_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    objectidentifierpattern_value_fn(sh_property)

    return sh_property


#
#   WeekNDay - Y.20.3
#


@value_shape_fn("WeekNDay")
def weeknday_value_fn(sh_property):
    graph.add((sh_property, SH.datatype, XSD.string))
    graph.add(
        (
            sh_property,
            SH.pattern,
            Literal("^([1-9][0-9]*|[*]),([1-9][0-9]*|[*]),([1-9][0-9]*|[*])$"),
        )
    )


@property_shape_fn("WeekNDay")
def weeknday_property_shape(sequence_uri, property_elem) -> BNode:
    sh_property = simple_path_shape(sequence_uri, property_elem)
    weeknday_value_fn(sh_property)

    return sh_property


#
#   __main__
#

# parse the XML Schema document and get the root element
doc = etree.parse(sys.stdin)
root = doc.getroot()

# simplify the element names by pulling out the local name
for elem in root.getiterator(tag=etree.Element):
    elem.tag = etree.QName(elem).localname
etree.cleanup_namespaces(root)

# start with an empty graph
graph = Graph()

# register the BACnet namespace
graph.bind("bacnet", BACNET)
graph.bind("sh", SH)

for x in root.xpath("/CSML/Definitions"):
    for y in x:
        if not isinstance(y.tag, str):
            continue
        if y.tag not in define_fns:
            raise RuntimeError(f"missing fn: {y}")
        define_fns[y.tag](y, "")

for child_type, sequence_uri, child_elem in postponed_property_shapes:
    if child_type not in property_shape_fns:
        child_name = child_elem.attrib["name"]
        graph.add(
            (
                sequence_uri,
                BACNET["x-error"],
                Literal(f"{child_name} missing property shape: {child_type}"),
            )
        )
        continue
    property_shape_fns[child_type](sequence_uri, child_elem)

for reference_type, sh_property in postponed_value_shapes:
    if reference_type not in value_shape_fns:
        graph.add(
            (
                sequence_uri,
                BACNET["x-error"],
                Literal(f"missing type definition: {reference_type}"),
            )
        )
        continue
    value_shape_fns[reference_type](sh_property)


# dump the result
sys.stdout.write(graph.serialize(format="turtle"))
