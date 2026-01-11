def clamp(val, minv, maxv):
    return max(minv, min(maxv, val))

def norm_to_angle(norm):
    # map to servo angle 0-180
    angle = int(((norm + 1) / 2) * 180)
    return clamp(angle, 0, 180)


def estimate_distance(area):
    MAX_AREA = 640 * 480 * 0.6
    MIN_AREA = 2000

    area = clamp(area, MIN_AREA, MAX_AREA)

    z = 1-((area - MIN_AREA) / (MAX_AREA - MIN_AREA))
    return clamp(z, 0 ,1)
