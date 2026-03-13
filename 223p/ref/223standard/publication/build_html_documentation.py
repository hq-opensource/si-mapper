# /// script
# dependencies = [
#     "jinja2",
#     "rdflib",
# ]
# ///
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape
from rdflib import Namespace, BNode, RDF, RDFS, Graph

class SiteBuilder:
    def __init__(self, constraints_json_file: str):
        with open(constraints_json_file, 'r') as f:
            self.constraints = json.load(f)

    def build_definitions(self):
        # list of dictionaries, each with:
        # - class (concept URI)
        # - name
        # - label
        # - immediate_subgraph (cbd)
        # - see also (all constraints and rules)
        definitions = []
        for concept, defn in self.constraints.items():
            print(concept)
            print(json.dumps(defn, indent=2))
            print('---')
            definitions.append({
                "class": concept,
                "name": defn["stable_id"],
                "label": defn["label"],
                "immediate_subgraph": defn["cbd"],
            })
        return definitions

    def build(self):
        env = Environment(
            loader=FileSystemLoader('html-documentation-templates'),
            autoescape=select_autoescape()
        )
        template = env.get_template("index.html")

        definitions = self.build_definitions()
        #prop_defns = self.build_property_shapes()

        # Now render the template
        with open("index.html", "w") as f:
            f.write(template.render(
                concepts=definitions,
                #property_shapes=[d.to_dict() for d in prop_defns],
            ))

if __name__ == "__main__":
    builder = SiteBuilder("constraints.json")
    builder.build()
