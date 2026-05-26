import shutil
from datetime import datetime
from pathlib import Path


def fazer_backup():
    db = Path("solar.db")
    if not db.exists():
        print("solar.db ainda não existe — backup ignorado.")
        return

    pasta = Path("backups")
    pasta.mkdir(exist_ok=True)

    ts   = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = pasta / f"solar_{ts}.db"
    shutil.copy2(db, dest)
    print(f"Backup criado: {dest.name}")

    # Mantém só os 30 mais recentes
    todos = sorted(pasta.glob("solar_*.db"))
    for antigo in todos[:-30]:
        antigo.unlink()
        print(f"Backup antigo removido: {antigo.name}")


if __name__ == "__main__":
    fazer_backup()
