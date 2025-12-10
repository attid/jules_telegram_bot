import unittest
from unittest.mock import MagicMock, AsyncMock, patch
import sys
import os

# Add the project root to sys.path so we can import bot
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'jules_bot')))

# We need to mock the environment variables before importing bot
with patch.dict(os.environ, {
    "TG_TOKEN": "fake_tg_token",
    "JULES_TOKEN": "fake_jules_token",
    "ADMIN_CHAT_ID": "123456"
}):
    # Import the module to test.
    # Note: We need to be careful because importing bot.py executes code.
    # Ideally, we should refactor bot.py to not run global code, but for now we mock what we can.
    # We will mock asyncio.run to prevent the main block from running if we were running bot.py directly,
    # but here we are importing it.
    pass

# To avoid importing the actual bot and triggering its initialization (which requires env vars and connects to APIs),
# we will duplicate the *logic* of the monitoring loop here for testing, or better,
# we can refactor the monitoring logic into a standalone class/function in a new file.
# However, given the constraints, I will create a test that implements the *proposed* logic
# to verify it works as expected before applying it to the main file.

class TestMonitoringLogic(unittest.TestCase):
    def setUp(self):
        self.session_states = {}
        self.changes_detected = []
        self.logs = []

    def log(self, message):
        self.logs.append(message)

    def run_check(self, sessions):
        # This function mimics the proposed logic for the monitoring loop
        changes = []

        for session in sessions:
            s_id = session.get("id")
            s_title = session.get("title", "No Title")
            s_state = session.get("state", "UNKNOWN")

            if not s_id:
                continue

            # Log to console requirement
            self.log(f"Checking session {s_id} ({s_title}): {s_state}")

            previous_state = self.session_states.get(s_id)

            should_notify = False

            # Condition 1: Critical status on first sight
            if previous_state is None:
                if s_state in ["AWAITING_PLAN_APPROVAL", "AWAITING_USER_FEEDBACK"]:
                    should_notify = True

            # Condition 2: State change
            elif s_state != previous_state:
                should_notify = True

            if should_notify:
                changes.append(f"Session: {s_title} ({s_id})\nStatus: {s_state}")

            # Update state
            self.session_states[s_id] = s_state

        return changes

    def test_monitoring_flow(self):
        # Iteration 1
        sessions_1 = [
            {"id": "1", "title": "Task 1", "state": "RUNNING"},
            {"id": "2", "title": "Task 2", "state": "AWAITING_PLAN_APPROVAL"},
            {"id": "3", "title": "Task 3", "state": "COMPLETED"}
        ]

        changes_1 = self.run_check(sessions_1)

        # Expectation:
        # Task 1: No alert (Running is not critical for first sight)
        # Task 2: Alert (Awaiting Plan Approval is critical)
        # Task 3: No alert

        self.assertTrue(any("Task 2" in c for c in changes_1), "Should notify about Task 2 (AWAITING_PLAN_APPROVAL)")
        self.assertFalse(any("Task 1" in c for c in changes_1), "Should NOT notify about Task 1 (RUNNING)")
        self.assertFalse(any("Task 3" in c for c in changes_1), "Should NOT notify about Task 3 (COMPLETED)")

        # Verify Logs
        self.assertTrue(any("Checking session 1" in l for l in self.logs))
        self.assertTrue(any("Checking session 2" in l for l in self.logs))

        # Clear logs for next run
        self.logs = []

        # Iteration 2
        sessions_2 = [
            {"id": "1", "title": "Task 1", "state": "COMPLETED"}, # Changed from RUNNING
            {"id": "2", "title": "Task 2", "state": "AWAITING_PLAN_APPROVAL"}, # No change
            {"id": "4", "title": "Task 4", "state": "AWAITING_USER_FEEDBACK"} # New critical
        ]

        changes_2 = self.run_check(sessions_2)

        # Expectation:
        # Task 1: Alert (Changed from RUNNING to COMPLETED)
        # Task 2: No alert (Same state)
        # Task 4: Alert (New critical)

        self.assertTrue(any("Task 1" in c for c in changes_2), "Should notify about Task 1 change")
        self.assertFalse(any("Task 2" in c for c in changes_2), "Should NOT notify about Task 2 (No change)")
        self.assertTrue(any("Task 4" in c for c in changes_2), "Should notify about Task 4 (New Critical)")

if __name__ == '__main__':
    unittest.main()
