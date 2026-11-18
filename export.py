"""Render the canonical editorial document as an Open XML Word file."""
from io import BytesIO
from xml.etree import ElementTree as ET
from zipfile import ZIP_DEFLATED, ZipFile

WORD = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
REL = "http://schemas.openxmlformats.org/package/2006/relationships"
OFFICE_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
ET.register_namespace("w", WORD)


def w(name):
    return f"{{{WORD}}}{name}"


def paragraph(body, text, style=None):
    p = ET.SubElement(body, w("p"))
    if style:
        props = ET.SubElement(p, w("pPr"))
        ET.SubElement(props, w("pStyle"), {w("val"): style})
    run = ET.SubElement(p, w("r"))
    node = ET.SubElement(run, w("t"), {XML_SPACE: "preserve"})
    node.text = "".join(c for c in text if ord(c) >= 32 and ord(c) not in (0xFFFE, 0xFFFF) and not 0xD800 <= ord(c) <= 0xDFFF)


def build_docx(brief, modules):
    document = ET.Element(w("document"))
    body = ET.SubElement(document, w("body"))
    paragraph(body, brief["theme"], "Title")
    paragraph(body, f"{brief['kind']} · {brief['level']} · {brief['audience']}")
    paragraph(body, "Sumário", "Heading1")
    for module in modules:
        paragraph(body, f"{module['id']}. {module['title']}")
    for module in modules:
        paragraph(body, f"Módulo {module['id']} · {module['title']}", "Heading1")
        for line in module["content"].splitlines():
            paragraph(body, line)
    styles = ET.Element(w("styles"))
    for name, size in (("Title", "48"), ("Heading1", "32")):
        style = ET.SubElement(styles, w("style"), {w("type"): "paragraph", w("styleId"): name})
        ET.SubElement(style, w("name"), {w("val"): name})
        props = ET.SubElement(style, w("rPr"))
        ET.SubElement(props, w("b"))
        ET.SubElement(props, w("sz"), {w("val"): size})
    content_types = f"""<Types xmlns="{TYPES}">
      <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
      <Default Extension="xml" ContentType="application/xml"/>
      <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
      <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
    </Types>"""
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as package:
        package.writestr("[Content_Types].xml", content_types)
        package.writestr("_rels/.rels", relationships("officeDocument", "word/document.xml"))
        package.writestr("word/_rels/document.xml.rels", relationships("styles", "styles.xml"))
        package.writestr("word/document.xml", ET.tostring(document, encoding="utf-8", xml_declaration=True))
        package.writestr("word/styles.xml", ET.tostring(styles, encoding="utf-8", xml_declaration=True))
    return buf.getvalue()


def relationships(kind, target):
    return f'<Relationships xmlns="{REL}"><Relationship Id="rId1" Type="{OFFICE_REL}/{kind}" Target="{target}"/></Relationships>'
