# Documents

Fun things to read.

## Markdown Conversion

The **schema.md** file has been converted to PDF using **pandoc** like this:

    $ sudo apt-get install texlive-latex-base texlive-fonts-recommended \
        texlive-fonts-extra texlive-latex-extra
    $ pandoc -f markdown -t pdf schema.md -o schema.pdf

