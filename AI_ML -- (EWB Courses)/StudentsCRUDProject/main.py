
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
from schemas import StudentCreate, StudentUpdate, StudentResponse


# Create tables if they do not already exist.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Students Database CRUD API",
    description="Student records management using FastAPI and SQLite",
    version="1.0.0",
)


@app.get("/")
def home():
    return {
        "message": "Students CRUD API is running!",
        "docs": "/docs",
    }


# CREATE: Add a student.
@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
):
    new_student = models.Student(**student_data.model_dump())
    db.add(new_student)

    try:
        db.commit()
        db.refresh(new_student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email already exists.",
        )

    return new_student


# READ: List students, with optional filters.
@app.get("/students", response_model=list[StudentResponse])
def list_students(
    name: str | None = None,
    course: str | None = None,
    born_before: date | None = None,
    db: Session = Depends(get_db),
):
    statement = select(models.Student)

    if name and name.strip():
        statement = statement.where(
            models.Student.name.ilike(f"%{name.strip()}%")
        )

    if course and course.strip():
        statement = statement.where(
            models.Student.course.ilike(f"%{course.strip()}%")
        )

    if born_before:
        statement = statement.where(
            models.Student.date_of_birth < born_before
        )

    statement = statement.order_by(models.Student.id)
    return list(db.scalars(statement).all())


# READ: Get one student by ID.
@app.get("/students/{student_id}", response_model=StudentResponse)
def get_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = db.get(models.Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    return student


# UPDATE: Change only the fields supplied by the client.
@app.patch("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    updates: StudentUpdate,
    db: Session = Depends(get_db),
):
    student = db.get(models.Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    changes = updates.model_dump(exclude_unset=True)

    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide at least one field to update.",
        )

    for field in ("name", "date_of_birth"):
        if field in changes and changes[field] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null.",
            )

    for field, value in changes.items():
        setattr(student, field, value)

    try:
        db.commit()
        db.refresh(student)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A student with this email already exists.",
        )

    return student


# DELETE: Remove a student by ID.
@app.delete(
    "/students/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
):
    student = db.get(models.Student, student_id)

    if student is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found",
        )

    db.delete(student)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
