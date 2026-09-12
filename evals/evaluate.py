import argparse,json

def load(p):
    with open(p,encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]

def metrics(rows):
    tp=fp=fn=0
    for x in rows:
        pred=x.get("predicted_priority")
        exp=x.get("expected_priority")
        if pred=="HIGH" and exp=="HIGH": tp+=1
        elif pred=="HIGH" and exp!="HIGH": fp+=1
        elif pred!="HIGH" and exp=="HIGH": fn+=1
    p=tp/(tp+fp) if tp+fp else 0
    r=tp/(tp+fn) if tp+fn else 0
    f=2*p*r/(p+r) if p+r else 0
    return p,r,f

ap=argparse.ArgumentParser()
ap.add_argument("--file",required=True)
a=ap.parse_args()
rows=load(a.file)
p,r,f=metrics(rows)
print(f"Examples: {len(rows)}")
print(f"HIGH precision: {p:.3f}")
print(f"HIGH recall:    {r:.3f}")
print(f"HIGH F1:        {f:.3f}")
