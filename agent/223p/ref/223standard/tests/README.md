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

## Test Artifacts

As part of the validation process, the unit tests will save the fully materialized versions of all models in the `data/` directory (but not the `data/nonconforming/` directory) in a `data/compiled/` directory which is made available as a build artifact.

## GitLab Runners

**Note: Only need to do this if you are setting up your own runner. Gabe has volunteered some server space to run a single GitLab Runner, which should be sufficient for now.**

To see if your tests run successfully on GitLab, you will need to configure a GitLab runner to run the tests.

First register a local Docker-based GitLab runner, using config information given [here](https://bas-im.emcs.cornell.edu/223/223standard/-/settings/ci_cd), under "Runners", and "Set up a specific runner manually".
During configuration, make sure to choose the `docker` executor and a default image of `ubuntu:latest`.

```bash
docker run --rm -it -v gitlab-runner-config:/etc/gitlab-runner gitlab/gitlab-runner:latest register
```

Then, execute the actual runner:

```bash
docker run -d --name gitlab-runner --restart always \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v gitlab-runner-config:/etc/gitlab-runner \
    gitlab/gitlab-runner:latest
```
