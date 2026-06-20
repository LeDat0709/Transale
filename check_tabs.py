import json
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
d=json.load(open('token.json'))
c=Credentials(token=d['token'],refresh_token=d['refresh_token'],token_uri=d['token_uri'],client_id=d['client_id'],client_secret=d['client_secret'])
s=build('sheets','v4',credentials=c)
r=s.spreadsheets().get(spreadsheetId='1szAxSMvyYhoTRrRUudhKsYYemDxZWJpl2RUeRttCRbc').execute()
print([sheet['properties']['title'] for sheet in r.get('sheets',[])])
