from mmap import PAGESIZE
import os
import json
import time
import requests
import pandas as pd
from dateutil import parser
from datetime import datetime
import sys
import warnings

### Global Variables
MADS_FILE_NAME              = "query_config.xlsx"
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
            if row[4] != "" and row[5] != "":
                tempVal = unitsE(row[1],int(row[2]),row[3],False,row[4],row[5])
            else:
                tempVal = unitsE(row[1],int(row[2]),row[3])
            units[int(row[0])] = tempVal
            break

    df = pd.read_excel(io=MADS_FILE_NAME, sheet_name=COLUMNS_TO_QUERY)
    df = df.fillna("")
    for _, row in df.iterrows():
        col.append(row[0])
    return units

def configure_account_fields():
    global ACCOUNT_LOGIN
    ACCOUNT_LOGIN = {} # dict where keys are email and password

    ACCOUNT_LOGIN["email"] = input("Enter your email:")
    ACCOUNT_LOGIN["password"] = input("Enter your password:")   

def run_mad_status(key, unitsVal, curr_time, start_time, token, ls = [], pageNumber = 1):
    os.makedirs("output", exist_ok=True)
    
    # key: name, value: (online/offline, loc, remarks)
    status = {}
    try:
        # get details
        unit_name = unitsVal.name
        endpoint = (
            "https://datakrewtech.com/api/iot_mgmt/orgs/3/projects/70/gateways/"
            + str(key)
            + "/data_dump_index"
        )
        headers = {"Authorization": f"Bearer {token}",
                   "Connection": "keep-alive"}
        params = {
            "page_size": LOGS_DISPLAY_PAGE_SIZE,
            "page_number": pageNumber,
            "to_date": curr_time,
            "from_date": start_time,
        }
        sys.stdout.write('%s %s - %s%s%s\r' % ("Waiting for", unit_name, "Page ", pageNumber, "          "))
        sys.stdout.flush()
        response = requests.get(endpoint, headers=headers, params=params)
        if response.status_code != 200:
            print("Error in fetching " + unit_name + " data for MADs, HTTP status code: ", response.status_code)
            status[unit_name] = ("error", FAILED_RETRIEVAL)
            if response.status_code == 500:
                response = retry_ping(response, unit_name, endpoint, headers, params, 0)
        else:
            try:
                json_dump = response.json()
                DataCount=0
                TotalDataCount = len(json_dump["data_dumps"])
                for value in json_dump["data_dumps"]:
                    date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value["data"]["timestamp"]))
                    tempVal = round(DataCount*100/TotalDataCount,1)
                    sys.stdout.write('%s%s: %s%s%s\r' % ("Retrieving data for ", unit_name, tempVal, '%', "          "))
                    sys.stdout.flush()
                    ls_temp = []
                    for index, value_temp in enumerate(col):
                        if index == 0:
                            ls_temp.append(date_time)
                        else:
                            ls_temp.append(value["data"]["assets_params"][value_temp])
                    ls.append(ls_temp)
                    DataCount += 1
                if TotalDataCount == LOGS_DISPLAY_PAGE_SIZE:
                    run_mad_status(key, unitsVal, curr_time, start_time, token, ls, pageNumber+1)
                else:
                    sys.stdout.write('%s%s%s\r' % ("Writing data into Excel sheet for ", unit_name, "                    "))
                    sys.stdout.flush()
                    df = pd.DataFrame(ls, columns=col)
                    fileName = "output\output_"+ unit_name + ".xlsx"
                    df[::-1].to_excel(fileName,sheet_name="Generated Data")
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
                    print("Error Messsage: ", e)
                    print("Resend")
                    run_mad_status(key, unitsVal, curr_time, start_time, token, ls, pageNumber)
            else:
                print(e)
        except:
            print(e)

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
        # get details
        unit_name = unitsVal.name
        endpoint = (
            "https://backend.vflowtechiot.com/api/iot_mgmt/orgs/3/projects/70/gateways/"
            + str(key)
            + "/data_dump_index"
        )
        headers = {"Authorization": f"Bearer {token}",
                   "Connection": "keep-alive"}
        params = {
            "page_size": LOGS_DISPLAY_PAGE_SIZE,
            "page_number": pageNumber,
            "to_date": curr_time,
            "from_date": start_time,
        }
        sys.stdout.write('%s%s - %s%s%s\r' % ("Waiting for ", unit_name, "Page ", pageNumber, "          "))
        sys.stdout.flush()
        response = requests.get(endpoint, headers=headers, params=params)
        if response.status_code != 200:
            print("Error in fetching " + unit_name + " data for VFT, HTTP status code: ", response.status_code)
            status[unit_name] = ("error", FAILED_RETRIEVAL)
            if response.status_code == 500:
                response = retry_ping(response, unit_name, endpoint, headers, params, 0)
        else:
            try:
                json_dump = response.json()
                DataCount=0
                TotalDataCount = len(json_dump["data_dumps"])
                for value in json_dump["data_dumps"]:
                    date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value["data"]["timestamp"]))
                    tempVal = round(DataCount*100/TotalDataCount,1)
                    sys.stdout.write('%s%s: %s%s%s\r' % ("Retrieving data for ", unit_name, tempVal, '%', "          "))
                    sys.stdout.flush()
                    ls_temp = []
                    for index, value_temp in enumerate(col):
                        if index == 0:
                            ls_temp.append(date_time)
                        else:
                            ls_temp.append(value["data"]["assets_params"][value_temp])
                    ls.append(ls_temp)
                    DataCount += 1
                if TotalDataCount == LOGS_DISPLAY_PAGE_SIZE:
                    run_vft_status(key, unitsVal, curr_time, start_time, token, ls, pageNumber+1)
                else:
                    sys.stdout.write('%s%s%s\r' % ("Writing data into Excel sheet for ", unit_name, "                    "))
                    sys.stdout.flush()
                    df = pd.DataFrame(ls, columns=col)
                    fileName = "output\output_"+ unit_name + ".xlsx"
                    df[::-1].to_excel(fileName,sheet_name="Generated Data")
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
                    print("Error Messsage: ", e)
                    print("Resend")
                    run_vft_status(key, unitsVal, curr_time, start_time, token, ls, pageNumber)
            else:
                print(e.args[0])
        except:
            print(e)

### Utils
def get_date_time(date):
    # print(parser.parse(date))
    return parser.parse(date)

def get_time_stamp(date):
    value = int(datetime.timestamp(date))* 1000
    # print(value)
    return value

def get_current_time():
    return int(time.time() * 1000)

def get_partial_from(curr_time, WITHIN_DAYS):
    return curr_time - 60 * 60 * 24 * WITHIN_DAYS * 1000

def get_online_from(curr_time, WITHIN_HOURS):
    return curr_time - 60 * 60 * WITHIN_HOURS * 1000

class unitsE:
    def __init__(self, name, days, plt, dayDate=True, FDate='1800-01-01 00:00:00', TDate='1800-01-01 00:00:00'):
        # True = day, False = date
        self.name = name
        self.days = days
        self.plt = plt
        self.FromDate = get_time_stamp(FDate)
        self.ToDate = get_time_stamp(TDate)
        self.dayDate = dayDate

### Main Code
def generate_report(mads = False):
    tracked_units = configure()
    for key, values in tracked_units.items():
        mads = getPlt(values.plt)
        if mads:
            try:
                # get auth token
                url = "https://datakrewtech.com/api/sign-in"
                rq = requests.post(url, data=ACCOUNT_LOGIN)
                token = rq.json()["access_token"]
                if values.dayDate:
                    curr_time = get_current_time()
                    within_days = values.days
                    start_time = get_partial_from(curr_time, within_days) # consider logs from WITHIN_DAYS ago
                else:
                    curr_time = values.ToDate
                    start_time = values.FromDate
                run_mad_status(key, values, curr_time, start_time, token)
            except Exception as e:
                print(e)
                print("Check your internet connection.")
        else:
            try:
                # get auth token
                login_url = "https://backend.vflowtechiot.com/api/sign-in"
                login_rq = requests.post(login_url, data=ACCOUNT_LOGIN)
                login_token = login_rq.json()["access_token"]

                url = "https://backend.vflowtechiot.com/api/orgs/3/sign-in"
                org_headers = {"Auth-Token": f"{login_token}"}
                rq = requests.post(url, headers=org_headers)
                token = rq.json()["access_token"]

                if values.dayDate:
                    curr_time = get_current_time()
                    within_days = values.days
                    start_time = get_partial_from(curr_time, within_days) # consider logs from WITHIN_DAYS ago
                else:
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

def getPlt(val):
    if val in "MADS":
        return True
    elif val == "":
        return True
    elif val in "VFT":
        return False
    else:
        print("Invalid Input!")
        quit()

if __name__ == "__main__":
    input("\033[91m(Reminder) Have you configured query_config.xlsx to proceed with this prompt?\033[0m")
    warnings.simplefilter(action='ignore', category=UserWarning)
    generate_report()
    # sendEmail()
   

    

        
