from fastapi import Depends, FastAPI, HTTPException, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import engine, get_db
from app.models import Base, HuntLog, WantedCriminal
from app.schemas import CriminalOut, HuntCreate, HuntOut, HuntUpdate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Space Bounty Hunters")


def _get_criminal_or_404(db: Session, criminal_id: int) -> WantedCriminal:
    criminal = db.get(WantedCriminal, criminal_id)
    if criminal is None:
        raise HTTPException(status_code=404, detail="Criminal not found")
    return criminal


def _get_hunt_or_404(db: Session, hunt_id: int) -> HuntLog:
    hunt = db.get(HuntLog, hunt_id)
    if hunt is None:
        raise HTTPException(status_code=404, detail="Hunt log not found")
    return hunt


@app.get("/api/criminals/", response_model=list[CriminalOut])
def list_criminals(
    min_reward: float | None = None,
    max_reward: float | None = None,
    armed: bool | None = None,
    has_crew: bool | None = None,
    escape_master: bool | None = None,
    sort: str | None = None,
    db: Session = Depends(get_db),
):
    if sort is not None and sort not in {"reward", "-reward"}:
        raise HTTPException(status_code=422, detail="sort must be 'reward' or '-reward'")

    query = select(WantedCriminal)
    if min_reward is not None:
        query = query.where(WantedCriminal.reward >= min_reward)
    if max_reward is not None:
        query = query.where(WantedCriminal.reward <= max_reward)
    if armed is not None:
        query = query.where(WantedCriminal.armed == armed)
    if has_crew is not None:
        query = query.where(WantedCriminal.has_crew == has_crew)
    if escape_master is not None:
        query = query.where(WantedCriminal.escape_master == escape_master)

    if sort == "reward":
        query = query.order_by(WantedCriminal.reward.asc(), WantedCriminal.id.asc())
    elif sort == "-reward":
        query = query.order_by(WantedCriminal.reward.desc(), WantedCriminal.id.asc())
    else:
        query = query.order_by(WantedCriminal.id.asc())

    return db.scalars(query).all()


@app.get("/api/criminals/{criminal_id}/", response_model=CriminalOut)
def get_criminal(criminal_id: int, db: Session = Depends(get_db)):
    return _get_criminal_or_404(db, criminal_id)


@app.get("/api/hunts/", response_model=list[HuntOut])
def list_hunts(
    criminal_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = select(HuntLog).order_by(HuntLog.id.asc())
    if criminal_id is not None:
        query = query.where(HuntLog.criminal_id == criminal_id)
    return db.scalars(query).all()


@app.get("/api/hunts/{hunt_id}/", response_model=HuntOut)
def get_hunt(hunt_id: int, db: Session = Depends(get_db)):
    return _get_hunt_or_404(db, hunt_id)


@app.post("/api/hunts/", response_model=HuntOut, status_code=201)
def create_hunt(payload: HuntCreate, db: Session = Depends(get_db)):
    _get_criminal_or_404(db, payload.criminal_id)
    hunt = HuntLog(
        criminal_id=payload.criminal_id,
        success=payload.success,
        notes=payload.notes,
    )
    db.add(hunt)
    db.commit()
    db.refresh(hunt)
    return hunt


@app.patch("/api/hunts/{hunt_id}/", response_model=HuntOut)
def update_hunt(hunt_id: int, payload: HuntUpdate, db: Session = Depends(get_db)):
    hunt = _get_hunt_or_404(db, hunt_id)
    updates = payload.model_dump(exclude_unset=True)
    if "success" in updates and updates["success"] is None:
        raise HTTPException(status_code=422, detail="success cannot be null")
    if "notes" in updates and updates["notes"] is None:
        raise HTTPException(status_code=422, detail="notes cannot be null")
    if not updates:
        raise HTTPException(status_code=400, detail="Provide success or notes to update")
    if "success" in updates:
        hunt.success = updates["success"]
    if "notes" in updates:
        hunt.notes = updates["notes"]
    db.commit()
    db.refresh(hunt)
    return hunt


@app.delete("/api/hunts/{hunt_id}/", status_code=204)
def delete_hunt(hunt_id: int, db: Session = Depends(get_db)):
    hunt = _get_hunt_or_404(db, hunt_id)
    db.delete(hunt)
    db.commit()
    return Response(status_code=204)
