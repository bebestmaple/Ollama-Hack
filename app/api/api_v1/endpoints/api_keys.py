from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import crud_api_key
from app.db.database import get_db
from app.schemas.schemas import ApiKey, ApiKeyCreate

router = APIRouter()


@router.post("/", response_model=ApiKey)
def create_api_key(api_key: ApiKeyCreate, db: Session = Depends(get_db)):
    return crud_api_key.create_api_key(db, api_key)


@router.get("/", response_model=List[ApiKey])
def read_api_keys(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    api_keys = crud_api_key.get_api_keys(db, skip=skip, limit=limit)
    return api_keys


@router.get("/{api_key_id}", response_model=ApiKey)
def read_api_key(api_key_id: int, db: Session = Depends(get_db)):
    db_api_key = crud_api_key.get_api_key_by_id(db, api_key_id)
    if db_api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    return db_api_key


@router.delete("/{api_key_id}")
def delete_api_key(api_key_id: int, db: Session = Depends(get_db)):
    success = crud_api_key.delete_api_key(db, api_key_id)
    if not success:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"detail": "API key deleted successfully"}


@router.put("/{api_key_id}/deactivate")
def deactivate_api_key(api_key_id: int, db: Session = Depends(get_db)):
    db_api_key = crud_api_key.deactivate_api_key(db, api_key_id)
    if db_api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    return {"detail": "API key deactivated successfully"}
