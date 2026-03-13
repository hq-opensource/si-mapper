## Compiling 223P Into a Single File

Install the requirements in `requirements.txt` using pip, or use [`uv`](https://github.com/astral-sh/uv)
to execute the script (and handle the dependencies automatically).

Remember to run `compile-223p.py` from *the root of the repository*

```bash
# with pip
python -m venv toolsvenv
. toolsvenv/bin/activate
pip install -r tools/requirements.txt
python tools/compile-223p.py

# with uv
uv run tools/compile-223p.py
```

This will output the '223p.ttl' turtle file in the root of the repository.
