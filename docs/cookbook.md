* autorun - create constant
```python
const.check("constant_name", "Description", "value")
```
* autorun - ensure empty primary key
```python
ensure_empty_pk("table_name")
```

* Form/Grid - selected rows
```python
rows = form.get_grid_selected_rows()
for x in rows:
	row = form.model.get_record(x)
	# Do smth with row
	# update(form.model.get_table_name(), row)
form.refresh()
```

* Inserting data into database table, with progress bar
```python
contacts = [{...}, {...}, ..., {...}]
w = q2wait(len(contacts), "Inserting records")
transaction()
for row in contacts:
    w.step(100)  # update progress bar, every 100 msec
    if not insert("contacts", row):
        q2wait(f"Error while inserting records into table <b>Contacts</b>- {last_error()}!")
w.close()
commit()
```

* Get something defined in module (function, class, variable) by `module_name` and  `name`
```python
# get func
_module_function = ffinder("module_name","name")
# run func
_module_function()
```

# Hooks
## _e_control 
* Adding extra columns (controls) into form `_dbanken_kontobewegung` after control `date`
```python
if name == "_dbanken_kontobewegung": # check form name by mem._name (or just name)
    if control["column"] == "date": # check desirable column by mem.controls (or control)
        cu = q2cursor("""
                    select *
                    from `lines`
                    where name == '_school__dbanken_kontobewegung'
                    """, myapp.db_logic)
        for x in cu.records():
            form.add_control(**x)
```

* Adding extra columns (controls) into form `_dbanken_kontobewegung` after control `date`
```python
if mem._name == "sheet_keys": # check form name by mem._name (or just name)
    if mem.controls[-1].get("column") == "key_value": # check desirable column by mem.controls (or control)
        mem.controls.extend(get_form("_test_sheet_keys").controls) # add extra columns
```
## _e_action - 
* Adding extra grid action into form name 
```python
```
