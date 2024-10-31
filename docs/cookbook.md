* progressbar & error
```python
import time
try:
    w = q2wait(2)
    time.sleep(1)
    w.step()
    1+""
    time.sleep(1)
    w.step()
except Exception as e:
    q2mess(f"{e}")
finally:
    w.close()
```

* select file and encode in base64 ascii
```python
import base64
filename, filetype = myapp.get_open_file_dialoq("Select file", 
    filter="PDF(*.pdf);;DOCX(*.docx);;All files(*.*)")
if filename:
    doc_base64  = base64.b64encode(open(filename,"rb").read()).decode("ascii")
```

* add control from another form
```python
form.add_control(**myapp.get_form("another_form_name").c.control_name)
```

* constant editing form
```python
#  in Before Form Show script
for x in mem.controls:
    column = x["column"]
    if column:
        mem.s.__setattr__(column, const.__getattr__(column))
#  in Valid script
for x in mem.controls:
    column = x["column"]
    if column:
        const.__setattr__(column, mem.s.__getattr__(column))
```

* auto_filter form
```python
#  in Build script
auto_filter("sales", mem)
#  in Before Form Show script - initiate control value and turn it on
mem.s.date____1=const.date1  # _*4
mem.s.date____2 = const.date2
mem.w.date____1.set_checked()
```

* open document or folder
```python
open_document("name.pdf")
open_folder("name.pdf")
open_folder("folder name")
```

* autorun - ensure empty primary key
```python
ensure_empty_pk("table_name")
```

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
    # or
    # form.set_grid_index(x)
    # row = form.get_current_record()

	# Do smth with row
	# update(form.model.get_table_name(), row)
form.refresh()
```
* Form/grid - get current row
```python
form.get_current_record()
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
