from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.registry import ModelRegistry
from app.schemas.models import ModelResponse
from app.services.model_registry import seed_registry

router = APIRouter(prefix="/api/v1/models", tags=["models"])


@router.get("", response_model=list[ModelResponse])
def list_models(db: Session = Depends(get_db)) -> list[ModelResponse]:
    seed_registry(db)
    return [
        ModelResponse.model_validate(model, from_attributes=True)
        for model in db.scalars(
            select(ModelRegistry)
            .where(ModelRegistry.status == "available")
            .order_by(ModelRegistry.display_name)
        ).all()
    ]
