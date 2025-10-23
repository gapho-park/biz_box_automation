import os
import time
import pandas as pd
from datetime import datetime, timedelta
import pytz
from playwright.sync_api import sync_playwright
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class BizBoxPlaywright:
    def __init__(self):
        self.bizbox_id = os.getenv("BIZBOX_ENCODED_ID")
        self.bizbox_pw = os.getenv("BIZBOX_ENCODED_PW")
        self.sheet_id = "147uYiSvi7Wl6LQbjqE2ae1nk7WjI2kUt_W-0gDxswas"
        self.sheet_name = "TEST"
        self.host = "http://58.224.161.247"
        
        if not self.bizbox_id or not self.bizbox_pw:
            raise ValueError("BIZBOX_ENCODED_ID, BIZBOX_ENCODED_PW is required")
        
        self.init_sheets_api()

    def init_sheets_api(self):
        """Google Sheets API 인증 초기화"""
        credentials = Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.sheets_service = build('sheets', 'v4', credentials=credentials)

    def login(self, page):
        """BizBox 로그인"""
        print("Logging in to BizBox...")
        page.goto(f"{self.host}/gw/bizbox.do", wait_until="networkidle")
        
        # 로그인 폼 입력
        page.fill('input[name="id"]', self.bizbox_id)
        page.fill('input[name="password"]', self.bizbox_pw)
        
        # 로그인 버튼 클릭
        page.click('button[type="submit"], input[type="submit"]')
        
        # 로그인 완료 대기
        time.sleep(3)
        print("Login successful")

    def get_disbursement_data(self, page):
        """지출결의 데이터 수집"""
        print("Navigating to disbursement page...")
        
        # 지출결의 페이지로 이동
        page.goto(
            f"{self.host}/exp/ex/admin/report/ExApprovalSlipList.do?menu_no=810101500",
            wait_until="networkidle"
        )
        
        time.sleep(3)
        
        # 날짜 설정 (필요시)
        korea_tz = pytz.timezone('Asia/Seoul')
        end_date = (datetime.now(korea_tz) + timedelta(days=14)).strftime("%Y-%m-%d")
        
        print(f"Collecting data up to {end_date}")
        
        # 테이블 데이터 추출
        try:
            # 모든 행 선택
            rows = page.query_selector_all("table tbody tr")
            print(f"Found {len(rows)} rows")
            
            data = []
            headers = []
            
            # 헤더 추출
            header_cells = page.query_selector_all("table thead th")
            for cell in header_cells:
                headers.append(cell.text_content().strip())
            
            if headers:
                data.append(headers)
            
            # 데이터 행 추출
            for row in rows:
                cells = row.query_selector_all("td")
                row_data = [cell.text_content().strip() for cell in cells]
                if row_data:
                    data.append(row_data)
            
            print(f"Extracted {len(data)} rows including header")
            return data
            
        except Exception as e:
            print(f"Error extracting data: {e}")
            return []

    def save_to_sheets(self, data):
        """Google Sheets에 데이터 저장"""
        if not data:
            print("No data to save")
            return
        
        print(f"Saving {len(data)} rows to Google Sheets...")
        
        body = {
            'values': data
        }
        
        # 기존 데이터 모두 삭제
        self.sheets_service.spreadsheets().values().clear(
            spreadsheetId=self.sheet_id,
            range=f"{self.sheet_name}!A:Z"
        ).execute()
        
        # 새 데이터 작성
        self.sheets_service.spreadsheets().values().update(
            spreadsheetId=self.sheet_id,
            range=f"{self.sheet_name}!A1",
            valueInputOption="RAW",
            body=body
        ).execute()
        
        print(f"Successfully saved {len(data)} rows to Google Sheets")

    def run(self):
        """메인 실행"""
        with sync_playwright() as p:
            # Headless 모드로 브라우저 실행
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            try:
                # 로그인
                self.login(page)
                
                # 데이터 수집
                data = self.get_disbursement_data(page)
                
                # Google Sheets 저장
                if data:
                    self.save_to_sheets(data)
                    print("Process completed successfully!")
                else:
                    print("No data collected")
                    
            except Exception as e:
                print(f"Error occurred: {e}")
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    BizBoxPlaywright().run()
