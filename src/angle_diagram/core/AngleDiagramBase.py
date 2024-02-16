import pathlib
import webbrowser
from functools import cached_property

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
        self.validate()

    def validate(self):
        a_diff_b = self.place_ids - self.place_ids_from_roads
        b_diff_a = self.place_ids_from_roads - self.place_ids

        if b_diff_a:
            for place_id in sorted(list(b_diff_a)):
                print(f'    "{place_id}": [],')
                gmaps_link = f'https://www.google.com/maps/place/{place_id}'
                webbrowser.open(gmaps_link)
            raise Exception(f'Places not in places: {b_diff_a}')

        if a_diff_b:
            raise Exception(f'Places not in roads: {a_diff_b}')

    @cached_property
    def place_ids(self):
        return set(self.places.keys())

    @cached_property
    def place_ids_from_roads(self):
        place_ids = set()
        for road, places in self.roads.items():
            for place in places:
                place_ids.add(place)
        return place_ids

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
