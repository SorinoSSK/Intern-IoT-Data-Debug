import os
import json
import time
import requests
import pandas as pd

### Global Variables
MADS_FILE_NAME              = "mads_config.xlsx"
VFT_FILE_NAME               = "vft_config.xlsx"
UNITS_TO_QUERY              = "units_to_query"
DATA_SHEET                  = "data_sheet"
ACCOUNT_SHEET               = "account_sheet"
OUTPUT_FILE                 = "unit_status.docx"
# Account details and fields to be initialized
DATAPLICITY_LOGIN = {}
ACCOUNT_LOGIN               = "to intialize"
LOGS_DISPLAY_PAGE_SIZE      = "to intialize"
LOGS_DISPLAY_PAGE_NUMBER    = "to intialize"
WITHIN_HOURS                = "to intialize"
WITHIN_DAYS                 = "to intialize"
# Email details and authentication
SMTP_SERVER                 = None
SENDER_EMAIL                = None
RECIPIENTS                  = None
EMAIL_API_KEY               = None
PORT                        = None
col                         = ["date", "bvolt", "bpow", "bcurr", "bsoc"]
# Error message
FAILED_RETRIEVAL = "Likely a server issue. Refresh the unit's logs data page on platform."

### User-input data
def configure_mads():
    configure_account_fields()
    configure_data_fields(MADS_FILE_NAME)
    
    df = pd.read_excel(io=MADS_FILE_NAME, sheet_name=UNITS_TO_QUERY)
    df = df.fillna("")
    
    units = {}
    for _, row in df.iterrows():
        units[row[0]] = row[1]
    return units

def configure_vft():
    configure_account_fields()
    configure_data_fields(VFT_FILE_NAME)
    
    df = pd.read_excel(io=VFT_FILE_NAME, sheet_name=UNITS_TO_QUERY)
    df = df.fillna("")
    
    units = {}
    for _, row in df.iterrows():
        units[row[0]] = (row[1], row[2], row[3])
    return units

def configure_account_fields():
    global ACCOUNT_LOGIN
    ACCOUNT_LOGIN = {} # dict where keys are email and password

    ACCOUNT_LOGIN["email"] = input("Enter your email:")
    ACCOUNT_LOGIN["password"] = input("Enter your password:")

def configure_data_fields(PLATFORM_FILE_NAME):
    global LOGS_DISPLAY_PAGE_SIZE, LOGS_DISPLAY_PAGE_NUMBER, WITHIN_HOURS, WITHIN_DAYS
    
    df = pd.read_excel(io=PLATFORM_FILE_NAME, sheet_name=DATA_SHEET)
    WITHIN_HOURS = int(df.iloc[0][1])
    WITHIN_DAYS = int(df.iloc[1][1])
    LOGS_DISPLAY_PAGE_SIZE = int(df.iloc[2][1])
    LOGS_DISPLAY_PAGE_NUMBER = int(df.iloc[3][1])    

def run_mad_status(units):
    os.makedirs("output", exist_ok=True)
    
    # key: name, value: (online/offline, loc, remarks)
    status = {}
    count = 1

    # get auth token
    url = "https://datakrewtech.com/api/sign-in"
    rq = requests.post(url, data=ACCOUNT_LOGIN)
    try:    
        token = rq.json()["access_token"]

        curr_time = get_current_time()
        start_time = get_partial_from(curr_time, WITHIN_DAYS) # consider logs from WITHIN_DAYS ago
        ls = []
        for key, values in units.items():
            # get details
            unit_name = values
            endpoint = (
                "https://datakrewtech.com/api/iot_mgmt/orgs/3/projects/70/gateways/"
                + str(key)
                + "/data_dump_index"
            )
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "page_size": LOGS_DISPLAY_PAGE_SIZE,
                "page_number": LOGS_DISPLAY_PAGE_NUMBER,
                "to_date": curr_time,
                "from_date": start_time,
            }
            
            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code != 200:
                print("Error in fetching " + unit_name + " data for MADs, HTTP status code: ", response.status_code)
                status[unit_name] = ("error", FAILED_RETRIEVAL)
                if response.status_code == 500:
                    response = retry_ping(response, unit_name, endpoint, headers, params, 0)
                continue # do not process further

            try:
                json_dump = response.json()
                for value in json_dump["data_dumps"]:
                    date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value["data"]["timestamp"]))
                    ls.append([date_time, value["data"]["assets_params"][col[1]], value["data"]["assets_params"][col[2]], value["data"]["assets_params"][col[3]], value["data"]["assets_params"][col[4]]])
                df = pd.DataFrame(ls, columns=col)
                fileName = "output\output_"+ unit_name + ".xlsx"
                df.to_excel(fileName,sheet_name="Generated Data")
                print("Data retrieved for", unit_name, ", and saved on", fileName)
                    
            except json.JSONDecodeError:
                print(
                    "JSONDecodeError for "
                    + unit_name
                    + ", check if unit_id is entered correctly in config.json"
                )
            count += 1
    except:
        print("Invalid Account!")

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

def run_vft_status(units):
    os.makedirs("output", exist_ok=True)

    # key: name, value: online/offline
    status = {}
    count = 1

    try:
        # get auth token
        login_url = "https://backend.vflowtechiot.com/api/sign-in"
        login_rq = requests.post(login_url, data=ACCOUNT_LOGIN)
        login_token = login_rq.json()["access_token"]

        url = "https://backend.vflowtechiot.com/api/orgs/3/sign-in"
        org_headers = {"Auth-Token": f"{login_token}"}
        rq = requests.post(url, headers=org_headers)
        token = rq.json()["access_token"]
        

        curr_time = get_current_time()
        start_time = get_partial_from(curr_time, WITHIN_DAYS) # consider logs from WITHIN_DAYS days ago
        ls = []
        for key, values in units.items():
            # get details
            unit_name = values
            endpoint = (
                "https://backend.vflowtechiot.com/api/iot_mgmt/orgs/3/projects/70/gateways/"
                + str(key)
                + "/data_dump_index"
            )
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "page_size": LOGS_DISPLAY_PAGE_SIZE,
                "page_number": LOGS_DISPLAY_PAGE_NUMBER,
                "to_date": curr_time,
                "from_date": start_time,
            }

            response = requests.get(endpoint, headers=headers, params=params)

            if response.status_code != 200:
                print("Error in fetching " + unit_name + " data for VFT, HTTP status code: ", response.status_code)
                status[unit_name] = ("error", FAILED_RETRIEVAL)
                continue # do not process further

            try:
                json_dump = response.json()
                for value in json_dump["data_dumps"]:
                    date_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value["data"]["timestamp"]))
                    ls.append([date_time, value["data"]["assets_params"][col[1]], value["data"]["assets_params"][col[2]], value["data"]["assets_params"][col[3]], value["data"]["assets_params"][col[4]]])
                df = pd.DataFrame(ls, columns=col)
                fileName = "output\output_"+ unit_name + ".xlsx"
                df.to_excel(fileName,sheet_name="Generated Data")
                print("Data retrieved for", unit_name, ", and saved on", fileName)
                    
            except json.JSONDecodeError:
                print(
                    "JSONDecodeError for "
                    + unit_name
                    + ", check if unit_id is entered correctly in config.json"
                )

            count += 1
    except:
        print("Invalid Account!")    

### Utils
def get_current_time():
    return int(time.time() * 1000)

def get_partial_from(curr_time, WITHIN_DAYS):
    return curr_time - 60 * 60 * 24 * WITHIN_DAYS * 1000

def get_online_from(curr_time, WITHIN_HOURS):
    return curr_time - 60 * 60 * WITHIN_HOURS * 1000

### Main Code
def generate_report(mads = False):
    if mads:
        tracked_units = configure_mads()
        run_mad_status(tracked_units)
    else:
        tracked_units = configure_vft()
        run_vft_status(tracked_units)            

def getPlt():
    val = input("Select platform, (mads)/vft:").upper()
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
    generate_report(getPlt())
    # sendEmail()
   

    

        
