# Modeling Assumptions

This document outlines a *profile* (commonly called a *fragment* or *sublanguage* in computational logic) that is a trimmed down version of RDF, RDFS, OWL2 RL, and SHACL that will be used in the project.  Based on similar OWL 2 profiles, it trades
some expressive power for efficiency in reasoning.

This profile is based on a subset of the RDFS and OWL 2 QL profile, we are
expecting that SHACL rules will be used for instance validation.

## Model Literals

Model literals are limited to supported the following datatypes:

* xsd:boolean
* xsd:decimal
* xsd:integer
* xsd:float
* xsd:double
* xsd:string
* xsd:hexBinary
* xsd:base64Binary
* xsd:dateTime
* xsd:dateTimeStamp
* xsd:anyURI

At the current time there are no expected use cases that required a distinction
between the following datatypes and therefore should be considered equivalent:

* xsd:float
* xsd:double

These integer value datatypes have restricted values.  Where it is
necessary the value limits are expressed in SHACL rules:

* xsd:nonNegativeInteger
* xsd:nonPositiveInteger
* xsd:positiveInteger
* xsd:negativeInteger
* xsd:long
* xsd:int
* xsd:short
* xsd:byte
* xsd:unsignedLong
* xsd:unsignedInt
* xsd:unsignedShort
* xsd:unsignedByte

These string value datatypes have restricted content.  Where it is
necessary the value limits are expressed in SHACL rules:

* xsd:normalizedString
* xsd:token

## RDF Classes

The following RDF/RDFS classes are supported:

* rdfs:Class
* rdf:Property

## RDF Properties

The following RDF/RDFS properties are supported:

* rdfs:range
* rdfs:domain
* rdf:type
* rdfs:subClassOf
* rdfs:subPropertyOf
* rdfs:label
* rdfs:comment

## RDF Containers

There is no support for RDF Containers or the subclasses rdf:Bag, rdf:Seq, or
rdf:Alt.

## RDF List

The rdfs:List is supported and the properties called rdf:_1, rdf:_2, rdf:_3...
etc., along with the properties rdf:first, rdf:rest, and rdf:nil.

## OWL Properties

* owl:ObjectProperty
* owl:DatatypeProperty

The following property classes are reserved for future consideration:

* owl:ReflexiveProperty
* owl:SymmetricRelation
* owl:TransitiveProperty

The following properties are reserved for future consideration:

* owl:inverseOf

## OWL Individuals

The following class is supported:

* owl:NamedIndividual

## Annotation Properties

* dct:description

## Properties from External Ontologies

### QUDT

* qudt:applicableUnit - used in validation queries to find the units appropriate for a given kind of quantity, (such as Pressure or Temperature). This property returns the set of valid units, (e.g. Degree Celsius, Degree Fahrenheit,... for Temperature).

* qudt:hasQuantityKind - used to specify the kind of quantity that is being specified or observed (such as Pressure or Temperature).

* qudt:hasUnit - used to characterize a quantity value by specifying the unit of measure being used.

### Brick

* brick:Equipment (and its subclasses): will be aligned with certain subclasses of 223's System and Device and Part concepts, providing a higher-level language that simplifies the data model and application queries at the expense of certain detail. In many cases, the Brick class will be a "shortcut" to a collection of 223-compliant statements where there is not a 1-1 class correlation. For example, a Brick class such as Exhaust Damper captures the context of the equipment in addition to its classification as a damper. In these cases, SHACL shapes or OWL Restrictions will be used to formalize the exact set of 223 statements that are equivalent to the Brick class.
* brick:Point (and its subclasses): will be used to capture the digital representation (e.g. "BMS Point") of the observable and actuatable properties defined in the 223 model. Similar to how Equipment is handled above, some Brick Points will be formalized as a collection of 223-compliant statements
* brick:Location (and its subclasses): will be used to capture the relationship of 223 components to the spatial elements of the building. This will be done in conjunction with a BOT alignment
