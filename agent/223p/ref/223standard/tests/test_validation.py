"""
Performs validation of the model/schema and data files in the 223P repository
"""
import glob
import logging
import rdflib
import ontoenv
from brick_tq_shacl import validate
from pathlib import Path


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def copy_graph(g: rdflib.Graph) -> rdflib.Graph:
    c = rdflib.Graph()
    for t in g.triples((None, None, None)):
        c.add(t)
    return c


def test_schema_validation():
    """
    Validates the schema definition against the specified shapes
    """
    # load in schema validation shapes
    shape_graph = rdflib.Graph()
    for shape_file in glob.glob("../validation/*.ttl"):
        shape_graph.parse(shape_file, format="turtle")
    for shape_file in glob.glob("../inference/*.ttl"):
        shape_graph.parse(shape_file, format="turtle")
    for shape_file in glob.glob("../models/*.ttl"):
        shape_graph.parse(shape_file, format="turtle")
    for shape_file in glob.glob("../vocab/*.ttl"):
        shape_graph.parse(shape_file, format="turtle")
    for shape_file in glob.glob("../imports/**/*.ttl"):
        shape_graph.parse(shape_file, format="turtle")

    # import dependencies on other ontologies
    env = ontoenv.OntoEnv(path="..", read_only=True)
    imported = env.import_dependencies(shape_graph)
    print(f"Imported {imported}")

    logger.info("Validating schema definition")
    # validate with topquadrant shacl
    report, valid, _ = validate(shape_graph, min_iterations=5, max_iterations=6)

    assert valid, f"Schema files not passing SHACL validation:\n{report.serialize(format='ttl')}"


def test_data_validation(data_file):
    """
    Validates the graphs in the data/ folder against the data and model shapes

    WARNS but does not fail the test on a validation error for a shape with sh:Info severity
    """
    data_file = Path(data_file)


    env = ontoenv.OntoEnv(path="..", read_only=True)
    data_graph = rdflib.Graph().parse(data_file, format="turtle")
    # check that model imports "http://data.ashrae.org/standard223/1.0/model/all"
    if (None, rdflib.URIRef("http://www.w3.org/2002/07/owl#imports"), rdflib.URIRef("http://data.ashrae.org/standard223/1.0/model/all")) not in data_graph:
        assert False, f"Model file {data_file} does not import the s223 ontology"

    # load in all dependent data validation and model definition shapes
    imported = env.import_dependencies(data_graph)
    print(f"Imported {imported}")

    logger.info("Validating data definition of %s (%d triples)", data_file, len(data_graph))
    # run topquadrant shacl and get the report
    valid, report_graph, _report_str = validate(data_graph, min_iterations=5, max_iterations=6)
    # make 'compiled' directory
    assert valid, report_graph.serialize(format='ttl')
