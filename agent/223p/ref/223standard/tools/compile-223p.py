# /// script
# dependencies = [
#     "rdflib",
#     "pyontoenv>=0.4.0a9",
#     "pytz",
#     "gitpython"
# ]
# ///
import rdflib
import ontoenv
from git import Repo
import pytz
import os

S223 = rdflib.Namespace("http://data.ashrae.org/standard223#")
OWL = rdflib.OWL
SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
G36 = rdflib.Namespace("http://data.ashrae.org/standard223/1.0/extensions/g36#")
BACNET= rdflib.Namespace("http://data.ashrae.org/bacnet/2020#")
QUDT = rdflib.Namespace("http://qudt.org/schema/qudt/")
QUDT_QK = rdflib.Namespace("http://qudt.org/vocab/quantitykind/")
QUDT_UNIT = rdflib.Namespace("http://qudt.org/vocab/unit/")
ROOT = rdflib.URIRef("http://data.ashrae.org/standard223/1.0/model/all")
S223DOC = rdflib.URIRef("http://sample.org/doc#")

########################################
# Setup environment to find ontologies #
########################################
# create an environment that knows about those files
env = ontoenv.OntoEnv(
    # look for ontologies in these directories
    search_directories=[
        "collections",
        "extensions",
        "inference",
        "models",
        "validation",
        "vocab",
    ],
    # don't write anything to disk
    temporary=True,
    # don't download any referenced graphs. Only use local files.
    offline=True,
    # don't fail if an import is missing
    strict=False,
)

s223graph = rdflib.Graph()
s223graph.bind("s223", S223)
s223graph.bind("sh", SH)
s223graph.bind("qudt", QUDT)
s223graph.bind("quantitykind", QUDT_QK)
s223graph.bind("unit", QUDT_UNIT)
s223graph.bind("g36", G36)
s223graph.bind("bacnet", BACNET)

# build the imports closure
s223graph, imported = env.get_closure(
    "http://data.ashrae.org/standard223/1.0/model/all",
    s223graph,
    rewrite_sh_prefixes=True,
    remove_owl_imports=True,
)
print(f"Imported {len(imported)} files")
for i in imported:
    print(i)

########################
# Get git version info.
# This will either be the tag (if present) or branch@commit + timestamp.
# If we are in CI/CD, we can use environment variables.
# Otherwise, we use GitPython to get the info from the local git repo.
########################

tag = os.getenv("CI_COMMIT_TAG", "")
# this is true if we are running in GitLab CI/CD
in_ci_cd = bool(os.getenv("CI_COMMIT_SHA"))
if not tag:
    if in_ci_cd:
        # then assemble from other env vars
        branch = (
            os.getenv("CI_COMMIT_BRANCH")
            or os.getenv("CI_COMMIT_REF_NAME")
        )
        commit = os.getenv("CI_COMMIT_SHA")
        timestamp = os.getenv("CI_COMMIT_TIMESTAMP")
    else:
        # not in CI/CD; we will get info from git repo below
        repo = Repo(".")
        timestamp = repo.head.object.committed_datetime.astimezone(pytz.UTC).strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )
        commit = repo.head.commit.hexsha
        branch = [h.name for h in repo.heads if h.commit.hexsha == commit]
        branch = branch[0] if branch else "HEAD"


###########
# Remove doc:subclauses, s223doc:subclauses predicates, and everything in the
# list they point to.
# Also remove all pub: nodes and their triples.
##########
for o in s223graph.objects(predicate=rdflib.URIRef("http://sample.org/doc#subclauses")):
    # delete list starting at o
    rdflist = rdflib.collection.Collection(s223graph, o)
    rdflist.clear()
s223graph.remove(
        (None, rdflib.URIRef("http://sample.org/doc#subclauses"), None)
)
# remove s223doc:title
s223graph.remove(
        (None, rdflib.URIRef("http://sample.org/doc#title"), None)
        )
# remove subjects in the pub: namespace and all their triples
for s in s223graph.subjects():
    if str(s).startswith("pub:"):
        s223graph.remove((s, None, None))


########################################
# Now update the ontology version info #
########################################
# remove duplicate sh:declare (sh:prefix, sh:namespace) pairs
# we have this kind of construct after we merge the sh:declare statements:
# <x> a owl:Ontology ;
# sh:declare [ sh:namespace "http://data.ashrae.org/standard223#"^^xsd:anyURI ;
#            sh:prefix "s223"^^xsd:string ],
#        [ sh:namespace "http://data.ashrae.org/standard223#"^^xsd:anyURI ;
#            sh:prefix "s223"^^xsd:string ],
#        [ sh:namespace "http://data.ashrae.org/standard223#"^^xsd:anyURI ;
#            sh:prefix "s223"^^xsd:string ],
#        ...
# Here, we remove the duplicates. Eventually this will be fixed in ontoenv
for ontology in s223graph.subjects(rdflib.RDF.type, rdflib.OWL.Ontology):
    declares = list(s223graph.objects(ontology, SH.declare))
    unique_declares = set()
    for declare in declares:
        prefix = s223graph.value(declare, SH.prefix)
        namespace = s223graph.value(declare, SH.namespace)
        unique_declares.add((prefix, namespace))
    # remove all existing sh:declare statements
    s223graph.remove((ontology, SH.declare, None))
    s223graph.remove((None, SH.prefix, None))
    s223graph.remove((None, SH.namespace, None))
    # add back the unique ones
    for prefix, namespace in unique_declares:
        bnode = rdflib.BNode()
        s223graph.add((ontology, SH.declare, bnode))
        s223graph.add((bnode, SH.prefix, prefix))
        s223graph.add((bnode, SH.namespace, namespace))

# write out the version info
s223graph.remove((None, OWL.versionInfo, None))
# Build version string: tag only if present; otherwise git metadata
version_string = tag if tag else f"git:{branch}@{commit} date:{timestamp}"
s223graph.add((ROOT, OWL.versionInfo, rdflib.Literal(version_string)))
print(f"Set version to {version_string}.")

s223graph.serialize("223p.ttl", format="turtle")
