# The RAD (rapid application development) system. 

**(code less, make more)**  
**Based on:**  
    q2db        (https://pypi.org/project/q2db)  
    q2gui       (https://pypi.org/project/q2gui)  
    q2report    (https://pypi.org/project/q2report)  

## [Read the docs](docs/index.md) 
## Install & run
**Linux**
```bash
mkdir q2rad && \
    cd q2rad && \
    python3 -m pip install --upgrade pip && \
    python3 -m venv q2rad && \
    source q2rad/bin/activate && \
    python3 -m pip install --upgrade q2rad && \
    q2rad
```
**Windows**
```bash
mkdir q2rad &&^
cd q2rad &&^
py -m pip install --upgrade pip &&^
py -m venv q2rad &&^
call q2rad/scripts/activate &&^
pip install --upgrade q2rad &&^
q2rad
```
**Mac**
```bash
mkdir q2rad && \
    cd q2rad && \
    python3 -m pip install --upgrade pip && \
    python3 -m venv q2rad && \
    source q2rad/bin/activate && \
    python3 -m pip install --upgrade q2rad && \
    q2rad
```
**Docker**
```bash
curl -s https://raw.githubusercontent.com/AndreiPuchko/q2rad/main/docker-x11/dockerfile > dockerfile && \
    mkdir -p q2rad_storage/Desktop && \
    chmod -R 777 q2rad_storage && \
    sudo docker build -t q2rad . && \
    sudo docker run -it \
        -v /tmp/.X11-unix:/tmp/.X11-unix \
        -v $(pwd)/q2rad_storage:/home/q2rad \
        -e DISPLAY=$DISPLAY \
        -u q2rad q2rad python3 -m q2rad

```
## Concept:
Application as a database
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

Modules:      #  python scripts

Queries:      #  query development and debugging tool

Reports:      #  multiformat (HTML, DOCX, XLSX) reporting tool 
```
