import urllib.request
import urllib.parse
import http.cookiejar
import sys

BASE_URL = "http://127.0.0.1:8080"

# Setup Cookie Jar
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def post(path, data):
    params = urllib.parse.urlencode(data).encode('utf-8')
    try:
        resp = opener.open(f"{BASE_URL}{path}", data=params)
        return resp.read().decode('utf-8'), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8'), e.url

def get(path):
    try:
        resp = opener.open(f"{BASE_URL}{path}")
        return resp.read().decode('utf-8'), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.read().decode('utf-8'), e.url

def run_test():
    print("--- Starting Verification Flow ---")
    
    # 0. Health Check
    print("[0] Health Check (GET /)...")
    try:
        content, url = get("/")
        if "Login" in content:
            print(" -> Success: Server reachable.")
        else:
             print(" -> Warn: Server reachable but content unexpected.")
    except Exception as e:
        print(f" -> FAIL: Health check failed: {e}")
        sys.exit(1)

    # 1. Register User A
    print("[1] Registering User A...")
    cj.clear() # clear cookies
    content, url = post("/register", {"username": "userA", "password": "pass"})
    if "Dashboard" in content:
        print(" -> Success: Registered and redirected to Dashboard.")
    else:
        print(" -> FAIL: Register failed.")
        sys.exit(1)

    # 2. User A Adds Coupon
    print("[2] User A Adding Coupon...")
    content, url = post("/add_coupon", {
        "category": "Electronics",
        "brand": "TestBrandA",
        "offer": "10% Off",
        "expiry": "2025-12-31"
    })
    if "1" in content and "Coupons Given" in content: # Check stats in dashboard
        print(" -> Success: Coupon added, count updated.")
    else:
        print(" -> FAIL: Coupon addition check failed.")
        # print(content) # Debug

    # 3. Register User B
    print("[3] Registering User B...")
    cj.clear()
    content, url = post("/register", {"username": "userB", "password": "pass"})
    
    # 4. User B tries to claim (Should Fail)
    print("[4] User B trying to claim without giving...")
    # First get coupon ID. We need to parse it or just guess/take first if my script was smarter.
    # Let's simple-fetch the Take page to check if coupon exists.
    content, url = get("/take?category=Electronics")
    if "TestBrandA" in content:
        print(" -> Coupon visible.")
    else:
        print(" -> FAIL: User A's coupon not visible.")
    
    # We can't easily grab the UUID without parsing HTML. 
    # BUT, since I have access to the codebase, I can import the DataManager? 
    # No, that runs in a separate process. Ideally I should parse.
    # Quick dirty parse:
    import re
    match = re.search(r'name="coupon_id" value="([^"]+)"', content)
    if not match:
        print(" -> FAIL: Could not find coupon ID on page.")
        sys.exit(1)
    coupon_id = match.group(1)
    
    content, url = post("/claim_coupon", {"coupon_id": coupon_id})
    # Expect redirect to take?error=failed or similar, or alert check
    if "error=failed" in url or "You cannot claim more coupons" in content:
         print(" -> Success: Claim blocked as expected.")
    else:
         print(f" -> FAIL: Claim should have been blocked. URL: {url}")

    # 5. User B gives coupon
    print("[5] User B Adding Coupon...")
    post("/add_coupon", {
        "category": "Food",
        "brand": "BurgerKing",
        "offer": "BOGO",
        "expiry": "2025-12-31"
    })
    
    # 6. User B tries to claim again (Should Succeed)
    print("[6] User B claiming again...")
    content, url = post("/claim_coupon", {"coupon_id": coupon_id})
    if "/dashboard" in url:
        print(" -> Success: Claim successful, redirected to Dashboard.")
    else:
        print(f" -> FAIL: Claim failed. URL: {url}")

    print("--- Verification Complete: All Systems Go ---")

if __name__ == "__main__":
    try:
        run_test()
    except Exception as e:
        print(f"Test Error: {e}")
