import sys

G36_HEADER = """# baseURI: http://data.ashrae.org/standard223/data/{sample_name}
# imports: http://data.ashrae.org/standard223/1.0/model/all

@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://data.ashrae.org/standard223/data/{sample_name}>
  a owl:Ontology ;
  rdfs:isDefinedBy <http://data.ashrae.org/standard223/data/{sample_name}> ;
  rdfs:label "{sample_name}" ;
  owl:imports <http://data.ashrae.org/standard223/1.0/model/all> .

"""


def g36_header(sample_name):
    """Prints the sample header."""
    return G36_HEADER.format(sample_name=sample_name)
