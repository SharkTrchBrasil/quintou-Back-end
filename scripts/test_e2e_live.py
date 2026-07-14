"""
Quintou - Teste E2E Completo
Cobre: Auth, Perfil, Espacos, Favoritos, Chat, Reservas, Cancelamentos, Reviews, Seguranca
Usa os dois usuarios reais: csatrabalho1@gmail.com (Host) e csatrabalho3@gmail.com (Guest)
"""
import httpx
import asyncio
import json
import sys
import os
from datetime import datetime, timedelta, timezone, date, time
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

API_URL = "https://ifo1usk4zzs6kf3w1axrg1y9.207.180.251.156.sslip.io"
DATABASE_URL = 'postgresql+asyncpg://postgres:kGTVCdBwYwJ1Fet4BVYpX65tJxfwkx3ZnArkP2E3RpXypEPcVJuUutEUBw2c7gwE@207.180.251.156:5431/postgres'

USER_A_EMAIL = "csatrabalho1@gmail.com"
USER_B_EMAIL = "csatrabalho3@gmail.com"
PASSWORD = "Alpha20219@"
CATEGORY_ID = "5f9bc6b6-b925-42a6-867a-3ef0082c0032"

async def approve_space_in_db(space_id: str):
    """Aprova o espaco diretamente no banco para testes E2E"""
    engine = create_async_engine(DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await session.execute(text('UPDATE spaces SET is_approved = true WHERE id = :id'), {'id': space_id})
        await session.commit()
    await engine.dispose()

passed = 0
failed = 0
errors = []

def ok(name, detail=""):
    global passed
    passed += 1
    print(f"  ✅ {name}" + (f" — {detail}" if detail else ""))

def fail(name, detail=""):
    global failed
    failed += 1
    errors.append(f"{name}: {detail}")
    print(f"  ❌ {name}" + (f" — {detail}" if detail else ""))

def check(name, condition, detail=""):
    if condition:
        ok(name, detail)
    else:
        fail(name, detail)

async def run_e2e():
    print(f"\n{'='*60}")
    print(f"  QUINTOU E2E — Teste Completo de Plataforma")
    print(f"  API: {API_URL}")
    print(f"  Hora: {datetime.now().isoformat()}")
    print(f"{'='*60}\n")

    async with httpx.AsyncClient(base_url=API_URL, verify=False, timeout=20.0) as c:

        # ══════════════════════════════════════════════════════════
        # FASE 1: HEALTH & INFRA
        # ══════════════════════════════════════════════════════════
        print("── FASE 1: Health & Infra ──")
        r = await c.get("/health")
        check("GET /health", r.status_code == 200, f"status={r.status_code}")

        r = await c.get("/categories")
        check("GET /categories", r.status_code == 200, f"count={len(r.json())}")

        # ══════════════════════════════════════════════════════════
        # FASE 2: AUTH — Login, Token, Segurança
        # ══════════════════════════════════════════════════════════
        print("\n── FASE 2: Auth ──")

        # Login com senha errada
        r = await c.post("/auth/login", json={"email": USER_A_EMAIL, "password": "SenhaErrada123!"})
        check("Login com senha errada retorna 401", r.status_code == 401, f"status={r.status_code}")

        # Login com email inexistente
        r = await c.post("/auth/login", json={"email": "naoexiste@naoexiste.com", "password": PASSWORD})
        check("Login com email inexistente retorna 401/404", r.status_code in (401, 404), f"status={r.status_code}")

        # Login correto User A (Host)
        r = await c.post("/auth/login", json={"email": USER_A_EMAIL, "password": PASSWORD})
        check("Login User A (Host)", r.status_code == 200, f"status={r.status_code}")
        data_a = r.json()
        token_a = data_a.get("accessToken") or data_a.get("access_token")
        refresh_a = data_a.get("refreshToken") or data_a.get("refresh_token")
        headers_a = {"Authorization": f"Bearer {token_a}"}
        check("Token A presente", token_a is not None)

        # Login correto User B (Guest)
        r = await c.post("/auth/login", json={"email": USER_B_EMAIL, "password": PASSWORD})
        check("Login User B (Guest)", r.status_code == 200, f"status={r.status_code}")
        data_b = r.json()
        token_b = data_b.get("accessToken") or data_b.get("access_token")
        headers_b = {"Authorization": f"Bearer {token_b}"}
        check("Token B presente", token_b is not None)

        # Refresh Token
        if refresh_a:
            r = await c.post("/auth/refresh", json={"refresh_token": refresh_a})
            check("Refresh Token", r.status_code == 200, f"status={r.status_code}")
            if r.status_code == 200:
                new_data = r.json()
                token_a = new_data.get("accessToken") or new_data.get("access_token") or token_a
                headers_a = {"Authorization": f"Bearer {token_a}"}

        # Acesso sem token
        r = await c.get("/users/me")
        check("GET /users/me sem token retorna 401/403", r.status_code in (401, 403), f"status={r.status_code}")

        # Token inválido
        r = await c.get("/users/me", headers={"Authorization": "Bearer token_invalido_falso"})
        check("Token inválido retorna 401/403", r.status_code in (401, 403), f"status={r.status_code}")

        # ══════════════════════════════════════════════════════════
        # FASE 3: PERFIL — Get/Update
        # ══════════════════════════════════════════════════════════
        print("\n── FASE 3: Perfil ──")

        r = await c.get("/users/me", headers=headers_a)
        check("GET /users/me User A", r.status_code == 200)
        user_a_data = r.json()
        user_a_id = user_a_data.get("id")
        check("User A tem ID", user_a_id is not None, f"id={user_a_id}")

        r = await c.get("/users/me", headers=headers_b)
        check("GET /users/me User B", r.status_code == 200)
        user_b_data = r.json()
        user_b_id = user_b_data.get("id")

        # Become host (User A)
        r = await c.put("/users/me/become-host", headers=headers_a)
        check("User A become-host", r.status_code == 200, f"status={r.status_code}")

        # Get user by ID (público)
        r = await c.get(f"/users/{user_a_id}")
        check("GET /users/:id público", r.status_code == 200)

        # ══════════════════════════════════════════════════════════
        # FASE 4: ESPAÇOS — CRUD Completo
        # ══════════════════════════════════════════════════════════
        print("\n── FASE 4: Espaços (CRUD) ──")

        space_data = {
            "title": "E2E Salão de Festas Premium",
            "description": "Espaço completo com piscina, churrasqueira e salão coberto para até 50 pessoas.",
            "categoryId": CATEGORY_ID,
            "addressLine": "Rua dos Testes E2E, 999",
            "city": "São Paulo",
            "state": "SP",
            "zipCode": "01001-000",
            "neighborhood": "Centro",
            "latitude": -23.5505,
            "longitude": -46.6333,
            "maxGuests": 50,
            "price": 150.0,
            "pricePerHour": 150.0,
            "pricingMode": "PER_HOUR",
            "minHours": 2,
            "maxHours": 12,
            "isActive": True,
            "listingType": "SPACE",
            "amenities": ["WiFi", "Piscina", "Churrasqueira", "Estacionamento"],
            "rules": "Proibido fumar. Barulho permitido até 22h.",
            "allowsParties": True,
            "allowsAlcohol": True,
            "allowsChildren": True,
            "hasParking": True,
            "hasRestroom": True,
            "cancellationPolicy": "FLEXIVEL"
        }

        # Guest tenta criar espaço (deve falhar — não é host)
        r = await c.post("/spaces", json=space_data, headers=headers_b)
        check("Guest não pode criar espaço", r.status_code in (403, 401, 400), f"status={r.status_code}")

        # Host cria espaço
        r = await c.post("/spaces", json=space_data, headers=headers_a)
        check("Host cria espaço", r.status_code == 201, f"status={r.status_code}")
        if r.status_code == 201:
            space = r.json()
            space_id = space.get("id")
            check("Space tem ID", space_id is not None, f"id={space_id}")
            check("Space título correto", space.get("title") == "E2E Salão de Festas Premium")
        else:
            print(f"    ERRO criando space: {r.text[:300]}")
            space_id = None

        if not space_id:
            print("\n⛔ Não foi possível criar espaço. Abortando testes dependentes.")
            print_summary()
            return

        # Aprovar espaço no banco (simula admin approval)
        await approve_space_in_db(space_id)
        ok("Espaço aprovado no banco (admin)", f"id={space_id}")

        # GET espaço específico
        r = await c.get(f"/spaces/{space_id}")
        check("GET /spaces/:id", r.status_code == 200)

        # Update espaço
        r = await c.put(f"/spaces/{space_id}", json={"title": "E2E Salão Atualizado", "price": 200.0}, headers=headers_a)
        check("PUT /spaces/:id update", r.status_code == 200, f"status={r.status_code}")
        if r.status_code == 200:
            check("Título atualizado", r.json().get("title") == "E2E Salão Atualizado")

        # Guest tenta atualizar espaço de outro (deve falhar)
        r = await c.put(f"/spaces/{space_id}", json={"title": "Hack!"}, headers=headers_b)
        check("Guest não pode editar espaço alheio", r.status_code in (403, 401, 400), f"status={r.status_code}")

        # List spaces
        r = await c.get("/spaces")
        check("GET /spaces lista", r.status_code == 200)

        # My spaces (host)
        r = await c.get("/spaces/my", headers=headers_a)
        check("GET /spaces/my do host", r.status_code == 200)

        # Autocomplete
        r = await c.get("/spaces/autocomplete?q=E2E")
        check("GET /spaces/autocomplete", r.status_code == 200)

        # Increment views
        r = await c.post(f"/spaces/{space_id}/view")
        check("POST /spaces/:id/view", r.status_code == 200)

        # ══════════════════════════════════════════════════════════
        # FASE 5: FAVORITOS
        # ══════════════════════════════════════════════════════════
        print("\n── FASE 5: Favoritos ──")

        r = await c.post(f"/favorites/{space_id}", headers=headers_b)
        check("Adicionar favorito", r.status_code == 201, f"status={r.status_code}")

        r = await c.get("/favorites", headers=headers_b)
        check("Listar favoritos", r.status_code == 200)
        if r.status_code == 200:
            favs = r.json()
            check("Favorito na lista", len(favs) >= 1 if isinstance(favs, list) else True)

        # Favoritar de novo (deve dar erro ou idempotente)
        r = await c.post(f"/favorites/{space_id}", headers=headers_b)
        check("Favoritar duplicado", r.status_code in (201, 200, 400, 409), f"status={r.status_code}")

        r = await c.delete(f"/favorites/{space_id}", headers=headers_b)
        check("Remover favorito", r.status_code == 204, f"status={r.status_code}")

        # Remover favorito já removido
        r = await c.delete(f"/favorites/{space_id}", headers=headers_b)
        check("Remover favorito inexistente", r.status_code in (204, 404), f"status={r.status_code}")

        # ══════════════════════════════════════════════════════════
        # FASE 6: CHAT — Conversas e Mensagens
        # ══════════════════════════════════════════════════════════
        print("\n── FASE 6: Chat ──")

        # Guest abre conversa
        r = await c.post("/conversations", json={"spaceId": space_id}, headers=headers_b)
        check("Criar conversa", r.status_code in (200, 201), f"status={r.status_code}")
        conv = r.json()
        conv_id = conv.get("id")
        check("Conversa tem ID", conv_id is not None)

        # Guest envia mensagem
        r = await c.post(f"/conversations/{conv_id}/messages", json={"content": "Olá! Gostaria de alugar."}, headers=headers_b)
        check("Guest envia mensagem", r.status_code in (200, 201), f"status={r.status_code}")

        # Host responde
        r = await c.post(f"/conversations/{conv_id}/messages", json={"content": "Claro! Está disponível."}, headers=headers_a)
        check("Host responde mensagem", r.status_code in (200, 201), f"status={r.status_code}")

        # Listar mensagens
        r = await c.get(f"/conversations/{conv_id}/messages", headers=headers_b)
        check("Listar mensagens da conversa", r.status_code == 200)
        if r.status_code == 200:
            msgs = r.json()
            check("Pelo menos 2 mensagens", len(msgs) >= 2, f"count={len(msgs)}")

        # Listar conversas
        r = await c.get("/conversations", headers=headers_b)
        check("Listar conversas do Guest", r.status_code == 200)

        r = await c.get("/conversations", headers=headers_a)
        check("Listar conversas do Host", r.status_code == 200)

        # Unread total
        r = await c.get("/conversations/unread-total", headers=headers_a)
        check("Unread total", r.status_code == 200)

        # Marcar como lido
        r = await c.put(f"/conversations/{conv_id}/read", headers=headers_a)
        check("Marcar conversa como lida", r.status_code == 204, f"status={r.status_code}")

        # Segurança: mensagem com telefone (contact filter)
        r = await c.post(f"/conversations/{conv_id}/messages", json={"content": "Me liga (11) 99999-9999"}, headers=headers_b)
        check("Filtro de contato bloqueia telefone", r.status_code == 400, f"status={r.status_code}")

        # ══════════════════════════════════════════════════════════
        # FASE 7: RESERVAS — Fluxo Completo
        # ══════════════════════════════════════════════════════════
        print("\n── FASE 7: Reservas ──")

        booking_date = (datetime.now(timezone.utc) + timedelta(days=7)).date()

        booking_payload = {
            "spaceId": space_id,
            "date": booking_date.isoformat(),
            "startTime": "10:00",
            "endTime": "14:00",
            "numGuests": 10,
            "numAdults": 8,
            "numChildren": 2,
            "numInfants": 0,
            "guestMessage": "Festa de aniversário para 10 pessoas!"
        }

        # Guest cria reserva
        r = await c.post("/bookings", json=booking_payload, headers=headers_b)
        check("Guest cria reserva", r.status_code == 201, f"status={r.status_code}")
        if r.status_code == 201:
            booking = r.json()
            booking_id = booking.get("id")
            check("Booking tem ID", booking_id is not None)
            check("Booking status PENDING", booking.get("status") == "PENDING")
            check("Total price calculado", float(booking.get("totalPrice", 0)) > 0, f"total={booking.get('totalPrice')}")
        else:
            print(f"    ERRO criando booking: {r.text[:300]}")
            booking_id = None

        # Host tenta reservar em seu próprio espaço (não deveria funcionar)
        r = await c.post("/bookings", json=booking_payload, headers=headers_a)
        check("Host não pode reservar próprio espaço", r.status_code in (400, 403, 422), f"status={r.status_code}")

        # Guest lista suas reservas
        r = await c.get("/bookings/my", headers=headers_b)
        check("Guest lista suas reservas", r.status_code == 200)

        # Host lista reservas recebidas
        r = await c.get("/bookings/host", headers=headers_a)
        check("Host lista reservas recebidas", r.status_code == 200)

        if booking_id:
            # Get booking by ID
            r = await c.get(f"/bookings/{booking_id}", headers=headers_b)
            check("GET /bookings/:id", r.status_code == 200)

            # Guest não-dono tenta ver booking
            r2 = await c.get(f"/bookings/{booking_id}", headers=headers_a)
            check("Host pode ver booking do seu espaço", r2.status_code == 200)

            # Host confirma reserva
            r = await c.put(f"/bookings/{booking_id}/confirm", headers=headers_a)
            check("Host confirma reserva", r.status_code == 200, f"status={r.status_code}")
            if r.status_code == 200:
                check("Status mudou para CONFIRMED", r.json().get("status") == "CONFIRMED")

            # Host completa reserva
            r = await c.put(f"/bookings/{booking_id}/complete", headers=headers_a)
            check("Host completa reserva", r.status_code == 200, f"status={r.status_code}")
            if r.status_code == 200:
                check("Status mudou para COMPLETED", r.json().get("status") == "COMPLETED")

        # ══════════════════════════════════════════════════════════
        # FASE 8: CANCELAMENTO DE RESERVA
        # ══════════════════════════════════════════════════════════
        print("\n── FASE 8: Cancelamento ──")

        booking2_date = (datetime.now(timezone.utc) + timedelta(days=14)).date()
        booking2_payload = {
            "spaceId": space_id,
            "date": booking2_date.isoformat(),
            "startTime": "15:00",
            "endTime": "18:00",
            "numGuests": 5,
            "numAdults": 5,
            "numChildren": 0,
            "numInfants": 0,
            "guestMessage": "Reserva para cancelar"
        }

        r = await c.post("/bookings", json=booking2_payload, headers=headers_b)
        check("Criar segunda reserva (para cancelar)", r.status_code == 201, f"status={r.status_code}")
        booking2_id = r.json().get("id") if r.status_code == 201 else None

        if booking2_id:
            # Guest cancela
            r = await c.put(f"/bookings/{booking2_id}/cancel?reason=Mudei+de+planos", headers=headers_b)
            check("Guest cancela reserva", r.status_code == 200, f"status={r.status_code}")
            if r.status_code == 200:
                check("Status CANCELLED_BY_GUEST", r.json().get("status") == "CANCELLED_BY_GUEST")

        # Host rejeita reserva
        booking3_date = (datetime.now(timezone.utc) + timedelta(days=21)).date()
        booking3_payload = {
            "spaceId": space_id,
            "date": booking3_date.isoformat(),
            "startTime": "09:00",
            "endTime": "12:00",
            "numGuests": 3,
            "numAdults": 3,
            "numChildren": 0,
            "numInfants": 0,
            "guestMessage": "Reserva para o host rejeitar"
        }
        r = await c.post("/bookings", json=booking3_payload, headers=headers_b)
        booking3_id = r.json().get("id") if r.status_code == 201 else None

        if booking3_id:
            r = await c.put(f"/bookings/{booking3_id}/reject", headers=headers_a)
            check("Host rejeita reserva", r.status_code == 200, f"status={r.status_code}")
            if r.status_code == 200:
                check("Status CANCELLED_BY_HOST", r.json().get("status") == "CANCELLED_BY_HOST")

        # ══════════════════════════════════════════════════════════
        # FASE 9: REVIEWS
        # ══════════════════════════════════════════════════════════
        print("\n── FASE 9: Reviews ──")

        if booking_id:
            review_payload = {
                "bookingId": booking_id,
                "rating": 5,
                "comment": "Espaço incrível! Recomendo para festas.",
                "cleanlinessRating": 5,
                "accuracyRating": 4,
                "communicationRating": 5,
                "valueRating": 4
            }
            r = await c.post("/reviews", json=review_payload, headers=headers_b)
            check("Guest cria review", r.status_code == 201, f"status={r.status_code}")
            if r.status_code == 201:
                review = r.json()
                check("Review tem rating 5", review.get("rating") == 5)

            # Review duplicada (mesmo booking)
            r = await c.post("/reviews", json=review_payload, headers=headers_b)
            check("Review duplicada bloqueada", r.status_code in (400, 409, 422), f"status={r.status_code}")

        # ══════════════════════════════════════════════════════════
        # FASE 10: SEGURANÇA — Acesso cruzado
        # ══════════════════════════════════════════════════════════
        print("\n── FASE 10: Segurança ──")

        # Guest tenta deletar espaço do host
        r = await c.delete(f"/spaces/{space_id}", headers=headers_b)
        check("Guest não pode deletar espaço alheio", r.status_code in (403, 401, 400), f"status={r.status_code}")

        # Acesso a espaço inexistente
        r = await c.get("/spaces/00000000-0000-0000-0000-000000000000")
        check("Espaço inexistente retorna 404", r.status_code == 404)

        # Booking em espaço inexistente
        r = await c.post("/bookings", json={
            "spaceId": "00000000-0000-0000-0000-000000000000",
            "date": booking_date.isoformat(),
            "startTime": "10:00",
            "endTime": "14:00",
            "numGuests": 5
        }, headers=headers_b)
        check("Booking em espaço inexistente falha", r.status_code in (404, 400, 422), f"status={r.status_code}")

        # Host Dashboard
        r = await c.get("/host/dashboard", headers=headers_a)
        check("GET /host/dashboard", r.status_code == 200, f"status={r.status_code}")

        # ══════════════════════════════════════════════════════════
        # CLEANUP
        # ══════════════════════════════════════════════════════════
        print("\n── CLEANUP ──")
        r = await c.delete(f"/spaces/{space_id}", headers=headers_a)
        check("Deletar espaço de teste", r.status_code == 204, f"status={r.status_code}")

    print_summary()

def print_summary():
    global passed, failed, errors
    total = passed + failed
    print(f"\n{'='*60}")
    print(f"  RESULTADO FINAL: {passed}/{total} testes passaram")
    if failed == 0:
        print(f"  🎉 TODOS OS TESTES PASSARAM!")
    else:
        print(f"  ⚠️  {failed} teste(s) falharam:")
        for e in errors:
            print(f"    • {e}")
    print(f"{'='*60}\n")

    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_e2e())
