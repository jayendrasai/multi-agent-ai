def test_api_and_worker_imports() -> None:
    import app.main  # noqa: F401
    import app.worker  # noqa: F401
