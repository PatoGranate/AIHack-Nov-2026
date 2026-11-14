"""Fast evaluator (prime-product lookup + flush table). Copied verbatim into bot.py."""
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
