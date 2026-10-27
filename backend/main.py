
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from backend.database import get_connection
from psycopg import sql
from agents.supervisor import run_supervisor


app = FastAPI(
    title="AI Task Manager API",
    description="Backend API for an AI-powered task management application.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.get("/tasks")
def get_tasks():
    # 1. Connect to PostgreSQL
    with get_connection() as conn:
        with conn.cursor() as cursor:

            # 2. Retrieve all tasks from the database
            cursor.execute(
                """
                SELECT id, title, description, completed, created_at, due_at
                FROM tasks
                ORDER BY id
                """
            )

            # 3. Check that column information is available
            if cursor.description is None:
                raise RuntimeError(
                    "Query returned no column information"
                )

            # 4. Get the column names
            columns = [
                column.name for column in cursor.description
            ]

            # 5. Retrieve all database rows
            rows = cursor.fetchall()

            # 6. Convert each row into a dictionary
            tasks_from_db = [
                dict(zip(columns, row))
                for row in rows
            ]

            # 7. Return the tasks as JSON
            return {"tasks": tasks_from_db}



@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-task-manager-backend",
    }


from pydantic import BaseModel

class TaskCreate(BaseModel):
    title: str
    description: str = ""


@app.post("/tasks", status_code=201)
def create_task(task: TaskCreate):
    # 1. Connect to PostgreSQL
    with get_connection() as conn:
        with conn.cursor() as cursor:

            # 2. Insert the new task into the database
            cursor.execute(
                """
                INSERT INTO tasks (title, description)
                VALUES (%s, %s)
                RETURNING id, title, description, completed, created_at
                """,
                (task.title, task.description)
            )

            # 3. Retrieve the inserted task
            row = cursor.fetchone()

            # 4. Check that PostgreSQL returned a row
            if row is None:
                raise RuntimeError(
                    "Database did not return the created task"
                )

            # 5. Check that column information is available
            if cursor.description is None:
                raise RuntimeError(
                    "Query returned no column information"
                )

            # 6. Get the column names
            columns = [
                column.name for column in cursor.description
            ]

            # 7. Convert the row into a dictionary
            new_task = dict(zip(columns, row))

            return new_task


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    completed: bool | None = None


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, updates: TaskUpdate):
    # 1. Get only the fields provided by the user
    changes = updates.model_dump(exclude_unset=True)

    # 2. Reject empty update requests
    if not changes:
        raise HTTPException(
            status_code=400,
            detail="No fields provided for update"
        )

    # 3. Validate the fields and their values
    allowed_fields = {"title", "description", "completed"}

    if any(
        field not in allowed_fields or value is None
        for field, value in changes.items()
    ):
        raise HTTPException(
            status_code=422,
            detail="Invalid task update"
        )

    # 4. Build the SQL SET clause safely
    set_clause = sql.SQL(", ").join(
        sql.SQL("{} = %s").format(sql.Identifier(field))
        for field in changes
    )

    # 5. Build the complete UPDATE query
    query = sql.SQL("""
        UPDATE tasks
        SET {}
        WHERE id = %s
        RETURNING id, title, description, completed, created_at
    """).format(set_clause)

    # 6. Prepare the parameter values
    values = list(changes.values())
    values.append(task_id)

    # 7. Connect to PostgreSQL and execute the query
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, values)

            row = cursor.fetchone()

            # 8. Handle a task that does not exist
            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found"
                )

            # 9. Verify that column information exists
            if cursor.description is None:
                raise RuntimeError(
                    "Query returned no column information"
                )

            # 10. Convert the database result into a dictionary
            columns = [
                column.name for column in cursor.description
            ]

            updated_task = dict(zip(columns, row))

            return updated_task




@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    # 1. Connect to PostgreSQL
    with get_connection() as conn:
        with conn.cursor() as cursor:

            # 2. Delete the task and return its information
            cursor.execute(
                """
                DELETE FROM tasks
                WHERE id = %s
                RETURNING id, title, description, completed, created_at
                """,
                (task_id,)
            )

            # 3. Retrieve the deleted task
            row = cursor.fetchone()

            # 4. Handle a task that does not exist
            if row is None:
                raise HTTPException(
                    status_code=404,
                    detail="Task not found"
                )

            # 5. Check that column information is available
            if cursor.description is None:
                raise RuntimeError(
                    "Query returned no column information"
                )

            # 6. Get the column names
            columns = [
                column.name for column in cursor.description
            ]

            # 7. Convert the deleted task into a dictionary
            deleted_task = dict(zip(columns, row))

            # 8. Return the result
            return {
                "message": "Task deleted successfully",
                "deleted_task": deleted_task
            }


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    answer = run_supervisor(request.message)

    return ChatResponse(response=answer)
