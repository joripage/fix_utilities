# FIX Spec Utilities

This set of scripts is used to process custom FIX specifications which are outside the official standard.

## Features

- **Generate Custom FIX File**  
  Create a custom FIX definition file using declarations from a CSV input.  
  Useful for defining non-standard messages not covered by the official FIX spec.

- **Merge FIX Definitions**  
  Merge custom FIX definitions with the official FIX spec into a single output file.  
  Supports checking for and removing duplicate messages, tags, and fields.

- **Cleanup Unused Definitions**  
  Remove unnecessary messages, components, and fields from the final FIX output to reduce size and improve maintainability.

## Usage

- Input your data in data/custom.csv

|msg_type|msg_name       |tag_number|field_name   |required|format|enum_values                                 |
|--------|---------------|----------|-------------|--------|------|--------------------------------------------|
|C01     |CustomMessage01|20001     |CustomField01|Y       |STRING|Enum01:Enum 01&#124;Enum02:Enum 02&#124;Enum03:Enum 03|
|C01     |CustomMessage01|20002     |CustomField02|N       |STRING|Enum04:Enum 04&#124;Enum05:Enum 05               |
|C01     |CustomMessage01|55        |Symbol       |N       |STRING|                                            |
|C02     |CustomMessage02|20010     |CustomField03|Y       |INT   |                                            |

- Input messages to keep in data/filter_config.json
- Run script

```python
# Generate Custom FIX File
python ./00_csv_to_fixxml.py 

# Merge FIX Definitions
python ./01_merge_fixxml_dictionaries.py 

# Cleanup Unused Definitions
python ./02_strip_fixxml_by_message.py 
```

## Notes

- Enum values in the CSV input should be defined in the `enum_values` column, separated by the `|` character.
- XML field tags must be unique; duplicate tag declarations will be flagged and removed.
