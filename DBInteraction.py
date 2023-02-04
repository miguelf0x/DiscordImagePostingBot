import aiosqlite
import os


import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Main")
logger.setLevel(level=logging.DEBUG)
def logged(func):
    def inner(function: func, *args, **kwags):
        logger.info(f"Function {func.__name__} called with:\n"
                    f"args = {args}, kwargs = {kwags}")
        return func(function, *args, **kwags)


    inner.__name__ = func.__name__
    return inner


class Database(object):
    db_con = None

    def __init__(self, db_path: str):
        if not self.db_con:
            if os.path.exists(db_path):
                self.db_con = aiosqlite.connect(db_path)
            else:
                trimmed_path = db_path.rsplit("/", 1)[0]
                os.makedirs(trimmed_path)
                with open(db_path, 'w') as file:
                    file.write("")
                file.close()
                self.db_con = aiosqlite.connect(db_path)

    async def query(self, sql):
        db_cur = await Database.db_con.cursor()
        await db_cur.execute(sql)
        result = await db_cur.fetchone()
        await db_cur.commit()
        return result


@logged
async def create_db_structure(db: Database):
    await db.query(
        "CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, post_id INTEGER, user_id INTEGER, action INTEGER DEFAULT 0)"
    )


@logged
async def create_db_record(db: Database, post_id, user_id, action):
    INSERT_QUERY = f"INSERT INTO posts(post_id, user_id, action) VALUES({post_id}, {user_id}, {action})"
    REMOVE_QUERY = f"DELETE FROM posts WHERE post_id == {post_id} AND user_id == {user_id} AND action == {action}"
    CHECK_QUERY = f"SELECT * FROM posts WHERE post_id == {post_id} AND user_id == {user_id} AND action == {action}"

    check = await db.query(CHECK_QUERY)
    if check[0] is None:
        await db.query(INSERT_QUERY)
    else:
        await db.query(REMOVE_QUERY)


@logged
async def get_image_score(db: Database, post_id) -> list:

    upvotes_t = await db.query(
        f"SELECT SUM(action) FROM posts WHERE post_id == {post_id} AND action > 0"
    )

    if upvotes_t[0] is None:
        upvotes = 0
    else:
        upvotes = int(upvotes_t[0])

    dnvotes_t = await db.query(
        f"SELECT SUM(action) FROM posts WHERE post_id == {post_id} AND action < 0 AND action > -1000"
    )

    if dnvotes_t[0] is None:
        dnvotes = 0
    else:
        dnvotes = int(dnvotes_t[0])

    rmvotes_t = await db.query(
        f"SELECT SUM(action) FROM posts WHERE post_id == {post_id} AND action == -1000"
    )

    if rmvotes_t[0] is None:
        rmvotes = 0
    else:
        rmvotes = int(rmvotes_t[0])

    return [upvotes, abs(dnvotes), rmvotes / -1000]


@logged
async def get_last_image_index(db: Database):
    base_returned = await db.query("SELECT MAX(post_id) FROM posts")
    if base_returned[0] is None:
        last_image_index = 0
    else:
        last_image_index = int(base_returned[0])
    print("last_image_index type is " + str(type(last_image_index)))
    print("last_image_index value is " + str(last_image_index))

    return last_image_index
