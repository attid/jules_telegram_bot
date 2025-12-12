
import asyncio
import re
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import os

# We mock aiogram.Bot so it doesn't validate the token
with patch('aiogram.client.bot.Bot.__init__', return_value=None):
    from jules_bot.bot import _send_session_info, cmd_info_regex, cmd_activities_dynamic, ADMIN_CHAT_ID

class TestInfoLogic(unittest.IsolatedAsyncioTestCase):

    async def test_send_session_info_success(self):
        """Test _send_session_info helper with valid data."""
        # Mock message
        mock_message = AsyncMock()

        # Mock jules_client in bot module
        with patch('jules_bot.bot.jules_client') as mock_client:
            mock_client.get_session.return_value = {
                "id": "sessions/123456",
                "title": "Test Session",
                "state": "ACTIVE",
                "url": "https://example.com"
            }

            await _send_session_info(mock_message, "123456")

            # Verify get_session called
            mock_client.get_session.assert_called_with(session_id="123456")

            # Verify response sent
            # We expect 2 calls: one for "Fetching..." and one for the result
            self.assertEqual(mock_message.answer.call_count, 2)

            # check the second call args
            args, kwargs = mock_message.answer.call_args
            text = args[0]
            self.assertIn("123456", text)
            self.assertIn("Test Session", text)
            self.assertIn("ACTIVE", text)
            self.assertIn("/list_activities_123456", text)

    async def test_send_session_info_not_found(self):
        """Test _send_session_info helper when session not found."""
        mock_message = AsyncMock()

        with patch('jules_bot.bot.jules_client') as mock_client:
            mock_client.get_session.return_value = {} # Empty dict for error/not found

            await _send_session_info(mock_message, "999")

            self.assertEqual(mock_message.answer.call_count, 2)
            args, kwargs = mock_message.answer.call_args
            text = args[0]
            self.assertIn("not found", text)

    async def test_cmd_info_regex(self):
        """Test the regex handler logic extraction."""
        mock_message = AsyncMock()
        mock_message.chat.id = ADMIN_CHAT_ID
        mock_message.text = "/info_12345"

        # We need to mock _send_session_info since we are testing the extraction here
        with patch('jules_bot.bot._send_session_info', new_callable=AsyncMock) as mock_send:
            await cmd_info_regex(mock_message)
            mock_send.assert_called_with(mock_message, "12345")

    async def test_cmd_activities_dynamic(self):
        """Test /list_activities_<id> handler."""
        mock_message = AsyncMock()
        mock_message.chat.id = ADMIN_CHAT_ID
        mock_message.text = "/list_activities_555"

        with patch('jules_bot.bot.jules_client') as mock_client:
            mock_client.list_activities.return_value = {
                "activities": [
                    {"type": "COMMENT", "createTime": "2023-10-10T10:00:00Z"}
                ]
            }

            await cmd_activities_dynamic(mock_message)

            mock_client.list_activities.assert_called_with(session_id="555", page_size=10)

            args, kwargs = mock_message.answer.call_args
            text = args[0]
            self.assertIn("COMMENT", text)
            self.assertIn("2023-10-10", text)

if __name__ == "__main__":
    unittest.main()
