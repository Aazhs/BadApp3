import subprocess
import sys
import unittest
from pathlib import Path
from threading import Event
from unittest.mock import Mock, patch

from PIL import Image

from functions import (
    DEFAULT_PRESET,
    CaptureRegion,
    CodexError,
    RequestCancelled,
    ask_codex,
    build_command,
    describe_failure,
)
from main import CAPTURE_QUESTION, ScreenAssistant


class CaptureRegionTests(unittest.TestCase):
    def test_retina_drag_maps_to_image_pixels(self):
        region = CaptureRegion.from_drag(
            (300, 200), (50, 20), (1440, 900), (2880, 1800)
        )
        self.assertEqual(region, CaptureRegion((100, 40, 600, 400), (2880, 1800)))

    def test_outside_drag_is_clamped_and_small_drag_is_ignored(self):
        self.assertEqual(
            CaptureRegion.from_drag((-10, 8), (120, 92), (100, 100), (200, 200)).box,
            (0, 16, 200, 184),
        )
        self.assertIsNone(CaptureRegion.from_drag((1, 1), (3, 5), (100, 100), (200, 200)))


class CodexTests(unittest.TestCase):
    def test_command_sets_model_and_attaches_every_image(self):
        command = build_command("codex", DEFAULT_PRESET, ["capture-1.png", "capture-2.png"])
        self.assertIn("gpt-6-luna", command)
        self.assertIn("model_reasoning_effort=none", command)
        self.assertIn("--ephemeral", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertEqual(command[-3:], ["--image=capture-1.png", "--image=capture-2.png", "-"])

    def test_passes_prompt_and_images_and_reads_answer_after_waiting(self):
        script = """
import sys
import time
from pathlib import Path

assert "What color?" in sys.stdin.read()
assert Path("capture-1.png").is_file()
assert Path("capture-2.png").is_file()
time.sleep(0.25)
Path("answer.txt").write_text("Blue", encoding="utf-8")
"""
        image = Image.new("RGB", (10, 10), "blue")
        with patch("functions.build_command", return_value=[sys.executable, "-c", script]):
            answer = ask_codex("codex", DEFAULT_PRESET, "What color?", (image, image), Event())
        self.assertEqual(answer, "Blue")

    def test_timeout_cleans_up_subprocess_and_workspace(self):
        with (
            patch("functions.REQUEST_TIMEOUT", 0.25),
            patch("functions.build_command", return_value=[
                sys.executable, "-c", "import time; time.sleep(60)"
            ]),
            patch("functions.subprocess.Popen", wraps=subprocess.Popen) as popen,
        ):
            with self.assertRaisesRegex(CodexError, "timed out"):
                ask_codex("codex", DEFAULT_PRESET, "Hello", (), Event())
        self.assertFalse(Path(popen.call_args.kwargs["cwd"]).exists())

    def test_cancelled_request_does_not_start_process(self):
        cancel = Event()
        cancel.set()
        with patch("functions.subprocess.Popen") as process:
            with self.assertRaises(RequestCancelled):
                ask_codex("codex", DEFAULT_PRESET, "Hello", (), cancel)
            process.assert_not_called()

    def test_json_errors_are_explained_without_raw_diagnostics(self):
        event = '{"type":"turn.failed","error":{"message":"usage limit: private detail"}}'
        message = describe_failure(event, "unrelated stderr")
        self.assertIn("allowance", message)
        self.assertNotIn("private detail", message)


class CaptureAnswerTests(unittest.TestCase):
    def test_capture_submits_only_the_new_crop(self):
        app = Mock()
        saved_image = Image.new("RGB", (20, 20), "red")
        app.images = [saved_image]
        screen = Image.new("RGB", (100, 100), "blue")
        region = CaptureRegion((10, 20, 40, 70), screen.size)

        ScreenAssistant.finish_capture(app, screen, region)

        app.start_request.assert_called_once_with(
            (app.latest_capture,), default_question=CAPTURE_QUESTION
        )
        self.assertEqual(app.latest_capture.size, (30, 50))
        self.assertEqual(app.latest_capture.getpixel((0, 0)), (0, 0, 255))
        self.assertEqual(app.images, [saved_image])

    def test_choosing_an_area_does_not_send_a_request(self):
        app = Mock()
        screen = Image.new("RGB", (100, 100))
        region = CaptureRegion((10, 20, 40, 70), screen.size)

        ScreenAssistant.finish_capture(app, screen, region, ask=False)

        self.assertEqual(app.region, region)
        app.start_request.assert_not_called()


if __name__ == "__main__":
    unittest.main()
