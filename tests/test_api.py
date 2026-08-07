from app.main import app, models


def test_model_catalog_lists_all_models():
    assert [model.id for model in models()] == [
        "two-tanks",
        "water-pipe",
        "garden-irrigation",
    ]


def test_model_api_routes_are_registered():
    paths = {route.path for route in app.routes}
    assert "/api/models" in paths
    assert "/api/models/two-tanks/simulations" in paths
    assert "/api/models/water-pipe/simulations" in paths
    assert "/api/models/garden-irrigation/simulations" in paths
    assert "/api/simulations" in paths
