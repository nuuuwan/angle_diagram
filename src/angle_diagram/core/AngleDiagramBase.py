import pathlib

from utils import JSONFile, Log

from utils_future import LatLng

log = Log('AngleDiagramBase')


class AngleDiagramBase:
    def __init__(
        self,
        title: str,
        sub_title: str,
        footer: str,
        places: dict[str, LatLng],
        roads: dict[str, tuple[str]],
        width_height: tuple[float, float],
        padding: float,
    ):

        self.title = title
        self.sub_title = sub_title
        self.footer = footer
        self.places = places
        self.roads = roads
        self.width_height = width_height
        self.padding = padding

    def to_dict(self) -> dict:
        return dict(
            title=self.title,
            sub_title=self.sub_title,
            footer=self.footer,
            places={
                place: latlng.to_tuple()
                for place, latlng in sorted(
                    self.places.items(), key=lambda x: x[0]
                )
            },
            roads={
                road: places
                for road, places in sorted(
                    self.roads.items(), key=lambda x: x[0]
                )
            },
            width_height=self.width_height,
            padding=self.padding,
        )

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            title=d['title'],
            sub_title=d['sub_title'],
            footer=d['footer'],
            places={
                place: LatLng.from_tuple(latlng)
                for place, latlng in d['places'].items()
            },
            roads={
                road: tuple(places) for road, places in d['roads'].items()
            },
            width_height=d['width_height'],
            padding=d['padding'],
        )

    @classmethod
    def from_file(cls, path: pathlib.Path):
        d = JSONFile(path).read()
        diagram = cls.from_dict(d)
        diagram.to_file(path)
        return diagram

    def to_file(self, path: pathlib.Path):
        JSONFile(path).write(self.to_dict())
