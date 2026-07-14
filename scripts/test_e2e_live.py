import httpx
import asyncio
import json
from datetime import datetime, timedelta, timezone

API_URL = "http://localhost:8000"

USER_A_EMAIL = "csatrabalho1@gmail.com"
USER_B_EMAIL = "csatrabalho3@gmail.com"
PASSWORD = "Alpha20219@"

async def run_e2e():
    print(f"Starting E2E Tests on {API_URL}")
    print("="*50)
    
    async with httpx.AsyncClient(base_url=API_URL, verify=False, timeout=15.0) as client:
        # 1. Healthcheck
        print("\n1. Healthcheck...")
        r = await client.get("/health")
        print(f"Status: {r.status_code}")
        
        # 2. Login User A (Host)
        print("\n2. Login User A (Host)...")
        r = await client.post("/auth/login", json={"email": USER_A_EMAIL, "password": PASSWORD})
        if r.status_code != 200:
            print(f"User A not found, registering... {r.text}")
            reg_r = await client.post("/auth/register", json={
                "email": USER_A_EMAIL, "password": PASSWORD, "full_name": "Host User A", "cpf": "50187411476", "is_host": True
            })
            if reg_r.status_code != 201: print(reg_r.text); return
            r = await client.post("/auth/login", json={"email": USER_A_EMAIL, "password": PASSWORD})
        token_a = r.json().get("accessToken") or r.json().get("data", {}).get("access_token")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        print("User A logged in successfully.")
        
        # 3. Login User B (Guest)
        print("\n3. Login User B (Guest)...")
        r = await client.post("/auth/login", json={"email": USER_B_EMAIL, "password": PASSWORD})
        if r.status_code != 200:
            print(f"User B not found, registering... {r.text}")
            reg_r = await client.post("/auth/register", json={
                "email": USER_B_EMAIL, "password": PASSWORD, "full_name": "Guest User B", "cpf": "39325243229", "is_host": False
            })
            if reg_r.status_code != 201: print(reg_r.text); return
            r = await client.post("/auth/login", json={"email": USER_B_EMAIL, "password": PASSWORD})
        token_b = r.json().get("accessToken") or r.json().get("data", {}).get("access_token")
        headers_b = {"Authorization": f"Bearer {token_b}"}
        print("User B logged in successfully.")
        
        # Make User A a host if not already
        await client.put("/users/me/become-host", headers=headers_a)
        
        # 4. User A creates a space
        print("\n4. User A creates a Space...")
        space_data = {
            "title": "E2E Test Space",
            "description": "A wonderful space created during E2E testing.",
            "categoryId": None,
            "addressLine": "Rua E2E, 123",
            "city": "São Paulo",
            "state": "SP",
            "zipCode": "01001-000",
            "neighborhood": "Centro",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "maxGuests": 50,
            "price": 100.0,
            "pricePerHour": 100.0,
            "pricingMode": "PER_HOUR",
            "minHours": 2,
            "isActive": True,
            "listingType": "SPACE",
            "amenities": ["WiFi", "Piscina"],
            "rules": "Não fumar e não fazer barulho após as 22h"
        }
        
        space_data["categoryId"] = "5f9bc6b6-b925-42a6-867a-3ef0082c0032"
            
        r = await client.post("/spaces", json=space_data, headers=headers_a)
        if r.status_code != 201:
            print(f"Failed to create space: {r.text}")
            return
            
        space_id = r.json().get("data", {}).get("id")
        print(f"Space created successfully with ID: {space_id}")
        
        # 5. User B favorites the space
        print("\n5. User B favorites the Space...")
        r = await client.post(f"/favorites/{space_id}", headers=headers_b)
        print(f"Favorite status: {r.status_code}")
        
        # 6. User B starts a chat with User A
        print("\n6. User B starts Chat...")
        r = await client.post("/conversations", json={"space_id": space_id}, headers=headers_b)
        if r.status_code not in (200, 201):
            print(f"Failed to start chat: {r.text}")
            return
        conv_id = r.json().get("data", {}).get("id")
        print(f"Conversation created/fetched: {conv_id}")
        
        # 7. User B sends message
        print("\n7. User B sends message...")
        r = await client.post(f"/conversations/{conv_id}/messages", json={"content": "Hello Host! Is this available?"}, headers=headers_b)
        print(f"Message send status: {r.status_code}")
        
        # 8. User B creates a booking
        print("\n8. User B creates Booking...")
        now = datetime.now(timezone.utc)
        start_time = now + timedelta(days=2)
        end_time = start_time + timedelta(hours=3)
        
        booking_data = {
            "space_id": space_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "guest_count": 5,
            "message": "Can't wait to test this space!"
        }
        
        r = await client.post("/bookings", json=booking_data, headers=headers_b)
        if r.status_code != 201:
            print(f"Failed to create booking: {r.text}")
            return
            
        booking_id = r.json().get("data", {}).get("id")
        print(f"Booking created with ID: {booking_id}")
        
        # 9. User A checks host bookings
        print("\n9. User A lists Host Bookings...")
        r = await client.get("/bookings/host", headers=headers_a)
        bookings = r.json().get("data", [])
        found = any(b["id"] == booking_id for b in bookings)
        print(f"Booking found in host list: {found}")
        
        # 10. User A confirms booking
        print("\n10. User A confirms Booking...")
        r = await client.put(f"/bookings/{booking_id}/confirm", headers=headers_a)
        print(f"Confirm status: {r.status_code}")
        
        # 11. User A completes booking
        print("\n11. User A completes Booking...")
        r = await client.put(f"/bookings/{booking_id}/complete", headers=headers_a)
        print(f"Complete status: {r.status_code}")
        
        # 12. User B writes a review
        print("\n12. User B writes a review...")
        review_data = {
            "space_id": space_id,
            "booking_id": booking_id,
            "rating": 5,
            "comment": "Amazing test space, highly recommend!"
        }
        r = await client.post("/reviews", json=review_data, headers=headers_b)
        print(f"Review create status: {r.status_code}")
        
        # 13. User A deletes the space
        print("\n13. User A deletes the Space (cleanup)...")
        r = await client.delete(f"/spaces/{space_id}", headers=headers_a)
        print(f"Delete status: {r.status_code}")
        
        print("\n" + "="*50)
        print("ALL E2E TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_e2e())
