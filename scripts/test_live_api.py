import httpx
import asyncio
import sys

API_URL = "https://ifo1usk4zzs6kf3w1axrg1y9.207.180.251.156.sslip.io"

async def test_live_api():
    print(f"Testing live API at: {API_URL}")
    
    async with httpx.AsyncClient(base_url=API_URL, verify=False) as client:
        # 1. Healthcheck
        try:
            print("1. Testing Healthcheck...")
            resp = await client.get("/health")
            print(f"Healthcheck Status: {resp.status_code}")
            print(f"Healthcheck Response: {resp.text}")
        except Exception as e:
            print(f"Healthcheck failed: {e}")
            
        # 2. Register a new user
        test_email = "livetest2_user@example.com"
        print(f"\n2. Testing User Registration ({test_email})...")
        user_data = {
            "email": test_email,
            "password": "Password123!",
            "full_name": "Live Test User",
            "cpf": "12345678900",
            "phone": "+5511999999999"
        }
        
        token = None
        resp = await client.post("/auth/register", json=user_data)
        if resp.status_code == 201:
            print("Registration Successful!")
            # 3. Login
            print("\n3. Testing Login...")
            login_data = {
                "username": test_email,
                "password": "Password123!"
            }
            login_resp = await client.post("/auth/login", data=login_data)
            if login_resp.status_code == 200:
                print("Login Successful!")
                token = login_resp.json()["access_token"]
            else:
                print(f"Login failed: {login_resp.status_code} {login_resp.text}")
        elif resp.status_code == 400 and "Email already registered" in resp.text:
            print("User already exists, trying to login...")
            login_data = {
                "username": test_email,
                "password": "Password123!"
            }
            login_resp = await client.post("/auth/login", data=login_data)
            if login_resp.status_code == 200:
                print("Login Successful!")
                token = login_resp.json()["access_token"]
        else:
            print(f"Registration failed: {resp.status_code} {resp.text}")
            try:
                print(resp.json())
            except:
                pass
            
        if not token:
            print("\nCannot proceed with authenticated tests without a token. Exiting.")
            return

        # Setup Auth Headers
        headers = {"Authorization": f"Bearer {token}"}
        
        # 4. Get current user
        print("\n4. Testing /users/me...")
        me_resp = await client.get("/users/me", headers=headers)
        if me_resp.status_code == 200:
            print(f"User retrieved: {me_resp.json()['email']}")
        else:
            print(f"Failed to get user: {me_resp.status_code} {me_resp.text}")

        # 5. List spaces
        print("\n5. Testing /spaces (List)...")
        spaces_resp = await client.get("/spaces")
        if spaces_resp.status_code == 200:
            spaces = spaces_resp.json()
            print(f"Successfully listed {len(spaces)} spaces.")
        else:
            print(f"Failed to list spaces: {spaces_resp.status_code} {spaces_resp.text}")

if __name__ == "__main__":
    asyncio.run(test_live_api())
