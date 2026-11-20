import sys
sys.path.append(".")
import asyncio
from app.database.mongodb import connect_to_mongo
from app.services.auth_service import seed_demo_users, login_user

async def main():
    await connect_to_mongo()
    await seed_demo_users()
    res = await login_user("student@crowdmic.com", "password123")
    print("SUCCESS LOGGED IN:", res["user"])

if __name__ == "__main__":
    asyncio.run(main())
