"""
Audio module for Grow Your Forest.
Plays user-provided rain audio in an infinite loop with volume control
using Windows native WPF MediaPlayer via rain_service.ps1.
Zero third-party package dependencies!
"""

import atexit
import os
import sys
import subprocess
import threading
import time

AUDIO_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
USER_AUDIO_PATH = os.path.join(AUDIO_DIR, "user_rain.mp3")
SERVICE_SCRIPT = os.path.join(AUDIO_DIR, "rain_service.ps1")
FALLBACK_WAV = os.path.join(AUDIO_DIR, "rain_master.wav")

CREATE_NO_WINDOW = 0x08000000


class RainSoundPlayer:
    """Manages playing, infinite looping, and volume control of rain audio."""

    def __init__(self, audio_path=USER_AUDIO_PATH):
        self.audio_path = audio_path
        self.is_playing = False
        self.volume = 70  # 0 to 100
        self._proc = None
        self._lock = threading.Lock()

        atexit.register(self.stop_service)

    def _ensure_service(self):
        """Ensure the background powershell media player service is running."""
        with self._lock:
            if self._proc is not None and self._proc.poll() is None:
                return True

            target_path = self.audio_path if os.path.exists(self.audio_path) else FALLBACK_WAV
            if not os.path.exists(target_path):
                return False

            cmd = [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy", "Bypass",
                "-WindowStyle", "Hidden",
                "-File", SERVICE_SCRIPT,
                "-AudioPath", target_path
            ]

            try:
                self._proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True,
                    bufsize=1,
                    creationflags=CREATE_NO_WINDOW
                )

                # Wait for READY signal
                ready = self._proc.stdout.readline().strip()
                if ready == "READY":
                    # Apply initial volume
                    self._send_cmd(f"VOLUME {self.volume}")
                    return True
                else:
                    self._proc = None
                    return False
            except Exception as e:
                print(f"Error starting audio service: {e}")
                self._proc = None
                return False

    def _send_cmd(self, command):
        """Send a single command to the service."""
        try:
            if self._proc and self._proc.poll() is None and self._proc.stdin:
                self._proc.stdin.write(command.strip() + "\n")
                self._proc.stdin.flush()
                # Read acknowledgement line
                res = self._proc.stdout.readline().strip()
                return res
        except Exception:
            pass
        return None

    def play(self):
        """Start playing ambient rain sound in an infinite loop."""
        if not self._ensure_service():
            return False

        with self._lock:
            res = self._send_cmd("PLAY")
            if res and "OK" in res:
                self.is_playing = True
                return True
            return False

    def stop(self):
        """Stop playing ambient rain sound."""
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._send_cmd("STOP")
            self.is_playing = False

    def toggle(self):
        """Toggle rain sound on/off."""
        if self.is_playing:
            self.stop()
            return False
        else:
            return self.play()

    def set_volume(self, volume):
        """Set volume (0 to 100) and update playback seamlessly."""
        self.volume = max(0, min(100, int(volume)))
        with self._lock:
            if self._proc and self._proc.poll() is None:
                self._send_cmd(f"VOLUME {self.volume}")

    def stop_service(self):
        """Clean shutdown of background audio service."""
        with self._lock:
            if self._proc and self._proc.poll() is None:
                try:
                    self._send_cmd("QUIT")
                    self._proc.wait(timeout=1.5)
                except Exception:
                    try:
                        self._proc.kill()
                    except Exception:
                        pass
                self._proc = None
            self.is_playing = False


# Global player instance
player = RainSoundPlayer()
