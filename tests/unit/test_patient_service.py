from unittest import mock

from app.services import patient_service


def test_get_patient_name_skips_request_without_token():
    """
    Without a bearer token the lookup can only come back 401, so it should
    short-circuit to "Unknown" rather than make a blocking round trip. This is
    what keeps cascaded deletes - which call this once per affected row - from
    firing an unbounded number of pointless requests.
    """
    with mock.patch("app.services.patient_service.get_patient_by_id") as mock_get:
        result = patient_service.get_patient_name(patient_id=1, bearer_token="")

    assert result == "Unknown"
    mock_get.assert_not_called()


def test_get_patient_name_skips_request_when_token_omitted():
    """Same short-circuit when the caller omits the argument entirely."""
    with mock.patch("app.services.patient_service.get_patient_by_id") as mock_get:
        result = patient_service.get_patient_name(patient_id=1)

    assert result == "Unknown"
    mock_get.assert_not_called()


def test_get_patient_name_returns_name_with_token():
    """With a token the lookup still happens and the name is returned."""
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"name": "DANIEL ANG"}}

    with mock.patch(
        "app.services.patient_service.get_patient_by_id", return_value=mock_response
    ) as mock_get:
        result = patient_service.get_patient_name(patient_id=1, bearer_token="a-token")

    assert result == "DANIEL ANG"
    mock_get.assert_called_once()


def test_get_patient_name_falls_back_to_unknown_on_error():
    """A failed lookup is still swallowed into "Unknown" as before."""
    with mock.patch(
        "app.services.patient_service.get_patient_by_id", side_effect=Exception("boom")
    ):
        result = patient_service.get_patient_name(patient_id=1, bearer_token="a-token")

    assert result == "Unknown"


def test_patient_requests_set_a_timeout():
    """
    requests has no default timeout, so a slow Patient service would otherwise
    block the calling request indefinitely.
    """
    mock_response = mock.MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {}}

    with mock.patch(
        "app.services.patient_service.requests.get", return_value=mock_response
    ) as mock_get:
        patient_service.get_patient_by_id(
            require_auth=True, bearer_token="a-token", patient_id=1
        )
        patient_service.get_patient_allocation_by_patient_id(
            require_auth=True, bearer_token="a-token", patient_id=1
        )

    assert mock_get.call_count == 2
    for call in mock_get.call_args_list:
        assert call.kwargs["timeout"] == patient_service.REQUEST_TIMEOUT_SECONDS
