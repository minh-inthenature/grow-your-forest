#!/usr/bin/env python3
"""
Grow Your Forest - Debian / Ubuntu (.deb) Package Builder
Builds a standard, installable .deb package for Ubuntu / Debian.
Can run natively on Ubuntu (via dpkg-deb) or on Windows / macOS (via built-in Python packager).
"""

import io
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import time

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VERSION = "1.0.1"
PKG_NAME = "grow-your-forest"
PKG_ARCH = "all"
DEB_FILENAME = f"{PKG_NAME}_{VERSION}_{PKG_ARCH}.deb"
DIST_DIR = os.path.join(REPO_DIR, "dist")
OUTPUT_DEB = os.path.join(DIST_DIR, DEB_FILENAME)


def calculate_dir_size_kb(path):
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return max(1, total // 1024)


def create_staging_tree(staging_dir):
    """Populate Linux filesystem tree in staging directory."""
    os.makedirs(staging_dir, exist_ok=True)

    debian_dir = os.path.join(staging_dir, "DEBIAN")
    bin_dir = os.path.join(staging_dir, "usr", "bin")
    apps_dir = os.path.join(staging_dir, "usr", "share", "applications")
    pixmaps_dir = os.path.join(staging_dir, "usr", "share", "pixmaps")
    icon_dir = os.path.join(staging_dir, "usr", "share", "icons", "hicolor", "64x64", "apps")
    fonts_install_dir = os.path.join(staging_dir, "usr", "share", "fonts", "truetype", "grow-your-forest")
    app_install_dir = os.path.join(staging_dir, "usr", "share", "grow-your-forest")

    for d in (debian_dir, bin_dir, apps_dir, pixmaps_dir, icon_dir, fonts_install_dir, app_install_dir):
        os.makedirs(d, exist_ok=True)

    # 1. Application Files
    app_files = [
        "app.py",
        "audio_player.py",
        "database.py",
        "scenery.py",
        "tree_renderer.py",
        "forest_data.db",
        "forest.ico",
        "forest.png",
        "user_rain.mp3",
        "rain_master.wav",
        "README.md",
    ]
    for fname in app_files:
        src = os.path.join(REPO_DIR, fname)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(app_install_dir, fname))

    # Fonts in app directory
    fonts_src = os.path.join(REPO_DIR, "fonts")
    if os.path.isdir(fonts_src):
        fonts_dest = os.path.join(app_install_dir, "fonts")
        if os.path.exists(fonts_dest):
            shutil.rmtree(fonts_dest)
        shutil.copytree(fonts_src, fonts_dest)

        # Also copy TTF to system font directory
        for ff in os.listdir(fonts_src):
            if ff.lower().endswith(".ttf"):
                shutil.copy2(os.path.join(fonts_src, ff), os.path.join(fonts_install_dir, ff))

    # 2. Icons
    png_icon = os.path.join(REPO_DIR, "forest.png")
    if os.path.exists(png_icon):
        shutil.copy2(png_icon, os.path.join(pixmaps_dir, "grow-your-forest.png"))
        shutil.copy2(png_icon, os.path.join(icon_dir, "grow-your-forest.png"))

    # 3. Desktop Entry (/usr/share/applications/grow-your-forest.desktop)
    desktop_content = """[Desktop Entry]
Version=1.0
Type=Application
Name=Grow Your Forest
GenericName=Focus Timer
Comment=Cozy desktop focus timer with tree growth and ambient rain
Icon=grow-your-forest
Exec=grow-your-forest
Terminal=false
Categories=Utility;Education;Office;
Keywords=focus;timer;pomodoro;study;forest;productivity;
StartupWMClass=GrowYourForest
"""
    with open(os.path.join(apps_dir, "grow-your-forest.desktop"), "w", encoding="utf-8", newline="\n") as f:
        f.write(desktop_content)

    # 4. Executable Wrapper (/usr/bin/grow-your-forest)
    bin_wrapper = """#!/bin/sh
# Launcher wrapper for Grow Your Forest
exec /usr/bin/python3 /usr/share/grow-your-forest/app.py "$@"
"""
    bin_path = os.path.join(bin_dir, "grow-your-forest")
    with open(bin_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(bin_wrapper)
    try:
        os.chmod(bin_path, 0o755)
    except Exception:
        pass

    # 5. Installed size
    installed_size = calculate_dir_size_kb(staging_dir)

    # 6. DEBIAN/control
    control_content = f"""Package: {PKG_NAME}
Version: {VERSION}
Section: utils
Priority: optional
Architecture: {PKG_ARCH}
Installed-Size: {installed_size}
Depends: python3 (>= 3.8), python3-tk, alsa-utils | pulseaudio-utils | mpv | ffmpeg
Maintainer: Trinh Duc Minh <minhtrinhduc4@gmail.com>
Homepage: https://github.com/minh-inthenature/grow-your-forest
Description: Cozy desktop focus timer with ambient rain and forest sanctuary
 Grow Your Forest is a cozy desktop focus timer built with Python & Tkinter.
 Complete study/focus sessions to grow distinct trees (Cherry Blossom, Pine,
 Angel Oak, Classic Oak) across a layered 2D forest sanctuary with ambient
 rain sound and four atmospheric themes: Morning, Afternoon, Night, and Chill.
 Features local SQLite progress tracking, focus statistics, achievements,
 and smooth theme transitions.
"""
    with open(os.path.join(debian_dir, "control"), "w", encoding="utf-8", newline="\n") as f:
        f.write(control_content)

    # 7. DEBIAN/postinst
    postinst_content = """#!/bin/sh
set -e

if [ "$1" = "configure" ]; then
    if which update-desktop-database >/dev/null 2>&1; then
        update-desktop-database -q /usr/share/applications || true
    fi
    if which fc-cache >/dev/null 2>&1; then
        fc-cache -f /usr/share/fonts/truetype/grow-your-forest >/dev/null 2>&1 || true
    fi
    if which gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -q /usr/share/icons/hicolor || true
    fi
fi

exit 0
"""
    postinst_path = os.path.join(debian_dir, "postinst")
    with open(postinst_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(postinst_content)
    try:
        os.chmod(postinst_path, 0o755)
    except Exception:
        pass

    # 8. DEBIAN/postrm
    postrm_content = """#!/bin/sh
set -e

if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then
    if which update-desktop-database >/dev/null 2>&1; then
        update-desktop-database -q /usr/share/applications || true
    fi
    if which fc-cache >/dev/null 2>&1; then
        fc-cache -f >/dev/null 2>&1 || true
    fi
    if which gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -q /usr/share/icons/hicolor || true
    fi
fi

exit 0
"""
    postrm_path = os.path.join(debian_dir, "postrm")
    with open(postrm_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(postrm_content)
    try:
        os.chmod(postrm_path, 0o755)
    except Exception:
        pass


def make_ar_header(name, size, mode=0o100644, mtime=None):
    """Create a 60-byte standard Unix ar header."""
    name_str = name.ljust(16)[:16]
    mtime_val = int(mtime or time.time())
    mtime_str = str(mtime_val).ljust(12)[:12]
    uid_str = "0".ljust(6)[:6]
    gid_str = "0".ljust(6)[:6]
    mode_str = oct(mode)[2:].rjust(8)[:8]
    size_str = str(size).ljust(10)[:10]
    trailer = b"\x60\n"
    hdr = (name_str + mtime_str + uid_str + gid_str + mode_str + size_str).encode("ascii") + trailer
    assert len(hdr) == 60, f"Invalid AR header length: {len(hdr)}"
    return hdr


def build_deb_pure_python(staging_dir, output_deb_path):
    """Build .deb file without requiring dpkg-deb tool."""
    now = int(time.time())

    # Build control.tar.gz
    debian_dir = os.path.join(staging_dir, "DEBIAN")
    control_buf = io.BytesIO()
    with tarfile.open(fileobj=control_buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        # Add root entry ./
        root_ti = tarfile.TarInfo(name="./")
        root_ti.type = tarfile.DIRTYPE
        root_ti.mode = 0o755
        root_ti.mtime = now
        root_ti.uname = "root"
        root_ti.gname = "root"
        tar.addfile(root_ti)

        for fname in sorted(os.listdir(debian_dir)):
            full_p = os.path.join(debian_dir, fname)
            arcname = f"./{fname}"
            ti = tarfile.TarInfo(name=arcname)
            ti.size = os.path.getsize(full_p)
            ti.mtime = now
            ti.uname = "root"
            ti.gname = "root"
            if fname in ("postinst", "postrm", "preinst", "prerm"):
                ti.mode = 0o755
            else:
                ti.mode = 0o644
            with open(full_p, "rb") as f:
                tar.addfile(ti, f)
    control_data = control_buf.getvalue()

    # Build data.tar.gz
    data_buf = io.BytesIO()
    with tarfile.open(fileobj=data_buf, mode="w:gz", format=tarfile.GNU_FORMAT) as tar:
        usr_dir = os.path.join(staging_dir, "usr")
        for root, dirs, files in os.walk(usr_dir):
            rel_dir = os.path.relpath(root, staging_dir).replace("\\", "/")
            dir_ti = tarfile.TarInfo(name=f"./{rel_dir}/")
            dir_ti.type = tarfile.DIRTYPE
            dir_ti.mode = 0o755
            dir_ti.mtime = now
            dir_ti.uname = "root"
            dir_ti.gname = "root"
            tar.addfile(dir_ti)

            for f in sorted(files):
                full_fp = os.path.join(root, f)
                rel_fp = os.path.relpath(full_fp, staging_dir).replace("\\", "/")
                file_ti = tarfile.TarInfo(name=f"./{rel_fp}")
                file_ti.size = os.path.getsize(full_fp)
                file_ti.mtime = now
                file_ti.uname = "root"
                file_ti.gname = "root"
                if rel_fp.startswith("usr/bin/"):
                    file_ti.mode = 0o755
                else:
                    file_ti.mode = 0o644
                with open(full_fp, "rb") as fh:
                    tar.addfile(file_ti, fh)
    data_data = data_buf.getvalue()

    # debian-binary content
    deb_binary_data = b"2.0\n"

    # Assemble ar archive
    os.makedirs(os.path.dirname(output_deb_path), exist_ok=True)
    with open(output_deb_path, "wb") as deb:
        deb.write(b"!<arch>\n")

        # 1. debian-binary
        deb.write(make_ar_header("debian-binary", len(deb_binary_data), 0o100644, now))
        deb.write(deb_binary_data)
        if len(deb_binary_data) % 2 != 0:
            deb.write(b"\n")

        # 2. control.tar.gz
        deb.write(make_ar_header("control.tar.gz", len(control_data), 0o100644, now))
        deb.write(control_data)
        if len(control_data) % 2 != 0:
            deb.write(b"\n")

        # 3. data.tar.gz
        deb.write(make_ar_header("data.tar.gz", len(data_data), 0o100644, now))
        deb.write(data_data)
        if len(data_data) % 2 != 0:
            deb.write(b"\n")


def build_deb():
    """Main build entrypoint."""
    staging_dir = os.path.join(REPO_DIR, "build", "deb_staging")
    if os.path.exists(staging_dir):
        shutil.rmtree(staging_dir)

    print(f"Building {DEB_FILENAME}...")
    create_staging_tree(staging_dir)

    os.makedirs(DIST_DIR, exist_ok=True)

    # Use dpkg-deb if available (on Linux/Ubuntu)
    dpkg_deb = shutil.which("dpkg-deb")
    if dpkg_deb:
        print(f"Using native dpkg-deb: {dpkg_deb}")
        cmd = [dpkg_deb, "--build", "--root-owner-group", staging_dir, OUTPUT_DEB]
        subprocess.run(cmd, check=True)
    else:
        print("dpkg-deb not found; using pure-Python standard AR packager...")
        build_deb_pure_python(staging_dir, OUTPUT_DEB)

    size = os.path.getsize(OUTPUT_DEB)
    print(f"\n[SUCCESS] Debian package created successfully:")
    print(f"  Path: {OUTPUT_DEB}")
    print(f"  Size: {size:,} bytes ({size / (1024 * 1024):.2f} MB)")
    return OUTPUT_DEB


if __name__ == "__main__":
    build_deb()
