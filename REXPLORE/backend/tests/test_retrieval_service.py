from services import retrieval_service


def test_keyword_search_ranks_relevant_chunk_first():
    chunks = [
        {"text": "The methodology uses a convolutional neural network trained with Adam.", "section_name": "Methodology", "page_number": 3},
        {"text": "Unrelated discussion about weather patterns and climate.", "section_name": "Discussion", "page_number": 5},
        {"text": "The dataset used was CIFAR-10 with 60000 images.", "section_name": "Experiments", "page_number": 4},
    ]
    results = retrieval_service.keyword_search("what neural network architecture was used", chunks, top_k=2)
    assert results
    assert results[0]["section_name"] == "Methodology"


def test_keyword_search_empty_chunks_returns_empty():
    assert retrieval_service.keyword_search("anything", [], top_k=5) == []
