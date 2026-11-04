import json
from pathlib import Path
r=Path(__file__).resolve().parents[1]; q=sorted((r/"episodes/queue").glob("ep*.json"))
if not q: raise SystemExit("No hay episodios pendientes")
for p in q:
 d=json.loads(p.read_text(encoding="utf-8"))
 for k in ("titulo_pt","lugar","fondo","escenas","cierre_pt","descripcion_pt","hashtags"):
  if k not in d: raise SystemExit(f"{p}: falta {k}")
 if d["fondo"] not in {"mercado","playa","escuela","granja","cocina","parque"} or len(d["escenas"])!=4: raise SystemExit(f"{p}: fondo o número de escenas inválido")
 for s in d["escenas"]:
  if s.get("pose") not in {"neutral","feliz","sorprendido","saludando","hablando_abierta","hablando_cerrada"} or len(s.get("palabras_es",[]))!=1: raise SystemExit(f"{p}: escena inválida")
  if not all(s["palabras_es"][0].get(k) for k in ("es","pt")): raise SystemExit(f"{p}: palabra bilingüe incompleta")
print(f"OK: {len(q)} episodios validados")
