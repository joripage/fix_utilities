"""
- Generate fix documents from a CSV file.
- Enum types are supported via the enum_values field, with individual values separated by the | character.
"""

from collections import defaultdict
import xml.etree.ElementTree as ET
import csv


def parse_enum_values(enum_str, tag_number, errors):
    """
    parse enum values (enum_value:description)
    """

    enum_list = []
    if not enum_str:
        return enum_list
    parts = enum_str.strip().split("|")
    for part in parts:
        if ":" not in part:
            errors.append(
                f"❌ ERROR: Invalid enum format for tag {tag_number}: '{part}' (missing ':')")
            continue
        enum_code, enum_desc = part.split(":", 1)
        enum_list.append((enum_code.strip(), enum_desc.strip()))
    return enum_list


def csv_to_fix_xml(csv_path: str, output_xml_path: str):
    """
    generate fix documents from a CSV file
    """
    messages = defaultdict(list)
    fields_map = {}
    errors = []
    duplicates = set()

    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            msg_type = row["msg_type"].strip()
            msg_name = row["msg_name"].strip()
            tag_number = row["tag_number"].strip()
            element_name = row["element_name"].strip()
            element_type = row["element_type"].strip()
            required = row["required"].strip().upper()
            data_type = row["data_type"].strip().upper()
            enum_raw = row.get("enum_values", "").replace(" ", "").upper()

            if element_name in fields_map:
                existing = fields_map[element_name]
                if existing["element_name"] != element_name or existing["data_type"] != data_type or existing["tag_number"] != tag_number:
                    errors.append(
                        f"⚠️ WARNING: Tag {tag_number} defined multiple times with different name/type:\n"
                        f"  → First:  element_name={existing['element_name']}, data_type={existing['data_type']}, tag_number={existing['tag_number']}\n"
                        f"  → Now:    element_name={element_name}, data_type={data_type}, tag_number={tag_number}"
                    )
                    continue  # skip conflicting field
                duplicates.add(element_name)
            else:
                fields_map[element_name] = {
                    "element_type": element_type,
                    "tag_number": tag_number,
                    "element_name": element_name,
                    "data_type": data_type,
                    "enums": parse_enum_values(enum_raw, tag_number, errors)
                }

            messages[(msg_type, msg_name)].append({
                "element_type": element_type,
                "element_name": element_name,
                "required": required
            })

    # XML root
    fix = ET.Element("fix", attrib={
        "type": "FIX",
        "major": "4",
        "minor": "4",
        "servicepack": "0"
    })

    # Messages
    messages_el = ET.SubElement(fix, "messages")
    for (msg_type, msg_name), fields in messages.items():
        msg_el = ET.SubElement(messages_el, "message", attrib={
            "name": msg_name,
            "msgtype": msg_type,
            "msgcat": "app"
        })
        seen_fields = set()
        for field in fields:
            if field["element_name"] in seen_fields:
                continue  # avoid duplicate field in same message
            seen_fields.add(field["element_name"])
            ET.SubElement(msg_el, field["element_type"], attrib={
                "name": field["element_name"],
                "required": field["required"]
            })

    # Fields
    fields_el = ET.SubElement(fix, "fields")
    for _, field in fields_map.items():
        if field["element_type"] == "field":
            field_el = ET.SubElement(fields_el, "field", attrib={
                "number": field["tag_number"],
                "name": field["element_name"],
                "type": field["data_type"]
            })
            for enum_code, enum_desc in field["enums"]:
                ET.SubElement(field_el, "value", attrib={
                    "enum": enum_code,
                    "description": enum_desc
                })
        elif field["element_type"] == "component":
            field_el = ET.SubElement(fields_el, "component", attrib={
                "name": field["element_name"],
                "type": field["data_type"]
            })

    # Output XML
    tree = ET.ElementTree(fix)
    try:
        ET.indent(tree, space="  ", level=0)
    except Exception as ex:
        print('Indent fail with exception', ex)

    tree.write(output_xml_path, encoding="utf-8", xml_declaration=True)

    print(f"✅ FIX XML generated: {output_xml_path}")
    if duplicates:
        print(
            f"ℹ️ Duplicate fields detected (same tag, same definition): {sorted(duplicates)}")
    if errors:
        print("\n".join(errors))


CSV_PATH = "data/custom.csv"
OUTPUT_XML_PATH = "data/FIX-CUSTOM.xml"
if __name__ == "__main__":
    csv_to_fix_xml(CSV_PATH, OUTPUT_XML_PATH)
