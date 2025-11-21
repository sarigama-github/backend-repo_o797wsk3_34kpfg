"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogpost" collection
"""

from pydantic import BaseModel, Field
from typing import Optional, List

class Task(BaseModel):
    """
    Embedded task schema for a routine
    """
    id: str = Field(..., description="Client-generated id for the task")
    name: str = Field(..., description="Task title or description")
    time: Optional[str] = Field(None, description="Optional time like 06:30")
    completed: bool = Field(False, description="Completion status")

class Routine(BaseModel):
    """
    Morning routines collection schema
    Collection name: "routine"
    """
    client_id: str = Field(..., description="Anonymous client identifier for grouping routines")
    title: str = Field(..., description="Routine name")
    wake_time: Optional[str] = Field(None, description="Daily wake time like 06:00")
    reminders_enabled: bool = Field(True, description="Whether local reminders should be enabled")
    days: List[str] = Field(default_factory=lambda: ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], description="Days of week the routine applies")
    tasks: List[Task] = Field(default_factory=list, description="List of tasks in the routine")
