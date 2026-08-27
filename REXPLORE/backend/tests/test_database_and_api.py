from app import models


def test_paper_and_related_rows_cascade_delete(test_db):
    paper = models.Paper(
        original_filename="test.pdf",
        stored_filename="abc123.pdf",
        file_path="/tmp/abc123.pdf",
        status="ready",
    )
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    section = models.PaperSection(paper_id=paper.id, name="Abstract", raw_text="Some text.")
    feature = models.PaperFeature(paper_id=paper.id, feature_type="algorithm", value="CNN")
    dataset = models.Dataset(paper_id=paper.id, mentioned_name="CIFAR-10")
    test_db.add_all([section, feature, dataset])
    test_db.commit()

    assert test_db.query(models.PaperSection).count() == 1
    assert test_db.query(models.PaperFeature).count() == 1
    assert test_db.query(models.Dataset).count() == 1

    test_db.delete(paper)
    test_db.commit()

    assert test_db.query(models.PaperSection).count() == 0
    assert test_db.query(models.PaperFeature).count() == 0
    assert test_db.query(models.Dataset).count() == 0


def test_query_history_source_relationship(test_db):
    paper = models.Paper(original_filename="a.pdf", stored_filename="a1.pdf", file_path="/tmp/a1.pdf", status="ready")
    test_db.add(paper)
    test_db.commit()
    test_db.refresh(paper)

    q = models.QueryHistory(paper_id=paper.id, query_text="What dataset was used?", answer_text="CIFAR-10 was used.")
    test_db.add(q)
    test_db.commit()
    test_db.refresh(q)

    src = models.QuerySource(query_id=q.id, section_name="Experiments", page_number=4, snippet="CIFAR-10", score=0.87)
    test_db.add(src)
    test_db.commit()

    assert len(q.sources) == 1
    assert q.sources[0].section_name == "Experiments"
