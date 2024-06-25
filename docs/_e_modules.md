### _e_controls
```python
if mem._name == "sheet_keys":
    if mem.controls[-1].get("column") == "key_value":
        mem.controls.extend(get_form("_test_sheet_keys").controls)
```