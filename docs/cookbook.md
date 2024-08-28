* Form/Grid - selected rows
```python
rows = form.get_grid_selected_rows()
for x in rows:
	row = form.model.get_record(x)
	# Do smth with row
	# update(form.model.get_table_name(), row)
form.refresh()
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
if name == "_dbanken_kontobewegung":
    if control["column"] == "date":
        cu = q2cursor("""
                    select *
                    from `lines`
                    where name == '_school__dbanken_kontobewegung'
                    """, myapp.db_logic)
        for x in cu.records():
            form.add_control(**x)
```

## _e_action - 
* Adding extra grid action into form name 
```python
```
