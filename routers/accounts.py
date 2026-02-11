from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Account
from schemas import AccountUpdate, AccountOut

router = APIRouter(prefix="/v1/account", tags=["account"])


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

