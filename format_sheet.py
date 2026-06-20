import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_FILE = 'token.json'
SPREADSHEET_ID = '1szAxSMvyYhoTRrRUudhKsYYemDxZWJpl2RUeRttCRbc'
# Lấy GID từ link của bạn
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
    print("🚀 Đang gửi lệnh căn chỉnh tự động lên Google Sheets...")
    sheets_api = load_google_sheets()
    
    # Định dạng toàn bộ các dòng từ 997 đến 1200, từ cột C đến cột I
    requests = [
        {
            "repeatCell": {
                "range": {
                    "sheetId": SHEET_GID,
                    "startRowIndex": 996,  # 0-based index của dòng 997
                    "endRowIndex": 1200,
                    "startColumnIndex": 2, # 0-based của cột C
                    "endColumnIndex": 9    # Qua cột I
                },
                "cell": {
                    "userEnteredFormat": {
                        "wrapStrategy": "WRAP", # Tự động xuống dòng
                        "verticalAlignment": "TOP" # Căn lên trên cùng
                    }
                },
                "fields": "userEnteredFormat(wrapStrategy,verticalAlignment)"
            }
        }
    ]
    
    body = {
        'requests': requests
    }
    
    try:
        sheets_api.batchUpdate(spreadsheetId=SPREADSHEET_ID, body=body).execute()
        print("✅ Đã làm đẹp xong! Các ô chữ sẽ tự động xuống dòng và không bị tràn nữa.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

if __name__ == "__main__":
    main()
