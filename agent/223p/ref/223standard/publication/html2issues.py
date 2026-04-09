from lxml import etree

_debug = 0


def td_to_text(td) -> str:
    """
    Encode the td as html, strip off the <td> and </td>, remove newline
    characters that break the table.
    """
    txt = etree.tostring(td).decode()[4:-6]
    return txt.replace("\n", " ")


# static file for now
doc = etree.parse("223p-APR1-Comments.html")
root = doc.getroot()

tables = list(root.xpath("/html/table/tbody"))
while tables:
    comment_table, response_table, *tables = tables
    td = list(comment_table.xpath("tr/td"))

    assert td[0].text == "Comment Key"
    comment_key = td[1].text

    assert td[12].text == "Comment Title"
    comment_title = td_to_text(td[13])

    assert td[20].text == "Comment Text"
    comment = td_to_text(td[21])

    assert td[24].text == "Substantiating Comments"
    substantiating_comment = td_to_text(td[25])

    print(
        f"""
## {comment_title}

|  |  |
|--|--|
| Comment Key | {comment_key} |
| Comment Text | {comment} |
| Substantiating Comments | {substantiating_comment} |

    """
    )
    print("next: ", end="")
    next = input()
