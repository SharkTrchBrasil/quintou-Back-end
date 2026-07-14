from pydantic import BaseModel

class DashboardStats(BaseModel):
    total_users: int
    total_spaces: int
    total_bookings: int
    pending_spaces: int
    open_reports: int
    total_revenue_platform: float
