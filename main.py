from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models import Pereval, User, Coord, Level, Images
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uvicorn

app = FastAPI(title="Pereval API Sprint 2")


# Pydantic модели
class CoordinateSchema(BaseModel):
    latitude: float
    longitude: float


class LevelSchema(BaseModel):
    winter: Optional[str] = None
    summer: Optional[str] = None
    autumn: Optional[str] = None
    spring: Optional[str] = None


class UserSchema(BaseModel):
    email: str
    phone: str
    fam: str
    name: str
    otc: Optional[str] = None


class ImageSchema(BaseModel):
    data: str
    title: str


class PerevalCreate(BaseModel):
    beauty_title: str
    title: str
    other_titles: Optional[str] = None
    connect: Optional[str] = None
    add_time: datetime
    user: UserSchema
    coords: CoordinateSchema
    level: LevelSchema
    images: Optional[List[ImageSchema]] = []


class PerevalUpdate(BaseModel):
    beauty_title: Optional[str] = None
    title: Optional[str] = None
    other_titles: Optional[str] = None
    connect: Optional[str] = None
    coords: Optional[CoordinateSchema] = None
    level: Optional[LevelSchema] = None
    images: Optional[List[ImageSchema]] = None


# 1. POST /submitData
@app.post("/submitData")
def add_pereval(data: PerevalCreate, db: Session = Depends(get_db)):
    existing = db.query(Pereval).join(User).filter(
        User.email == data.user.email,
        Pereval.beauty_title == data.beauty_title,
        Pereval.title == data.title
    ).first()

    if existing:
        return {"status": 500, "message": "Duplicate entry", "id": None}

    user = db.query(User).filter(User.email == data.user.email).first()
    if not user:
        user = User(
            email=data.user.email,
            phone=data.user.phone,
            fam=data.user.fam,
            name=data.user.name,
            otc=data.user.otc
        )
        db.add(user)
        db.flush()

    coords = Coord(latitude=data.coords.latitude, longitude=data.coords.longitude)
    db.add(coords)
    db.flush()

    levels = Level(
        winter=data.level.winter,
        summer=data.level.summer,
        autumn=data.level.autumn,
        spring=data.level.spring
    )
    db.add(levels)
    db.flush()

    pereval = Pereval(
        beauty_title=data.beauty_title,
        title=data.title,
        other_titles=data.other_titles,
        connect=data.connect,
        add_time=data.add_time,
        user_id=user.id,
        coord_id=coords.id,
        level_id=levels.id,
        status='new'
    )
    db.add(pereval)
    db.flush()

    for img in data.images or []:
        image = Images(pereval_id=pereval.id, data=img.data, title=img.title)
        db.add(image)

    db.commit()
    return {"status": 200, "message": "Success", "id": pereval.id}


# 2. GET /submitData/{id}
@app.get("/submitData/{pereval_id}")
def get_pereval(pereval_id: int, db: Session = Depends(get_db)):
    pereval = db.query(Pereval).filter(Pereval.id == pereval_id).first()
    if not pereval:
        raise HTTPException(status_code=404, detail="Pereval not found")

    user = db.query(User).filter(User.id == pereval.user_id).first()
    coords = db.query(Coord).filter(Coord.id == pereval.coord_id).first()
    level = db.query(Level).filter(Level.id == pereval.level_id).first()
    images = db.query(Images).filter(Images.pereval_id == pereval.id).all()

    return {
        "id": pereval.id,
        "beauty_title": pereval.beauty_title,
        "title": pereval.title,
        "other_titles": pereval.other_titles,
        "connect": pereval.connect,
        "add_time": pereval.add_time,
        "status": pereval.status,
        "user": {
            "email": user.email,
            "phone": user.phone,
            "fam": user.fam,
            "name": user.name,
            "otc": user.otc
        },
        "coords": {"latitude": coords.latitude, "longitude": coords.longitude},
        "level": {
            "winter": level.winter,
            "summer": level.summer,
            "autumn": level.autumn,
            "spring": level.spring
        },
        "images": [{"id": img.id, "title": img.title, "data": img.data} for img in images]
    }


# 3. PATCH /submitData/{id}
@app.patch("/submitData/{pereval_id}")
def update_pereval(pereval_id: int, update_data: PerevalUpdate, db: Session = Depends(get_db)):
    pereval = db.query(Pereval).filter(Pereval.id == pereval_id).first()
    if not pereval:
        return {"state": 0, "message": "Запись не найдена"}
    if pereval.status != 'new':
        return {"state": 0, "message": f"Нельзя редактировать, статус = {pereval.status}"}

    if update_data.beauty_title is not None:
        pereval.beauty_title = update_data.beauty_title
    if update_data.title is not None:
        pereval.title = update_data.title
    if update_data.other_titles is not None:
        pereval.other_titles = update_data.other_titles
    if update_data.connect is not None:
        pereval.connect = update_data.connect

    if update_data.coords:
        coords = db.query(Coord).filter(Coord.id == pereval.coord_id).first()
        if coords:
            coords.latitude = update_data.coords.latitude
            coords.longitude = update_data.coords.longitude

    if update_data.level:
        level = db.query(Level).filter(Level.id == pereval.level_id).first()
        if level:
            level.winter = update_data.level.winter
            level.summer = update_data.level.summer
            level.autumn = update_data.level.autumn
            level.spring = update_data.level.spring

    if update_data.images is not None:
        db.query(Images).filter(Images.pereval_id == pereval_id).delete()
        for img in update_data.images:
            new_image = Images(pereval_id=pereval_id, data=img.data, title=img.title)
            db.add(new_image)

    db.commit()
    return {"state": 1, "message": "Запись успешно обновлена"}


# 4. GET /submitData?user_email=...
@app.get("/submitData")
def get_user_perevals(
        user_email: str = Query(..., description="Email пользователя"),
        db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        return []
    perevals = db.query(Pereval).filter(Pereval.user_id == user.id).all()
    return [
        {
            "id": p.id,
            "beauty_title": p.beauty_title,
            "title": p.title,
            "other_titles": p.other_titles,
            "connect": p.connect,
            "add_time": p.add_time,
            "status": p.status
        }
        for p in perevals
    ]


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)