from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import random
import datetime
import config
import requests
import json
from elo import rate_1vs1
import sys
import time

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = config.SPREADSHEET_ID
MENU_RANGE = config.MENU_RANGE
HISTORY_RANGE = config.HISTORY_RANGE
SLACK_CHANNEL = config.SLACK_CHANNEL
URL = config.SLACK_WEBHOOK
TOKEN_FILE_PATH = config.TOKEN_FILE_PATH


def send_to_slack(text):
    payload_json = {
        "link_names": 1,
        "text": text,
        "username": "MakanBot",
        "icon_emoji": ":bento:",
        "channel": SLACK_CHANNEL
    }
    headers = {
        'Content-Type': "application/json",
        'cache-control': "no-cache",
        }
    response = requests.request(
        "POST", URL, data=json.dumps(payload_json), headers=headers)


def get_service():
    """Shows basic usage of the Sheets API.
    Prints values from a sample spreadsheet.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(TOKEN_FILE_PATH):
        with open(TOKEN_FILE_PATH, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE_PATH, SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open(TOKEN_FILE_PATH, 'wb') as token:
            pickle.dump(creds, token)

    service = build('sheets', 'v4', credentials=creds)
    return service


def get_menu():
    result = SPREADSHEET.values().get(
        spreadsheetId=SPREADSHEET_ID, range=MENU_RANGE).execute()
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
    result = SPREADSHEET.values().get(spreadsheetId=SPREADSHEET_ID,
                                      range=HISTORY_RANGE).execute()
    values = result.get('values', [])
    today_id = int(datetime.datetime.now().strftime("%w"))
    while days > 0:
        yesterday = today_id-days if today_id-days > 0 else today_id-days + 5
        days_history.append(yesterday)
        days = days - 1
    for row in values:
        history.extend([row[1], row[2]]) if (
            int(row[0]) in days_history and len(row) > 2) else ()
    return history


def random_menu(menu, size):
    history = get_history_days(3)
    res = []
    while (len(res) < size):
        x = random.randint(1, len(menu))
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
    SPREADSHEET.values().update(spreadsheetId=SPREADSHEET_ID, range=range_history
                                + str(today_id+1), valueInputOption='RAW', body=body).execute()


def get_new_score():
    score_res = SPREADSHEET.values().get(
        spreadsheetId=SPREADSHEET_ID, range=MENU_RANGE).execute()
    score_values = score_res.get('values', [])

    voting_res = SPREADSHEET.values().get(spreadsheetId=SPREADSHEET_ID,
                                          range=HISTORY_RANGE).execute()
    voting_values = voting_res.get('values', [])

    score = {}
    voting = {}
    if not score_values:
        print('No Menu data found.')
    else:
        for row in score_values:
            score[(row[1])] = float(row[2])

    if not voting_values:
        print('No History data found')
    else:
        for row in voting_values:
            winner = 1 if(row[3] > row[4]) else 2
            loser = 2 if winner == 1 else 1
            is_draw = 1 if row[3] == row[4] else 0
            win_score, lose_score = rate_1vs1(
                score[row[winner]], score[row[loser]], is_draw)
            score[row[winner]] = win_score
            score[row[loser]] = lose_score

    return score


def write_score(score):
    range_update = 'Lunch!B2:C'

    body = {
        "range": range_update,
        "majorDimension": 'ROWS',
        "values": score
    }
    SPREADSHEET.values().update(spreadsheetId=SPREADSHEET_ID, range=range_update,
                                valueInputOption='RAW', body=body).execute()


def main():
    if (len(sys.argv) == 1):
        menu = get_menu()
        lunch_options = random_menu(menu, 2)
        send_to_slack("@here Mau makan apa siang ini? :sheepy:")
        for m in lunch_options:
            send_to_slack('`' + m + '`')
        write_history(lunch_options)
        print("Timestamp: " + str(datetime.datetime.now()))
    else:
        if (sys.argv[1] == 'update_score'):
            new_score = get_new_score()
            score_list = [[k, v] for k, v in new_score.items()]
            write_score(score_list)
            print("Timestamp: " + str(datetime.datetime.now()))


SPREADSHEET = get_service().spreadsheets()
main()
