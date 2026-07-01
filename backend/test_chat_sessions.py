import asyncio
import httpx
import uuid

async def main():
    email = f'test_{uuid.uuid4()}@test.com'
    async with httpx.AsyncClient() as client:
        r = await client.post('http://localhost:8000/api/auth/register', json={'email': email, 'password': 'password123'})
        print("Register:", r.status_code, r.text)
        
        r2 = await client.post('http://localhost:8000/api/auth/login', data={'username': email, 'password': 'password123'})
        token = r2.json().get('access_token')
        
        r3 = await client.post('http://localhost:8000/api/chat', json={'message': 'find hospitals in guntur'}, headers={'Authorization': 'Bearer ' + token})
        print("Chat POST:", r3.status_code)
        sid = r3.json().get('session_id')
        print('Session ID:', sid)
        
        r4 = await client.get(f'http://localhost:8000/api/chat/sessions/{sid}', headers={'Authorization': 'Bearer ' + token})
        print('Get Session:', r4.status_code, r4.text)

asyncio.run(main())
