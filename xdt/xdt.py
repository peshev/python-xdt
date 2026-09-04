import lxml.etree
import re

xdt_ns = "http://schemas.microsoft.com/XML-Document-Transform"
locator_qname = lxml.etree.QName(xdt_ns, "Locator")
transform_qname = lxml.etree.QName(xdt_ns, "Transform")
xdt_attribs = {locator_qname, transform_qname}
attr_regex = re.compile(r"(?P<type>\w+)(?:\((?P<value>.+)\))?")


def locator_match(attribute, transform_element):
    match_value = transform_element.attrib[attribute]

    def apply(source_element):
        return source_element.attrib.get(attribute) == match_value

    return apply


def locator_xpath(xpath, _):
    def apply(source_element):
        return source_element in source_element.getroot().xpath(xpath)

    return apply


def locator_condition(condition, _):
    def apply(source_element):
        return source_element in source_element.getparent().xpath(f"{source_element.tag}[{condition}]")

    return apply


def remove_xdt_attribs(e):
    return remove_attribs(e, xdt_attribs)


def remove_attribs(e, attribs):
    for a in attribs:
        if a in e.attrib:
            del e.attrib[a]
    return e


def copy_element(from_element: lxml.etree.Element) -> lxml.etree.Element:
    to_element = lxml.etree.Element(
        from_element.tag,
        {k: v for k, v in from_element.attrib.items() if k not in xdt_attribs},
        None)
    to_element.tail = from_element.tail
    to_element.text = from_element.text
    for child in from_element:
        to_element.append(copy_element(child))
    return to_element


locator_types = {
    "Match": locator_match,
    "Condition": locator_condition,
    "XPath": locator_xpath,
}
transform_types = {
    "Replace": lambda v, te, se: se.getparent().replace(se, copy_element(te)),
    "Insert": lambda v, te, se: se.getparent().append(copy_element(te)),
    "InsertBefore": lambda v, te, se: se.addprevious(copy_element(te)),
    "InsertAfter": lambda v, te, se: se.addnext(copy_element(te)),
    "Remove": lambda v, te, se: se.getparent().remove(se),
    "RemoveAll": lambda v, te, se: se.getparent().remove(se),
    "RemoveAttributes": lambda v, te, se: remove_attribs(se, v.split(",")),
    "SetAttributes": lambda v, te, se: se.attrib.update(copy_element(te).attrib),
}


def is_element(node):
    return node.tag not in {lxml.etree.Comment, lxml.etree.Entity}


def transform_elements(transform_parent, source_parent):
    changed = False
    for te in transform_parent:
        if not is_element(te):
            continue
        locator = attr_regex.match(te.attrib[locator_qname]).groupdict() if locator_qname in te.attrib else {}
        locator_fn = locator_types[locator["type"]](locator["value"], te) if locator else lambda x: True
        source_elements = locator_fn(source_parent) if locator.get("type") == "XPath" else source_parent
        found = False
        for se in source_elements:
            if is_element(se) and ((te.tag == se.tag and locator_fn(se)) or locator.get("type") == "XPath"):
                found = True
                if transform_qname in te.attrib:
                    _transform = attr_regex.match(te.attrib[transform_qname]).groupdict()
                    transform_types[_transform["type"]](_transform["value"], te, se)
                    changed |= True
                    if _transform["type"] == "Remove":
                        break
                else:
                    changed |= transform_elements(te, se)
        if not found:
            se = copy_element(te)
            source_parent.append(se)
            transform_elements(te, se)
            changed |= True
    return changed


def file(f, mode="rb"):
    try:
        _ = f.read
        return f
    except AttributeError:
        return open(f, mode)


def transform(source_file, transform_file, target_file):
    source_tree = lxml.etree.parse(file(source_file))
    changed = transform_elements(
        lxml.etree.parse(file(transform_file)).getroot(),
        source_tree.getroot())
    if changed:
        source_tree.write(
            target_file,
            encoding="utf-8",
            pretty_print=True,
            xml_declaration=True
        )
    return changed
