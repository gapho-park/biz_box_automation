import os
import socket
import urllib.request
import urllib.error
from playwright.sync_api import sync_playwright


def test_network_connectivity():
    """네트워크 연결 테스트"""
    print("=" * 50)
    print("네트워크 연결 테스트")
    print("=" * 50)
    
    host = "58.224.161.247"
    
    # DNS 해석
    try:
        ip = socket.gethostbyname(host)
        print(f"✓ DNS 해석 성공: {host} -> {ip}")
    except socket.gaierror as e:
        print(f"✗ DNS 해석 실패: {e}")
        return False
    
    # 포트 연결 테스트
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, 80))
        sock.close()
        
        if result == 0:
            print(f"✓ 포트 80 연결 성공")
        else:
            print(f"✗ 포트 80 연결 실패: 오류 코드 {result}")
            return False
    except Exception as e:
        print(f"✗ 포트 연결 테스트 실패: {e}")
        return False
    
    # HTTP 요청 테스트
    try:
        response = urllib.request.urlopen("http://58.224.161.247/gw/bizbox.do", timeout=10)
        print(f"✓ HTTP 요청 성공: 상태 코드 {response.status}")
        print(f"  응답 크기: {len(response.read())} bytes")
        return True
    except urllib.error.URLError as e:
        print(f"✗ HTTP 요청 실패: {e}")
        return False
    except Exception as e:
        print(f"✗ HTTP 요청 실패: {e}")
        return False


def test_playwright_basic():
    """Playwright 기본 연결 테스트"""
    print("\n" + "=" * 50)
    print("Playwright 연결 테스트")
    print("=" * 50)
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            print("✓ 브라우저 시작 성공")
            
            # 간단한 페이지 로드
            try:
                page.goto("http://58.224.161.247/gw/bizbox.do", timeout=30000)
                print(f"✓ 페이지 로드 성공")
                print(f"  URL: {page.url}")
                print(f"  Title: {page.title()}")
                
                # 로그인 폼 요소 확인
                try:
                    id_input = page.query_selector('input[name="id"]')
                    pw_input = page.query_selector('input[name="password"]')
                    
                    if id_input:
                        print(f"✓ ID 입력 필드 발견")
                    else:
                        print(f"✗ ID 입력 필드 없음")
                    
                    if pw_input:
                        print(f"✓ 비밀번호 입력 필드 발견")
                    else:
                        print(f"✗ 비밀번호 입력 필드 없음")
                    
                    # 페이지 소스 일부 출력
                    print("\n  [페이지 HTML 일부]")
                    html = page.content()
                    print(f"  전체 크기: {len(html)} bytes")
                    print("  " + html[500:1000].replace('\n', '\n  '))
                    
                except Exception as e:
                    print(f"✗ 페이지 요소 확인 실패: {e}")
            
            except Exception as e:
                print(f"✗ 페이지 로드 실패: {e}")
            
            browser.close()
            return True
    
    except Exception as e:
        print(f"✗ Playwright 실패: {e}")
        return False


def test_with_credentials():
    """자격증명을 사용한 로그인 테스트"""
    print("\n" + "=" * 50)
    print("로그인 테스트")
    print("=" * 50)
    
    bizbox_id = os.getenv("BIZBOX_ENCODED_ID")
    bizbox_pw = os.getenv("BIZBOX_ENCODED_PW")
    
    if not bizbox_id or not bizbox_pw:
        print("✗ 환경 변수 설정 필요: BIZBOX_ENCODED_ID, BIZBOX_ENCODED_PW")
        return False
    
    print(f"✓ 자격증명 확인 (ID 길이: {len(bizbox_id)})")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto("http://58.224.161.247/gw/bizbox.do", timeout=30000)
            
            # 폼 입력
            page.fill('input[name="id"]', bizbox_id)
            page.fill('input[name="password"]', bizbox_pw)
            print("✓ 자격증명 입력 완료")
            
            # 로그인 버튼 찾기
            button = page.query_selector('button[type="submit"]') or \
                     page.query_selector('input[type="submit"]') or \
                     page.query_selector('button:has-text("로그인")')
            
            if button:
                print("✓ 로그인 버튼 발견")
                button.click()
                print("✓ 로그인 버튼 클릭 완료")
                
                # 로그인 결과 대기
                page.wait_for_timeout(5000)
                print(f"  로그인 후 URL: {page.url}")
                print(f"  로그인 후 Title: {page.title()}")
            else:
                print("✗ 로그인 버튼을 찾을 수 없음")
            
            browser.close()
    
    except Exception as e:
        print(f"✗ 로그인 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    print("\n🔍 BizBox 자동화 진단 시작\n")
    
    network_ok = test_network_connectivity()
    playwright_ok = test_playwright_basic()
    
    if network_ok and playwright_ok:
        print("\n✓ 기본 연결 성공, 로그인 테스트 진행...\n")
        test_with_credentials()
    else:
        print("\n✗ 기본 연결 실패, 추가 테스트 스킵")
    
    print("\n" + "=" * 50)
    print("진단 완료")
    print("=" * 50)
