"""
- Merge default FIX and custom FIX definitions into a single output file.
- Support checking and removing duplicate tag, field.
"""

import xml.etree.ElementTree as ET
from collections import defaultdict


def merge_fix_xml(default_xml_path, custom_xml_path, output_xml_path):
    """
    merge fix xml
    warning when there duplicate tag, field in default and custom FIX
    """

    default_tree = ET.parse(default_xml_path)
    custom_tree = ET.parse(custom_xml_path)
    default_root = default_tree.getroot()
    custom_root = custom_tree.getroot()

    default_fields = default_root.find("fields")
    custom_fields = custom_root.find("fields")

    # Check duplicate in custom file
    tag_counts = defaultdict(list)
    for f in custom_fields.findall("field"):
        tag = f.attrib.get("number")
        if tag:
            tag_counts[tag].append(f)

    for tag, items in tag_counts.items():
        if len(items) > 1:
            print(
                f"⚠️ Field tag {tag} is declared {len(items)} times in FIX44-CUSTOM.xml:")
            for i, f in enumerate(items):
                print(
                    f"   #{i+1}: name={f.attrib.get('name')}, type={f.attrib.get('type')}")

    # Merge and compare with default
    default_field_map = {
        f.attrib["number"]: f for f in default_fields.findall("field")
    }

    for cf in custom_fields.findall("field"):
        num = cf.attrib.get("number")
        if num in default_field_map:
            df = default_field_map[num]
            if (
                df.attrib.get("name") != cf.attrib.get("name")
                or df.attrib.get("type") != cf.attrib.get("type")
            ):
                print(
                    f"⚠️ TAG {num} has same name but different type:")
                print(f"  → default FIX: {df.attrib}")
                print(f"  → custom FIX: {cf.attrib}")
            else:
                print(
                    f"⚠️ TAG {num} exists in default FIX (same name & type).")

    for cf in custom_fields.findall("field"):
        num = cf.attrib["number"]
        if num in default_field_map:
            df = default_field_map[num]
            existing_enums = {v.attrib["enum"] for v in df.findall("value")}
            for val in cf.findall("value"):
                if val.attrib["enum"] not in existing_enums:
                    df.append(val)
        else:
            default_fields.append(cf)

    # Merge messages / components
    def merge_section(name, key_attr):
        d_sec = default_root.find(name)
        c_sec = custom_root.find(name)
        if c_sec is None:
            return

        existing_keys = {e.attrib.get(key_attr) for e in d_sec.findall("*")}
        for element in c_sec.findall("*"):
            key = element.attrib.get(key_attr)
            if key and key not in existing_keys:
                d_sec.append(element)

        # For messages, we need to add more MsgType enum
        if name == "messages":
            msg_type_field = default_root.find(".//field[@number='35']")
            for msg in c_sec:
                enum = msg.get("msgtype")
                description = msg.get("name").upper()

                # Check if this value already exists
                exists = msg_type_field.find(f"./value[@enum='{enum}']")
                if exists is None:
                    ET.SubElement(msg_type_field, "value",
                                  enum=enum, description=description)

    merge_section("messages", "name")
    merge_section("components", "name")

    try:
        ET.indent(default_tree, space="  ", level=0)
    except Exception as ex:
        print('Indent fail with exception', ex)

    default_tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)
    print(f"✅ Merged FIX dictionary into: {output_xml_path}")


DEFAULT_XML_PATH = "data/FIX44.xml"
CUSTOM_XML_PATH = "data/FIX-CUSTOM.xml"
OUTPUT_XML_PATH = "data/FIX-MERGED.xml"
if __name__ == "__main__":
    merge_fix_xml(
        DEFAULT_XML_PATH,
        CUSTOM_XML_PATH,
        OUTPUT_XML_PATH
    )
