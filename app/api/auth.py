# app/api/auth.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel
from app.core.database import get_connection
from app.core.auth import hash_password, verify_password, create_access_token, get_current_user
from app.services.gmail_services import GmailService


router = APIRouter(tags=["Auth"], prefix="/auth")


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str



def _send_registration_email(to_email: str, full_name: str):
    try:
        gmail = GmailService()
        subject = "Registration Successful – Welcome!"
        body = f"""
Hello {full_name},

Your account has been successfully created.

You can now log in using your registered email.

Regards,
Team
"""
        gmail.send_email(to_email=to_email, subject=subject, message_text=body)
    except Exception as e:
        # Log the exception to stdout or your logger
        print("Failed to send registration email (background):", e)


@router.post('/register')
async def register(req: RegisterRequest, background_tasks: BackgroundTasks):
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail='DB connection failed')
    cursor = conn.cursor()
    # check exists
    cursor.execute('SELECT id FROM users WHERE email = %s', (req.email,))
    if cursor.fetchone():
        cursor.close(); conn.close()
        raise HTTPException(status_code=400, detail='User already exists')

    pwd_hash = hash_password(req.password)
    cursor.execute(
        'INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)',
        (req.email, pwd_hash, req.full_name)
    )
    conn.commit()
    user_id = cursor.lastrowid
    cursor.close(); conn.close()

    # schedule email to be sent after response is returned
    background_tasks.add_task(_send_registration_email, req.email, req.full_name)

    token = create_access_token({"user_id": user_id, "email": req.email})
    return {"access_token": token, "token_type": "bearer", "email_queued": True}
# @router.post('/register')
# async def register(req: RegisterRequest):
#     conn = get_connection()
#     if conn is None:
#         raise HTTPException(status_code=500, detail='DB connection failed')
#     cursor = conn.cursor()
#     # check exists
#     cursor.execute('SELECT id FROM users WHERE email = %s', (req.email,))
#     if cursor.fetchone():
#         cursor.close(); conn.close()
#         raise HTTPException(status_code=400, detail='User already exists')


#     pwd_hash = hash_password(req.password)
#     cursor.execute('INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s)',
#     (req.email, pwd_hash, req.full_name))
#     conn.commit()
#     user_id = cursor.lastrowid
#     cursor.close(); conn.close()


#     token = create_access_token({"user_id": user_id, "email": req.email})
#     return {"access_token": token, "token_type": "bearer"}




@router.post('/login')
async def login(req: LoginRequest):
    conn = get_connection()
    if conn is None:
        raise HTTPException(status_code=500, detail='DB connection failed')
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT id, password_hash FROM users WHERE email = %s', (req.email,))
    row = cursor.fetchone()
    cursor.close(); conn.close()
    if not row:
        raise HTTPException(status_code=401, detail='Invalid credentials')


    if not verify_password(req.password, row['password_hash']):
        raise HTTPException(status_code=401, detail='Invalid credentials')


    token = create_access_token({"user_id": row['id'], "email": req.email})
    return {"access_token": token, "token_type": "bearer"}




@router.get('/me')
async def me(user=Depends(get_current_user)):
# returns basic user info
    return {"id": user['id'], "email": user['email'], "full_name": user.get('full_name'), "role": user.get('role')}




@router.post('/logout')
async def logout():
# Stateless JWT: logout on client side by deleting token. If you need server invalidation,
    return {"message": "Logged out"} 