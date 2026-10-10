from pathlib import Path
from sqlmodel import SQLModel, create_engine, Session, select
from infrastructure.db.models import SystemConfig

# Place app.db inside infrastructure/db/
DB_DIR = Path(__file__).resolve().parent
DB_PATH = DB_DIR / "app.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

def init_db():
    """
    Creates tables if they don't exist and seeds default SystemConfig record.
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)
    SQLModel.metadata.create_all(engine)
    
    # Ensure default system config row exists
    with Session(engine) as session:
        config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
        if not config:
            default_config = SystemConfig(id=1)
            session.add(default_config)
            session.commit()
            print(f"[SQLite DB] Initialized default configuration at '{DB_PATH}'")

def get_session():
    """
    FastAPI dependency that provides a database session per request.
    """
    with Session(engine) as session:
        yield session