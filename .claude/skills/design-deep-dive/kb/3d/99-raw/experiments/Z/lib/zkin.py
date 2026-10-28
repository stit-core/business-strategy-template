"""zkin — кинематика «Звена» как в scene.js (оси three) → матрицы Blender. Дорожка Z.

three: матрица модуля M_k = T(разнос·out) · W_k · R_xyz(er·out·0,5; er·out; er·out·0,3), где W_k — мировая матрица шарнира
(цепочка T(смещение) · R(ось, угол)). Euler 'XYZ' three = Rx·Ry·Rz (не как mathutils). В Blender: B = C · M3 · C⁻¹,
C: three (x, y, z) → Blender (x, −z, y). Геометрия модулей строится сразу в локальных осях Blender (= C · локальные three).
"""
import math
from mathutils import Matrix, Vector

from zpass import PIVOTS, ORDER, POSE_KEY, EXPLODE

C4 = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
C4i = C4.inverted()


def t2b(v):
    """Точка three → Blender."""
    return Vector((v[0], -v[2], v[1]))


def b2t(v):
    return (v[0], v[2], -v[1])


def _rot(axis, ang):
    return Matrix.Rotation(ang, 4, axis)


def pivot_world_three(pose):
    """{модуль: мировая матрица шарнира (оси three)} для позы (рад)."""
    W = {}
    for k in ORDER:
        parent, off, axis = PIVOTS[k]
        local = Matrix.Translation(Vector(off))
        if axis is not None and k in POSE_KEY:
            local = local @ _rot(axis, pose.get(POSE_KEY[k], 0.0))
        W[k] = (W[parent] @ local) if parent else local
    return W


def module_world_three(pose, explode=0.0, per_module=None):
    """Матрицы модулей как в storyFrame: T(ex·out, ey·out, ez·out) · W · Rx(er·out·0,5)·Ry(er·out)·Rz(er·out·0,3).
    per_module — {модуль: out} (иначе один explode на всех)."""
    W = pivot_world_three(pose)
    M = {}
    for k in ORDER:
        out = per_module.get(k, explode) if per_module else explode
        ex, ey, ez, er = EXPLODE[k]
        T = Matrix.Translation(Vector((ex * out, ey * out, ez * out)))
        R = _rot("X", er * out * 0.5) @ _rot("Y", er * out) @ _rot("Z", er * out * 0.3)
        M[k] = T @ W[k] @ R
    return M


def to_blender(m3):
    return C4 @ m3 @ C4i


def module_world_blender(pose, explode=0.0, per_module=None):
    return {k: to_blender(m) for k, m in module_world_three(pose, explode, per_module).items()}


def self_test():
    """Прямая поза: шарниры на оси Y на высотах кода; hero: захват где-то справа-сверху."""
    from zpass import POSE_REST, POSE_WORK
    W = pivot_world_three(POSE_REST)
    ys = {k: round(W[k].translation.y, 4) for k in ORDER}
    assert ys == {"base": 0.0, "j1": 0.34, "j2": 0.935, "l1": 0.935, "j3": 2.145, "l2": 2.145, "wrist": 3.115,
                  "grip": 3.415}, ys
    Wb = module_world_blender(POSE_WORK)
    g = Wb["grip"].translation
    return {"rest_y": ys, "hero_grip_blender": [round(x, 3) for x in g]}
