from mmap import PAGESIZE
import os
import json
import time
import requests
import numpy as np
import pandas as pd
from dateutil import parser
from datetime import datetime
import sys
import warnings

### Global Variables
MADS_FILE_NAME              = "query_config_urgent_query.xlsx"
UNITS_TO_QUERY              = "units_to_query"
COLUMNS_TO_QUERY            = "columns_to_query"
DATA_SHEET                  = "data_sheet"
ACCOUNT_SHEET               = "account_sheet"
OUTPUT_FILE                 = "unit_status.docx"
# Account details and fields to be initialized
DATAPLICITY_LOGIN = {}
ACCOUNT_LOGIN               = "to intialize"
LOGS_DISPLAY_PAGE_SIZE      = 20000
# Email details and authentication
SMTP_SERVER                 = None
SENDER_EMAIL                = None
RECIPIENTS                  = None
EMAIL_API_KEY               = None
PORT                        = None
col                         = []
# Error message
FAILED_RETRIEVAL = "Likely a server issue. Refresh the unit's logs data page on platform."

### User-input data
def configure():
    configure_account_fields()
    
    df = pd.read_excel(io=MADS_FILE_NAME, sheet_name=UNITS_TO_QUERY)
    df = df.fillna("")
    
    units = {}
    for _, row in df.iterrows():
        if row[0] != "":
            units[int(row[1])] = unitsE(int(row[0]),int(row[2]),int(row[3]),row[4],row[5],row[6])
            break

    return units

def configure_account_fields():
    global ACCOUNT_LOGIN
    ACCOUNT_LOGIN = {} # dict where keys are email and password

    ACCOUNT_LOGIN["email"] = input("Enter your email:")
    ACCOUNT_LOGIN["password"] = input("Enter your password:")    

def retry_ping(response, unit_name, endpoint, headers, params, count):
    if count < 5:
        print("Error probably due to delay in data loading, sleep for 5 seconds.")
        time.sleep(5)
        response = requests.get(endpoint, headers=headers, params=params)
        if response.status_code == 500:
            retry_ping(response, unit_name, endpoint, headers, params, count+1)
        else:
            if response.status_code != 200:
                print("Error in fetching " + unit_name + " data, HTTP status code: ", response.status_code)
            return response
    else:
        print("Error in fetching " + unit_name + " data, HTTP status code: ", response.status_code)
        return response

def run_vft_status(key, unitsVal, curr_time, start_time, token, ls = [], pageNumber = 1):
    os.makedirs("output", exist_ok=True)

    # key: name, value: online/offline
    status = {}
    try:       
        unit_name = unitsVal.name
        endpoint = (
            "https://backend.vflowtechiot.com/api/dash_mgmt/orgs/3/dashboards/"
            +str(key)
            +"/panels/"
            +str(unitsVal.panelID)
        )
        headers = {"Authorization": f"Bearer {token}",
                   "Connection": "keep-alive"}
        data = {
            "filter_metadata":{
                "aggregate_func":"no",
                "from_date":start_time,
                "to_date":curr_time,
                "group_interval":30,
                "group_interval_type":"minute",
                "type":"historical",
                "last":"custom"
            }
        }
        sys.stdout.write('%s%s%s\r' % ("Waiting for ", unit_name, "          "))
        sys.stdout.flush()
        response = requests.put(endpoint, headers=headers, json=data)
        # get details
        endpoint = (
            "https://backend.vflowtechiot.com/api/dash_mgmt/orgs/3/panels/"
            +str(unitsVal.panelID)
            +"/widgets/"
            +str(unitsVal.widgetID)
            +"/widget_instances/"
            +str(unitsVal.widgetInstance)
        )
        headers = {"Authorization": f"Bearer {token}",
                   "Connection": "keep-alive"}
        params = {}
        response = requests.get(endpoint, headers=headers, json=params)
        if response.status_code != 200:
            print("Error in fetching " + unit_name + " data for VFT, HTTP status code: ", response.status_code)
            status[unit_name] = ("error", FAILED_RETRIEVAL)
            if response.status_code == 500:
                response = retry_ping(response, unit_name, endpoint, headers, params, 0)
        else:
            try:
                sys.stdout.write('%s%s%s\r' % ("Retrieving data for ", unit_name, "          "))
                sys.stdout.flush()
                json_dump = response.json()
                index = 0
                time_stamp = []
                col.append("date")
                for value in json_dump["series"]:
                    ls_temp = []
                    col.append(value["name"])
                    for i in value["data"]:
                        if index == 0:
                            date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(i[0]/1000))
                            time_stamp.append(date_time)
                        ls_temp.append(float(i[1]))
                    if time_stamp != [] and index == 0:
                        ls.append(time_stamp)
                        index = index + 1
                    ls.append(ls_temp)
                set_zeros(ls)
                df = pd.DataFrame(np.array(ls).T.tolist(), columns=col, dtype=float)
                fileName = "output\output_"+ unit_name + ".xlsx"
                df[::-1].to_excel(fileName,sheet_name="Generated Data",float_format="%0.5f")
                print("Data retrieved for", unit_name, ", and saved on", fileName)         
            except json.JSONDecodeError:
                print(
                    "JSONDecodeError for "
                    + unit_name
                    + ", check if unit_id is entered correctly in config.json"
                )
    except Exception as e:
        try:
            if e.args[0] in "access_token":
                print("Invalid Account!")
            elif (len(e.args) > 1):
                if e.args[0].upper() in "CONNECTION ABORTED":
                    print("Error Messsage: ", e, "                        ")
                    print("Resend", "                        ")
                    run_vft_status(key, unitsVal, curr_time, start_time, token, ls, pageNumber)
            else:
                print(e.args[0], "                        ")
        except:
            print(e, "                        ")

### Utils
def get_date_time(date):
    # print(parser.parse(date))
    return parser.parse(date)

def get_time_stamp(date):
    value = int(datetime.timestamp(date))* 1000
    # print(value)
    return value

def set_zeros(ls):
    max = -1
    for val in ls:
        if len(val) > max:
            max = len(val)
    for (index, val) in enumerate(ls):
        if len(val) < max:
            toAdd = max - len(val)
            ls[index] = ls[index] + [0]*toAdd
            
def get_current_time():
    return int(time.time() * 1000)

def get_partial_from(curr_time, WITHIN_DAYS):
    return curr_time - 60 * 60 * 24 * WITHIN_DAYS * 1000

def get_online_from(curr_time, WITHIN_HOURS):
    return curr_time - 60 * 60 * WITHIN_HOURS * 1000

class unitsE:
    def __init__(self, panelID, widgetID, widgetInstance, name, FDate, TDate):
        # True = day, False = date
        self.name = name
        self.panelID = panelID
        self.widgetID = widgetID
        self.widgetInstance = widgetInstance
        self.FromDate = get_time_stamp(FDate)
        self.ToDate = get_time_stamp(TDate) + 24*60*60*1000
        # print(self.ToDate, self.FromDate)
        if self.ToDate < self.FromDate:
            print("\033[91mError: Your \"To Date\" is larger than \"From Date\". Please reconfigure your dates in query_config.xlsx.\033[0m")
            sys.exit()

### Main Code
def generate_report():
    tracked_units = configure()
    for key, values in tracked_units.items():
        try:
            # get auth token
            login_url = "https://backend.vflowtechiot.com/api/sign-in"
            login_rq = requests.post(login_url, data=ACCOUNT_LOGIN)
            login_token = login_rq.json()["access_token"]
            url = "https://backend.vflowtechiot.com/api/orgs/3/sign-in"
            org_headers = {"Auth-Token": f"{login_token}"}
            rq = requests.post(url, headers=org_headers)
            token = rq.json()["access_token"]
            curr_time = values.ToDate
            start_time = values.FromDate
            run_vft_status(key, values, curr_time, start_time, token)
        except Exception as e:
            try:
                if e.args[0] in "access_token":
                    print("Invalid Account!")
                else:
                    print(e.args[0])
            except:
                print(e)
                print("Check your internet connection.")

if __name__ == "__main__":
    input("\033[91m(Reminder) Have you configured query_config_urgent_query.xlsx to proceed with this prompt?\033[0m")
    warnings.simplefilter(action='ignore', category=UserWarning)
    warnings.simplefilter(action='ignore', category=FutureWarning)
    generate_report()
    # sendEmail()