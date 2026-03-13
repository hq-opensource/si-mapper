## Turtle

```turtle
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix s223: <http://data.ashrae.org/standard223/> .
@prefix s231: <http://data.ashrae.org/standard231/> .
@prefix bacnet: <http://data.ashrae.org/bacnet/> .

@prefix exf: <urn:ex/Abs#> .
@prefix exg: <urn:ex/Min#> .

_:00001 a s223:FunctionInput ;
    s223:hasExternalReference [
        bacnet:device-identifier "device,12345";
        bacnet:object-identifier "analog-input,1";
        bacnet:property-identifier "present-value";
    ] .

_:00002 a exf:Abs ;
    exf:x _:00001 ;
    exf:y _:00003 .

_:00004 a exg:Min ;
    exg:u1 _:00003 ;
    exg:u2 [ rdf:value 100.0 ] ;
    exg:y _:00005 .
```

## JSON-LD Context

```json-ld
{
    "@context": {
        "bacnet": "http://data.ashrae.org/bacnet/",
        "exf": "urn:ex/Abs#",
        "exg": "urn:ex/Min#",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "s223": "http://data.ashrae.org/standard223/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",

        "rdf:type": { "@type": "@id" },
        "exf:x": { "@type": "@id" },
        "exf:y": { "@type": "@id" },
        "exg:u1": { "@type": "@id" },
        "exg:u2": { "@type": "@id" },
        "exg:y": { "@type": "@id" }
    }
}
```
