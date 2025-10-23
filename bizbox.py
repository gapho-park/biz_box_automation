import os
import time
import pandas as pd
from datetime import datetime, timedelta
import pytz
from playwright.sync_api import sync_playwright, expect
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
        
        try:
            # 페이지 로드 (타임아웃 증가)
            page.goto(f"{self.host}/gw/bizbox.do", timeout=60000)
            print("Page loaded, waiting for form elements...")
            
            # 로그인 폼 요소 대기
            page.wait_for_selector('input[name="id"]', timeout=10000)
            print("Login form found")
            
            # 폼 입력
            page.fill('input[name="id"]', self.bizbox_id)
            page.fill('input[name="password"]', self.bizbox_pw)
            print("Credentials filled")
            
            # 로그인 버튼 클릭
            print("Attempting to click login button...")
            try:
                # div.login_submit으로 찾기
                page.click('.login_submit', timeout=5000)
                print("Clicked login button (div.login_submit)")
            except Exception as e:
                print(f"Failed to click div.login_submit: {e}")
                print("Trying alternative selectors...")
                try:
                    page.click('button:has-text("로그인")', timeout=5000)
                    print("Clicked button with text '로그인'")
                except:
                    raise
            
            # 로그인 완료 대기
            print("Waiting for login to complete...")
            page.wait_for_timeout(3000)  # 기본 대기
            
            # 로그인 성공 여부 확인
            try:
                page.wait_for_selector('.container, main, [class*="dashboard"], [class*="content"]', timeout=5000)
                print("Login successful - main page loaded")
            except:
                print("Warning: Could not confirm main page loaded, continuing anyway...")
            
        except Exception as e:
            print(f"Login error: {e}")
            print("Page URL:", page.url)
            print("Page title:", page.title())
            
            # 디버깅 정보
            try:
                print("Page HTML snippet:")
                print(page.content()[:500])
            except:
                pass
            
            raise

    def get_disbursement_data(self, page):
        """지출결의 데이터 수집"""
        print("Navigating to disbursement page...")
        
        try:
            # 지출결의 페이지로 이동
            page.goto(
                f"{self.host}/exp/ex/admin/report/ExApprovalSlipList.do?menu_no=810101500",
                timeout=60000
            )
            
            print("Waiting for table to load...")
            page.wait_for_timeout(2000)
            
            # 테이블 데이터 추출
            try:
                rows = page.query_selector_all("table tbody tr")
                print(f"Found {len(rows)} rows")
                
                if len(rows) == 0:
                    print("No rows found, attempting alternative selectors...")
                    rows = page.query_selector_all("tr")
                    print(f"Alternative selector found {len(rows)} rows")
                
                data = []
                
                # 헤더 추출
                header_cells = page.query_selector_all("table thead th")
                if not header_cells:
                    header_cells = page.query_selector_all("thead th")
                
                headers = [cell.text_content().strip() for cell in header_cells]
                if headers:
                    data.append(headers)
                    print(f"Headers: {headers}")
                
                # 데이터 행 추출
                for idx, row in enumerate(rows):
                    cells = row.query_selector_all("td")
                    row_data = [cell.text_content().strip() for cell in cells]
                    if row_data and len(row_data) > 0:
                        data.append(row_data)
                        if idx < 2:  # 첫 2개만 출력
                            print(f"Row {idx}: {row_data[:3]}...")
                
                print(f"Extracted {len(data)} rows including header")
                return data
                
            except Exception as e:
                print(f"Error extracting table data: {e}")
                return []
        
        except Exception as e:
            print(f"Error navigating to disbursement page: {e}")
            return []

    def save_to_sheets(self, data):
        """Google Sheets에 데이터 저장"""
        if not data:
            print("No data to save")
            return
        
        try:
            print(f"Saving {len(data)} rows to Google Sheets...")
            
            body = {
                'values': data
            }
            
            # 기존 데이터 모두 삭제
            self.sheets_service.spreadsheets().values().clear(
                spreadsheetId=self.sheet_id,
                range=f"{self.sheet_name}!A:Z"
            ).execute()
            print("Cleared existing data")
            
            # 새 데이터 작성
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=self.sheet_id,
                range=f"{self.sheet_name}!A1",
                valueInputOption="RAW",
                body=body
            ).execute()
            
            print(f"Successfully saved {len(data)} rows to Google Sheets")
            print(f"Updated cells: {result.get('updatedCells')}")
            
        except Exception as e:
            print(f"Error saving to Google Sheets: {e}")
            raise

    def run(self):
        """메인 실행"""
        with sync_playwright() as p:
            # Headless 모드로 브라우저 실행
            browser = p.chromium.launch(
                headless=True,
                args=['--disable-blink-features=AutomationControlled']  # 자동화 탐지 방지
            )
            page = browser.new_page()
            
            # 타임아웃 설정
            page.set_default_timeout(30000)
            page.set_default_navigation_timeout(60000)
            
            try:
                # 로그인
                self.login(page)
                
                # 데이터 수집
                data = self.get_disbursement_data(page)
                
                # Google Sheets 저장
                if data and len(data) > 1:  # 헤더 + 1개 이상의 데이터 행
                    self.save_to_sheets(data)
                    print("Process completed successfully!")
                else:
                    print("No valid data collected")
                    
            except Exception as e:
                print(f"Error occurred: {e}")
                import traceback
                traceback.print_exc()
                raise
            finally:
                browser.close()


if __name__ == "__main__":
    BizBoxPlaywright().run()
