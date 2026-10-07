from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session
import time

from app.infrastructure.database import get_db
from app.domain.executions.models import ExecutionModel, ExecutionStatus

router = APIRouter(prefix="/executions", tags=["executions"])


class CreateExecutionRequest(BaseModel):
    type: str
    input_data: Dict[str, Any]


class ExecutionResponse(BaseModel):
    id: str
    type: str
    status: str
    input_data: Dict[str, Any]
    result_data: Dict[str, Any] | None


def simulate_dag_execution(execution_id: str):
    """Background task to simulate the DAG running."""
    # Note: In a real system, this would be picked up by the Worker Engine via Redis Streams
    time.sleep(2)
    # The actual execution happens here (mocked for now, will link to MLflow next)


@router.post("", response_model=ExecutionResponse, status_code=201)
def create_execution(
    request: CreateExecutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    # 1. Initialize execution in QUEUED state
    db_exec = ExecutionModel(
        type=request.type,
        input_data=request.input_data,
        status=ExecutionStatus.QUEUED.value,
    )
    db.add(db_exec)
    db.commit()
    db.refresh(db_exec)

    # 2. Trigger background execution simulation
    background_tasks.add_task(simulate_dag_execution, db_exec.id)

    return ExecutionResponse(
        id=db_exec.id,
        type=db_exec.type,
        status=db_exec.status,
        input_data=db_exec.input_data,
        result_data=db_exec.result_data,
    )


@router.get("/{execution_id}", response_model=ExecutionResponse)
def get_execution(execution_id: str, db: Session = Depends(get_db)):
    db_exec = db.query(ExecutionModel).filter(ExecutionModel.id == execution_id).first()
    if not db_exec:
        raise HTTPException(status_code=404, detail="Execution not found")

    return ExecutionResponse(
        id=db_exec.id,
        type=db_exec.type,
        status=db_exec.status,
        input_data=db_exec.input_data,
        result_data=db_exec.result_data,
    )
