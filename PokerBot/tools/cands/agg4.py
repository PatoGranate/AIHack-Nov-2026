"""AlgoSoc Pokerbot v3.

Preflop: hand ranking + offline equity tables vs ranges; opponents' ranges are
estimated from their observed VPIP / PFR / shove rate this round.
Postflop: Monte-Carlo vs each opponent's *weighted* range (preflop range,
narrowed by how they've bet this hand), plus a per-opponent continue model fit
to their observed fold-to-bet rate. Actions are chosen by approximate EV
(check / bet sizes, fold / call / raise sizes).
Everything is wrapped so act() always returns a legal action.
"""
import random
import time

RANKS = "23456789TJQKA"
SUITS = "cdhs"
_PR = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41]
CP = [_PR[c >> 2] for c in range(52)]          # card -> prime of rank
CB = [1 << (c >> 2) for c in range(52)]        # card -> rank bit
CS = [c & 3 for c in range(52)]                # card -> suit

_STR = [-1] * 8192
for _m in range(8192):
    _x = (_m << 1) | (1 if _m & 4096 else 0)
    for _t in range(13, 3, -1):
        if (_x >> (_t - 4)) & 31 == 31:
            _STR[_m] = _t - 1
            break


def _top(mask, k):
    out = 0
    n = 0
    r = 12
    while n < k and r >= 0:
        if mask >> r & 1:
            out = (out << 4) | r
            n += 1
        r -= 1
    while n < k:
        out <<= 4
        n += 1
    return out


# flush score for a suit mask with >=5 bits
FL = [0] * 8192
for _m in range(8192):
    if bin(_m).count("1") >= 5:
        _s = _STR[_m]
        FL[_m] = (8 << 20) | _s if _s >= 0 else (5 << 20) | _top(_m, 5)


def _rank_score(counts):
    mask = 0
    for r in range(13):
        if counts[r]:
            mask |= 1 << r
    quad = -1
    trips = []
    pairs = []
    for r in range(12, -1, -1):
        n = counts[r]
        if n == 4:
            quad = r
        elif n == 3:
            trips.append(r)
        elif n == 2:
            pairs.append(r)
    if quad >= 0:
        return (7 << 20) | (quad << 4) | _top(mask & ~(1 << quad), 1)
    if trips and (len(trips) > 1 or pairs):
        second = trips[1] if len(trips) > 1 else -1
        if pairs and pairs[0] > second:
            second = pairs[0]
        return (6 << 20) | (trips[0] << 4) | second
    sh = _STR[mask]
    if sh >= 0:
        return (4 << 20) | sh
    if trips:
        t = trips[0]
        return (3 << 20) | (t << 8) | _top(mask & ~(1 << t), 2)
    if len(pairs) >= 2:
        p1, p2 = pairs[0], pairs[1]
        return (2 << 20) | (p1 << 8) | (p2 << 4) | _top(mask & ~(1 << p1) & ~(1 << p2), 1)
    if pairs:
        p = pairs[0]
        return (1 << 20) | (p << 12) | _top(mask & ~(1 << p), 3)
    return _top(mask, 5)


class _RT(dict):
    """prime-product -> rank-only score, filled lazily."""
    def __missing__(self, p):
        counts = [0] * 13
        q = p
        for r in range(13):
            pr = _PR[r]
            while q % pr == 0:
                counts[r] += 1
                q //= pr
        v = _rank_score(counts)
        self[p] = v
        return v


RT = _RT()


def evaluate(cards):
    """Score of best hand from 5-7 int cards (higher wins)."""
    p = 1
    sc = [0, 0, 0, 0]
    sm = [0, 0, 0, 0]
    for c in cards:
        p *= CP[c]
        s = c & 3
        sc[s] += 1
        sm[s] |= CB[c]
    v = RT[p]
    for s in range(4):
        if sc[s] >= 5:
            f = FL[sm[s]]
            if f > v:
                v = f
    return v

RANK = ['AA', 'KK', 'QQ', 'JJ', 'TT', '99', '88', 'AKs', 'AQs', '77', 'AJs', 'AKo', 'ATs', 'AQo', 'AJo', 'KQs', '66', 'ATo', 'A9s', 'KJs', 'A8s', 'KTs', 'KQo', 'A7s', 'A9o', 'KJo', '55', 'A5s', 'QJs', 'KTo', 'K9s', 'A8o', 'A6s', 'QTs', 'A4s', 'A7o', 'A3s', 'K8s', 'QJo', 'A5o', 'Q9s', 'K9o', 'JTs', 'QTo', 'A6o', 'K7s', 'A2s', '44', 'A4o', 'A3o', 'K6s', 'K8o', 'K5s', 'Q8s', 'J9s', 'JTo', 'K7o', 'Q9o', 'K4s', 'A2o', 'Q7s', 'J8s', 'K3s', 'T9s', 'K6o', '33', 'K5o', 'Q8o', 'J9o', 'Q6s', 'K2s', 'Q5s', 'J7s', 'K4o', 'T8s', 'Q4s', 'Q7o', 'J8o', 'T9o', 'K3o', 'Q3s', 'Q6o', 'T7s', '22', '98s', 'Q5o', 'J6s', 'K2o', 'J7o', 'J5s', 'Q2s', '97s', 'T8o', 'Q4o', 'J4s', 'T6s', 'J3s', '98o', 'Q3o', '87s', 'J6o', 'T7o', 'T5s', '96s', 'J2s', 'J5o', 'Q2o', 'T4s', '97o', 'J4o', 'T6o', '86s', 'T3s', '95s', '76s', 'J3o', '87o', 'T2s', '96o', '85s', 'T5o', '94s', 'J2o', '75s', 'T4o', '93s', '86o', '65s', '95o', 'T3o', '92s', '84s', '76o', '74s', '54s', 'T2o', '85o', '64s', '94o', '83s', '75o', '93o', '73s', '65o', '53s', '82s', '63s', '84o', '92o', '74o', '43s', '54o', '72s', '64o', '52s', '62s', '83o', '82o', '73o', '42s', '53o', '32s', '63o', '43o', '72o', '52o', '62o', '42o', '32o']
F = [0.03, 0.05, 0.08, 0.12, 0.17, 0.23, 0.3, 0.4, 0.55, 0.75, 1.0]
EQR = {'AA': [0.801, 0.814, 0.84, 0.851, 0.857, 0.856, 0.859, 0.857, 0.853, 0.853, 0.855], 'KK': [0.693, 0.71, 0.715, 0.726, 0.743, 0.748, 0.756, 0.785, 0.802, 0.815, 0.825], 'QQ': [0.596, 0.625, 0.646, 0.669, 0.688, 0.693, 0.71, 0.729, 0.754, 0.783, 0.804], 'JJ': [0.48, 0.558, 0.57, 0.611, 0.642, 0.65, 0.668, 0.685, 0.713, 0.749, 0.771], 'TT': [0.375, 0.486, 0.523, 0.562, 0.598, 0.608, 0.633, 0.657, 0.679, 0.711, 0.746], '99': [0.275, 0.425, 0.484, 0.52, 0.559, 0.569, 0.6, 0.62, 0.644, 0.673, 0.715], '88': [0.193, 0.358, 0.435, 0.487, 0.521, 0.543, 0.566, 0.587, 0.611, 0.642, 0.687], 'AKs': [0.422, 0.474, 0.551, 0.605, 0.632, 0.651, 0.659, 0.67, 0.669, 0.671, 0.67], 'AQs': [0.394, 0.421, 0.478, 0.549, 0.587, 0.613, 0.632, 0.644, 0.655, 0.661, 0.661], '77': [0.19, 0.297, 0.4, 0.455, 0.498, 0.513, 0.548, 0.567, 0.591, 0.614, 0.661], 'AJs': [0.372, 0.388, 0.402, 0.49, 0.552, 0.588, 0.606, 0.623, 0.633, 0.651, 0.656], 'AKo': [0.392, 0.447, 0.526, 0.584, 0.619, 0.632, 0.637, 0.651, 0.655, 0.648, 0.647], 'ATs': [0.354, 0.356, 0.36, 0.453, 0.515, 0.559, 0.582, 0.604, 0.62, 0.64, 0.645], 'AQo': [0.365, 0.391, 0.449, 0.525, 0.564, 0.6, 0.613, 0.629, 0.642, 0.646, 0.644], 'AJo': [0.34, 0.349, 0.372, 0.459, 0.525, 0.561, 0.582, 0.605, 0.612, 0.628, 0.639], 'KQs': [0.382, 0.377, 0.384, 0.418, 0.463, 0.498, 0.514, 0.558, 0.602, 0.619, 0.642], '66': [0.2, 0.288, 0.381, 0.435, 0.473, 0.498, 0.523, 0.546, 0.563, 0.585, 0.635], 'ATo': [0.318, 0.329, 0.324, 0.419, 0.488, 0.534, 0.556, 0.582, 0.605, 0.619, 0.629], 'A9s': [0.317, 0.337, 0.34, 0.411, 0.466, 0.513, 0.541, 0.576, 0.597, 0.612, 0.628], 'KJs': [0.354, 0.368, 0.366, 0.388, 0.429, 0.472, 0.491, 0.539, 0.58, 0.607, 0.63], 'A8s': [0.305, 0.32, 0.332, 0.383, 0.438, 0.49, 0.517, 0.55, 0.579, 0.598, 0.619], 'KTs': [0.334, 0.359, 0.367, 0.373, 0.396, 0.444, 0.478, 0.521, 0.569, 0.599, 0.618], 'KQo': [0.349, 0.348, 0.347, 0.384, 0.432, 0.47, 0.484, 0.535, 0.575, 0.6, 0.617], 'A7s': [0.311, 0.307, 0.331, 0.369, 0.42, 0.462, 0.498, 0.536, 0.566, 0.594, 0.613], 'A9o': [0.283, 0.296, 0.301, 0.365, 0.439, 0.487, 0.522, 0.555, 0.576, 0.59, 0.61], 'KJo': [0.321, 0.334, 0.325, 0.353, 0.399, 0.444, 0.467, 0.512, 0.558, 0.59, 0.61], '55': [0.189, 0.281, 0.375, 0.412, 0.447, 0.471, 0.503, 0.52, 0.54, 0.557, 0.602], 'A5s': [0.323, 0.316, 0.334, 0.377, 0.414, 0.448, 0.477, 0.514, 0.546, 0.579, 0.593], 'QJs': [0.34, 0.371, 0.361, 0.38, 0.396, 0.431, 0.448, 0.485, 0.535, 0.579, 0.608], 'KTo': [0.297, 0.321, 0.325, 0.334, 0.361, 0.411, 0.445, 0.495, 0.544, 0.575, 0.603], 'K9s': [0.295, 0.326, 0.349, 0.349, 0.367, 0.411, 0.436, 0.494, 0.542, 0.574, 0.601], 'A8o': [0.265, 0.284, 0.289, 0.343, 0.401, 0.455, 0.497, 0.527, 0.553, 0.578, 0.598], 'A6s': [0.309, 0.304, 0.32, 0.365, 0.418, 0.454, 0.482, 0.519, 0.553, 0.582, 0.6], 'QTs': [0.317, 0.355, 0.359, 0.365, 0.388, 0.407, 0.429, 0.462, 0.514, 0.565, 0.594], 'A4s': [0.32, 0.319, 0.337, 0.377, 0.41, 0.448, 0.472, 0.507, 0.54, 0.56, 0.59], 'A7o': [0.267, 0.271, 0.285, 0.334, 0.39, 0.435, 0.47, 0.513, 0.536, 0.569, 0.59], 'A3s': [0.312, 0.313, 0.33, 0.375, 0.411, 0.445, 0.465, 0.503, 0.532, 0.557, 0.577], 'K8s': [0.27, 0.306, 0.329, 0.334, 0.345, 0.386, 0.411, 0.462, 0.511, 0.555, 0.585], 'QJo': [0.311, 0.334, 0.323, 0.347, 0.363, 0.4, 0.423, 0.454, 0.502, 0.559, 0.583], 'A5o': [0.279, 0.281, 0.288, 0.33, 0.38, 0.417, 0.45, 0.487, 0.519, 0.551, 0.578], 'Q9s': [0.28, 0.329, 0.347, 0.359, 0.371, 0.377, 0.407, 0.433, 0.491, 0.543, 0.58], 'K9o': [0.256, 0.293, 0.31, 0.309, 0.331, 0.374, 0.413, 0.465, 0.517, 0.547, 0.583], 'JTs': [0.3, 0.352, 0.36, 0.373, 0.388, 0.395, 0.416, 0.443, 0.481, 0.533, 0.574], 'QTo': [0.282, 0.321, 0.324, 0.336, 0.351, 0.373, 0.4, 0.435, 0.49, 0.54, 0.574], 'A6o': [0.265, 0.271, 0.283, 0.328, 0.38, 0.419, 0.456, 0.493, 0.522, 0.556, 0.578], 'K7s': [0.278, 0.3, 0.322, 0.339, 0.35, 0.378, 0.399, 0.448, 0.5, 0.545, 0.578], 'A2s': [0.309, 0.31, 0.321, 0.368, 0.411, 0.441, 0.459, 0.494, 0.529, 0.552, 0.571], '44': [0.191, 0.286, 0.368, 0.412, 0.441, 0.46, 0.481, 0.506, 0.526, 0.533, 0.573], 'A4o': [0.28, 0.284, 0.291, 0.333, 0.377, 0.414, 0.442, 0.479, 0.511, 0.54, 0.567], 'A3o': [0.274, 0.278, 0.286, 0.328, 0.373, 0.41, 0.434, 0.475, 0.505, 0.531, 0.555], 'K6s': [0.28, 0.298, 0.325, 0.334, 0.359, 0.381, 0.401, 0.443, 0.49, 0.537, 0.57], 'K8o': [0.233, 0.268, 0.296, 0.3, 0.307, 0.349, 0.378, 0.432, 0.482, 0.532, 0.556], 'K5s': [0.279, 0.293, 0.323, 0.328, 0.342, 0.367, 0.391, 0.427, 0.479, 0.524, 0.557], 'Q8s': [0.258, 0.307, 0.332, 0.344, 0.361, 0.366, 0.387, 0.406, 0.468, 0.522, 0.56], 'J9s': [0.266, 0.328, 0.344, 0.354, 0.374, 0.378, 0.393, 0.411, 0.452, 0.51, 0.555], 'JTo': [0.263, 0.322, 0.328, 0.339, 0.354, 0.357, 0.385, 0.409, 0.447, 0.507, 0.548], 'K7o': [0.239, 0.254, 0.287, 0.3, 0.312, 0.344, 0.37, 0.419, 0.474, 0.517, 0.553], 'Q9o': [0.243, 0.295, 0.307, 0.321, 0.339, 0.348, 0.373, 0.405, 0.462, 0.519, 0.558], 'K4s': [0.278, 0.295, 0.321, 0.327, 0.341, 0.37, 0.386, 0.42, 0.468, 0.51, 0.552], 'A2o': [0.268, 0.276, 0.281, 0.321, 0.371, 0.407, 0.43, 0.464, 0.496, 0.527, 0.545], 'Q7s': [0.252, 0.284, 0.311, 0.329, 0.349, 0.352, 0.373, 0.394, 0.444, 0.503, 0.548], 'J8s': [0.237, 0.301, 0.325, 0.341, 0.362, 0.373, 0.376, 0.391, 0.433, 0.494, 0.535], 'K3s': [0.274, 0.29, 0.314, 0.322, 0.335, 0.368, 0.381, 0.411, 0.464, 0.506, 0.539], 'T9s': [0.254, 0.326, 0.351, 0.368, 0.377, 0.379, 0.399, 0.411, 0.442, 0.489, 0.546], 'K6o': [0.239, 0.261, 0.288, 0.303, 0.319, 0.344, 0.367, 0.408, 0.46, 0.508, 0.55], '33': [0.185, 0.277, 0.365, 0.404, 0.433, 0.45, 0.467, 0.479, 0.5, 0.508, 0.537], 'K5o': [0.238, 0.256, 0.281, 0.289, 0.304, 0.332, 0.357, 0.391, 0.445, 0.486, 0.531], 'Q8o': [0.222, 0.273, 0.292, 0.307, 0.325, 0.331, 0.351, 0.377, 0.436, 0.494, 0.539], 'J9o': [0.23, 0.291, 0.309, 0.325, 0.338, 0.343, 0.359, 0.376, 0.424, 0.484, 0.534], 'Q6s': [0.255, 0.295, 0.317, 0.335, 0.355, 0.36, 0.376, 0.395, 0.439, 0.493, 0.539], 'K2s': [0.269, 0.283, 0.31, 0.318, 0.331, 0.366, 0.377, 0.406, 0.457, 0.497, 0.532], 'Q5s': [0.256, 0.29, 0.308, 0.327, 0.345, 0.342, 0.375, 0.38, 0.43, 0.481, 0.527], 'J7s': [0.237, 0.28, 0.307, 0.33, 0.353, 0.35, 0.367, 0.383, 0.417, 0.475, 0.521], 'K4o': [0.237, 0.26, 0.28, 0.291, 0.304, 0.336, 0.35, 0.385, 0.436, 0.481, 0.527], 'T8s': [0.232, 0.31, 0.341, 0.346, 0.366, 0.373, 0.384, 0.396, 0.42, 0.472, 0.522], 'Q4s': [0.255, 0.287, 0.31, 0.331, 0.348, 0.349, 0.364, 0.375, 0.418, 0.475, 0.52], 'Q7o': [0.216, 0.249, 0.273, 0.295, 0.318, 0.313, 0.339, 0.359, 0.414, 0.476, 0.522], 'J8o': [0.205, 0.264, 0.287, 0.314, 0.318, 0.331, 0.343, 0.354, 0.402, 0.467, 0.51], 'T9o': [0.214, 0.292, 0.319, 0.325, 0.342, 0.347, 0.363, 0.379, 0.413, 0.46, 0.515], 'K3o': [0.231, 0.252, 0.274, 0.286, 0.296, 0.334, 0.348, 0.375, 0.428, 0.476, 0.513], 'Q3s': [0.25, 0.283, 0.305, 0.321, 0.338, 0.347, 0.358, 0.372, 0.41, 0.467, 0.509], 'Q6o': [0.219, 0.262, 0.277, 0.299, 0.321, 0.328, 0.336, 0.359, 0.401, 0.466, 0.514], 'T7s': [0.227, 0.283, 0.326, 0.333, 0.36, 0.358, 0.373, 0.387, 0.4, 0.453, 0.508], '22': [0.18, 0.269, 0.357, 0.396, 0.426, 0.441, 0.453, 0.466, 0.481, 0.486, 0.504], '98s': [0.214, 0.294, 0.336, 0.358, 0.364, 0.378, 0.393, 0.4, 0.416, 0.45, 0.507], 'Q5o': [0.219, 0.255, 0.27, 0.287, 0.304, 0.308, 0.331, 0.347, 0.387, 0.45, 0.501], 'J6s': [0.23, 0.28, 0.296, 0.324, 0.339, 0.351, 0.354, 0.369, 0.395, 0.455, 0.507], 'K2o': [0.227, 0.245, 0.27, 0.28, 0.296, 0.333, 0.344, 0.373, 0.426, 0.467, 0.503], 'J7o': [0.198, 0.241, 0.271, 0.297, 0.315, 0.318, 0.334, 0.343, 0.38, 0.441, 0.495], 'J5s': [0.232, 0.275, 0.293, 0.321, 0.333, 0.335, 0.35, 0.357, 0.385, 0.441, 0.495], 'Q2s': [0.248, 0.277, 0.299, 0.319, 0.335, 0.339, 0.352, 0.367, 0.407, 0.461, 0.5], '97s': [0.217, 0.273, 0.328, 0.346, 0.365, 0.365, 0.378, 0.393, 0.4, 0.432, 0.494], 'T8o': [0.192, 0.272, 0.303, 0.314, 0.327, 0.34, 0.353, 0.363, 0.389, 0.439, 0.492], 'Q4o': [0.215, 0.253, 0.27, 0.288, 0.31, 0.313, 0.333, 0.344, 0.388, 0.449, 0.494], 'J4s': [0.228, 0.273, 0.295, 0.323, 0.34, 0.339, 0.346, 0.359, 0.382, 0.437, 0.489], 'T6s': [0.218, 0.277, 0.313, 0.324, 0.344, 0.352, 0.363, 0.38, 0.391, 0.437, 0.489], 'J3s': [0.227, 0.27, 0.287, 0.313, 0.328, 0.337, 0.344, 0.355, 0.379, 0.425, 0.475], '98o': [0.175, 0.263, 0.307, 0.325, 0.333, 0.344, 0.363, 0.368, 0.384, 0.422, 0.482], 'Q3o': [0.212, 0.249, 0.261, 0.282, 0.304, 0.308, 0.324, 0.338, 0.378, 0.436, 0.483], '87s': [0.208, 0.273, 0.325, 0.349, 0.365, 0.375, 0.389, 0.401, 0.405, 0.427, 0.476], 'J6o': [0.192, 0.24, 0.258, 0.289, 0.301, 0.311, 0.318, 0.332, 0.362, 0.428, 0.478], 'T7o': [0.187, 0.245, 0.283, 0.297, 0.318, 0.323, 0.34, 0.351, 0.366, 0.423, 0.482], 'T5s': [0.209, 0.261, 0.295, 0.31, 0.327, 0.327, 0.346, 0.357, 0.373, 0.41, 0.47], '96s': [0.208, 0.273, 0.32, 0.337, 0.353, 0.361, 0.37, 0.382, 0.391, 0.419, 0.476], 'J2s': [0.222, 0.263, 0.282, 0.309, 0.324, 0.333, 0.34, 0.352, 0.374, 0.423, 0.466], 'J5o': [0.194, 0.234, 0.255, 0.277, 0.292, 0.303, 0.314, 0.318, 0.351, 0.411, 0.467], 'Q2o': [0.208, 0.244, 0.255, 0.277, 0.299, 0.306, 0.323, 0.335, 0.369, 0.427, 0.469], 'T4s': [0.21, 0.266, 0.3, 0.311, 0.33, 0.333, 0.341, 0.356, 0.363, 0.404, 0.462], '97o': [0.177, 0.24, 0.289, 0.314, 0.33, 0.331, 0.347, 0.358, 0.366, 0.401, 0.469], 'J4o': [0.187, 0.236, 0.256, 0.281, 0.299, 0.301, 0.314, 0.32, 0.351, 0.405, 0.463], 'T6o': [0.177, 0.241, 0.273, 0.29, 0.305, 0.316, 0.33, 0.34, 0.357, 0.404, 0.461], '86s': [0.201, 0.267, 0.317, 0.34, 0.357, 0.371, 0.377, 0.385, 0.392, 0.41, 0.466], 'T3s': [0.205, 0.262, 0.293, 0.31, 0.326, 0.327, 0.336, 0.354, 0.364, 0.396, 0.46], '95s': [0.19, 0.26, 0.304, 0.32, 0.335, 0.338, 0.355, 0.361, 0.371, 0.398, 0.454], '76s': [0.212, 0.264, 0.32, 0.343, 0.372, 0.378, 0.384, 0.394, 0.402, 0.415, 0.458], 'J3o': [0.184, 0.233, 0.254, 0.273, 0.289, 0.298, 0.304, 0.316, 0.335, 0.394, 0.448], '87o': [0.167, 0.237, 0.291, 0.313, 0.336, 0.338, 0.351, 0.362, 0.369, 0.395, 0.454], 'T2s': [0.198, 0.253, 0.288, 0.302, 0.322, 0.325, 0.335, 0.342, 0.361, 0.396, 0.447], '96o': [0.17, 0.234, 0.286, 0.302, 0.319, 0.327, 0.336, 0.346, 0.358, 0.39, 0.445], '85s': [0.189, 0.254, 0.302, 0.321, 0.337, 0.347, 0.356, 0.364, 0.373, 0.385, 0.437], 'T5o': [0.164, 0.226, 0.257, 0.269, 0.288, 0.289, 0.308, 0.316, 0.329, 0.38, 0.437], '94s': [0.182, 0.249, 0.295, 0.311, 0.322, 0.33, 0.337, 0.345, 0.357, 0.376, 0.437], 'J2o': [0.181, 0.226, 0.242, 0.271, 0.286, 0.294, 0.301, 0.312, 0.338, 0.392, 0.437], '75s': [0.206, 0.252, 0.308, 0.329, 0.351, 0.354, 0.372, 0.375, 0.39, 0.393, 0.432], 'T4o': [0.165, 0.227, 0.263, 0.273, 0.294, 0.298, 0.305, 0.319, 0.332, 0.372, 0.43], '93s': [0.179, 0.244, 0.294, 0.309, 0.32, 0.33, 0.336, 0.344, 0.358, 0.376, 0.432], '86o': [0.163, 0.23, 0.278, 0.307, 0.321, 0.334, 0.343, 0.349, 0.357, 0.38, 0.44], '65s': [0.22, 0.263, 0.316, 0.341, 0.358, 0.369, 0.377, 0.38, 0.391, 0.397, 0.429], '95o': [0.156, 0.219, 0.266, 0.285, 0.295, 0.299, 0.319, 0.319, 0.335, 0.356, 0.425], 'T3o': [0.159, 0.223, 0.257, 0.268, 0.288, 0.292, 0.299, 0.314, 0.325, 0.364, 0.426], '92s': [0.177, 0.24, 0.29, 0.304, 0.318, 0.324, 0.332, 0.343, 0.349, 0.371, 0.42], '84s': [0.175, 0.241, 0.293, 0.309, 0.332, 0.336, 0.344, 0.351, 0.354, 0.375, 0.427], '76o': [0.175, 0.23, 0.281, 0.311, 0.332, 0.343, 0.349, 0.362, 0.369, 0.379, 0.425], '74s': [0.193, 0.238, 0.299, 0.32, 0.341, 0.343, 0.35, 0.363, 0.37, 0.373, 0.42], '54s': [0.216, 0.263, 0.312, 0.337, 0.359, 0.362, 0.371, 0.377, 0.381, 0.387, 0.412], 'T2o': [0.154, 0.218, 0.251, 0.263, 0.285, 0.29, 0.295, 0.309, 0.322, 0.362, 0.417], '85o': [0.149, 0.216, 0.262, 0.288, 0.303, 0.31, 0.324, 0.326, 0.335, 0.352, 0.409], '64s': [0.207, 0.253, 0.308, 0.333, 0.349, 0.363, 0.356, 0.368, 0.371, 0.382, 0.412], '94o': [0.141, 0.208, 0.254, 0.276, 0.284, 0.294, 0.301, 0.308, 0.325, 0.339, 0.407], '83s': [0.158, 0.229, 0.275, 0.296, 0.316, 0.323, 0.331, 0.335, 0.341, 0.353, 0.407], '75o': [0.168, 0.215, 0.269, 0.295, 0.317, 0.319, 0.334, 0.334, 0.35, 0.359, 0.402], '93o': [0.137, 0.204, 0.252, 0.272, 0.281, 0.294, 0.299, 0.309, 0.322, 0.339, 0.399], '73s': [0.176, 0.226, 0.278, 0.302, 0.325, 0.334, 0.336, 0.351, 0.356, 0.361, 0.399], '65o': [0.183, 0.226, 0.281, 0.303, 0.321, 0.33, 0.339, 0.346, 0.358, 0.359, 0.397], '53s': [0.2, 0.25, 0.298, 0.321, 0.344, 0.346, 0.352, 0.359, 0.368, 0.375, 0.393], '82s': [0.159, 0.223, 0.273, 0.292, 0.312, 0.322, 0.327, 0.333, 0.342, 0.352, 0.402], '63s': [0.191, 0.241, 0.293, 0.319, 0.337, 0.348, 0.346, 0.358, 0.358, 0.366, 0.394], '84o': [0.134, 0.202, 0.253, 0.276, 0.292, 0.301, 0.305, 0.316, 0.323, 0.334, 0.391], '92o': [0.133, 0.203, 0.249, 0.266, 0.278, 0.287, 0.299, 0.303, 0.313, 0.332, 0.387], '74o': [0.153, 0.201, 0.258, 0.284, 0.302, 0.311, 0.315, 0.328, 0.335, 0.343, 0.387], '43s': [0.197, 0.25, 0.295, 0.321, 0.335, 0.343, 0.351, 0.357, 0.364, 0.367, 0.381], '54o': [0.178, 0.228, 0.279, 0.302, 0.32, 0.326, 0.333, 0.343, 0.348, 0.354, 0.379], '72s': [0.159, 0.21, 0.269, 0.291, 0.316, 0.32, 0.321, 0.334, 0.337, 0.347, 0.382], '64o': [0.168, 0.216, 0.271, 0.294, 0.315, 0.326, 0.324, 0.331, 0.337, 0.347, 0.382], '52s': [0.185, 0.235, 0.281, 0.308, 0.328, 0.335, 0.34, 0.344, 0.351, 0.356, 0.382], '62s': [0.174, 0.226, 0.278, 0.305, 0.322, 0.335, 0.335, 0.34, 0.352, 0.355, 0.376], '83o': [0.114, 0.188, 0.235, 0.26, 0.273, 0.287, 0.293, 0.298, 0.308, 0.319, 0.37], '82o': [0.113, 0.185, 0.233, 0.258, 0.272, 0.284, 0.289, 0.301, 0.304, 0.318, 0.365], '73o': [0.135, 0.188, 0.241, 0.267, 0.287, 0.297, 0.299, 0.311, 0.32, 0.325, 0.376], '42s': [0.182, 0.232, 0.281, 0.306, 0.322, 0.335, 0.336, 0.343, 0.347, 0.353, 0.37], '53o': [0.16, 0.212, 0.261, 0.284, 0.302, 0.309, 0.317, 0.32, 0.332, 0.339, 0.363], '32s': [0.179, 0.233, 0.28, 0.305, 0.321, 0.326, 0.331, 0.34, 0.344, 0.346, 0.361], '63o': [0.151, 0.203, 0.255, 0.278, 0.3, 0.314, 0.309, 0.324, 0.321, 0.334, 0.363], '43o': [0.157, 0.213, 0.259, 0.284, 0.3, 0.308, 0.312, 0.322, 0.324, 0.331, 0.348], '72o': [0.115, 0.172, 0.226, 0.251, 0.274, 0.28, 0.289, 0.294, 0.304, 0.308, 0.345], '52o': [0.144, 0.197, 0.244, 0.27, 0.287, 0.296, 0.302, 0.309, 0.32, 0.319, 0.343], '62o': [0.133, 0.187, 0.239, 0.265, 0.284, 0.296, 0.299, 0.304, 0.309, 0.317, 0.344], '42o': [0.14, 0.193, 0.244, 0.27, 0.285, 0.296, 0.299, 0.308, 0.311, 0.316, 0.327], '32o': [0.139, 0.193, 0.243, 0.267, 0.283, 0.292, 0.29, 0.303, 0.307, 0.308, 0.328]}
EQM = {'AA': [], 'KK': [], 'QQ': [], 'JJ': [], 'TT': [], '99': [], '88': [], 'AKs': [], 'AQs': [], '77': [], 'AJs': [], 'AKo': [], 'ATs': [], 'AQo': [], 'AJo': [], 'KQs': [], '66': [], 'ATo': [], 'A9s': [], 'KJs': [], 'A8s': [], 'KTs': [], 'KQo': [], 'A7s': [], 'A9o': [], 'KJo': [], '55': [], 'A5s': [], 'QJs': [], 'KTo': [], 'K9s': [], 'A8o': [], 'A6s': [], 'QTs': [], 'A4s': [], 'A7o': [], 'A3s': [], 'K8s': [], 'QJo': [], 'A5o': [], 'Q9s': [], 'K9o': [], 'JTs': [], 'QTo': [], 'A6o': [], 'K7s': [], 'A2s': [], '44': [], 'A4o': [], 'A3o': [], 'K6s': [], 'K8o': [], 'K5s': [], 'Q8s': [], 'J9s': [], 'JTo': [], 'K7o': [], 'Q9o': [], 'K4s': [], 'A2o': [], 'Q7s': [], 'J8s': [], 'K3s': [], 'T9s': [], 'K6o': [], '33': [], 'K5o': [], 'Q8o': [], 'J9o': [], 'Q6s': [], 'K2s': [], 'Q5s': [], 'J7s': [], 'K4o': [], 'T8s': [], 'Q4s': [], 'Q7o': [], 'J8o': [], 'T9o': [], 'K3o': [], 'Q3s': [], 'Q6o': [], 'T7s': [], '22': [], '98s': [], 'Q5o': [], 'J6s': [], 'K2o': [], 'J7o': [], 'J5s': [], 'Q2s': [], '97s': [], 'T8o': [], 'Q4o': [], 'J4s': [], 'T6s': [], 'J3s': [], '98o': [], 'Q3o': [], '87s': [], 'J6o': [], 'T7o': [], 'T5s': [], '96s': [], 'J2s': [], 'J5o': [], 'Q2o': [], 'T4s': [], '97o': [], 'J4o': [], 'T6o': [], '86s': [], 'T3s': [], '95s': [], '76s': [], 'J3o': [], '87o': [], 'T2s': [], '96o': [], '85s': [], 'T5o': [], '94s': [], 'J2o': [], '75s': [], 'T4o': [], '93s': [], '86o': [], '65s': [], '95o': [], 'T3o': [], '92s': [], '84s': [], '76o': [], '74s': [], '54s': [], 'T2o': [], '85o': [], '64s': [], '94o': [], '83s': [], '75o': [], '93o': [], '73s': [], '65o': [], '53s': [], '82s': [], '63s': [], '84o': [], '92o': [], '74o': [], '43s': [], '54o': [], '72s': [], '64o': [], '52s': [], '62s': [], '83o': [], '82o': [], '73o': [], '42s': [], '53o': [], '32s': [], '63o': [], '43o': [], '72o': [], '52o': [], '62o': [], '42o': [], '32o': []}

DEBUG = False
_BUILT = [False]


def prebuild():
    """Fill the 5/6/7-card rank table (~1 s) so act() never misses."""
    if _BUILT[0]:
        return
    _BUILT[0] = True
    counts = [0] * 13

    def rec(n, start, prod):
        if n == 0:
            if prod not in RT:
                RT[prod] = _rank_score(counts)
            return
        for r in range(start, 13):
            if counts[r] < 4:
                counts[r] += 1
                rec(n - 1, r, prod * _PR[r])
                counts[r] -= 1
    for k in (5, 6, 7):
        rec(k, 0, 1)


P = {
    'pri_vpip': 0.3,
    'pri_pfr': 0.15,
    'pri_ftb': 0.65,
    'r3_mult': 0.35,
    'call_lo': 0.6,
    'bb_raise': 0.15,
    'open_size': 4.0,
    'loose_add': 1.0,
    'o_btn': 0.85,
    'o_sb': 0.75,
    'o_co': 0.6,
    'o_hj': 0.46,
    'o_mp': 0.36,
    'o_ep': 0.28,
    'steal_k': 1.5,
    'iso_mult': 1.0,
    'overlimp': 0.3,
    'sb_limp': 0.0,
    'multi_exp': 0.6,
    'real_ip': 1.1,
    'real_oop': 0.98,
    'eq_3b': 0.5,
    'eq_4b': 0.54,
    '3b_ip': 3.0,
    '3b_oop': 3.6,
    'pf_call_margin': 0.0,
    'bluff_base': 0.15,
    'bluff_af': 1.2,
    'w_r_air': 0.5,
    'w_r_weak': 0.25,
    'w_r_mid': 0.6,
    'w_b_weak': 0.55,
    'w_b_mid': 0.85,
    'c_air': 0.15,
    'c_weak': 0.55,
    'c_mid': 0.88,
    'size_exp': 1.0,
    'max_sims': 1500,
    'max_ms': 2.5,
    'bet_sizes': [0.75, 1.2, 2.0],
    'raise_sizes': [1.0, 2.0],
    'shove_spr': 8,
    'chk_ip': 0.75,
    'chk_oop': 0.65,
    'bet_margin': -0.06,
    'call_tax': 0.0,
    'fold_vs_raise': 1.0,
    'raise_margin': -0.03,
}

# ---------------------------------------------------------------- tables
CLS_PCT = {}
ALLC = []
_cum = 0
for _c in RANK:
    _a, _b = RANKS.index(_c[0]), RANKS.index(_c[1])
    for _s1 in range(4):
        for _s2 in range(4):
            _x, _y = _a * 4 + _s1, _b * 4 + _s2
            if _x == _y:
                continue
            if len(_c) == 2 and _s1 >= _s2:
                continue
            if len(_c) == 3 and (_c[2] == "s") != (_s1 == _s2):
                continue
            ALLC.append((_x, _y))
    CLS_PCT[_c] = len(ALLC) / 1326.0
NC = len(ALLC)


def to_int(card):
    return RANKS.index(card[0]) * 4 + SUITS.index(card[1])


def hand_key(hole):
    a, b = RANKS.index(hole[0][0]), RANKS.index(hole[1][0])
    if a < b:
        a, b = b, a
    if a == b:
        return RANKS[a] + RANKS[b]
    return RANKS[a] + RANKS[b] + ("s" if hole[0][1] == hole[1][1] else "o")


def eq_vs_range(cls, f):
    row = EQR[cls]
    if f <= F[0]:
        return row[0]
    for i in range(1, len(F)):
        if f <= F[i]:
            t = (f - F[i - 1]) / (F[i] - F[i - 1])
            return row[i - 1] * (1 - t) + row[i] * t
    return row[-1]


def clamp(x, lo, hi):
    return lo if x < lo else hi if x > hi else x


class Stats:
    __slots__ = ("hands", "vpip", "pfr", "big", "pbet", "pcall", "pcheck", "faced", "ffold",
                 "f3", "f3fold", "sd", "sdwin")

    def __init__(self):
        for k in Stats.__slots__:
            setattr(self, k, 0)


# ---------------------------------------------------------------- agent
class Agent:
    def __init__(self):
        self.rng = random.Random()
        self.seat = 0
        self.n = 8
        self.total_hands = 1000
        self.spent = 0.0
        self.bank = 8.5
        self.hands_seen = 0
        self.st = {}
        self.post_decisions = 0

    def on_table_start(self, info):
        self.seat = info.get("seat", 0)
        self.n = info.get("num_players", 8)
        self.total_hands = info.get("hands", 1000) or 1000
        try:
            prebuild()
        except Exception:
            pass

    def S(self, seat):
        s = self.st.get(seat)
        if s is None:
            s = self.st[seat] = Stats()
        return s

    # ------------------------------------------------------------- stats
    def on_hand_end(self, summary):
        try:
            self._learn(summary)
        except Exception:
            pass

    def _learn(self, summary):
        self.hands_seen += 1
        hist = summary.get("history") or []
        seats = set(h.get("seat") for h in hist)
        bb = 20
        for h in hist:
            if h.get("action") == "big_blind":
                bb = h.get("amount") or 20
        for s in seats:
            self.S(s).hands += 1
        street = None
        cur = 0
        nraise = 0
        vp, pr = set(), set()
        for h in hist:
            a = h.get("action")
            s = h.get("seat")
            st = h.get("street")
            if st != street:
                street = st
                cur = bb if st == "preflop" else 0
                nraise = 0
                bets = {}
            if a in ("small_blind", "big_blind"):
                bets[s] = h.get("amount") or 0
                continue
            o = self.S(s)
            if st == "preflop":
                if a in ("call", "raise"):
                    vp.add(s)
                if nraise >= 1 and a in ("fold", "call", "raise"):
                    o.f3 += 1
                    if a == "fold":
                        o.f3fold += 1
                if a == "raise":
                    pr.add(s)
                    if (h.get("amount") or 0) >= 600:
                        o.big += 1
            else:
                if a == "raise":
                    o.pbet += 1
                elif a == "call":
                    o.pcall += 1
                elif a == "check":
                    o.pcheck += 1
                if cur > 0 and a in ("fold", "call", "raise"):
                    o.faced += 1
                    if a == "fold":
                        o.ffold += 1
            if a == "raise":
                cur = h.get("amount") or cur
                nraise += 1
        for s in vp:
            self.S(s).vpip += 1
        for s in pr:
            self.S(s).pfr += 1
        shown = summary.get("shown") or {}
        for k in shown:
            try:
                o = self.S(int(k))
                o.sd += 1
            except Exception:
                pass

    def vpip(self, s):
        o = self.S(s)
        return (o.vpip + P["pri_vpip"] * 12) / (o.hands + 12)

    def pfr(self, s):
        o = self.S(s)
        return (o.pfr + P["pri_pfr"] * 12) / (o.hands + 12)

    def bigrate(self, s):
        o = self.S(s)
        return (o.big + 0.05 * 10) / (o.hands + 10)

    def ftb(self, s):
        o = self.S(s)
        return (o.ffold + P["pri_ftb"] * 8) / (o.faced + 8)

    def af(self, s):
        o = self.S(s)
        return (o.pbet + 0.3 * 10) / (o.pbet + o.pcall + o.pcheck + 10)

    # ------------------------------------------------------------- time
    def budget(self):
        left = self.bank - self.spent
        if left <= 0.4:
            return 0.0
        hands_left = max(1, self.total_hands - self.hands_seen)
        per = left / (hands_left * 0.9 + 1)
        return clamp(per, 0.0, P["max_ms"] / 1000.0)

    # ------------------------------------------------------------- api
    def act(self, state):
        t0 = time.perf_counter()
        try:
            out = self.decide(state)
        except Exception:
            if DEBUG:
                raise
            out = None
        out = self.legalise(state, out)
        self.spent += time.perf_counter() - t0 + 0.0002
        return out

    def legalise(self, state, out):
        legal = state.get("legal_actions") or []
        to_call = state.get("to_call") or 0
        if not isinstance(out, dict):
            out = {}
        a = out.get("action")
        if a == "raise" or a == "all_in":
            if "raise" in legal:
                lo, hi = state.get("min_raise_to"), state.get("max_raise_to")
                if lo is None or hi is None:
                    return {"action": "all_in"}
                if a == "all_in":
                    return {"action": "raise", "amount": int(hi)}
                try:
                    amt = int(out.get("amount", lo))
                except Exception:
                    amt = lo
                return {"action": "raise", "amount": int(max(lo, min(hi, amt)))}
            a = "call"
        if a == "call":
            if to_call > 0 and "call" in legal:
                return {"action": "call"}
            return {"action": "check"} if to_call == 0 else {"action": "fold"}
        return {"action": "check"} if to_call == 0 else {"action": "fold"}

    def decide(self, state):
        if state["street"] == "preflop":
            return self.preflop(state)
        return self.postflop(state)

    # ------------------------------------------------------------- ranges
    def pf_range(self, state, j):
        """(lo, hi) fraction of ALLC that seat j's preflop actions suggest."""
        raised = False
        threeb = False
        called = False
        big = False
        nr = 0
        for h in state["history"]:
            if h["street"] != "preflop":
                break
            a = h["action"]
            if h["seat"] == j:
                if a == "raise":
                    raised = True
                    if nr >= 1:
                        threeb = True
                    if (h.get("amount") or 0) >= 600:
                        big = True
                elif a == "call":
                    called = True
            if a == "raise":
                nr += 1
        if big:
            f = clamp(max(self.bigrate(j), self.pfr(j) * 0.25), 0.025, 0.6)
            return 0.0, f
        if threeb:
            return 0.0, clamp(self.pfr(j) * P["r3_mult"], 0.025, 0.4)
        if raised:
            return 0.0, clamp(self.pfr(j), 0.04, 0.7)
        if called:
            hi = clamp(self.vpip(j), 0.1, 1.0)
            lo = clamp(self.pfr(j) * P["call_lo"], 0.0, hi * 0.5) if nr else 0.0
            return lo, hi
        return 0.0, 1.0

    # ------------------------------------------------------------- preflop
    def preflop(self, state):
        hole = state["hole_cards"]
        key = hand_key(hole)
        pct = CLS_PCT[key]
        bb = state["big_blind"]
        tc = state["to_call"]
        n = len(state["stacks"])
        me = state["seat"]
        btn = state["button"]
        pos = (me - btn) % n          # 0 BTN 1 SB 2 BB 3 UTG ...
        bets = state["bets"]
        stack = state["stacks"][me] + bets[me]
        cur = max(bets)
        pot = state["pot"]
        hist = [h for h in state["history"] if h["street"] == "preflop"]
        raises = [h for h in hist if h["action"] == "raise"]
        nlimp = sum(1 for h in hist if h["action"] == "call")
        folded = state["folded"]
        live = [i for i in range(n) if not folded[i] and i != me]
        acted = set(h["seat"] for h in hist if h["action"] not in ("small_blind", "big_blind"))
        behind = [i for i in live if i not in acted and i != me]

        if not raises:
            # open / iso / BB option
            if pos == 2 and tc == 0:
                if pct <= P["bb_raise"]:
                    return self.r(bb * (P["open_size"] + 1 + nlimp))
                return {"action": "check"}
            pk = {0: "o_btn", 1: "o_sb"}.get(pos)
            if pk is None:
                from_end = (n - pos) % n  # CO=1, HJ=2, ...
                pk = {1: "o_co", 2: "o_hj", 3: "o_mp"}.get(from_end, "o_ep")
            f = P[pk]
            if behind:
                av = sum(self.vpip(i) for i in behind) / len(behind)
                f *= clamp(1 + P["steal_k"] * (P["pri_vpip"] - av), 0.6, 2.2)
            if nlimp:
                f = max(f * P["iso_mult"], 0.06)
            if pct <= f:
                tabv = sum(self.vpip(i) for i in live) / max(1, len(live))
                size = P["open_size"] + (P["loose_add"] if tabv > 0.4 else 0) + nlimp
                if pos == 1:
                    size += 0.5
                return self.r(bb * size)
            if nlimp and tc <= bb and pct <= P["overlimp"] and pos in (0, 1, n - 1):
                return {"action": "call"}
            if pos == 1 and nlimp == 0 and tc <= bb // 2 and pct <= P["sb_limp"]:
                return {"action": "call"}
            return {"action": "check"} if tc == 0 else {"action": "fold"}

        # facing raise(s)
        raiser = raises[-1]["seat"]
        lo, hi = self.pf_range(state, raiser)
        e = eq_vs_range(key, hi)
        others = [i for i in live if i != raiser and (bets[i] > bb or i in acted and bets[i] >= cur)]
        extra = len([i for i in others if bets[i] >= cur])
        if extra:
            e = e ** (1 + P["multi_exp"] * extra)
        order = lambda s: (s - btn - 1) % n
        ip = order(me) > order(raiser)
        allin_call = tc >= state["stacks"][me]
        real = 1.0 if allin_call else (P["real_ip"] if ip else P["real_oop"])
        if pct <= 0.03:
            real = 1.0
        ev_call = e * real * (pot + tc) - tc
        nr = len(raises)
        if "raise" in state["legal_actions"] and nr < 4:
            thr = P["eq_3b"] if nr == 1 else P["eq_4b"]
            if e >= thr and not (extra and e < thr + 0.05):
                tgt = cur * (P["3b_ip"] if ip else P["3b_oop"]) + (pot - cur - bets[me]) * 0.5
                if nr >= 2 or tgt >= stack * 0.35:
                    return {"action": "all_in"}
                return self.r(tgt)
        if ev_call > P["pf_call_margin"] * bb:
            return {"action": "call"}
        return {"action": "fold"}

    def r(self, amt):
        return {"action": "raise", "amount": int(amt)}

    # ------------------------------------------------------------- postflop
    def opp_models(self, state, me):
        folded = state["folded"]
        stacks = state["stacks"]
        hist = state["history"]
        street = state["street"]
        models = []
        for j in range(len(folded)):
            if j == me or folded[j]:
                continue
            lo, hi = self.pf_range(state, j)
            agg = 0
            calls = 0
            raise_over = False
            for h in hist:
                if h["seat"] != j or h["street"] == "preflop":
                    continue
                if h["action"] == "raise":
                    agg += 1
                elif h["action"] == "call":
                    calls += 1
            # did j raise over someone else's bet this street?
            seen_bet = False
            for h in hist:
                if h["street"] != street:
                    continue
                if h["action"] == "raise":
                    if h["seat"] == j and seen_bet:
                        raise_over = True
                    seen_bet = True
            bl = clamp(P["bluff_base"] + (self.af(j) - 0.3) * P["bluff_af"], 0.04, 0.9)
            if agg >= 2 or raise_over:
                w = (bl * P["w_r_air"], P["w_r_weak"], P["w_r_mid"], 1.0)
            else:
                w = (bl, P["w_b_weak"], P["w_b_mid"], 1.0)
            m = self.ftb(j) / P["pri_ftb"]
            cont = (clamp(1 - (1 - P["c_air"]) * m, 0.0, 1), clamp(1 - (1 - P["c_weak"]) * m, 0.0, 1),
                    clamp(1 - (1 - P["c_mid"]) * m, 0.0, 1), 1.0)
            if agg >= 2 or raise_over:
                pass
            elif agg == 0 and calls:
                w = (max(0.02, cont[0]), max(0.05, cont[1]), max(0.1, cont[2]), 1.0)
            elif agg == 0:
                w = (1.0, 1.0, 1.0, 1.0)
            allin = stacks[j] == 0
            models.append((j, int(lo * NC), max(int(lo * NC) + 6, int(hi * NC)), w, cont, allin))
        return models

    def simulate(self, hole, board, models, sizes, budget):
        """Weighted MC. Returns eq, [(fold_prob, eq_when_called) per size]."""
        rng = self.rng
        my = [to_int(c) for c in hole]
        bd = [to_int(c) for c in board]
        dead = set(my) | set(bd)
        deck = [c for c in range(52) if c not in dead]
        need = 5 - len(bd)
        # current-board info for strength levels
        bprod = 1
        bsc = [0, 0, 0, 0]
        bsm = [0, 0, 0, 0]
        brc = [0] * 13
        for c in bd:
            bprod *= CP[c]
            bsc[c & 3] += 1
            bsm[c & 3] |= CB[c]
            brc[c >> 2] += 1
        top = max(c >> 2 for c in bd)
        bpairs = set(r for r in range(13) if brc[r] >= 2)
        draw_st = need > 0
        k = len(models)
        exps = [min(2.5, (s / 0.6) ** P["size_exp"]) for s in sizes]
        conts = []
        for (_, _, _, _, cont, allin) in models:
            row = []
            for e in exps:
                if allin:
                    row.append((1.0, 1.0, 1.0, 1.0))
                else:
                    row.append((cont[0] ** e, cont[1] ** e, cont[2] ** e, 1.0 if e < 2.0 else 0.92))
            conts.append(row)
        ns = len(sizes)
        W = 0.0
        E = 0.0
        FW = [0.0] * ns
        CW = [0.0] * ns
        CE = [0.0] * ns
        sims = 0
        t_end = time.perf_counter() + budget
        RTl = RT
        FLl = FL
        mp = CP[my[0]] * CP[my[1]]
        while True:
            for _ in range(4):
                used = set(dead)
                hands = []
                for (_, lo, hi, _, _, _) in models:
                    for _t in range(12):
                        h = ALLC[rng.randrange(lo, hi)]
                        if h[0] not in used and h[1] not in used:
                            break
                    else:
                        while True:
                            h = tuple(rng.sample(deck, 2))
                            if h[0] not in used and h[1] not in used:
                                break
                    used.add(h[0])
                    used.add(h[1])
                    hands.append(h)
                # strength levels on current board
                w = 1.0
                lv = []
                for idx in range(k):
                    h1, h2 = hands[idx]
                    v = RTl[bprod * CP[h1] * CP[h2]]
                    s1, s2 = h1 & 3, h2 & 3
                    for s in range(4):
                        cnt = bsc[s] + (s1 == s) + (s2 == s)
                        if cnt >= 5:
                            fv = FLl[bsm[s] | (CB[h1] if s1 == s else 0) | (CB[h2] if s2 == s else 0)]
                            if fv > v:
                                v = fv
                        elif cnt == 4 and draw_st and (s1 == s or s2 == s):
                            v = -1 if v < (1 << 20) else v  # flag flush draw w/ no pair
                    if v == -1:
                        L = 1
                    else:
                        cat = v >> 20
                        if cat >= 4:
                            L = 3
                        elif cat == 3:
                            L = 0 if brc[(v >> 8) & 15] >= 3 else 3
                        elif cat == 2:
                            p1, p2 = (v >> 8) & 15, (v >> 4) & 15
                            if p1 in bpairs and p2 in bpairs:
                                L = 0
                            elif p1 in bpairs or p2 in bpairs:
                                o = p2 if p1 in bpairs else p1
                                L = 2 if o >= top else 1
                            else:
                                L = 3
                        elif cat == 1:
                            p = (v >> 12) & 15
                            L = 0 if p in bpairs else (2 if p >= top else 1)
                        else:
                            L = 0
                    lv.append(L)
                    w *= models[idx][3][L]
                if w < 0.01:
                    w = 0.01
                # runout
                if need:
                    run = []
                    while len(run) < need:
                        c = deck[rng.randrange(len(deck))]
                        if c not in used:
                            used.add(c)
                            run.append(c)
                    full = bd + run
                else:
                    full = bd
                fp = 1
                fsc = [0, 0, 0, 0]
                fsm = [0, 0, 0, 0]
                for c in full:
                    fp *= CP[c]
                    fsc[c & 3] += 1
                    fsm[c & 3] |= CB[c]
                fs = -1
                for s in range(4):
                    if fsc[s] >= 3:
                        fs = s
                mv = RTl[fp * mp]
                if fs >= 0:
                    a, b = my
                    if fsc[fs] + ((a & 3) == fs) + ((b & 3) == fs) >= 5:
                        fv = FLl[fsm[fs] | (CB[a] if (a & 3) == fs else 0) | (CB[b] if (b & 3) == fs else 0)]
                        if fv > mv:
                            mv = fv
                best = 0
                ties = 0
                for (h1, h2) in hands:
                    v = RTl[fp * CP[h1] * CP[h2]]
                    if fs >= 0 and fsc[fs] + ((h1 & 3) == fs) + ((h2 & 3) == fs) >= 5:
                        fv = FLl[fsm[fs] | (CB[h1] if (h1 & 3) == fs else 0) | (CB[h2] if (h2 & 3) == fs else 0)]
                        if fv > v:
                            v = fv
                    if v > best:
                        best = v
                        ties = 0
                    elif v == best:
                        ties += 1
                if mv > best:
                    sh = 1.0
                elif mv == best:
                    sh = 1.0 / (ties + 2)
                else:
                    sh = 0.0
                W += w
                E += w * sh
                for si in range(ns):
                    pf = 1.0
                    for idx in range(k):
                        pf *= 1.0 - conts[idx][si][lv[idx]]
                    FW[si] += w * pf
                    wc = w * (1.0 - pf)
                    CW[si] += wc
                    CE[si] += wc * sh
                sims += 1
            if sims >= P["max_sims"] or (time.perf_counter() > t_end and sims >= 24):
                break
        self.last_sims = sims
        res = []
        for si in range(ns):
            res.append((FW[si] / W, CE[si] / CW[si] if CW[si] > 1e-9 else E / W))
        return E / W, res

    def postflop(self, state):
        me = state["seat"]
        pot = state["pot"]
        tc = state["to_call"]
        bets = state["bets"]
        my_bet = bets[me]
        cur = max(bets)
        stack = state["stacks"][me]
        n = len(bets)
        btn = state["button"]
        street = state["street"]
        lo_r, hi_r = state.get("min_raise_to"), state.get("max_raise_to")
        can_raise = "raise" in state["legal_actions"] and lo_r is not None
        models = self.opp_models(state, me)
        if not models:
            return {"action": "check"}
        # cap simulated opponents at 4
        models = models[:4]
        order = lambda s: (s - btn - 1) % n
        live = [m[0] for m in models]
        ip = all(order(me) > order(j) for j in live)
        cands = []
        if can_raise:
            if tc == 0:
                fr = P["bet_sizes"]
                base = pot
            else:
                fr = P["raise_sizes"]
                base = pot + tc
            seen = set()
            for f in fr:
                R = int(cur + tc * 0 + f * base) if tc == 0 else int(cur + f * base)
                R = max(lo_r, min(hi_r, R))
                if R not in seen:
                    seen.add(R)
                    cands.append(R)
            if hi_r not in seen and hi_r <= (my_bet + stack) and (hi_r - my_bet) <= P["shove_spr"] * pot:
                cands.append(hi_r)
        sizes = [max(0.05, (R - my_bet) / float(max(1, pot))) for R in cands]
        b = self.budget()
        if b <= 0:
            b = 0.0005
        e, res = self.simulate(state["hole_cards"], state["board"], models, sizes, b)
        if len(models) > 1:
            pass
        best_a = None
        if tc == 0:
            real = P["chk_ip"] if ip else P["chk_oop"]
            best_ev = e * pot * real
            best_a = {"action": "check"}
            for R, (f, ec) in zip(cands, res):
                add = R - my_bet
                ev = f * pot + (1 - f) * (ec * (pot + 2 * add) - add)
                if ev > best_ev + P["bet_margin"] * pot:
                    best_ev = ev
                    best_a = self.r(R)
            return best_a
        # facing a bet
        ev_call = e * (pot + tc) - tc
        if street != "river":
            ev_call -= P["call_tax"] * pot
        best_ev = 0.0
        best_a = {"action": "fold"}
        if ev_call > best_ev:
            best_ev = ev_call
            best_a = {"action": "call"}
        for R, (f, ec) in zip(cands, res):
            add = R - my_bet
            f2 = f * P["fold_vs_raise"]
            ev = f2 * pot + (1 - f2) * (ec * (pot + add + (R - cur)) - add)
            if ev > best_ev + P["raise_margin"] * pot:
                best_ev = ev
                best_a = self.r(R)
        return best_a
