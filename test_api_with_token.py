import requests
import random

email = f"test_api_{random.randint(1000, 9999)}@example.com"
pwd = "password123"

# 1. Register
reg_url = "https://ifo1usk4zzs6kf3w1axrg1y9.207.180.251.156.sslip.io/users/register"
res = requests.post(reg_url, json={"email": email, "password": pwd, "full_name": "Test Api", "phone": "123"})
print("Register:", res.status_code)

# 2. Login
login_url = "https://ifo1usk4zzs6kf3w1axrg1y9.207.180.251.156.sslip.io/auth/login"
res = requests.post(login_url, data={"username": email, "password": pwd, "grant_type": "password"})
print("Login:", res.status_code)
token = res.json().get("access_token")
if not token:
    print("Failed to get token", res.text)
    exit()

# 3. Test endpoint
url = "https://ifo1usk4zzs6kf3w1axrg1y9.207.180.251.156.sslip.io/spaces/my"
res = requests.get(url, headers={"Authorization": f"Bearer {token}"})
print(f"GET /spaces/my: {res.status_code}")
print(res.text[:200])

url2 = "https://ifo1usk4zzs6kf3w1axrg1y9.207.180.251.156.sslip.io/chat/conversations"
res2 = requests.get(url2, headers={"Authorization": f"Bearer {token}"})
print(f"GET /chat/conversations: {res2.status_code}")
print(res2.text[:200])
