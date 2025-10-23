import requests
import pandas as pd
from datetime import datetime, timedelta
import pytz
import time
import math
import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from urllib.parse import urlencode


class BizBox():
    def __init__(self):
        self.host = "http://58.224.161.247"
        self.bizbox_encoded_id = os.getenv("BIZBOX_ENCODED_ID")
        self.bizbox_encoded_pw = os.getenv("BIZBOX_ENCODED_PW")
        self.sheet_id = "147uYiSvi7Wl6LQbjqE2ae1nk7WjI2kUt_W-0gDxswas"
        self.sheet_name = "TEST"  # 시트 이름
        
        if not self.bizbox_encoded_id or not self.bizbox_encoded_pw:
            raise ValueError("BIZBOX_ENCODED_ID, BIZBOX_ENCODED_PW is required")
        
        # Google Sheets API 초기화
        self.init_sheets_api()

    def init_sheets_api(self):
        """Google Sheets API 인증 초기화"""
        credentials = Credentials.from_service_account_file(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.sheets_service = build('sheets', 'v4', credentials=credentials)

    def login(self):
        url = f"{self.host}/gw/uat/uia/actionLogin.do"
        params = {
            "isScLogin": "",
            "scUserId": "",
            "scUserPwd": "",
            "id": self.bizbox_encoded_id,
            "id_sub1": "",
            "id_sub2": "",
            "password": self.bizbox_encoded_pw
        }
        data = urlencode(params, doseq=True)
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate",
            "accept-language": "ko-KR,ko;q=0.9",
            "cache-control": "max-age=0",
            "connection": "keep-alive",
            "content-length": "148",
            "content-type": "application/x-www-form-urlencoded",
            "host": "58.224.161.247",
            "origin": "http://58.224.161.247",
            "referer": "http://58.224.161.247/gw/uat/uia/egovLoginUsr.do",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }

        response = requests.post(url, headers=headers, data=data)
        cookies = requests.utils.dict_from_cookiejar(response.history[0].cookies)
        self.cookies = cookies

    def get_disbursement_document(self):
        result = []
        korea_tz = pytz.timezone('Asia/Seoul')
        end_date = (datetime.now(korea_tz) + timedelta(days=14)).strftime("%Y%m%d")
        page_size = 10000
        page = 1
        url = f"{self.host}/exp/ex/report/ExSlipReportExpendAdmListInfoSelect.do"
        payload = f"page={page}&pageSize={page_size}&sortField=&sortType=&searchrepDateStartDate=20230101&searchrepDateEndDate={end_date}&searchexpendDateStartDate=19000101&searchexpendDateEndtDate=99991231&searchexpendReqDateStartDate=20240101&searchexpendReqDatendDate={end_date}&searchauthDateStartDate=19000101&searchauthDateEndDate=99991231&appUserName=&searchDocStatus=90&appDocNo=&appDocTitle=&formName=&bizCd=&erpSendYN=Y&erpSendName=&erpSendSeq=&erpUseDeptName=&erpUseEmpName=&summaryName=&authName=&projectName=&cardName=&partnerName=&acctCode=&acctName=&slipNote=&drcrGbn=cr&authNum="
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'host': '58.224.161.247',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Referer': 'http://58.224.161.247/exp/ex/admin/report/ExApprovalSlipList.do?menu_no=810101500'}
        res = requests.post(url, headers=headers, data=payload, cookies=self.cookies)
        res.raise_for_status()
        data = res.json()
        result.extend(data['aData']['resultList']['list'])
        total_pages = math.ceil(data['aData']['resultList']['totalCount'] / page_size)

        for page in range(2, total_pages + 1):
            time.sleep(3)
            payload = f"page={page}&pageSize={page_size}&sortField=&sortType=&searchrepDateStartDate=20230101&searchrepDateEndDate={end_date}&searchexpendDateStartDate=19000101&searchexpendDateEndtDate=99991231&searchexpendReqDateStartDate=20240101&searchexpendReqDatendDate={end_date}&searchauthDateStartDate=19000101&searchauthDateEndDate=99991231&appUserName=&searchDocStatus=90&appDocNo=&appDocTitle=&formName=&bizCd=&erpSendYN=A&erpSendName=&erpSendSeq=&erpUseDeptName=&erpUseEmpName=&summaryName=&authName=&projectName=&cardName=&partnerName=&acctCode=&acctName=&slipNote=&drcrGbn=A&authNum="
            res = requests.post(url, headers=headers, data=payload, cookies=self.cookies)
            data = res.json()
            res.raise_for_status()
            result.extend(data['aData']['resultList']['list'])

        return result

    def change(self, commpany):
        if commpany == "rapport_table":
            payload = "seq=rapportlabs%7C1405%7C1413"  # 라포테이블
        else:
            payload = "seq=rapportlabs%7C1443%7C1446"  # 라포스튜디오
        url = f"{self.host}/gw/systemx/changeUserPositionProc.do"
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-encoding": "gzip, deflate",
            "accept-language": "ko-KR,ko;q=0.9",
            "cache-control": "max-age=0",
            "connection": "keep-alive",
            "content-length": "29",
            "content-type": "application/x-www-form-urlencoded",
            "host": "58.224.161.247",
            "origin": "http://58.224.161.247",
            "referer": "http://58.224.161.247/gw/bizbox.do",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        }
        res = requests.post(url, headers=headers, data=payload, cookies=self.cookies)
        res.raise_for_status()

    def load(self, df):
        """Google Sheets에 데이터 덮어쓰기"""
        # 헤더 추가
        values = [df.columns.tolist()] + df.values.tolist()
        
        body = {
            'values': values
        }
        
        # 기존 데이터 모두 삭제 후 새로 쓰기
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
        
        print(f"Google Sheets 업데이트 완료: {len(df)} rows")

    def run(self):
        self.login()
        time.sleep(3)
        print("login success")
        labs_disbursement_data = self.get_disbursement_document()
        labs_df = pd.DataFrame(labs_disbursement_data)
        labs_df['company'] = 'rapport_labs'

        # 라포테이블 더이상 사용하지 않아서 주석처리
        # self.change('rapport_table')
        # table_disbursement_data = self.get_disbursement_document()
        # table_df = pd.DataFrame(table_disbursement_data)
        # table_df['company'] = 'rapport_table'

        self.change('rapport_studio')
        studio_disbursement_data = self.get_disbursement_document()
        studio_df = pd.DataFrame(studio_disbursement_data)
        studio_df['company'] = 'rapport_studio'

        total_df = pd.concat([labs_df, studio_df])

        # Google Sheets에 저장
        self.load(total_df)


if __name__ == "__main__":
    BizBox().run()
