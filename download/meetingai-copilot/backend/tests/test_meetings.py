"""
Tests for meetings API endpoints.

Covers audio upload, listing, detail retrieval, and deletion scenarios
including authentication enforcement and not-found handling.
"""

import uuid

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


class TestUploadMeeting:
    """Tests for the POST /api/v1/meetings/upload endpoint."""

    async def test_upload_audio_success(self, auth_client: AsyncClient) -> None:
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

    async def test_upload_no_auth(self, async_client: AsyncClient) -> None:
        """Upload without authentication, expect 403 Forbidden."""
        files = _make_audio_upload()
        data = {"title": "Unauthorized Upload"}
        response = await async_client.post(
            f"{API_PREFIX}/meetings/upload", files=files, data=data
        )

        assert response.status_code == 403


class TestListMeetings:
    """Tests for the GET /api/v1/meetings/ endpoint."""

    async def test_list_meetings(self, auth_client: AsyncClient) -> None:
        """List meetings for an authenticated user, expect 200 with list."""
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

    async def test_get_meeting_not_found(self, auth_client: AsyncClient) -> None:
        """Get a non-existent meeting, expect 404 Not Found."""
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
