SAMPLE_HEADER = """# baseURI: http://data.ashrae.org/standard223/1.0/sample/{sample_name}-{suffix}
# imports: http://data.ashrae.org/standard223/1.0/model/all

@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

<http://data.ashrae.org/standard223/1.0/data/{sample_name}>
  a owl:Ontology ;
  rdfs:isDefinedBy <http://data.ashrae.org/standard223/1.0/sample/{sample_name}-{suffix}> ;
  rdfs:label "{sample_name}-{suffix}" ;
  owl:imports <http://data.ashrae.org/standard223/1.0/model/all> .

"""


def sample_header(sample_name, suffix):
    """Prints the sample header."""
    # sys.stdout.write(SAMPLE_HEADER.format(sample_name=sample_name))
    return SAMPLE_HEADER.format(sample_name=sample_name, suffix=suffix)
