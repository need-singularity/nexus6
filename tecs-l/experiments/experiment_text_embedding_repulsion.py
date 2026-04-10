```python
#!/usr/bin/env python3
"""TREE-2: Text Embedding (Dense) + Repulsion Field — Comparison with TF-IDF (Sparse)"""
import sys, os, time, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torch, torch.nn as nn, torch.nn.functional as F, numpy as np

class SimpleEmbedding(nn.Module):
    """Word index → Trainable embedding → Average pooling"""
    def __init__(self, vocab_size, embed_dim, max_len):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, embed_dim)
        self.max_len = max_len
    def forward(self, x):
        e = self.embed(x.long())
        return e.mean(dim=1)

class TextRepulsionField(nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim):
        super().__init__()
        self.pole_a = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, output_dim))
        self.pole_b = nn.Sequential(nn.Linear(input_dim, hidden_dim), nn.ReLU(), nn.Linear(hidden_dim, output_dim))
        self.field = nn.Sequential(nn.Linear(output_dim, output_dim), nn.Tanh())
        self.scale = nn.Parameter(torch.tensor(1/3))
    def forward(self, x):
        a, b = self.pole_a(x), self.pole_b(x)
        rep = a - b
        tension = (rep**2).sum(-1, keepdim=True)
        eq = (a + b) / 2
        out = eq + self.scale * torch.sqrt(tension + 1e-8) * self.field(rep)
        return out, tension.squeeze(-1)

def main():
    from sklearn.datasets import fetch_20newsgroups
    from sklearn.feature_extraction.text import CountVectorizer
    print("="*55)
    print("  TREE-2: Dense Embedding + Repulsion Field (Text)")
    print("="*55)
    t0 = time.time()

    cats = ['alt.atheism', 'comp.graphics', 'sci.med', 'soc.religion.christian']
    train = fetch_20newsgroups(subset='train', categories=cats)
    test = fetch_20newsgroups(subset='test', categories=cats)

    # Word index conversion (top 2000 words)
    vec = CountVectorizer(max_features=2000, binary=True)
    vec.fit(train.data)
    vocab_size = 2001  # +1 for padding

    def texts_to_indices(texts, max_len=100):
        X = torch.zeros(len(texts), max_len, dtype=torch.long)
        for i, t in enumerate(texts):
            words = t.lower().split()[:max_len]
            for j, w in enumerate(words):
                idx = vec.vocabulary_.get(w, 0)
                X[i, j] = idx + 1  # 0=pad
        return X

    X_train = texts_to_indices(train.data)
    X_test = texts_to_indices(test.data)
    y_train = torch.tensor(train.target)
    y_test = torch.tensor(test.target)

    embed_dim = 64
    hidden = 32
    n_classes = 4

    results = {}
    for name, use_repulsion in [("Dense+Embed", False), ("Repulsion+Embed", True)]:
        print(f"\n  [{name}]")
        torch.manual_seed(42)
        embedder = SimpleEmbedding(vocab_size, embed_dim, 100)
        if use_repulsion:
            head = TextRepulsionField(embed_dim, hidden, n_classes)
        else:
            head = nn.Sequential(nn.Linear(embed_dim, hidden), nn.ReLU(), nn.Linear(hidden, n_classes))

        params = list(embedder.parameters()) + list(head.parameters())
        opt = torch.optim.Adam(params, lr=0.001)
        crit = nn.CrossEntropyLoss()

        for ep in range(15):
            embedder.train(); head.train()
            idx = torch.randperm(len(X_train))
            for start in range(0, len(idx), 64):
                batch = idx[start:start+64]
                x = embedder(X_train[batch])
                if use_repulsion:
                    out, _ = head(x)
                else:
                    out = head(x)
                loss = crit(out, y_train[batch])
                opt.zero_grad(); loss.backward(); opt.step()

            if (ep+1) % 5 == 0:
                embedder.eval(); head.eval()
                with torch.no_grad():
                    x = embedder(X_test)
                    if use_repulsion:
                        out, _ = head(x)
                    else:
                        out = head(x)
                    acc = (out.argmax(1) == y_test).float().mean().item()
                print(f"    Ep{ep+1}: {acc*100:.1f}%")

        embedder.eval(); head.eval()
        with torch.no_grad():
            x = embedder(X_test)
            if use_repulsion:
                out, tension = head(x)
            else:
                out = head(x)
                tension = None
            acc = (out.argmax(1) == y_test).float().mean().item()
        results[name] = acc
        print(f"  Final: {acc*100:.2f}%")

    print(f"\n{'='*55}")
    print(f"  Dense+Embed:     {results['Dense+Embed']*100:.2f}%")
    print(f"  Repulsion+Embed: {results['Repulsion+Embed']*100:.2f}%")
    delta = (results['Repulsion+Embed'] - results['Dense+Embed']) * 100
    print(f"  Delta: {delta:+.2f}%")
    print(f"\n  TF-IDF(sparse) delta was: -0.52%")
    print(f"  Embedding(dense) delta:    {delta:+.2f}%")
    print(f"  -> {'Dense embedding FIXES the sparse problem!' if delta > 0 else 'Still not working on text.'}")
    print(f"\n  Elapsed: {time.time()-t0:.1f}s")
    print("="*55)

if __name__ == '__main__':
    main()
```