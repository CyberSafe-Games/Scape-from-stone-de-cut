"""Cadência e pivô das poses preparadas de Jan-Pietro."""
NAME='corpo seco'
IDLE_FRAME_MS=160  # 6,25 quadros/s; ida e volta sem salto na emenda.
IDLE_POSE_ORDER=(0,2,4,6,7,5,3,1)  # Inspiração seguida de expiração.
IDLE_SEQUENCE=IDLE_POSE_ORDER+tuple(reversed(IDLE_POSE_ORDER[1:-1]))
FOOT_ANCHOR=(224,318)


def idle_frame(elapsed_ms):
    return IDLE_SEQUENCE[int(max(0,elapsed_ms)//IDLE_FRAME_MS)%len(IDLE_SEQUENCE)]
