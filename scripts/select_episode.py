import os
from pathlib import Path
root=Path(__file__).resolve().parents[1]
requested=os.getenv("EPISODE_ID","").strip()
if requested:
    if not requested.startswith("ep") or not requested[2:].isdigit():
        raise SystemExit("EPISODE_ID inválido; usa ep001")
    for folder in ("done","queue"):
        candidate=root/"episodes"/folder/f"{requested}.json"
        if candidate.exists():
            print(candidate.as_posix()); break
    else: raise SystemExit(f"No existe {requested} en queue ni done")
else:
    q=sorted((root/"episodes/queue").glob("ep*.json"))
    print(q[0].as_posix() if q else "NO_EPISODES")
