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

    # Load and parse FIX XML
    tree = ET.parse(fix_xml_path)
    root = tree.getroot()

    messages_el = root.find("messages")
    fields_el = root.find("fields")
    components_el = root.find("components")

    # Filter <messages> and collect used fields/components
    for msg in list(messages_el):
        msgtype = msg.attrib.get("msgtype")
        if (msgtype) not in messages_to_keep:
            messages_el.remove(msg)
        else:
            for field in msg.findall("field"):
                used_field_names.add(field.attrib["name"])
            for comp in msg.findall("component"):
                used_components.add(comp.attrib["name"])

    # Recursively collect nested components
    def collect_nested_components(comp_name):
        if comp_name not in component_map or comp_name in visited_components:
            return
        visited_components.add(comp_name)
        comp = component_map[comp_name]
        for field in comp.findall("field"):
            used_field_names.add(field.attrib["name"])
        for subcomp in comp.findall("component"):
            subname = subcomp.attrib["name"]
            used_components.add(subname)
            collect_nested_components(subname)

    # Create map of all components
    component_map = {}
    visited_components = set()
    if components_el is not None:
        for comp in components_el.findall("component"):
            name = comp.attrib["name"]
            component_map[name] = comp

        for comp in list(used_components):
            collect_nested_components(comp)

        # Remove unused components
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
