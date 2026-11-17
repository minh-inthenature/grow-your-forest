"""
Audio module for Grow Your Forest.
Plays user-provided rain audio in an infinite loop with volume control
using native Windows MCI (winmm.dll) on a dedicated worker thread, with
the non-blocking rain_service.ps1 WPF MediaPlayer as fallback.
Zero third-party package dependencies!
"""

import atexit
import ctypes
import os
import queue
import subprocess
import sys
import threading
import time

AUDIO_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
USER_AUDIO_PATH = os.path.join(AUDIO_DIR, "user_rain.mp3")
SERVICE_SCRIPT = os.path.join(AUDIO_DIR, "rain_service.ps1")
FALLBACK_WAV = os.path.join(AUDIO_DIR, "rain_master.wav")

CREATE_NO_WINDOW = 0x08000000


class RainSoundPlayer:
    """Manages playing, infinite looping, and smooth 400ms volume ramps of rain audio."""

    RAMP_DURATION_MS = 400
    RAMP_STEPS = 8

    def __init__(self, audio_path=USER_AUDIO_PATH):
        self.audio_path = audio_path
        self.is_playing = False
        self.volume = 70  # 0 to 100
        self._current_output_volume = 0
        self.last_ramp_ms = 0
        self._linux_active = False
        self._linux_proc = None
        self._linux_thread = None
        self._ps_ramp_gen = 0
        self._lock = threading.Lock()

        # Primary engine: single-threaded Windows MCI (winmm.dll) + watchdog
        self._alias = f"gyf_rain_{os.getpid()}_{id(self)}"
        self._cmd_queue = None
        self._worker = None
        self._mci_failed = False

        # Fallback engine: rain_service.ps1 subprocess
        self._proc = None

        atexit.register(self.stop_service)

    def _target_path(self):
        if self.audio_path and os.path.exists(self.audio_path):
            return self.audio_path
        if os.path.exists(FALLBACK_WAV):
            return FALLBACK_WAV
        return None

    # ──────────────── Primary Windows MCI Worker ────────────────

    def _mci_call(self, mci_fn, command):
        buf = ctypes.create_unicode_buffer(256)
        rc = mci_fn(command, buf, 256, 0)
        return rc, buf.value.strip()

    def _mci_query_state(self, mci_fn, alias):
        _, mode = self._mci_call(mci_fn, f"status {alias} mode")
        _, pos_s = self._mci_call(mci_fn, f"status {alias} position")
        try:
            pos_val = int(pos_s)
        except Exception:
            pos_val = 0
        return mode.lower(), pos_val

    def _mci_start_loop(self, mci_fn, alias, cur_vol, from_ms=None):
        self._mci_call(mci_fn, f"setaudio {alias} volume to {cur_vol * 10}")
        from_clause = f" from {from_ms}" if from_ms is not None else ""
        rc, _ = self._mci_call(mci_fn, f"play {alias}{from_clause} repeat")
        if rc != 0:
            # Retry without repeat flag; watchdog still loops cleanly
            rc, _ = self._mci_call(mci_fn, f"play {alias}{from_clause}")
        self._mci_call(mci_fn, f"setaudio {alias} volume to {cur_vol * 10}")
        return rc == 0

    def _mci_worker_loop(self, target_path, ready_ev, init_result):
        try:
            mci_fn = ctypes.windll.winmm.mciSendStringW
        except Exception:
            init_result["ok"] = False
            ready_ev.set()
            return

        alias = self._alias
        rc, _ = self._mci_call(mci_fn, f'open "{target_path}" type mpegvideo alias {alias}')
        if rc != 0:
            self._mci_call(mci_fn, f"close {alias}")
            init_result["ok"] = False
            ready_ev.set()
            return

        self._mci_call(mci_fn, f"set {alias} time format milliseconds")
        _, len_str = self._mci_call(mci_fn, f"status {alias} length")
        try:
            length_ms = int(len_str)
        except Exception:
            length_ms = 0

        active = False
        cur_vol = self.volume
        live_vol = 0.0
        ramp_target = None
        ramp_step_delta = 0.0
        pending_stop = False
        last_watchdog = time.monotonic()
        step_dt = (self.RAMP_DURATION_MS / 1000.0) / max(1, self.RAMP_STEPS)
        init_result["ok"] = True
        ready_ev.set()

        while True:
            wait_s = step_dt if ramp_target is not None else (0.35 if active else 2.0)
            try:
                op, arg, done_ev, out = self._cmd_queue.get(timeout=wait_s)
            except queue.Empty:
                op, arg, done_ev, out = None, None, None, None

            if op == "PLAY":
                pending_stop = False
                start_v = int(round(live_vol)) if active else 0
                active = self._mci_start_loop(mci_fn, alias, start_v)
                live_vol = float(start_v)
                self._current_output_volume = start_v
                if active and cur_vol != start_v:
                    ramp_target = float(cur_vol)
                    ramp_step_delta = (ramp_target - live_vol) / max(1, self.RAMP_STEPS)
                    self.last_ramp_ms = self.RAMP_DURATION_MS
                else:
                    ramp_target = None
                    ramp_step_delta = 0.0
                last_watchdog = time.monotonic()
                if out is not None:
                    out["ok"] = active
                if done_ev is not None:
                    done_ev.set()
                continue

            if op == "STOP":
                if active and live_vol > 1.0:
                    pending_stop = True
                    ramp_target = 0.0
                    ramp_step_delta = -live_vol / max(1, self.RAMP_STEPS)
                    self.last_ramp_ms = self.RAMP_DURATION_MS
                else:
                    pending_stop = False
                    active = False
                    ramp_target = None
                    live_vol = 0.0
                    self._current_output_volume = 0
                    self._mci_call(mci_fn, f"setaudio {alias} volume to 0")
                    self._mci_call(mci_fn, f"stop {alias}")
                    self._mci_call(mci_fn, f"seek {alias} to start")
                if out is not None:
                    out["ok"] = True
                if done_ev is not None:
                    done_ev.set()
                continue

            if op == "VOLUME":
                cur_vol = max(0, min(100, int(arg)))
                if active and not pending_stop:
                    ramp_target = float(cur_vol)
                    ramp_step_delta = (ramp_target - live_vol) / max(1, self.RAMP_STEPS // 2)
                else:
                    live_vol = float(cur_vol)
                    self._current_output_volume = cur_vol
                    self._mci_call(mci_fn, f"setaudio {alias} volume to {cur_vol * 10}")
                if out is not None:
                    out["ok"] = True
                if done_ev is not None:
                    done_ev.set()
                continue

            if op == "SEEK":
                pos_ms = max(0, int(arg))
                if active:
                    ok = self._mci_start_loop(mci_fn, alias, int(round(live_vol)), from_ms=pos_ms)
                else:
                    rc_s, _ = self._mci_call(mci_fn, f"seek {alias} to {pos_ms}")
                    ok = (rc_s == 0)
                if out is not None:
                    out["ok"] = ok
                if done_ev is not None:
                    done_ev.set()
                continue

            if op == "STATUS":
                mode, pos_val = self._mci_query_state(mci_fn, alias)
                if out is not None:
                    out["mode"] = mode
                    out["pos_ms"] = pos_val
                    out["length_ms"] = length_ms
                if done_ev is not None:
                    done_ev.set()
                continue

            if op == "QUIT":
                pending_stop = False
                ramp_target = None
                active = False
                self._current_output_volume = 0
                self._mci_call(mci_fn, f"stop {alias}")
                self._mci_call(mci_fn, f"close {alias}")
                if done_ev is not None:
                    done_ev.set()
                break

            # Advance smooth 400ms volume fade-in / fade-out ramp
            if ramp_target is not None:
                live_vol += ramp_step_delta
                done_ramp = (
                    (ramp_step_delta >= 0.0 and live_vol >= ramp_target)
                    or (ramp_step_delta <= 0.0 and live_vol <= ramp_target)
                )
                if done_ramp:
                    live_vol = ramp_target
                    ramp_target = None
                    ramp_step_delta = 0.0

                out_v = max(0, min(100, int(round(live_vol))))
                self._mci_call(mci_fn, f"setaudio {alias} volume to {out_v * 10}")
                self._current_output_volume = out_v

                if ramp_target is None and pending_stop:
                    pending_stop = False
                    active = False
                    self._mci_call(mci_fn, f"stop {alias}")
                    self._mci_call(mci_fn, f"seek {alias} to start")
                    continue

            # Watchdog tick while playing: guarantee infinite wrap even if codec drops repeat
            now = time.monotonic()
            if active and not pending_stop and (now - last_watchdog) >= 0.35:
                last_watchdog = now
                mode, pos_val = self._mci_query_state(mci_fn, alias)
                near_end = (length_ms > 500 and pos_val >= length_ms - 250)
                if mode != "playing" or near_end:
                    self._mci_start_loop(mci_fn, alias, int(round(live_vol)), from_ms=0)

    def _ensure_mci_worker(self):
        if self._mci_failed:
            return False
        if self._worker is not None and self._worker.is_alive():
            return True

        target_path = self._target_path()
        if not target_path:
            return False

        self._cmd_queue = queue.Queue()
        ready_ev = threading.Event()
        init_result = {"ok": False}
        t = threading.Thread(
            target=self._mci_worker_loop,
            args=(target_path, ready_ev, init_result),
            daemon=True,
            name="RainAudioMCI",
        )
        t.start()
        ready_ev.wait(timeout=3.0)
        if init_result.get("ok"):
            self._worker = t
            return True

        self._mci_failed = True
        self._cmd_queue = None
        return False

    def _mci_request(self, op, arg=None, timeout=2.0):
        if self._cmd_queue is None or self._worker is None or not self._worker.is_alive():
            return None
        ev = threading.Event()
        out = {}
        self._cmd_queue.put((op, arg, ev, out))
        if ev.wait(timeout=timeout):
            return out
        return None

    # ──────────────── PowerShell Fallback Service ────────────────

    def _ensure_ps_service(self):
        if self._proc is not None and self._proc.poll() is None:
            return True

        target_path = self._target_path()
        if not target_path or not os.path.exists(SERVICE_SCRIPT):
            return False

        cmd = [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy", "Bypass",
            "-WindowStyle", "Hidden",
            "-File", SERVICE_SCRIPT,
            "-AudioPath", target_path,
        ]
        try:
            self._proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                creationflags=CREATE_NO_WINDOW,
            )
            ready = self._proc.stdout.readline().strip()
            if ready == "READY":
                self._send_ps_cmd(f"VOLUME {self.volume}")
                return True
            self._proc = None
            return False
        except Exception as e:
            print(f"Error starting audio service: {e}")
            self._proc = None
            return False

    def _send_ps_cmd(self, command):
        try:
            if self._proc and self._proc.poll() is None and self._proc.stdin:
                self._proc.stdin.write(command.strip() + "\n")
                self._proc.stdin.flush()
                return self._proc.stdout.readline().strip()
        except Exception:
            pass
        return None

    def _ramp_ps_volume(self, start_vol, end_vol, stop_after=False):
        """Smoothly ramp PowerShell MediaPlayer volume over RAMP_DURATION_MS."""
        self._ps_ramp_gen += 1
        gen = self._ps_ramp_gen
        self.last_ramp_ms = self.RAMP_DURATION_MS
        steps = max(1, self.RAMP_STEPS)
        step_dt = (self.RAMP_DURATION_MS / 1000.0) / steps

        def _worker():
            for i in range(1, steps + 1):
                if self._ps_ramp_gen != gen:
                    return
                v = int(round(start_vol + (end_vol - start_vol) * (i / steps)))
                v = max(0, min(100, v))
                with self._lock:
                    if self._ps_ramp_gen != gen:
                        return
                    self._current_output_volume = v
                    if self._proc and self._proc.poll() is None:
                        self._send_ps_cmd(f"VOLUME {v}")
                if i < steps:
                    time.sleep(step_dt)
            if stop_after and self._ps_ramp_gen == gen:
                with self._lock:
                    if self._proc and self._proc.poll() is None:
                        self._send_ps_cmd("STOP")

        threading.Thread(target=_worker, daemon=True, name="RainPSRamp").start()

    # ──────────────── Linux Audio Support ────────────────

    def _find_linux_player(self):
        import shutil
        for player in ("mpv", "ffplay", "paplay", "pw-play", "aplay"):
            if shutil.which(player):
                return player
        return None

    def _play_linux(self):
        self._stop_linux()
        backend = self._find_linux_player()
        if not backend:
            self.is_playing = True
            return True

        target_path = self._target_path()
        wav_path = FALLBACK_WAV if os.path.exists(FALLBACK_WAV) else os.path.join(AUDIO_DIR, "rain_master.wav")
        play_path = wav_path if (backend in ("paplay", "pw-play", "aplay") and os.path.exists(wav_path)) else target_path
        if not play_path or not os.path.exists(play_path):
            self.is_playing = False
            return False

        def _linux_loop():
            while self._linux_active:
                vol = max(0, min(100, int(self.volume)))
                if backend == "mpv":
                    cmd = ["mpv", "--no-video", "--loop=inf", f"--volume={vol}", play_path]
                elif backend == "ffplay":
                    cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-volume", str(vol), "-loop", "0", play_path]
                elif backend == "paplay":
                    pa_vol = int(round(65536 * (vol / 100.0)))
                    cmd = ["paplay", f"--volume={pa_vol}", play_path]
                elif backend == "pw-play":
                    cmd = ["pw-play", f"--volume={vol / 100.0:.2f}", play_path]
                elif backend == "aplay":
                    cmd = ["aplay", play_path]
                else:
                    break
                try:
                    self._linux_proc = subprocess.Popen(
                        cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    self._linux_proc.wait()
                except Exception:
                    break
                if backend in ("mpv", "ffplay"):
                    break

        self._linux_active = True
        self._linux_thread = threading.Thread(target=_linux_loop, daemon=True, name="LinuxRainLoop")
        self._linux_thread.start()
        self.is_playing = True
        return True

    def _stop_linux(self):
        self._linux_active = False
        if self._linux_proc and self._linux_proc.poll() is None:
            try:
                self._linux_proc.terminate()
            except Exception:
                pass
            self._linux_proc = None
        self.is_playing = False

    # ──────────────── Public API ────────────────

    def play(self):
        """Start playing ambient rain sound in an infinite loop with a 400ms fade-in."""
        with self._lock:
            if sys.platform.startswith("linux"):
                return self._play_linux()

            if self._ensure_mci_worker():
                res = self._mci_request("PLAY")
                if res and res.get("ok"):
                    self.is_playing = True
                    return True

            if not self._ensure_ps_service():
                return False
            self._send_ps_cmd("VOLUME 0")
            self._current_output_volume = 0
            res = self._send_ps_cmd("PLAY")
            if res and "OK" in res:
                self.is_playing = True
                self._ramp_ps_volume(0, self.volume, stop_after=False)
                return True
            return False

    def stop(self):
        """Fade out ambient rain sound smoothly over 400ms before stopping."""
        with self._lock:
            if sys.platform.startswith("linux"):
                self._stop_linux()
                return

            if self._worker is not None and self._worker.is_alive():
                self._mci_request("STOP")
            if self._proc and self._proc.poll() is None:
                if self.is_playing and self._current_output_volume > 1:
                    self._ramp_ps_volume(self._current_output_volume, 0, stop_after=True)
                else:
                    self._ps_ramp_gen += 1
                    self._send_ps_cmd("STOP")
            self.is_playing = False

    def toggle(self):
        """Toggle rain sound on/off."""
        if self.is_playing:
            self.stop()
            return False
        return self.play()

    def set_volume(self, volume):
        """Set volume (0 to 100) and update playback seamlessly."""
        self.volume = max(0, min(100, int(volume)))
        with self._lock:
            if sys.platform.startswith("linux"):
                if self._linux_active:
                    self._play_linux()
                return
            if self._worker is not None and self._worker.is_alive():
                self._mci_request("VOLUME", self.volume)
            if self._proc and self._proc.poll() is None:
                self._send_ps_cmd(f"VOLUME {self.volume}")

    def seek_ms(self, ms):
        """Seek playback position in milliseconds (useful for verification tests)."""
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                res = self._mci_request("SEEK", ms)
                return bool(res and res.get("ok"))
            return False

    def get_status(self):
        """Return (mode, pos_ms, length_ms) for the active MCI worker."""
        with self._lock:
            if self._worker is not None and self._worker.is_alive():
                res = self._mci_request("STATUS")
                if res:
                    return res.get("mode", ""), res.get("pos_ms", 0), res.get("length_ms", 0)
            return ("playing" if self.is_playing else "stopped"), 0, 0

    def stop_service(self):
        """Clean shutdown of background audio worker/service."""
        with self._lock:
            if sys.platform.startswith("linux"):
                self._stop_linux()
                return

            if self._worker is not None and self._worker.is_alive() and self._cmd_queue is not None:
                try:
                    self._mci_request("QUIT", timeout=1.5)
                    self._worker.join(timeout=1.5)
                except Exception:
                    pass
                self._worker = None
                self._cmd_queue = None
            if self._proc and self._proc.poll() is None:
                try:
                    self._send_ps_cmd("QUIT")
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
