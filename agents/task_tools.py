
from backend.database import get_connection
from psycopg.rows import dict_row
from psycopg import sql


def list_tasks() -> list[dict]:
    """
    Retrieve all tasks from PostgreSQL.

    This function will become a tool that our AI agent
    can call when the user asks to see their tasks.
    """

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT id, title, description, completed, created_at
                FROM tasks
                ORDER BY id
                """
            )

            tasks = cursor.fetchall()

            return tasks


def create_task(title: str, description: str = "") -> dict:
    """
    Create a new task in PostgreSQL.

    Args:
        title: The task title.
        description: Optional additional information.

    Returns:
        The newly created task as a dictionary.
    """

    # Validate the task title
    if not title.strip():
        raise ValueError("Task title cannot be empty")

    # Connect to PostgreSQL
    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:

            # Insert the new task
            cursor.execute(
                """
                INSERT INTO tasks (title, description)
                VALUES (%s, %s)
                RETURNING id, title, description, completed, created_at
                """,
                (title, description)
            )

            # Retrieve the created record
            new_task = cursor.fetchone()

            if new_task is None:
                raise RuntimeError(
                    "Database did not return the created task"
                )

            return new_task


def update_task(
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    completed: bool | None = None,
) -> dict:
    """
    Update an existing task in PostgreSQL.

    Only fields provided by the caller will be updated.
    """

    updates = {}

    if title is not None:
        if not title.strip():
            raise ValueError("Task title cannot be empty")
        updates["title"] = title

    if description is not None:
        updates["description"] = description

    if completed is not None:
        updates["completed"] = completed

    if not updates:
        raise ValueError("No fields provided to update")

    assignments = sql.SQL(", ").join(
        sql.SQL("{} = {}").format(
            sql.Identifier(field),
            sql.Placeholder()
        )
        for field in updates
    )

    query = sql.SQL(
        """
        UPDATE tasks
        SET {}
        WHERE id = {}
        RETURNING id, title, description, completed, created_at
        """
    ).format(assignments, sql.Placeholder())

    values = list(updates.values()) + [task_id]

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(query, values)

            updated_task = cursor.fetchone()

            if updated_task is None:
                raise ValueError(
                    f"Task with ID {task_id} was not found"
                )

            return updated_task


def delete_task(task_id: int) -> dict:
    """
    Delete a task from PostgreSQL.

    Args:
        task_id: ID of the task to delete.

    Returns:
        The deleted task as a dictionary.
    """

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                DELETE FROM tasks
                WHERE id = %s
                RETURNING id, title, description, completed, created_at
                """,
                (task_id,)
            )

            deleted_task = cursor.fetchone()

            if deleted_task is None:
                raise ValueError(
                    f"Task with ID {task_id} was not found"
                )

            return deleted_task


def schedule_task(task_id: int, due_at: str) -> dict:
    """
    Set the deadline of an existing task.

    Args:
        task_id: The ID of the task to schedule.
        due_at: An ISO 8601 date and time with a UTC offset,
                such as '2026-10-30T18:00:00+01:00'.

    Returns:
        The updated task, including its deadline.
    """
    if task_id <= 0:
        raise ValueError("Task ID must be positive.")

    with get_connection() as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                UPDATE tasks
                SET due_at = %s
                WHERE id = %s
                RETURNING id, title, description,
                          completed, created_at, due_at
                """,
                (due_at, task_id),
            )

            result = cursor.fetchone()

            if result is None:
                raise ValueError(
                    f"Task {task_id} does not exist."
                )

            return result
