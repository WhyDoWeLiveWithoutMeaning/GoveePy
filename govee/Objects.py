class Color:
    r: int
    g: int
    b: int

    def __init__(self, r, g, b):
        self.r = r % 256
        self.g = g % 256
        self.b = b % 256