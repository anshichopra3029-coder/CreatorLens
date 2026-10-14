from pathlib import Path


VALID_CSV = (
    b"post_id,platform,category,post_datetime,views,likes,comments,shares,followers_gained\n"
    b"p1,Instagram,Tutorial,2026-10-01,1000,50,10,5,2\n"
    b"p2,YouTube,Community,2026-10-02,0,3,1,0,0\n"
)

PARTIAL_CSV = b"post_id,likes\n1,10\n"

MALFORMED_CSV = b'post_id,platform\n"unterminated,Instagram\n'


def _upload(client, filename: str, content: bytes, content_type: str = "text/csv"):
    return client.post(
        "/api/upload",
        files={"file": (filename, content, content_type)},
    )


def test_valid_csv_returns_metadata_without_saving(client):
    response = _upload(client, "posts.csv", VALID_CSV)
    assert response.status_code == 200
    body = response.json()
    assert body["filename"] == "posts.csv"
    assert body["size_bytes"] == len(VALID_CSV)
    assert body["row_count"] == 2
    assert "views" in body["column_names"]
    assert body["expected_columns"]["missing"] == []
    assert body["expected_columns"]["present"][0] == "post_id"
    assert body["is_demo"] is False
    assert body["data_source"] == "uploaded_csv"
    assert body["analysis_performed"] is False
    assert body["file_saved"] is False
    assert "not saved" in body["validation_message"]
    assert "no engagement analysis" in body["validation_message"]
    assert "p1" not in response.text
    assert "Instagram" not in response.text
    uploads = Path(__file__).resolve().parents[1] / "uploads"
    assert not uploads.exists()


def test_partial_csv_reports_missing_columns(client):
    response = _upload(client, "partial.csv", PARTIAL_CSV)
    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 1
    assert body["expected_columns"]["present"] == ["post_id", "likes"]
    assert "views" in body["expected_columns"]["missing"]
    assert body["analysis_performed"] is False
    assert any("missing" in warning for warning in body["warnings"])


def test_empty_file_is_rejected(client):
    response = _upload(client, "empty.csv", b"")
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_whitespace_file_is_rejected(client):
    response = _upload(client, "blank.csv", b"   \n")
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_wrong_extension_is_rejected(client):
    response = _upload(client, "notes.txt", b"post_id,likes\n1,2\n", "text/plain")
    assert response.status_code == 415
    assert "csv" in response.json()["detail"].lower()


def test_malformed_csv_is_rejected(client):
    response = _upload(client, "broken.csv", MALFORMED_CSV)
    assert response.status_code == 400
    assert "parsed" in response.json()["detail"].lower()


def test_non_utf8_csv_is_rejected(client):
    response = _upload(client, "binary.csv", b"\xff\xfe\x00\x00not-text")
    assert response.status_code == 400
    assert "UTF-8" in response.json()["detail"]


def test_oversized_csv_is_rejected(client, monkeypatch):
    from app.services import upload_service

    monkeypatch.setattr(type(upload_service.settings), "max_upload_bytes", property(lambda self: 16))
    response = _upload(client, "large.csv", b"post_id,likes\n" + b"x" * 40)
    assert response.status_code == 413
    assert "limit" in response.json()["detail"].lower()


def test_header_only_csv_is_metadata_with_a_warning(client):
    response = _upload(client, "headers.csv", b"post_id,platform,views\n")
    assert response.status_code == 200
    body = response.json()
    assert body["row_count"] == 0
    assert any("no data rows" in warning for warning in body["warnings"])
    assert body["file_saved"] is False


def test_filename_path_is_reduced_to_a_basename(client):
    response = _upload(client, r"..\secret\posts.csv", VALID_CSV)
    assert response.status_code == 200
    assert response.json()["filename"] == "posts.csv"
    assert "secret" not in response.text
