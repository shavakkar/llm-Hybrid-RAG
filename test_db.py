from infrastructure.db.session import init_db, get_session
from infrastructure.db.models import SystemConfig
from sqlmodel import select

if __name__ == "__main__":
    init_db()
    
    # Read back seeded configuration
    for session in get_session():
        config = session.exec(select(SystemConfig).where(SystemConfig.id == 1)).first()
        print("✅ DB Setup Success!")
        print(f"• Active Provider   : {config.provider}")
        print(f"• Active Embedder   : {config.selected_embed_model}")
        print(f"• Active Generator  : {config.selected_llm_model}")