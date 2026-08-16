from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.salary import SalarySnapshotOut
from app.services.salary_service import COMMON_LOCATIONS, COMMON_ROLES, get_salary_insights

router = APIRouter(prefix="/salary", tags=["salary"])


@router.get("", response_model=list[SalarySnapshotOut])
async def salary_insights(
    role: str = Query(..., description="Role title, e.g. 'Software Engineer'"),
    location: str = Query("", description="Location, e.g. 'United States' or 'Remote'"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await get_salary_insights(db, role, location)


@router.get("/suggestions")
async def salary_suggestions(_user: User = Depends(get_current_user)):
    """Curated role/location options the nightly refresh keeps warm - lets
    the frontend offer a fast-loading picker instead of a blank search box.
    """
    return {"roles": COMMON_ROLES, "locations": COMMON_LOCATIONS}
