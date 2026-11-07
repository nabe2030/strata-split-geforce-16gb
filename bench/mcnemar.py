# Exact McNemar test between two jamcqa_resume.py runs. Usage: mcnemar.py A/results.jsonl B/results.jsonl
import json,sys
from math import comb
def ld(p): return {r['qid']:r for r in map(json.loads,open(p))}
a=ld(sys.argv[1]); b=ld(sys.argv[2]); ks=sorted(set(a)&set(b))
n11=sum(a[k]['correct'] and b[k]['correct'] for k in ks); n10=sum(a[k]['correct'] and not b[k]['correct'] for k in ks)
n01=sum((not a[k]['correct']) and b[k]['correct'] for k in ks); n00=len(ks)-n11-n10-n01
same=sum(a[k]['pred']==b[k]['pred'] for k in ks)
m=n10+n01; kk=min(n10,n01); p=min(1,2*sum(comb(m,i) for i in range(kk+1))/2**m) if m else 1
print(f"n={len(ks)} both_correct={n11} only_A_correct={n10} only_B_correct={n01} both_wrong={n00} correct/incorrect_agreement={(n11+n00)/len(ks)*100:.2f}% same_choice={same/len(ks)*100:.2f}% discordant={m} exact_McNemar_p={p:.3f}")
