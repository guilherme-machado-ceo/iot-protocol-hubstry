"""Gera as fixtures de equivalência entre o núcleo Python e o porte TypeScript.

Rodar a partir da raiz do repositório:
    python3 server/tests/fixtures/gerar_fixtures_h16.py

O CI regenera o arquivo e falha se ele divergir do versionado, garantindo que
os testes comparem sempre com o núcleo Python atual.
"""
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))

from hpg_core.omnigrid import compute_hn  # noqa: E402
from hpg_core.hpm_config import get_channel_table  # noqa: E402
from hpg_core.signal_processing import generate_composite_signal, decode_fft  # noqa: E402

CASOS = [
    {"nome": "hpm10_6_canais_pot2", "f0": 16384.0, "harmonics": None, "duration": 1 / 64, "sample_rate": 131072.0},
    {"nome": "f0_1000_nao_pot2", "f0": 1000.0,
     "harmonics": [{"a": 3, "b": 2}, {"a": 5, "b": 4}, {"a": 7, "b": 3}],
     "duration": 0.1, "sample_rate": 8000.0},
    {"nome": "amplitudes_e_fases", "f0": 2048.0,
     "harmonics": [{"a": 1, "b": 1, "amplitude": 1.0, "phase": 0.0},
                   {"a": 5, "b": 3, "amplitude": 0.5, "phase": 1.0},
                   {"a": 11, "b": 7, "amplitude": 0.25, "phase": 2.5}],
     "duration": 0.125, "sample_rate": 16384.0},
]


def r(x):
    return round(float(x), 7)  # 7 casas: estável entre plataformas, abaixo da tolerância dos testes (1e-6)


saida = {
    "hn16": [{"a": f.numerator, "b": f.denominator} for f in sorted(compute_hn(16), key=lambda f: (float(f), f.denominator))],
    "canais": [{k: (r(v) if isinstance(v, float) else v) for k, v in ch.items()} for ch in get_channel_table()],
    "casos": [],
}
for c in CASOS:
    _, sinal, usados = generate_composite_signal(f0=c["f0"], harmonics=c["harmonics"],
                                                 duration=c["duration"], sample_rate=c["sample_rate"])
    picos = decode_fft(sinal, sample_rate=c["sample_rate"], f0=c["f0"])
    saida["casos"].append({
        "nome": c["nome"], "f0": c["f0"], "duration": c["duration"], "sample_rate": c["sample_rate"],
        "harmonics": [{"a": h["a"], "b": h["b"], "amplitude": h.get("amplitude", 1.0), "phase": h.get("phase", 0.0)} for h in usados],
        "n": len(sinal),
        "sinal_inicio": [r(v) for v in sinal[:32]],
        "picos": [{k: (r(v) if isinstance(v, float) else v) for k, v in p.items()} for p in picos],
    })

destino = pathlib.Path(__file__).with_name("h16-python.json")
destino.write_text(json.dumps(saida, indent=1, ensure_ascii=False) + "\n")
print(f"{destino.name}: |H16|={len(saida['hn16'])}, {len(saida['casos'])} casos")
