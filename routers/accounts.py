from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session
from database import get_db
from models import Account
from schemas import AccountUpdate, AccountOut, LoginRequest, TokenOut
from auth import verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/v1/account", tags=["account"])


# ─── Auth endpoints ───

@router.post("/login", response_model=TokenOut)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.email == body.email).first()
    if not account or not verify_password(body.password, account.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token({"sub": account.uid, "email": account.email})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/verify")
def verify_token(authorization: str = Header(default="")):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = authorization.split(" ", 1)[1]
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"valid": True, "uid": payload.get("sub"), "email": payload.get("email")}


# ─── Account CRUD ───

@router.get("", response_model=AccountOut)
def get_account(uid: str = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(Account)
    if uid:
        q = q.filter(Account.uid == uid)
    account = q.first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.put("", response_model=AccountOut)
def update_account(body: AccountUpdate, uid: str = Query(default=None), db: Session = Depends(get_db)):
    q = db.query(Account)
    if uid:
        q = q.filter(Account.uid == uid)
    account = q.first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(account, key, value)
    db.commit()
    db.refresh(account)
    return account

