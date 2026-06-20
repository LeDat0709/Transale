import json, sys, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8')
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
d=json.load(open('token.json'))
c=Credentials(**d)
s=build('sheets','v4',credentials=c)

for tab in ['Đạt_Mỹ', 'Đạt _ Đức']:
    r=s.spreadsheets().values().get(spreadsheetId='1szAxSMvyYhoTRrRUudhKsYYemDxZWJpl2RUeRttCRbc', range=f"'{tab}'!A997:I1000").execute()
    print(f"Found {len(r.get('values',[]))} rows in {tab}")
