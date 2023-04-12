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
    mads_config.xlsx
    ```
    or
    ```
    vft_config.xlsx
    ```
2. Modify the ```Unit ID``` and ```Unit name``` in the excel sheet with reference to ```vft_unit_list.xlsx```. You may enter details of multiple units.
3. Go to ```data_sheet``` within the same config excel file.
4. Modify ```LOGS_DISPLAY_PAGE_SIZE``` and ```WITHIN_DAYS``` to collect your data. 
&nbsp&nbsp - ```LOGS_DISPLAY_PAGE_SIZE``` represents the maximum number of data to be collected.
&nbsp&nbsp - ```WITHIN_DAYS``` represents the the number of days up to today. (Data tagged by dates)

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

For more details, see the documentation under `documentation/`.
