# The RAD (rapid application development) system.  
**(code less, make more)**  
**Based on:**  
    q2db        (https://pypi.org/project/q2db)  
    q2gui       (https://pypi.org/project/q2gui)  
    q2report    (https://pypi.org/project/q2report)  
## Install & run
**Linux**
```bash
pip install --upgrade pip && python3 -m venv q2rad && source q2rad/bin/activate && pip install --upgrade q2rad  && q2rad
```
**Windows**
```bash
pip install --upgrade pip && py -m venv q2rad && call q2rad/scripts/activate && pip install --upgrade q2rad  && q2rad
```
## Concept:
```python
Forms:        #  may have main menu (menubar) definitions
              #  may be linked to database table
    
    Lines:    #  form fields(type of data and type of form control) and 
              #  layout definitions
              #  when form is linked to database - database columns definitions
    
    Actions:  #  applies for database linked forms
              #  may be standard CRUD-action 
              #  or 
              #  run a script (run reports, forms and etc)
              #  or
              #  may have linked subforms (one-to-many)

Queries:      #  query development and debugging tool

Reports:      #  multiformat (HTML, DOCX, XLSX) reporting tool 
```
