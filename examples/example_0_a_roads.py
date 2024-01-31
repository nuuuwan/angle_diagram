import pathlib

from angle_diagram import AngleDiagram
from utils_future import LatLng


def main():  # noqa
    diagram = AngleDiagram.from_file(pathlib.Path(__file__).with_suffix('.json'))
    diagram.write(pathlib.Path(__file__).with_suffix('.svg'))


if __name__ == '__main__':
    main()
