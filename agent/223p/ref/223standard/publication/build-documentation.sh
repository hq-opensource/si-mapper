#!/bin/bash

# change this to where the index.html file will be stored
# The generated HTML file is in html-doc-gen/static/index.html
export S223_DOC_HOST="https://defs.open223.info"
# export S223_DOC_HOST="html-doc-gen/static/index.html"

ttl_files="./223standard.ttl $(find ../models ../vocab ../inference ../validation ../extensions -name '*.ttl')"

#
# make sure there are files
if [[ "$ttl_files" == "" ]]
then
    echo 'No .ttl files found'
    exit 1
fi

echo "Translating $ttl_files to 223p_publication.docx"

# convert the Turtle file to Markdown
python3 ttl2md.py 223p_publication.md $ttl_files

# convert the markdown to Word
pandoc 223p_publication.md -o 223p_publication.docx --reference-doc=custom-reference.docx

python3 build_html_documentation.py

# convert the markdown to PDF
# pandoc 223p_publication.md -o 223p_publication.pdf --pdf-engine=xelatex

