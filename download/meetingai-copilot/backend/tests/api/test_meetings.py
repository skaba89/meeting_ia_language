"""
Comprehensive tests for meetings API endpoints.

Covers audio upload, listing, detail retrieval, deletion, and
transcription triggering scenarios including authentication enforcement,
file validation, and not-found handling.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from tests.conftest import API_PREFIX


def _make_audio_upload(
    filename: str = "test_meeting.mp3",
    content: bytes = b"fake audio content for testing",
    content_type: str = "audio/mpeg",
) -> dict:
    """Helper to build the files argument for a multipart upload request."""
    return {"audio": (filename, content, content_type)}


class TestListMeetings:
    """Tests for the GET /api/v1/meetings/ endpoint."""

    async def test_list_meetings_authenticated(self, auth_client: AsyncClient) -> None:
        """List meetings when authenticated, expect 200 with list."""
        # First, upload a meeting so there is something to list
        files = _make_audio_upload("meeting1.mp3")
        data = {"title": "Meeting 1"}
        upload_resp = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )
        assert upload_resp.status_code == 201

        # List meetings
        response = await auth_client.get(f"{API_PREFIX}/meetings/")

        assert response.status_code == 200
        meetings = response.json()
        assert isinstance(meetings, list)
        assert len(meetings) >= 1
        assert any(m["title"] == "Meeting 1" for m in meetings)

    async def test_list_meetings_unauthenticated(self, async_client: AsyncClient) -> None:
        """List meetings without authentication, expect 401 Unauthorized."""
        response = await async_client.get(f"{API_PREFIX}/meetings/")

        assert response.status_code == 401

    async def test_list_meetings_empty(self, auth_client: AsyncClient) -> None:
        """List meetings for a user with no meetings, expect 200 with empty list."""
        response = await auth_client.get(f"{API_PREFIX}/meetings/")

        assert response.status_code == 200
        meetings = response.json()
        assert isinstance(meetings, list)
        assert len(meetings) == 0


class TestUploadMeeting:
    """Tests for the POST /api/v1/meetings/upload endpoint."""

    async def test_upload_meeting(self, auth_client: AsyncClient) -> None:
        """Upload a valid audio file, expect 201 Created."""
        files = _make_audio_upload()
        data = {"title": "Test Meeting"}
        response = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Test Meeting"
        assert result["status"] == "uploaded"
        assert result["audio_filename"] == "test_meeting.mp3"
        assert "id" in result

    async def test_upload_invalid_file_type(self, auth_client: AsyncClient) -> None:
        """Upload a non-audio file, expect 415 Unsupported Media Type."""
        files = {"audio": ("document.pdf", b"fake pdf content", "application/pdf")}
        data = {"title": "Invalid File Meeting"}
        response = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )

        assert response.status_code == 415

    async def test_upload_no_auth(self, async_client: AsyncClient) -> None:
        """Upload without authentication, expect 401 Unauthorized."""
        files = _make_audio_upload()
        data = {"title": "Unauthorized Upload"}
        response = await async_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )

        assert response.status_code == 401

    async def test_upload_with_target_language(self, auth_client: AsyncClient) -> None:
        """Upload an audio file with a target language specified."""
        files = _make_audio_upload()
        data = {"title": "Meeting with Language", "target_language": "fr"}
        response = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )

        assert response.status_code == 201
        result = response.json()
        assert result["title"] == "Meeting with Language"

    async def test_upload_with_invalid_target_language(
        self, auth_client: AsyncClient
    ) -> None:
        """Upload with an unsupported target language code, expect 422."""
        files = _make_audio_upload()
        data = {"title": "Bad Language Meeting", "target_language": "xx"}
        response = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )

        assert response.status_code == 422

    async def test_upload_wav_file(self, auth_client: AsyncClient) -> None:
        """Upload a WAV file, expect 201 Created."""
        files = {"audio": ("meeting.wav", b"fake wav content", "audio/wav")}
        data = {"title": "WAV Meeting"}
        response = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )

        assert response.status_code == 201
        assert response.json()["audio_filename"] == "meeting.wav"

    async def test_upload_ogg_file(self, auth_client: AsyncClient) -> None:
        """Upload an OGG file, expect 201 Created."""
        files = {"audio": ("meeting.ogg", b"fake ogg content", "audio/ogg")}
        data = {"title": "OGG Meeting"}
        response = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )

        assert response.status_code == 201
        assert response.json()["audio_filename"] == "meeting.ogg"


class TestGetMeeting:
    """Tests for the GET /api/v1/meetings/{meeting_id} endpoint."""

    async def test_get_meeting_detail(self, auth_client: AsyncClient) -> None:
        """Get a specific meeting by ID, expect 200 with full details."""
        # Upload a meeting first
        files = _make_audio_upload("detail_meeting.mp3")
        data = {"title": "Detail Meeting"}
        upload_resp = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )
        assert upload_resp.status_code == 201
        meeting_id = upload_resp.json()["id"]

        # Retrieve the meeting detail
        response = await auth_client.get(f"{API_PREFIX}/meetings/{meeting_id}")

        assert response.status_code == 200
        result = response.json()
        assert result["id"] == meeting_id
        assert result["title"] == "Detail Meeting"
        # MeetingDetail schema includes these optional fields
        assert "transcription_text" in result
        assert "summary_json" in result

    async def test_get_nonexistent_meeting(self, auth_client: AsyncClient) -> None:
        """Get a meeting that doesn't exist, expect 404 Not Found."""
        fake_id = str(uuid.uuid4())
        response = await auth_client.get(f"{API_PREFIX}/meetings/{fake_id}")

        assert response.status_code == 404


class TestDeleteMeeting:
    """Tests for the DELETE /api/v1/meetings/{meeting_id} endpoint."""

    async def test_delete_meeting(self, auth_client: AsyncClient) -> None:
        """Delete a meeting, expect 204 No Content."""
        # Upload a meeting first
        files = _make_audio_upload("delete_meeting.mp3")
        data = {"title": "Delete Me"}
        upload_resp = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )
        assert upload_resp.status_code == 201
        meeting_id = upload_resp.json()["id"]

        # Delete the meeting
        response = await auth_client.delete(f"{API_PREFIX}/meetings/{meeting_id}")

        assert response.status_code == 204

        # Verify it is gone
        get_resp = await auth_client.get(f"{API_PREFIX}/meetings/{meeting_id}")
        assert get_resp.status_code == 404

    async def test_delete_meeting_not_found(self, auth_client: AsyncClient) -> None:
        """Delete a non-existent meeting, expect 404 Not Found."""
        fake_id = str(uuid.uuid4())
        response = await auth_client.delete(f"{API_PREFIX}/meetings/{fake_id}")

        assert response.status_code == 404


class TestTranscribeMeeting:
    """Tests for the POST /api/v1/meetings/{meeting_id}/transcribe endpoint."""

    async def test_transcribe_meeting(self, auth_client: AsyncClient) -> None:
        """Trigger transcription for a meeting (mock the Celery task)."""
        # Upload a meeting first
        files = _make_audio_upload("transcribe_meeting.mp3")
        data = {"title": "Transcribe Me"}
        upload_resp = await auth_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )
        assert upload_resp.status_code == 201
        meeting_id = upload_resp.json()["id"]

        # Mock the Celery task to avoid actually running it
        with patch("app.api.meetings.process_transcription") as mock_task:
            mock_task.delay = MagicMock(return_value=MagicMock(id="fake-task-id"))

            response = await auth_client.post(
                f"{API_PREFIX}/meetings/{meeting_id}/transcribe"
            )

        assert response.status_code == 200
        result = response.json()
        assert result["status"] == "transcribing"
        mock_task.delay.assert_called_once()

    async def test_transcribe_nonexistent_meeting(
        self, auth_client: AsyncClient
    ) -> None:
        """Transcribe a non-existent meeting, expect 404."""
        fake_id = str(uuid.uuid4())
        response = await auth_client.post(
            f"{API_PREFIX}/meetings/{fake_id}/transcribe"
        )

        assert response.status_code == 404

    async def test_transcribe_unauthenticated(
        self, async_client: AsyncClient
    ) -> None:
        """Transcribe without authentication, expect 401 Unauthorized."""
        response = await async_client.post(
            f"{API_PREFIX}/meetings/{str(uuid.uuid4())}/transcribe"
        )

        assert response.status_code == 401
