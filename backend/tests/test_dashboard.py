from tests.assertions import assert_json_has_no_non_finite


def test_summary_is_labelled_demo_and_matches_the_dataset(client):
    response = client.get("/api/dashboard/summary")
    assert response.status_code == 200
    body = response.json()
    assert_json_has_no_non_finite(body)
    assert body["is_demo"] is True
    assert body["data_source"] == "demo"
    assert body["metric_formula"] == "(likes + comments + shares) / views * 100"
    assert body["posts_analyzed"] == 16
    assert body["best_category"] == "Tutorial"
    assert body["total_interactions"] > 0
    assert body["avg_engagement_rate"] is not None
    assert body["applied_filters"]["category"] is None


def test_summary_category_filter(client):
    response = client.get("/api/dashboard/summary", params={"category": "Tutorial"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_demo"] is True
    assert body["posts_analyzed"] == 4
    assert body["best_category"] == "Tutorial"
    assert body["applied_filters"]["category"] == "Tutorial"


def test_trends_are_ordered_demo_points(client):
    response = client.get("/api/dashboard/trends")
    assert response.status_code == 200
    body = response.json()
    assert_json_has_no_non_finite(body)
    assert body["is_demo"] is True
    points = body["points"]
    assert len(points) >= 4
    periods = [point["period"] for point in points]
    assert periods == sorted(periods)
    assert all(point["post_count"] > 0 for point in points)


def test_content_comparison_ranks_tutorial_first(client):
    response = client.get("/api/dashboard/content-comparison")
    assert response.status_code == 200
    body = response.json()
    assert_json_has_no_non_finite(body)
    assert body["is_demo"] is True
    names = [item["name"] for item in body["categories"]]
    assert names[0] == "Tutorial"
    assert len(names) == 5
    assert {item["name"] for item in body["platforms"]} == {"Instagram", "YouTube", "TikTok"}


def test_posts_use_the_shared_formula(client):
    response = client.get("/api/posts")
    assert response.status_code == 200
    body = response.json()
    assert_json_has_no_non_finite(body)
    assert body["is_demo"] is True
    assert body["count"] == 16
    hook = next(post for post in body["posts"] if post["post_id"] == "p-1009")
    assert hook["engagement_rate"] == 19.91
    assert hook["views"] == 22100
    dates = [post["post_datetime"] for post in body["posts"]]
    assert dates == sorted(dates, reverse=True)


def test_posts_date_filter(client):
    response = client.get("/api/posts", params={"start_date": "2026-10-01"})
    assert response.status_code == 200
    ids = {post["post_id"] for post in response.json()["posts"]}
    assert ids == {"p-1012", "p-1013", "p-1014", "p-1015", "p-1016"}


def test_invalid_date_filter_is_rejected(client):
    response = client.get("/api/posts", params={"start_date": "14-10-2026"})
    assert response.status_code == 400
    assert "YYYY-MM-DD" in response.json()["detail"]


def test_unknown_category_returns_an_empty_demo_result(client):
    response = client.get("/api/dashboard/summary", params={"category": "Not a category"})
    assert response.status_code == 200
    body = response.json()
    assert body["is_demo"] is True
    assert body["posts_analyzed"] == 0
    assert body["best_category"] is None
    assert body["avg_engagement_rate"] is None


def test_insights_are_demo_and_traceable(client):
    response = client.get("/api/insights")
    assert response.status_code == 200
    body = response.json()
    assert_json_has_no_non_finite(body)
    assert body["is_demo"] is True
    assert "demo dataset" in body["disclaimer"].lower()
    assert "not causal" in body["disclaimer"].lower()
    ids = [card["id"] for card in body["cards"]]
    assert ids == [
        "category-comparison",
        "engagement-patterns",
        "high-low-posts",
        "possible-trends",
    ]
    high_low = next(card for card in body["cards"] if card["id"] == "high-low-posts")
    assert "p-1009" in high_low["evidence"]
    comparison = next(card for card in body["cards"] if card["id"] == "category-comparison")
    assert "not evidence that the category caused" in comparison["evidence"]
