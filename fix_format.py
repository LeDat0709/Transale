import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = 'token.json'
SPREADSHEET_ID = '1szAxSMvyYhoTRrRUudhKsYYemDxZWJpl2RUeRttCRbc'
SHEET_GID = 747075331 

def load_google_sheets():
    with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
        d = json.load(f)
    creds = Credentials(
        token=d.get('token'), refresh_token=d.get('refresh_token'),
        token_uri=d.get('token_uri'), client_id=d.get('client_id'),
        client_secret=d.get('client_secret'), scopes=d.get('scopes')
    )
    return build('sheets', 'v4', credentials=creds).spreadsheets()

def main():
    print("🚀 Đang gửi lệnh ÉP KÍCH THƯỚC và XUỐNG DÒNG lên Google Sheets...")
    sheets_api = load_google_sheets()
    
    requests = [
        # 1. Ép tất cả các ô xuống dòng (WRAP)
        {
            "repeatCell": {
                "range": {
                    "sheetId": SHEET_GID,
                    "startRowIndex": 996,
                    "endRowIndex": 1200,
                    "startColumnIndex": 2, # Cột C
                    "endColumnIndex": 10   # Hết Cột J (exclusive)
                },
                "cell": {
                    "userEnteredFormat": {
                        "wrapStrategy": "WRAP",
                        "verticalAlignment": "TOP"
                    }
                },
                "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)"
            }
        },
        # 2. Xóa các chiều cao bị cố định bằng tay, tự động dãn chiều cao dòng theo nội dung
        {
            "autoResizeDimensions": {
                "dimensions": {
                    "sheetId": SHEET_GID,
                    "dimension": "ROWS",
                    "startIndex": 996,
                    "endIndex": 1200
                }
            }
        }
    ]
    
    body = {
        'requests': requests
    }
    
    try:
        sheets_api.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
        print("✅ Đã fix lỗi tràn chữ! Ô chữ đã tự động dãn ra.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()
