from surrealdb import Surreal

async def main(data, dbname):
    """Example of how to use the SurrealDB client."""
    print('dbname:', dbname)
    async with Surreal("ws://localhost:8000/rpc") as db:
        await db.signin({"user": "admin", "pass": "password"})
        await db.use(dbname, dbname)
        await db.select(dbname)
        # await db.create(
        #     dbname,
        #     data,
        # )
        # print(await db.delete(dbname))
        await db.update(dbname, data)
        
        # In SurrealQL you can do a direct insert and the table will be created if it doesn't exist
        
        # print("this is SurrealDB!\n", data[0],data[1],data[2], type(data[3]))
        # await db.query("""
        # insert into student {
        #     user: %s,
        #     class: %s,
        #     attendance: %s,
        #     img: %s
        #  };         
        # """ %(data[0],data[1],data[2],data[3])
        # )
        # print(await db.query("select * from "+dbname))
        # print(await db.query("delete student"))
