import os
import time
from datetime import datetime
from pathlib import Path
from uuid import UUID

import psycopg2
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
from rich import print as rprint

app = FastAPI()


class Post(BaseModel):
    id: UUID | None = None
    title: str
    content: str
    published: bool = True
    created_at: datetime | None = None


# --- Database connection ---

load_dotenv(Path("__file__").parent.parent.parent / ".db-env" / "postgres.env")

IS_RUNNING_IN_DOCKER = Path("/.dockerenv").exists()

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = "postgresdb" if IS_RUNNING_IN_DOCKER else "localhost"

while True:
    try:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            cursor_factory=RealDictCursor,  # to have columns' names
        )
        cursor = conn.cursor()
        rprint(":heavy_check_mark: [green]Database connection was successful[/green]")
        break
    except Exception as error:
        rprint(":no_entry_sign: [red]Connection to database failed[/red]")
        rprint(error)
        time.sleep(2)


@app.get("/posts/{post_id}")
async def get_post(post_id: UUID) -> dict:
    cursor.execute("""SELECT * FROM posts WHERE id = %s""", (str(post_id),))
    post = cursor.fetchone()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    return {"data": Post(**post)}


@app.get("/posts")
async def get_posts() -> dict:
    cursor.execute("""SELECT * FROM posts""")
    posts = cursor.fetchall()
    return {"data": posts}


@app.post("/posts", status_code=status.HTTP_201_CREATED)
async def create_post(post: Post) -> dict:
    cursor.execute(
        """INSERT INTO posts (title, content, published) VALUES (%s, %s, %s) RETURNING *""",
        (post.title, post.content, post.published),
    )
    new_post = cursor.fetchone()
    conn.commit()
    return {"message": "post added successfully", "data": new_post}


@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: UUID) -> None:
    cursor.execute("""DELETE FROM posts WHERE id = %s RETURNING *""", (str(post_id),))
    deleted_post = cursor.fetchone()
    conn.commit()
    if not deleted_post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.put("/posts/{post_id}")
async def update_post(post_id: UUID, post: Post) -> dict:
    cursor.execute(
        """UPDATE posts SET title = %s, content = %s, published = %s WHERE id = %s RETURNING *""",
        (post.title, post.content, post.published, str(post_id)),
    )
    updated_post = cursor.fetchone()
    conn.commit()
    if updated_post:
        return {"data": updated_post}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
