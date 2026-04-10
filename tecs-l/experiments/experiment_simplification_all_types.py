#!/usr/bin/env python3
"""ALL Data Types: Simplification Verification

Tests 4 variants across 12 data types (small-data first, MNIST/CIFAR via DataLoader):
  Dense | Original(scale*sqrt*dir) | Raw(A-G) | Scaled(s*(A-G))
"""
import sys, os, time, math
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_print = print
print = lambda *a, **k: (_print(*a, **k, flush=True))


# ═══════════════════════════════════════════
# Models
# ═══════════════════════════════════════════

class Dense(nn.Module):
    def __init__(self, d_in, d_hid, d_out):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d_in, d_hid), nn.ReLU(), nn.Dropout(0.3), nn.Linear(d_hid, d_out))
    def forward(self, x): return self.net(x)

class Original(nn.Module):
    def __init__(self, d_in, d_hid, d_out):
        super().__init__()
        self.a = nn.Sequential(nn.Linear(d_in, d_hid), nn.ReLU(), nn.Dropout(0.3), nn.Linear(d_hid, d_out))
        self.g = nn.Sequential(nn.Linear(d_in, d_hid), nn.ReLU(), nn.Dropout(0.3), nn.Linear(d_hid, d_out))
        self.scale = nn.Parameter(torch.ones(1))
    def forward(self, x):
        rep = self.a(x) - self.g(x)
        t = rep.pow(2).mean(dim=-1, keepdim=True)
        d = rep / (rep.norm(dim=-1, keepdim=True) + 1e-8)
        return self.scale * torch.sqrt(t + 1e-8) * d

class RawAG(nn.Module):
    def __init__(self, d_in, d_hid, d_out):
        super().__init__()
        self.a = nn.Sequential(nn.Linear(d_in, d_hid), nn.ReLU(), nn.Dropout(0.3), nn.Linear(d_hid, d_out))
        self.g = nn.Sequential(nn.Linear(d_in, d_hid), nn.ReLU(), nn.Dropout(0.3), nn.Linear(d_hid, d_out))
    def forward(self, x): return self.a(x) - self.g(x)

class ScaledAG(nn.Module):
    def __init__(self, d_in, d_hid, d_out):
        super().__init__()
        self.a = nn.Sequential(nn.Linear(d_in, d_hid), nn.ReLU(), nn.Dropout(0.3), nn.Linear(d_hid, d_out))
        self.g = nn.Sequential(nn.Linear(d_in, d_hid), nn.ReLU(), nn.Dropout(0.3), nn.Linear(d_hid, d_out))
        self.scale = nn.Parameter(torch.ones(1))
    def forward(self, x): return self.scale * (self.a(x) - self.g(x))


# ═══════════════════════════════════════════
# Data Loaders
# ═══════════════════════════════════════════

def load_timeseries():
    np.random.seed(42)
    X, y = [], []
    for _ in range(200):
        t = np.linspace(0, 2*np.pi, 50)
        X.append(np.sin(t) + np.random.randn(50)*0.1); y.append(0)
        X.append(np.sign(np.sin(t)) + np.random.randn(50)*0.1); y.append(1)
        X.append((t%(2*np.pi))/(2*np.pi)*2-1 + np.random.randn(50)*0.1); y.append(2)
    X, y = torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(y)
    s = int(0.8*len(X)); idx = torch.randperm(len(X))
    return X[idx[:s]], y[idx[:s]], X[idx[s:]], y[idx[s:]], 50, 3, 'Time Series'

def load_audio():
    np.random.seed(42); sr=8000; dur=0.5; nf=100; X, y = [], []
    for _ in range(100):
        for c, f in enumerate([200,500,1000]):
            t=np.linspace(0,dur,int(sr*dur))
            sig=np.sin(2*np.pi*f*t)+np.random.randn(len(t))*0.05
            fft=np.abs(np.fft.rfft(sig))[:nf]; X.append(fft/(fft.max()+1e-8)); y.append(c)
        t=np.linspace(0,dur,int(sr*dur))
        sig=np.sin(2*np.pi*200*t)+np.sin(2*np.pi*500*t)+np.random.randn(len(t))*0.05
        fft=np.abs(np.fft.rfft(sig))[:nf]; X.append(fft/(fft.max()+1e-8)); y.append(3)
        sig=np.random.randn(int(sr*dur)); fft=np.abs(np.fft.rfft(sig))[:nf]
        X.append(fft/(fft.max()+1e-8)); y.append(4)
    X, y = torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(y)
    s=int(0.8*len(X)); idx=torch.randperm(len(X))
    return X[idx[:s]], y[idx[:s]], X[idx[s:]], y[idx[s:]], nf, 5, 'Audio'

def _load_sk(fn, name):
    from sklearn.preprocessing import StandardScaler
    d=fn(); X=StandardScaler().fit_transform(d.data); y=d.target
    X,y = torch.tensor(X,dtype=torch.float32), torch.tensor(y,dtype=torch.long)
    s=int(0.8*len(X)); idx=torch.randperm(len(X),generator=torch.Generator().manual_seed(42))
    return X[idx[:s]], y[idx[:s]], X[idx[s:]], y[idx[s:]], X.shape[1], len(set(y.numpy())), name

def load_iris():
    from sklearn.datasets import load_iris; return _load_sk(load_iris, 'Tabular Iris')
def load_wine():
    from sklearn.datasets import load_wine; return _load_sk(load_wine, 'Tabular Wine')
def load_cancer():
    from sklearn.datasets import load_breast_cancer; return _load_sk(load_breast_cancer, 'Tabular Cancer')

def load_numbers():
    np.random.seed(42)
    def is_prime(n):
        if n<2: return False
        for i in range(2,int(n**0.5)+1):
            if n%i==0: return False
        return True
    def cdiv(n): return sum(1 for i in range(1,n+1) if n%i==0) if n>0 else 0
    fibs=set(); a,b=1,1
    while a<=1000: fibs.add(a); a,b=b,a+b
    pows2={2**i for i in range(11) if 2**i<=1000}
    squares={i*i for i in range(1,32) if i*i<=1000}
    X, y = [], []
    for n in range(1,1001):
        X.append([n/1000,n%2,n%3,n%6,sum(int(d) for d in str(n))/27,cdiv(n)/30,int(n%2==0),(n%10)/9,math.log(max(n,1))/math.log(1000),sum(d for d in range(1,n) if n%d==0)/max(n,1)])
        if is_prime(n): y.append(0)
        elif n in squares: y.append(1)
        elif n in fibs: y.append(2)
        elif n in pows2: y.append(3)
        else: y.append(4)
    X,y=torch.tensor(X,dtype=torch.float32),torch.tensor(y)
    return X[:800],y[:800],X[800:],y[800:],10,5,'Number System'

def load_music():
    np.random.seed(42); sr=8000; dur=0.5; nf=100
    intervals=[(1,1),(16,15),(9,8),(6,5),(5,4),(4,3),(45,32),(3,2),(2,1)]
    X,y=[],[]
    for _ in range(60):
        for c,(p,q) in enumerate(intervals):
            t=np.linspace(0,dur,int(sr*dur)); f2=200*p/q
            sig=np.sin(2*np.pi*200*t)+np.sin(2*np.pi*f2*t)+np.random.randn(len(t))*0.02
            fft=np.abs(np.fft.rfft(sig))[:nf]; X.append(fft/(fft.max()+1e-8)); y.append(c)
    X,y=torch.tensor(np.array(X),dtype=torch.float32),torch.tensor(y)
    s=int(0.8*len(X)); idx=torch.randperm(len(X))
    return X[idx[:s]],y[idx[:s]],X[idx[s:]],y[idx[s:]],nf,9,'Music Theory'

def load_text_tfidf():
    from sklearn.datasets import fetch_20newsgroups
    from sklearn.feature_extraction.text import TfidfVectorizer
    cats=['sci.space','rec.sport.baseball','comp.graphics','talk.politics.guns']
    tr=fetch_20newsgroups(subset='train',categories=cats,remove=('headers','footers','quotes'))
    te=fetch_20newsgroups(subset='test',categories=cats,remove=('headers','footers','quotes'))
    vec=TfidfVectorizer(max_features=500)
    Xtr=torch.tensor(vec.fit_transform(tr.data).toarray(),dtype=torch.float32)
    ytr=torch.tensor(tr.target,dtype=torch.long)
    Xte=torch.tensor(vec.transform(te.data).toarray(),dtype=torch.float32)
    yte=torch.tensor(te.target,dtype=torch.long)
    return Xtr,ytr,Xte,yte,500,4,'Text TF-IDF'

def load_text_embed():
    from sklearn.datasets import fetch_20newsgroups
    from collections import Counter
    cats=['sci.space','rec.sport.baseball','comp.graphics','talk.politics.guns']
    tr=fetch_20newsgroups(subset='train',categories=cats,remove=('headers','footers','quotes'))
    te=fetch_20newsgroups(subset='test',categories=cats,remove=('headers','footers','quotes'))
    all_w=' '.join(tr.data).lower().split()
    top=dict(enumerate([w for w,_ in Counter(all_w).most_common(3000)],1))
    w2i={v:k for k,v in top.items()}
    ED=32
    np.random.seed(42)
    emb_table=np.random.randn(3001,ED)*0.1
    def to_vec(texts):
        out=[]
        for t in texts:
            ids=[w2i.get(w,0) for w in t.lower().split()[:100]]
            if not ids: ids=[0]
            out.append(emb_table[ids].mean(axis=0))
        return torch.tensor(np.array(out),dtype=torch.float32)
    return to_vec(tr.data),torch.tensor(tr.target,dtype=torch.long),to_vec(te.data),torch.tensor(te.target,dtype=torch.long),ED,4,'Text Embedding'

def load_mnist_small():
    """MNIST subset (10K train, 2K test) to avoid OOM."""
    from torchvision import datasets, transforms
    t=transforms.Compose([transforms.ToTensor(),transforms.Normalize((0.1307,),(0.3081,))])
    tr=datasets.MNIST('./data',train=True,download=True,transform=t)
    te=datasets.MNIST('./data',train=False,transform=t)
    Xtr=tr.data[:10000].float().view(-1,784)/255.0; ytr=tr.targets[:10000]
    Xte=te.data[:2000].float().view(-1,784)/255.0; yte=te.targets[:2000]
    return Xtr,ytr,Xte,yte,784,10,'Image MNIST(10K)'

def load_cifar_small():
    """CIFAR subset (10K train, 2K test) to avoid OOM."""
    from torchvision import datasets, transforms
    t=transforms.Compose([transforms.ToTensor(),transforms.Normalize((0.5,0.5,0.5),(0.5,0.5,0.5))])
    tr=datasets.CIFAR10('./data',train=True,download=True,transform=t)
    te=datasets.CIFAR10('./data',train=False,transform=t)
    Xtr=torch.stack([tr[i][0] for i in range(10000)]).view(-1,3072)
    ytr=torch.tensor([tr[i][1] for i in range(10000)])
    Xte=torch.stack([te[i][0] for i in range(2000)]).view(-1,3072)
    yte=torch.tensor([te[i][1] for i in range(2000)])
    return Xtr,ytr,Xte,yte,3072,10,'Image CIFAR(10K)'


# ═══════════════════════════════════════════
# Training
# ═══════════════════════════════════════════

def train_eval(MCls, Xtr, ytr, Xte, yte, d_in, d_hid, d_out, epochs=20, lr=0.001):
    torch.manual_seed(42)
    m = MCls(d_in, d_hid, d_out)
    opt = torch.optim.Adam(m.parameters(), lr=lr)
    crit = nn.CrossEntropyLoss()
    for _ in range(epochs):
        m.train(); idx=torch.randperm(len(Xtr))
        for i in range(0,len(Xtr),64):
            bx,by = Xtr[idx[i:i+64]], ytr[idx[i:i+64]]
            opt.zero_grad(); crit(m(bx),by).backward(); opt.step()
    m.eval()
    with torch.no_grad():
        acc=(m(Xte).argmax(1)==yte).float().mean().item()
    return acc


def main():
    print("=" * 80)
    print("  ALL Data Types: Simplification Verification")
    print("  Dense vs Original(scale*sqrt*dir) vs Raw(A-G) vs Scaled(s*(A-G))")
    print("=" * 80)

    tasks = [
        # (loader, hidden_dim, epochs)
        (load_iris, 16, 50),
        (load_wine, 32, 50),
        (load_cancer, 32, 50),
        (load_timeseries, 32, 30),
        (load_audio, 32, 30),
        (load_numbers, 32, 30),
        (load_music, 32, 30),
        (load_text_tfidf, 64, 15),
        (load_text_embed, 32, 20),
        (load_mnist_small, 64, 10),
        (load_cifar_small, 128, 15),
    ]

    models = {'Dense': Dense, 'Original': Original, 'Raw(A-G)': RawAG, 'Scaled': ScaledAG}
    results = []

    for loader, d_hid, epochs in tasks:
        try:
            Xtr,ytr,Xte,yte,d_in,d_out,name = loader()
        except Exception as e:
            print(f"  SKIP {loader.__name__}: {e}")
            continue
        print(f"\n  [{name}] d={d_in}→{d_out} n_train={len(Xtr)} n_test={len(Xte)}")
        row = {'name': name}
        for mn, MC in models.items():
            acc = train_eval(MC, Xtr, ytr, Xte, yte, d_in, d_hid, d_out, epochs)
            row[mn] = acc
            print(f"    {mn:12s}: {acc*100:.2f}%")
        results.append(row)

    # ═══ Summary ═══
    print(f"\n{'=' * 80}")
    print(f"  SUMMARY")
    print(f"{'=' * 80}")
    print(f"\n  {'#':>2} {'Data':20s} | {'Dense':>7s} | {'Original':>8s} | {'Raw(AG)':>7s} | {'Scaled':>7s} | {'Winner':10s} | {'AG-Orig':>7s}")
    print(f"  {'─'*2} {'─'*20}-+-{'─'*7}-+-{'─'*8}-+-{'─'*7}-+-{'─'*7}-+-{'─'*10}-+-{'─'*7}")

    ag_better = 0
    for i, r in enumerate(results):
        vals = {k: r[k] for k in models}
        winner = max(vals, key=vals.get)
        delta = (r.get('Raw(A-G)',0) - r.get('Original',0)) * 100
        mk = '+' if delta >= 0 else '-'
        print(f"  {i+1:2d} {r['name']:20s} |"
              f" {r['Dense']*100:5.1f}% |"
              f" {r['Original']*100:6.1f}% |"
              f" {r['Raw(A-G)']*100:5.1f}% |"
              f" {r['Scaled']*100:5.1f}% |"
              f" {winner:10s} | {delta:+5.1f}% {mk}")
        if delta >= -0.01: ag_better += 1

    n = len(results)
    print(f"\n  Raw(A-G) >= Original: {ag_better}/{n}")
    print(f"  Original > Raw(A-G): {n-ag_better}/{n}")

    # Verdict
    if ag_better >= n * 0.7:
        print(f"\n  VERDICT: 'A-G' is sufficient for {ag_better}/{n} types.")
    else:
        print(f"\n  VERDICT: scale*sqrt*dir helps. Keep Original for {n-ag_better}/{n} types.")

    print(f"\n{'=' * 80}")


if __name__ == '__main__':
    main()
