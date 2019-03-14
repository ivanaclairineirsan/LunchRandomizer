from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import random
import datetime
import requests
import json

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1Zcqt-ORxbN8J6-h5DY0zRcOOJ-MA9fNMc54wej8heDE'
MENU_RANGE = 'Lunch!A2:B'
HISTORY_RANGE = 'History!A2:C'

def send_to_slack(text):
    url = "https://hooks.slack.com/services/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"

    payload_json = {
        "link_names": 1,
        "text": text,
        "username": "MakanBot",
        "icon_emoji": ":bento:",
        "channel": "#test-ivana"
    }
    headers = {
        'Content-Type': "application/json",
        'cache-control': "no-cache",
        'Postman-Token': "cdbd5deb-5a71-427d-bac5-038774a2a9f7"
        }
    response = requests.request("POST", url, data=json.dumps(payload_json), headers=headers)
#     print(response.text)

def get_service():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    return service

def get_menu():
    result = SPREADSHEET.values().get(spreadsheetId=SPREADSHEET_ID, range=MENU_RANGE).execute()
    values = result.get('values', [])
    menu = {}
    if not values:
        print('No data found.')
    else:
        for row in values:
            menu[int(row[0])] = row[1]
    return menu

def get_history_days(days):
    history = []
    days_history = []
    result = SPREADSHEET.values().get(spreadsheetId=SPREADSHEET_ID, range=HISTORY_RANGE).execute()
    values = result.get('values', [])
    today_id = int(datetime.datetime.now().strftime("%w"))
    while days > 0:
        yesterday = today_id-days if today_id-days > 0 else today_id-days + 5
        days_history.append(yesterday)
        days = days - 1
    for row in values:
        history.extend([row[1], row[2]]) if (int(row[0]) in days_history and len(row) > 2) else ()
    return history

def random_menu(menu, size):
    history = get_history_days(2)
    res = []
    while (len(res) < size):
        x = random.randint(1,len(menu))
        if menu[x] not in res and menu[x] not in history:
            res.append(menu[x])
    return res

def write_history(menu):
    x = datetime.datetime.now()
    today_id = int(datetime.datetime.now().strftime("%w"))
    range_history = 'History!B{}:C{}'
    range_history = range_history.format(str(today_id+1), str(today_id+1))

    body = {
        "range": range_history + str(today_id+1),
        "majorDimension": 'ROWS',
        "values": [menu]
    }
    SPREADSHEET.values().update(spreadsheetId=SPREADSHEET_ID, range=range_history + str(today_id+1), valueInputOption='RAW', body=body).execute()

def main():
    menu = get_menu()
    lunch_options = random_menu(menu, 2)
    send_to_slack("@here Mau makan apa siang ini? :sheepy:")
    for m in lunch_options:
        send_to_slack('`' + m + '`')
    write_history(lunch_options)
    print("Timestamp: " + str(datetime.datetime.now()))

SPREADSHEET = get_service().spreadsheets()
main()
