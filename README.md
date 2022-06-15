# The RAD (rapid application development) system.  
***(code less make more)***

Based on:
    q2db        (https://pypi.org/project/q2db)  
    q2gui       (https://pypi.org/project/q2gui)  
    q2report    (https://pypi.org/project/q2report)  
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