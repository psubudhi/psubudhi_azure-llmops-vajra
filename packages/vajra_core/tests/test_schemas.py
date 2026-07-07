from vajra_core.schemas import PredictionRequest


def test_prediction_request_defaults() -> None:
    request = PredictionRequest()
    assert request.source == "replay"
    assert request.strategy == "latest"
