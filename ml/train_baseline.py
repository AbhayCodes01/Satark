"""Train and evaluate the baseline Satark detector (task P2-02).

    pip install scikit-learn joblib       (once)
    python ml/train_baseline.py

Model: character n-gram TF-IDF (language-agnostic, works for Devanagari, Latin and the other
Indian scripts) -> logistic regression. Two heads:
  * scam vs ham
  * one-vs-rest reason codes (trained on scam rows)

HONESTY NOTE: the data is synthetic and built from a small set of scenario templates, and the
validation/test splits hold only a few scenarios per class. Numbers from this script show that
the pipeline works. They are NOT reportable detection accuracy. Report numbers only from the
hand-checked, real-style test set (data/handchecked/), kept separate from this.
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.multiclass import OneVsRestClassifier
from sklearn.preprocessing import MultiLabelBinarizer

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DATA = Path("data/processed/dataset_v0.jsonl")
OUT_MODEL = Path("models/baseline_v0.joblib")          # trained on train split only (for honest evaluation)
OUT_FULL = Path("models/baseline_v0_full.joblib")      # trained on ALL rows (used by ml/pipeline.py)
OUT_JSON = Path("ml/results/baseline_v0.json")


def load():
    rows = [json.loads(l) for l in DATA.read_text(encoding="utf-8").splitlines() if l.strip()]
    by = defaultdict(list)
    for r in rows:
        by[r["split"]].append(r)
    return by


def metrics(y_true, y_pred):
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    tp = int(((y_true == 1) & (y_pred == 1)).sum())
    fp = int(((y_true == 0) & (y_pred == 1)).sum())
    fn = int(((y_true == 1) & (y_pred == 0)).sum())
    tn = int(((y_true == 0) & (y_pred == 0)).sum())
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    fpr = fp / (fp + tn) if fp + tn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return {"n": len(y_true), "precision": round(prec, 4), "recall": round(rec, 4),
            "f1": round(f1, 4), "false_positive_rate": round(fpr, 4),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn}


def main():
    by = load()
    train, val, test = by["train"], by["val"], by["test"]
    y = lambda rows: [1 if r["label"] == "scam" else 0 for r in rows]

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True,
                          min_df=2, max_features=60000, lowercase=True)
    Xtr = vec.fit_transform([r["text"] for r in train])
    clf = LogisticRegression(C=10, class_weight="balanced", max_iter=2000)
    clf.fit(Xtr, y(train))

    scam_rows = [r for r in train if r["label"] == "scam"]
    mlb = MultiLabelBinarizer()
    Ycodes = mlb.fit_transform([r["codes"] for r in scam_rows])
    code_clf = OneVsRestClassifier(LogisticRegression(C=10, max_iter=2000))
    code_clf.fit(vec.transform([r["text"] for r in scam_rows]), Ycodes)

    # Threshold: chosen on validation to keep the false-positive rate low (legit messages matter).
    pv = clf.predict_proba(vec.transform([r["text"] for r in val]))[:, 1]
    best_t, best_key = 0.5, None
    for t in np.arange(0.2, 0.9, 0.05):
        m = metrics(y(val), (pv >= t).astype(int))
        key = (m["false_positive_rate"] <= 0.02, m["recall"], -m["false_positive_rate"])
        if best_key is None or key > best_key:
            best_key, best_t = key, float(round(t, 2))

    results = {"threshold": best_t, "train_rows": len(train), "synthetic_only": True,
               "note": "Synthetic templates, few scenarios per split. Not reportable accuracy."}
    for name, rows in (("val", val), ("test", test)):
        p = clf.predict_proba(vec.transform([r["text"] for r in rows]))[:, 1]
        pred = (p >= best_t).astype(int)
        results[name] = metrics(y(rows), pred)
        results[name]["by_language"] = {
            lang: metrics([1 if r["label"] == "scam" else 0 for r in rows if r["lang"] == lang],
                          pred[[i for i, r in enumerate(rows) if r["lang"] == lang]])
            for lang in sorted({r["lang"] for r in rows})}
        wrong = Counter(rows[i]["family_id"] for i in range(len(rows)) if pred[i] != y(rows)[i])
        results[name]["errors_by_family"] = dict(wrong)

    joblib.dump({"vectorizer": vec, "scam_clf": clf, "code_clf": code_clf,
                 "code_labels": list(mlb.classes_), "threshold": best_t}, OUT_MODEL)

    # Full model: same recipe, all scenarios, so every reason code is learned. NOT used for evaluation.
    allrows = train + val + test
    vec_f = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True,
                            min_df=2, max_features=60000, lowercase=True)
    Xf = vec_f.fit_transform([r["text"] for r in allrows])
    clf_f = LogisticRegression(C=10, class_weight="balanced", max_iter=2000).fit(Xf, y(allrows))
    scam_f = [r for r in allrows if r["label"] == "scam"]
    mlb_f = MultiLabelBinarizer()
    Yf = mlb_f.fit_transform([r["codes"] for r in scam_f])
    code_f = OneVsRestClassifier(LogisticRegression(C=10, max_iter=2000)).fit(
        vec_f.transform([r["text"] for r in scam_f]), Yf)
    joblib.dump({"vectorizer": vec_f, "scam_clf": clf_f, "code_clf": code_f,
                 "code_labels": list(mlb_f.classes_), "threshold": best_t}, OUT_FULL)
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"threshold (chosen on val): {best_t}")
    for name in ("val", "test"):
        m = results[name]
        print(f"{name:4s} n={m['n']:4d} precision={m['precision']:.3f} recall={m['recall']:.3f} "
              f"FPR={m['false_positive_rate']:.3f}  errors by scenario: {m['errors_by_family'] or 'none'}")
        for lang, lm in m["by_language"].items():
            print(f"       {lang:9s} n={lm['n']:3d} P={lm['precision']:.2f} R={lm['recall']:.2f} FPR={lm['false_positive_rate']:.2f}")
    print(f"saved models -> {OUT_MODEL} (eval), {OUT_FULL} (pipeline)   metrics -> {OUT_JSON}")
    print("REMINDER: synthetic data, few scenarios per split. These numbers are NOT reportable accuracy.")


if __name__ == "__main__":
    main()
