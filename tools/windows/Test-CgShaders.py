#!/usr/bin/env python3
"""Compile RoR's real managed PSSM shader entry points with the shipped Cg runtime.

Unlike source-contract checks, this invokes NVIDIA's Cg compiler using exactly
the Direct3D profiles listed in depthshadows.program. No GPU is required.
This cannot validate the generated terrain shader or actual scene rendering.
"""
from __future__ import annotations

import ctypes
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PROGRAM = ROOT / "resources/managed_materials/shadows/pssm/on/pssm.cg"
TARGETS = (
    ("shadow_caster_vs", "vs_2_0"),
    ("shadow_caster_ps", "ps_2_0"),
    ("shadow_caster_alpha_ps", "ps_2_0"),
    ("shadow_receiver_vs", "vs_1_1"),
    ("shadow_receiver_ps", "ps_2_x"),
)
CG_SOURCE = 4112


def run(redist: Path) -> int:
    cg_dll = redist / "cg.dll"
    if os.name != "nt":
        raise RuntimeError("This compiler integration test must run on Windows")
    if not cg_dll.is_file():
        raise FileNotFoundError(f"Missing packaged Cg compiler DLL: {cg_dll}")
    if not PROGRAM.is_file():
        raise FileNotFoundError(f"Missing PSSM shader: {PROGRAM}")

    # Python 3.8+ supports application-local dependent DLL search paths.
    directory_cookie = os.add_dll_directory(str(redist.resolve()))
    try:
        cg = ctypes.CDLL(str(cg_dll.resolve()))
        c_ptr = ctypes.c_void_p
        c_charp = ctypes.c_char_p
        cg.cgCreateContext.argtypes = []
        cg.cgCreateContext.restype = c_ptr
        cg.cgDestroyContext.argtypes = [c_ptr]
        cg.cgDestroyContext.restype = None
        cg.cgGetProfile.argtypes = [c_charp]
        cg.cgGetProfile.restype = ctypes.c_int
        cg.cgCreateProgram.argtypes = [
            c_ptr, ctypes.c_int, c_charp, ctypes.c_int, c_charp,
            ctypes.POINTER(c_charp),
        ]
        cg.cgCreateProgram.restype = c_ptr
        cg.cgIsProgramCompiled.argtypes = [c_ptr]
        cg.cgIsProgramCompiled.restype = ctypes.c_int
        cg.cgCompileProgram.argtypes = [c_ptr]
        cg.cgCompileProgram.restype = None
        cg.cgDestroyProgram.argtypes = [c_ptr]
        cg.cgDestroyProgram.restype = None
        cg.cgGetError.argtypes = []
        cg.cgGetError.restype = ctypes.c_int
        cg.cgGetErrorString.argtypes = [ctypes.c_int]
        cg.cgGetErrorString.restype = c_charp
        cg.cgGetLastListing.argtypes = [c_ptr]
        cg.cgGetLastListing.restype = c_charp

        ctx = cg.cgCreateContext()
        if not ctx:
            raise RuntimeError("NVIDIA Cg compiler could not create its context")
        try:
            shader_source = PROGRAM.read_bytes()
            failures = []
            for entry, profile_name in TARGETS:
                profile = cg.cgGetProfile(profile_name.encode("ascii"))
                if not profile:
                    failures.append(f"{entry} [{profile_name}]: profile not supported by compiler")
                    continue
                prog = cg.cgCreateProgram(
                    ctx, CG_SOURCE, shader_source, profile, entry.encode("ascii"), None
                )
                if prog:
                    try:
                        if not cg.cgIsProgramCompiled(prog):
                            cg.cgCompileProgram(prog)
                        compiled = bool(cg.cgIsProgramCompiled(prog))
                    finally:
                        cg.cgDestroyProgram(prog)
                else:
                    compiled = False

                error = cg.cgGetError()
                if not compiled:
                    error_text = cg.cgGetErrorString(error) or b"unknown Cg error"
                    listing = cg.cgGetLastListing(ctx) or b"no Cg compiler listing"
                    failures.append(
                        f"{entry} [{profile_name}]: "
                        f"{error_text.decode(errors='replace')}\n"
                        f"{listing.decode(errors='replace')[:6000]}"
                    )
                else:
                    print(f"PASS Cg compile: {entry} [{profile_name}]")
            if failures:
                print("\nCg compile failures:\n" + "\n\n".join(failures), file=sys.stderr)
                return 1
            print(f"PASS: compiled all {len(TARGETS)} managed PSSM entrypoints using packaged cg.dll")
            return 0
        finally:
            cg.cgDestroyContext(ctx)
    finally:
        directory_cookie.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: Test-CgShaders.py <Windows redist folder>", file=sys.stderr)
        raise SystemExit(2)
    raise SystemExit(run(Path(sys.argv[1]).resolve()))
