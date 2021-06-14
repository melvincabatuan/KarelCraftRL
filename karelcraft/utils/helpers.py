# Helpers and constants

INFINITY = -1


def vec2tup(v):
    '''
    Converts Vec2 or Vec3 to int tuple
    '''
    return tuple(map(int, v))


def vec2key(v):
    '''
    Converts Vec2 or Vec3 to int tuple key or 2D position
    '''
    return tuple(map(int, v))[:2]


def vec2id(pos, cols):
    '''
    Maps Vec3 position into an id
    '''
    return pos[1] * cols + pos[0]


class KarelException(Exception):
    def __init__(self, position: tuple,
                 direction: str,
                 action: str,
                 message: str) -> None:
        super().__init__()
        self.position = position
        self.direction = direction
        self.action = action
        self.message = message

    def __str__(self) -> str:
        return (
            f"Karel crashed while on position {self.position}, "
            f"facing {self.direction}\nInvalid action: {self.message}"
        )
