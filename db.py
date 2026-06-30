import asyncio
from typing import List
from sqlalchemy import ForeignKey, select, String, Boolean, exists, delete, BigInteger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, create_async_engine, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, selectinload, relationship
import uuid

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"

    id : Mapped[int] = mapped_column(primary_key=True)
    userid : Mapped[int] = mapped_column(BigInteger)
    msg_id : Mapped[str | None] = mapped_column(nullable=True)

    tasks : Mapped[List["Task"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "task"
    id : Mapped[int] = mapped_column(primary_key=True)
    title : Mapped[str] = mapped_column()
    zid : Mapped[str] = mapped_column()
    userid : Mapped[int] = mapped_column(ForeignKey("user.id"))
    user : Mapped[User] = relationship(back_populates="tasks")


class DB():
    def __init__(self, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB):
        self.DATABASE = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@db:5432/{POSTGRES_DB}"
        self.engine = create_async_engine(self.DATABASE)
        self.session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def check_user(self, uid : int):
        async with self.session() as session:
            stmt = select(User).where(User.userid == uid)
            usr = await session.scalar(stmt)
            if not usr:
                return False
            return True

    async def add_user(self, iud : int):
        async with self.session() as session:
            cur_user = User()
            cur_user.userid = iud
            session.add(cur_user)
            await session.commit()

    async def add_task_for_user(self, userid : int, titl : str, idd : str):
        async with self.session() as session:
            stmt = select(User).where(User.userid == userid).options(selectinload(User.tasks))
            usr = await session.scalar(stmt)
            usr.tasks.append(Task(title=titl, zid=idd))
            await session.commit()
            print("Таска добавлена")
    
    async def delete_task(self, iud : str):
        async with self.session() as session:
            stmt = delete(Task).where(Task.zid == iud)
            await session.execute(stmt)
            await session.commit()
            print("Таска удалена")
    
    
    async def update_msg_id(self, iud : str, nw_msg_id : str):
        async with self.session() as session:
            stmt = select(User).where(User.userid == iud)
            usr = await session.scalar(stmt)
            usr.msg_id = nw_msg_id
            await session.commit()

    async def get_msg_id(self, iud : str):
        async with self.session() as session:
            stmt = select(User).where(User.userid == iud)
            usr = await session.scalar(stmt)
            return usr.msg_id

    async def get_list_of_tasks(self, userid : str):
        async with self.session() as session:
            stmt = select(User).where(User.userid == userid).options(selectinload(User.tasks))
            my_usr = await session.scalar(stmt)
            result = []
            for tsk in my_usr.tasks:
                result.append([tsk.title, tsk.zid])
            return result

    async def init_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def del_db(self):
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)