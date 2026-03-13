# Evaluation Methodology

This document establishes an empirical methodology for evaluating the 223 standard in order to codify the properties of 223 that make it successful and suitable for its intended use cases. We draw some inspiration from [0], which established the empirical metadata evaluation methodology that drove development of the Brick ontology. The original Brick paper [1] lays out three general properties of an ontology that make it successful for the building domain: completeness, extensibility and usability. We define each of these terms in the context of 223 and outline the specific evaluation procedures used.



## Completeness

**Does the ontology name/describe/capture all of the necessary concepts and relationships with respect to existing standards and practices?**

It is intractible for 223 to exhaustively define all possible concepts in the smart building domain --- it is unclear how this full list would even be obtained or maintained. Instead, 223 should be *complete* with respect to the concepts and relationships which are important or necessary by virtue of their inclusion within existing standards and other digital representations of buildings and their components.

A non-exhaustive list of these resources is as follows:
- The [crowdsourcing document](https://docs.google.com/spreadsheets/d/1IrWjDpf4p5IfCvRpOP30Ys8_-Qi5_x2dz4VzTb8AsXk/edit#gid=1151522499)
- Data dictionaries:
    - [BEDES](https://bedes.lbl.gov/)
    - [BSDD](http://bsdd.buildingsmart.org/)
    - [ASHRAE](https://xp20.ashrae.org/terminology/)
    - [VBIS](https://vbis.com.au/search-and-download)
- Existing metadata formats, schemas and ontologies:
    - [IFC](https://technical.buildingsmart.org/standards/ifc/)
    - [gbXML](https://gbxml.org/)
    - [BuildingSync](https://buildingsync.net/)
    - [Project Haystack](https://project-haystack.org)
    - [Brick](https://brickschema.org)
    - [Real Estate Core](https://www.realestatecore.io/)
    - [Digital Buildings](https://github.com/google/digitalbuildings)
    - [Azue Digital Twin Definition Language](https://github.com/Azure/opendigitaltwins-building)
    - Control Description Language
- Existing and emerging standards:
    - ASHRAE Guidelines 36
    - ASHRAE 201 ?

Because the above resources are developed to be appropriate for particular stakeholders and stages of the building lifecycle, not all of the concepts and relationships they define are in scope for 223. The "completeness" of 223 shall be determined by how many of the relevant concepts and relationships expressed in other resources can be expressed in 223. This in part constitutes the creation of an "alignment" between 223 and these other building metadata representations. To a first order, the alignments can be expressed as a table with the following columns:

- Name of the building representation
- Concept/term/relationship from the building representation
- the class name, triple or set of triples from 223 that describe the intended concept/term/relationship

For linked data-based models, such as REC, Brick and  Digital Buildings, this mapping should be established programmatically or axiomatically when possible, to facilitate translation and simplify maintenance.


## Extensibility

**Can 223 gracefully expand to model new concepts and relationships as required?**

Due to the difficulty of creating an exhaustive list of all of the concepts and relationships that 223 must cover, it is important to ensure that 223 is sufficiently *extensible*. This means that 223's structure is not overfit to the concepts and relationships available to the authors during the development of 223, and that 223 permits the expression of new kinds of concepts and relationships that emerge either as the result of growing adoption (e.g. to include equipment used in non-US HVAC systems) or as the result of innovation in the building industry (e.g. new kinds of systems and equipment that must be described).

One way to measure extensibility is through *cross-validation*: in the collection of concepts/relationships (as detailed in the *Completeness* section above), a certain percentage (typically 10-20%) is withheld from consideration when creating the class hierarchies and other elements of the ontology. Then, the withheld items are reintroduced and folded into the 223 structure --- if the structure is sufficiently extensible, then these withheld concepts and relationships should be able to be incorporated without having to rearrange the ontology structure.

This can be complemented or supplanted by modeling real, existing and representative buildings and building systems using 223 and determining if any new concepts or relationships need to be introduced in order to adequately represent the input data. Some of these may come from public reference models (such as those provided by gbXML) or ASHRAE standards (such as the HVAC systems described in Figures A-2, A-9). Part of the non-normative release of 223 should be descriptions/figures of these systems and their RDF-representation in 223.

## Usability

**Does 223 support the queries and applications required by users while minimizing cognitive load?**

The usability of 223 can be determined by (a) the extent to which it supports answering queries required for a set of representative "building applications", as outlined by the official scope of 223, and (b) the complexity of those queries and the building models.

To measure (a), we assemble a list of building "application" descriptions from available publications, standards, engineering documents (such as sequence of operations descriptions) and experts. For each of these "use cases", we enumerate:

- a name/description of the application and its intended purpose
- a broad category:
    - fault detection and diagnosis
    - controls and optimization
    - energy audits
    - construction and commissioning
    - **these are preliminary and up for discussion**
- a list of data sources, equipment, devices, relationships required for the application to run
- SPARQL queries, SHACL shapes or other declarative, executable description of how the application requirements are epressed using 223

Complementary to this database of applications is a set of *competancy questions*, which are specific technical inquiries which should be answerable by querying an instance of the 223 model. These questions should be expressed using SPARQL queries, and will be organized by "building lifecycle stage" and by subsystem.

Together, the SPARQL queries, SHACL shapes and 223 reference models constitute the basis of a *unit and integration test suite* that provides both examples of use, and validation that the 223 implementation fulfills the requirements set forward by the use cases.

[0]: https://dl.acm.org/doi/10.1145/2821650.2821669
[1]: https://dl.acm.org/doi/abs/10.1145/2993422.2993577
