"""Synthesize stdin text with Kokoro to a wav file. Run inside the Kokoro virtualenv.

usage: kokoro_say.py <model.onnx> <voices.bin> <voice> <speed> <out.wav>
"""
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro


def main(argv: list[str]) -> int:
    model, voices, voice, speed, out = argv
    text = sys.stdin.read().strip()
    kokoro = Kokoro(model, voices)
    samples, rate = kokoro.create(text, voice=voice, speed=float(speed), lang="en-us")
    samples = np.asarray(samples, dtype="float32")
    peak = float(np.max(np.abs(samples))) or 1.0
    sf.write(out, samples / peak * 0.95, rate)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
