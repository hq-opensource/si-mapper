# Use Case Testing Framework

The use case testing framework organizes data graphs and SPARQL queries around different use cases. A simple ontology is developed to relate these concepts together and describe test cases, which are automatically read by a `pytest`-based test harness and executed.

## Overview

Below is a simple, minimal test case (stored in `tests/use-cases/sample1.ttl`):

```ttl
# an instance of the use case. Has a name + description to provide info to user.
# Use Cases are defined *independently* of implementations (e.g. to support comparison
# of a 223 vs Brick implementation). Use Cases should refer to source material when
# appropriate (e.g. fault detection cases from G36)
:sample1  a   uc:UseCase ;
    uc:description "Example test using the branch-20-sample.ttl file" ;
    uc:name "Example test" ;
.

# An Implementation implements a UseCase. It has exactly 1 data graph (a relative path
# to the tests/ folder), and 1 or more Queries
:223impl    a   uc:Implementation ;
    uc:implements   :sample1 ;
    uc:dataGraph    "../data/branch-20-sample.ttl" ;
    uc:hasQuery     :query1 ;
.

# An ImplementationQuery has a description describing what it intends to do, a SPARQL query
# definition, and a JSON file containing the expected results
:query1     a   uc:ImplementationQuery ;
    uc:description "Retrieves the current speed for each Fan in the model" ;
    uc:query    "SELECT ?fan ?speed ?unit WHERE { ?fan a d223:Fan . ?fan c223:hasProperty ?prop . ?prop qudt:hasQuantityKind quantitykind:AngularVelocity . ?prop c223:hasValue/c223:hasSimpleValue ?speed . ?prop c223:hasUnit ?unit }" ;
    uc:expectedResult "use-cases/sample1_q1.json" ;
.
```

Notice the required properties, and that all file paths are relative to the `tests/` directory. You can use data graphs defined in other parts of the repository (or even a URL to a datagraph encoded as a string literal).

## Testing Locally

(From inside the `test/` directory)

Install requirements and set up virtual environment if not already done:

```bash
$ python3 -m venv venv
$ . venv/bin/activate  # use this to activate the virtual environment later
(venv) $ pip install -r requirements.txt
```

To run the tests, just use `pytest`:

```bash
(venv) $ pytest -s -vvvv
```

## GitLab Runners

**Note: Only need to do this if you are setting up your own runner. Gabe has volunteered some server space to run a single GitLab Runner, which should be sufficient for now.**

To see if your tests run successfully on GitLab, you will need to configure a GitLab runner to run the tests.

First register a local Docker-based GitLab runner, using config information given [here](https://bas-im.emcs.cornell.edu/223/223standard/settings/ci_cd#js-runners-settings):

```bash
docker run --rm -it -v gitlab-runner-config:/etc/gitlab-runner gitlab/gitlab-runner:latest register
```

During configuration, make sure to choose the `docker` executor and a default image of `ubuntu:latest`.

Then, execute the actual runner:

```bash
docker run -d --name gitlab-runner --restart always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v gitlab-runner-config:/etc/gitlab-runner \
    gitlab/gitlab-runner:latest
```
