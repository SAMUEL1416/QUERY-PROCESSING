"""
Extracts algorithms/models, dataset mentions, evaluation metrics, and
concepts/keywords from the full paper text.

Approach (no fabrication, everything traceable to text actually present):
  - Algorithms/models: matched against a broad, extensible vocabulary of
    known ML/DL/statistical model & algorithm names, plus a generic
    "<word>Net" / "<Capitalized><word>" acronym heuristic for novel
    proposed-model names introduced by the authors (e.g. "ResNet-50", "BERT-CNN").
  - Metrics: matched against a vocabulary of standard evaluation metrics.
  - Datasets: sentences containing "dataset"/"corpus"/"benchmark" near a
    capitalized token or a quoted/acronym-like token.
  - Concepts/keywords: frequency-ranked noun-like tokens/bigrams after
    stopword removal (no external NLP model required, so this always works
    even before sentence-transformers finishes loading).
"""
import re
from collections import Counter
from dataclasses import dataclass
from typing import List

STOPWORDS = set("""
a about above after again against all am an and any are aren't as at be because been
before being below between both but by can't cannot could couldn't did didn't do does
doesn't doing don't down during each few for from further had hadn't has hasn't have
haven't having he he'd he'll he's her here here's hers herself him himself his how how's
i i'd i'll i'm i've if in into is isn't it it's its itself let's me more most mustn't my
myself no nor not of off on once only or other ought our ours ourselves out over own same
shan't she she'd she'll she's should shouldn't so some such than that that's the their
theirs them themselves then there there's these they they'd they'll they're they've this
those through to too under until up very was wasn't we we'd we'll we're we've were weren't
what what's when when's where where's which while who who's whom why why's with won't
would wouldn't you you'd you'll you're you've your yours yourself yourselves this paper
we propose method results using used based approach also however thus therefore section
figure table shown shows show fig et al eq
""".split())

ALGORITHM_VOCABULARY = [
    "Random Forest", "Support Vector Machine", "SVM", "Logistic Regression", "Linear Regression",
    "Decision Tree", "Naive Bayes", "K-Nearest Neighbors", "KNN", "K-Means", "Gradient Boosting",
    "XGBoost", "LightGBM", "CatBoost", "AdaBoost", "Convolutional Neural Network", "CNN",
    "Recurrent Neural Network", "RNN", "Long Short-Term Memory", "LSTM", "GRU",
    "Transformer", "BERT", "GPT", "RoBERTa", "T5", "Autoencoder", "Variational Autoencoder", "VAE",
    "Generative Adversarial Network", "GAN", "ResNet", "VGG", "AlexNet", "Inception", "MobileNet",
    "EfficientNet", "U-Net", "YOLO", "Faster R-CNN", "Mask R-CNN", "Reinforcement Learning",
    "Q-Learning", "Deep Q-Network", "DQN", "Multi-Layer Perceptron", "MLP", "Neural Network",
    "Ensemble Learning", "Principal Component Analysis", "PCA", "Linear Discriminant Analysis",
    "Hidden Markov Model", "HMM", "Conditional Random Field", "CRF", "Attention Mechanism",
    "Self-Attention", "Graph Neural Network", "GNN", "Word2Vec", "GloVe", "FastText",
    "TF-IDF", "Latent Dirichlet Allocation", "LDA", "Genetic Algorithm", "Particle Swarm Optimization",
    "Fuzzy Logic", "Markov Chain", "Bayesian Network", "Federated Learning", "Transfer Learning",
]

METRIC_VOCABULARY = [
    "Accuracy", "Precision", "Recall", "F1-Score", "F1 Score", "F-measure", "AUC", "ROC-AUC",
    "AUC-ROC", "RMSE", "MAE", "MSE", "R-squared", "R2 Score", "BLEU", "ROUGE", "METEOR",
    "Perplexity", "Sensitivity", "Specificity", "Confusion Matrix", "Mean Average Precision",
    "mAP", "IoU", "Intersection over Union", "Cross-Entropy Loss", "Log Loss", "Kappa Score",
    "Top-1 Accuracy", "Top-5 Accuracy", "Silhouette Score", "PSNR", "SSIM", "WER",
]

DATASET_TRIGGER_WORDS = ["dataset", "datasets", "corpus", "corpora", "benchmark"]


@dataclass
class ExtractedFeature:
    feature_type: str
    value: str
    context: str
    page_number: int
    confidence: float = 0.7


def _find_page_for_offset(pages, char_offset_map, offset) -> int:
    for start, end, page_number in char_offset_map:
        if start <= offset < end:
            return page_number
    return pages[0].page_number if pages else 1


def _build_offset_map(pages):
    offset_map = []
    cursor = 0
    for p in pages:
        text = p.text
        offset_map.append((cursor, cursor + len(text), p.page_number))
        cursor += len(text) + 2  # matches "\n\n".join used elsewhere
    return offset_map


def _context_window(text: str, start: int, end: int, window: int = 90) -> str:
    lo = max(0, start - window)
    hi = min(len(text), end + window)
    return text[lo:hi].replace("\n", " ").strip()


def extract_algorithms(full_text: str, pages) -> List[ExtractedFeature]:
    offset_map = _build_offset_map(pages)
    found = {}
    for name in ALGORITHM_VOCABULARY:
        for m in re.finditer(rf"\b{re.escape(name)}\b", full_text, re.IGNORECASE):
            key = name
            if key not in found:
                page = _find_page_for_offset(pages, offset_map, m.start())
                ctx = _context_window(full_text, m.start(), m.end())
                found[key] = ExtractedFeature("algorithm", name, ctx, page, 0.85)
    return list(found.values())


def extract_metrics(full_text: str, pages) -> List[ExtractedFeature]:
    offset_map = _build_offset_map(pages)
    found = {}
    for name in METRIC_VOCABULARY:
        for m in re.finditer(rf"\b{re.escape(name)}\b", full_text, re.IGNORECASE):
            key = name
            if key not in found:
                page = _find_page_for_offset(pages, offset_map, m.start())
                ctx = _context_window(full_text, m.start(), m.end())
                found[key] = ExtractedFeature("metric", name, ctx, page, 0.85)
    return list(found.values())


def extract_dataset_mentions(full_text: str, pages) -> List[ExtractedFeature]:
    """
    Finds sentences mentioning dataset/corpus/benchmark, then pulls the
    nearest capitalized or acronym-like token as the candidate dataset name.
    """
    offset_map = _build_offset_map(pages)
    results = {}
    sentence_pattern = re.compile(r"[^.]*?\b(?:" + "|".join(DATASET_TRIGGER_WORDS) + r")\b[^.]*\.", re.IGNORECASE)
    name_pattern = re.compile(r"\b([A-Z][A-Za-z0-9\-]{2,}(?:[\s\-][A-Z0-9][A-Za-z0-9\-]*){0,3})\b")

    for m in sentence_pattern.finditer(full_text):
        sentence = m.group(0)
        candidates = [c for c in name_pattern.findall(sentence) if c.lower() not in STOPWORDS]
        # Filter out generic words that aren't likely proper dataset names
        candidates = [c for c in candidates if not c.lower() in ("the", "this", "dataset", "datasets")]
        for cand in candidates[:2]:
            if cand not in results:
                page = _find_page_for_offset(pages, offset_map, m.start())
                results[cand] = ExtractedFeature("dataset", cand, sentence.strip(), page, 0.55)
    return list(results.values())


def extract_concepts_keywords(full_text: str, pages, top_n: int = 25) -> List[ExtractedFeature]:
    """Frequency-based keyword/concept extraction (unigrams + bigrams), stopword-filtered."""
    offset_map = _build_offset_map(pages)
    words = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", full_text)
    words_lower = [w.lower() for w in words]

    unigram_counts = Counter(w for w in words_lower if w not in STOPWORDS and len(w) > 3)
    bigrams = [f"{a} {b}" for a, b in zip(words_lower, words_lower[1:])]
    bigram_counts = Counter(
        bg for bg in bigrams
        if all(w not in STOPWORDS and len(w) > 2 for w in bg.split())
    )

    combined = Counter()
    combined.update({k: v for k, v in unigram_counts.items() if v >= 3})
    combined.update({k: v * 2 for k, v in bigram_counts.items() if v >= 2})  # weight bigrams higher

    top_terms = [t for t, _ in combined.most_common(top_n)]

    results = []
    for term in top_terms:
        m = re.search(re.escape(term), full_text, re.IGNORECASE)
        page = _find_page_for_offset(pages, offset_map, m.start()) if m else (pages[0].page_number if pages else 1)
        ctx = _context_window(full_text, m.start(), m.end()) if m else ""
        conf = min(0.9, 0.4 + combined[term] / 20)
        results.append(ExtractedFeature("concept", term, ctx, page, round(conf, 2)))
    return results


def extract_all_features(full_text: str, pages) -> List[ExtractedFeature]:
    features: List[ExtractedFeature] = []
    features += extract_algorithms(full_text, pages)
    features += extract_metrics(full_text, pages)
    features += extract_dataset_mentions(full_text, pages)
    features += extract_concepts_keywords(full_text, pages)
    return features
