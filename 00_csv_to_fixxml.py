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
            field_name = row["field_name"].strip()
            required = row["required"].strip().upper()
            fmt = row["format"].strip().upper()
            enum_raw = row.get("enum_values", "").replace(" ", "").upper()

            if tag_number in fields_map:
                existing = fields_map[tag_number]
                if existing["name"] != field_name or existing["type"] != fmt:
                    errors.append(
                        f"⚠️ WARNING: Tag {tag_number} defined multiple times with different name/type:\n"
                        f"  → First:  name={existing['name']}, type={existing['type']}\n"
                        f"  → Now:    name={field_name}, type={fmt}"
                    )
                    continue  # skip conflicting field
                duplicates.add(tag_number)
            else:
                fields_map[tag_number] = {
                    "name": field_name,
                    "type": fmt,
                    "enums": parse_enum_values(enum_raw, tag_number, errors)
                }

            messages[(msg_type, msg_name)].append({
                "tag": tag_number,
                "name": field_name,
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
            if field["tag"] in seen_fields:
                continue  # avoid duplicate field in same message
            seen_fields.add(field["tag"])
            ET.SubElement(msg_el, "field", attrib={
                "name": field["name"],
                "required": field["required"]
            })

    # Fields
    fields_el = ET.SubElement(fix, "fields")
    for tag_number, field in fields_map.items():
        field_el = ET.SubElement(fields_el, "field", attrib={
            "number": tag_number,
            "name": field["name"],
            "type": field["type"]
        })
        for enum_code, enum_desc in field["enums"]:
            ET.SubElement(field_el, "value", attrib={
                "enum": enum_code,
                "description": enum_desc
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
