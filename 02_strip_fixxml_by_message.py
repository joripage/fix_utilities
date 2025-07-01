"""
- Strip FIX xml by defined messages.
- Remove all messages (including components and fields) which are not in list.
"""

import xml.etree.ElementTree as ET
import json


def strip_fix_xml(fix_xml_path, config_path, output_path):
    """
    strip fix sml
    """

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    messages_to_keep = {(m) for m in config["messages_to_keep"]}
    used_field_names = set()
    used_components = set()
    visited_components = set()

    # Load and parse FIX XML
    tree = ET.parse(fix_xml_path)
    root = tree.getroot()

    messages_el = root.find("messages")
    fields_el = root.find("fields")
    components_el = root.find("components")
    header_el = root.find("header")
    trailer_el = root.find("trailer")

    component_map = {
        c.attrib["name"]: c for c in components_el} if components_el is not None else {}

    def collect_nested_components(name):
        if name in visited_components or name not in component_map:
            return
        visited_components.add(name)
        used_components.add(name)
        comp = component_map[name]
        collect_fields_groups_components(comp)

    def collect_fields_groups_components(elem):
        for f in elem.findall("field"):
            used_field_names.add(f.attrib["name"])
        for g in elem.findall("group"):
            used_field_names.add(g.attrib["name"])
            collect_fields_groups_components(g)
        for c in elem.findall("component"):
            cname = c.attrib["name"]
            collect_nested_components(cname)

    # Collect from message
    for msg in list(messages_el):
        msgtype = msg.attrib.get("msgtype")
        if (msgtype) not in messages_to_keep:
            messages_el.remove(msg)
        else:
            collect_fields_groups_components(msg)

    # Collect from header and trailer
    for section in [header_el, trailer_el]:
        if section is not None:
            collect_fields_groups_components(section)

    if components_el:
        for comp in list(components_el):
            if comp.attrib["name"] not in used_components:
                components_el.remove(comp)

    # Remove unused fields
    for field in list(fields_el):
        if field.attrib["name"] not in used_field_names:
            fields_el.remove(field)

    # Save output
    try:
        ET.indent(tree, space="  ", level=0)  # Python 3.9+
    except Exception as ex:
        print('Indent fail with exception', ex)

    tree.write(output_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ FIX XML saved to: {output_path}")
    print(
        f"✅ Messages kept: {len(messages_el)}, Fields kept: {len(used_field_names)}, Components kept: {len(used_components)}")


FIX_XML_PATH = "data/FIX-MERGED.xml"
CONFIG_PATH = "data/filter_config.json"
OUTPUT_PATH = "data/FIX-STRIPPED.xml"
if __name__ == "__main__":
    strip_fix_xml(
        FIX_XML_PATH,
        CONFIG_PATH,
        OUTPUT_PATH
    )
