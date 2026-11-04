from pathlib import Path
q=sorted((Path(__file__).resolve().parents[1]/"episodes/queue").glob("ep*.json"))
print(q[0].as_posix() if q else "NO_EPISODES")
