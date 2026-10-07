from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.domain.entities import Dataset
from app.infrastructure.database import get_db
from app.infrastructure.models import DatasetModel

router = APIRouter(prefix="/datasets", tags=["datasets"])


class CreateDatasetRequest(BaseModel):
    namespace: str
    name: str
    owner: str
    metadata: Dict[str, Any] = {}


class DatasetResponse(BaseModel):
    id: str
    namespace: str
    name: str
    owner: str
    state: str
    metadata: Dict[str, Any]


@router.post("", response_model=DatasetResponse, status_code=201)
def create_dataset(request: CreateDatasetRequest, db: Session = Depends(get_db)):
    try:
        # Create domain entity
        dataset = Dataset.create(
            namespace=request.namespace,
            name=request.name,
            owner=request.owner,
            metadata=request.metadata,
        )

        # Map to ORM model
        db_dataset = DatasetModel(
            id=str(dataset.id),
            namespace=dataset.namespace,
            name=dataset.name,
            owner=dataset.owner,
            state=dataset.state,
            metadata_json=dataset.metadata,
        )

        db.add(db_dataset)
        db.commit()
        db.refresh(db_dataset)

        return DatasetResponse(
            id=db_dataset.id,
            namespace=db_dataset.namespace,
            name=db_dataset.name,
            owner=db_dataset.owner,
            state=db_dataset.state,
            metadata=db_dataset.metadata_json,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[DatasetResponse])
def list_datasets(namespace: str = None, db: Session = Depends(get_db)):
    query = db.query(DatasetModel)
    if namespace:
        query = query.filter(DatasetModel.namespace == namespace)

    datasets = query.all()
    return [
        DatasetResponse(
            id=d.id,
            namespace=d.namespace,
            name=d.name,
            owner=d.owner,
            state=d.state,
            metadata=d.metadata_json,
        )
        for d in datasets
    ]
