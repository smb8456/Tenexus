"""AI component for Tenexus - written from scratch, no ML libraries.

1. NaiveBayesClassifier: sorts a tenant message into one of 9 categories and
   reports a confidence score.
2. TfidfIndex: finds the closest approved FAQ answer using TF-IDF and cosine
   similarity.

The AI only suggests. scoring.py decides what is allowed to happen.
"""
import math
import re
from collections import Counter, defaultdict

from ai_data import TRAINING

STOP_WORDS = frozenset("""
a an the and or but if of to in on at by for from with into onto over under is are was were be been am
i me my we our you your it its this that these those there here do does did can could would should will
have has had not no so very too just also as than then them they their he she his her us
""".split())
# 'no' and 'not' carry meaning here ("no heat", "not working"), so keep them.
STOP_WORDS = STOP_WORDS - {"no", "not"}

CONFIDENCE_THRESHOLD = 0.35


def stem(word):
    """A very small stemmer: leaking -> leak, clogged -> clog, mice stays mice."""
    if len(word) > 5 and word.endswith("ing"):
        word = word[:-3]
    elif len(word) > 4 and word.endswith("ed"):
        word = word[:-2]
    elif len(word) > 4 and word.endswith("ies"):
        word = word[:-3] + "y"
    elif len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        word = word[:-1]
    if len(word) > 3 and word[-1] == word[-2] and word[-1] not in "aeiouls":
        word = word[:-1]       # dripp -> drip, clogg -> clog
    return word


def tokenize(text):
    words = re.findall(r"[a-z']+", text.lower())
    return [stem(w.replace("'s", "").replace("'", "")) for w in words if w not in STOP_WORDS]


class NaiveBayesClassifier:
    """Multinomial Naive Bayes with Laplace smoothing."""

    def __init__(self, alpha=1.0):
        self.alpha = alpha
        self.labels = []
        self.priors = {}
        self.word_counts = {}
        self.totals = {}
        self.vocab = set()

    def fit(self, samples):
        """samples: iterable of (text, label)."""
        docs_per_label = Counter()
        counts = defaultdict(Counter)
        for text, label in samples:
            docs_per_label[label] += 1
            counts[label].update(tokenize(text))
        self.labels = sorted(docs_per_label)
        n_docs = sum(docs_per_label.values())
        self.priors = {l: math.log(docs_per_label[l] / n_docs) for l in self.labels}
        self.word_counts = dict(counts)
        self.vocab = {w for c in counts.values() for w in c}
        self.totals = {l: sum(counts[l].values()) for l in self.labels}
        return self

    def probabilities(self, text):
        """Return {label: probability}. Unknown words are ignored; if no word is
        known the answer is uniform (the classifier honestly does not know)."""
        known = [w for w in tokenize(text) if w in self.vocab]
        if not known:
            return {l: 1 / len(self.labels) for l in self.labels}
        v = len(self.vocab)
        scores = {}
        for label in self.labels:
            score = self.priors[label]
            for w in known:
                score += math.log((self.word_counts[label].get(w, 0) + self.alpha)
                                  / (self.totals[label] + self.alpha * v))
            scores[label] = score
        top = max(scores.values())
        exps = {l: math.exp(s - top) for l, s in scores.items()}
        total = sum(exps.values())
        return {l: e / total for l, e in exps.items()}

    def predict(self, text):
        """Return (label, confidence)."""
        probs = self.probabilities(text)
        label = max(probs, key=probs.get)
        return label, probs[label]


class TfidfIndex:
    """Finds the closest FAQ entry to a question."""

    def __init__(self, documents):
        """documents: list of (doc_id, text)."""
        self.ids = [d for d, _ in documents]
        tokens = [tokenize(t) for _, t in documents]
        n = len(tokens)
        df = Counter(w for toks in tokens for w in set(toks))
        self.idf = {w: math.log((1 + n) / (1 + c)) + 1 for w, c in df.items()}
        self.vectors = [self._vector(toks) for toks in tokens]

    def _vector(self, toks):
        tf = Counter(w for w in toks if w in self.idf)
        vec = {w: c * self.idf[w] for w, c in tf.items()}
        norm = math.sqrt(sum(x * x for x in vec.values()))
        return {w: x / norm for w, x in vec.items()} if norm else {}

    def search(self, query, min_score=0.2):
        """Return (doc_id, score) for the best match, or (None, score)."""
        q = self._vector(tokenize(query))
        best_id, best = None, 0.0
        for doc_id, vec in zip(self.ids, self.vectors):
            score = sum(x * vec.get(w, 0.0) for w, x in q.items())
            if score > best:
                best_id, best = doc_id, score
        return (best_id, best) if best >= min_score else (None, best)


class AIEngine:
    """What the rest of the app talks to."""

    def __init__(self, classifier):
        self.classifier = classifier

    @classmethod
    def trained(cls):
        samples = [(text, label) for label, texts in TRAINING.items() for text in texts]
        return cls(NaiveBayesClassifier().fit(samples))

    def classify(self, message):
        return self.classifier.predict(message)

    def best_faq(self, message, faqs):
        """faqs: list of dicts with id, question, answer. Returns the answer
        text of the closest approved FAQ, or None."""
        if not faqs:
            return None
        index = TfidfIndex([(f["id"], f["question"]) for f in faqs])
        doc_id, _ = index.search(message)
        if doc_id is None:
            return None
        return next(f["answer"] for f in faqs if f["id"] == doc_id)
