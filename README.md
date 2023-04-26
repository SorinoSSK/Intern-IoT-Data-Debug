# How To Use

## Requirements
1. Ensure you have [Python](https://www.python.org/downloads/) downloaded
2. Open CLI 
3. At the root, do:
    ```
    pip install -r requirements.txt
    ```
    Or
    ```
    pip3 install -r requirements.txt
    ```
    depending on your version of Python.

Notes:  
If you are receiving errors while installing using **pip install**, please run your command prompt using administration.

## Pre-RunScript Settings
1. Open up
    ```
    query_config.xlsx
    ```
2. Modify the ```Unit name```, ```Number of days```, and ```System``` in the excel sheet.  
&nbsp;&nbsp; - The program will only query for 1 unit, entering multiple units will not work.  
&nbsp;&nbsp; - Do not modify ```Unit ID```
3. Go to ```columns_to_query``` within the same ```query_config.xlsx``` excel file.
5. Add or remove column in ```Columns To Read```

## Run Script
1. Open CLI of choice / launch `unit_status.py` with Python's IDLE.
2. Run script via IDLE or on the CLI with 
    ```
    python unit_data.py
    ```
    Or
    ```
    python3 unit_data.py
    ```
3. Select mads or vft, by default (mads) is selected.
4. Login into your account.
