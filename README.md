# The RAD (rapid application development) system. 

**(code less, make more)**  
**Based on:**  
    q2db        (https://pypi.org/project/q2db)  
    q2gui       (https://pypi.org/project/q2gui)  
    q2report    (https://pypi.org/project/q2report)  

## [Read the docs](docs/index.md) 

## Install & run:
on *Linux* and Python >=3.11 make sure you have pip and virtualenv, if not:

```sudo apt install python3-pip python3-virtualenv```
## Install & run - Launcher (https://github.com/AndreiPuchko/q2radlauncher)
**Linux**: https://github.com/AndreiPuchko/q2radlauncher/blob/main/bin/linux/q2radlauncher

**Windows**: https://github.com/AndreiPuchko/q2radlauncher/blob/main/bin/windows/q2radlauncher.exe

**macOS**: run from terminal or ```git clone https://github.com/AndreiPuchko/q2radlauncher``` and build executable with ```build_executable.zsh```

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;https://github.com/AndreiPuchko/q2radlauncher/blob/main/bin/macos/q2radlauncher
## Install & run - Python script
**Linux, macOS**
```bash
wget https://raw.githubusercontent.com/AndreiPuchko/q2rad/main/install/get-q2rad.py -O - | python3 
```
**Windows**
```bash
wget https://raw.githubusercontent.com/AndreiPuchko/q2rad/main/install/get-q2rad.py  -O - | py get-q2rad.py; del get-q2rad.py
```
## Install & run - terminal
**Linux**
```bash
sudo apt install python3-venv python3-pip -y &&\
    mkdir -p q2rad && \
    cd q2rad && \
    python3 -m pip install --upgrade pip && \
    python3 -m venv q2rad && \
    source q2rad/bin/activate && \
    python3 -m pip install --upgrade q2rad && \
    q2rad
```
**Windows (Powershell)**
```bash
mkdir q2rad ;`
cd q2rad ;`
py -m pip install --upgrade pip ;`
py -m venv q2rad;q2rad/scripts/activate ;`
py -m pip install --upgrade q2rad ;`
q2rad
```
**macOS**
```bash
mkdir -p q2rad && \
    cd q2rad && \
    python3 -m pip install --upgrade pip && \
    python3 -m venv q2rad && \
    source q2rad/bin/activate && \
    python3 -m pip install --upgrade q2rad && \
    q2rad
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
