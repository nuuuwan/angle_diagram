import os
import pathlib
from functools import cache, cached_property

from utils import Log, _, JSONFile

from utils_future import BBox, LatLng

log = Log('AngleDiagram')


class AngleDiagram:
    class STYLES:
        class PLACE:
            CIRCLE = dict(r=9, fill='white', stroke='grey', stroke_width=6)
            TEXT = dict(
                text_anchor='start',
                dominant_baseline='middle',
                font_size=18,
                font_family="P22 Johnston Underground",
            )

        class ROAD:
            PATH = dict(stroke='red', stroke_width=6, fill='none')

    @staticmethod
    def norm_places(places: dict[str, LatLng]) -> dict[str, LatLng]:
        lat_list = [latlng.lat for latlng in places.values()]
        lng_list = [latlng.lng for latlng in places.values()]
        lat_to_i_lat = {lat: i for i, lat in enumerate(sorted(set(lat_list)))}
        lng_to_i_lng = {lng: i for i, lng in enumerate(sorted(set(lng_list)))}

        return {place: LatLng(lat_to_i_lat[lat], lng_to_i_lng[lng]) for place, (lat, lng) in places.items()}

    def __init__(
        self,
        places: dict[str, LatLng],
        roads: dict[str, tuple[str]],
        width_height: tuple[float, float],
        padding: float,
    ):
        self.places = AngleDiagram.norm_places(places)
        self.roads = roads
        self.width_height = width_height
        self.padding = padding

    def to_dict(self) -> dict: 
        return dict(
            places={place: latlng.to_tuple() for place, latlng in sorted(self.places.items(), key=lambda x: x[0])},
            roads={road: places for road, places in sorted(self.roads.items(), key=lambda x: x[0])},
            width_height=self.width_height,
            padding=self.padding,
        )
    
    @staticmethod 
    def from_dict(d: dict) -> 'AngleDiagram':
        return AngleDiagram(
            places={place: LatLng.from_tuple(latlng) for place, latlng in d['places'].items()},
            roads={road: tuple(places) for road, places in d['roads'].items()},
            width_height=d['width_height'],
            padding=d['padding'],
        )
    
    @staticmethod
    def from_file(path: pathlib.Path) -> 'AngleDiagram':
        d = JSONFile(path).read()
        diagram =  AngleDiagram.from_dict(d)
        JSONFile(path).write(diagram.to_dict())
        return diagram
    
    def to_file(self, path: pathlib.Path):
        JSONFile(path).write(self.to_dict())
    
    @cached_property
    def bbox(self) -> BBox:
        return BBox.fromLatLngList(self.places.values())

    @cached_property
    def transformer(self) -> callable:
        return self.bbox.get_transformer(self.width_height, self.padding)

    @cache
    def get_svg_place(self, place: str, latlng: LatLng) -> _:
        x, y = self.transformer(latlng)
        return _(
            'g',
            [
                _(
                    'circle',
                    None,
                    AngleDiagram.STYLES.PLACE.CIRCLE | dict(cx=x, cy=y),
                ),
                _(
                    'text',
                    str(place),
                    AngleDiagram.STYLES.PLACE.TEXT
                    | dict(
                        x=x + AngleDiagram.STYLES.PLACE.TEXT['font_size'], y=y
                    ),
                ),
            ],
        )

    @cached_property
    def svg_places(self):
        return _(
            'g',
            [
                self.get_svg_place(place, latlng)
                for place, latlng in self.places.items()
            ],
        )

    @cache
    def get_svg_road(self, road: str, places: tuple[str]) -> _:
        d_list = []
        n = len(places)
        for i in range(n - 1):
            latlng1 = self.places[places[i]]
            latlng2 = self.places[places[i + 1]]
            x1, y1 = self.transformer(latlng1)
            x2, y2 = self.transformer(latlng2)
            dx, dy = x2 - x1, y2 - y1
            if any([dx == dy, dx == 0, dy == 0]):
                d_list.append(f'M{x1},{y1}L{x2},{y2}')
            else:
                sign_x = dx / abs(dx)
                sign_y = dy / abs(dy)
                sign = sign_x * sign_y
                if abs(dx) < abs(dy):
                    x3, y3 = x2 - dx, y2 - dx * sign
                else:
                    x3, y3 = x2 - dy * sign, y2 - dy

                d_list.append(f'M{x1},{y1}L{x3},{y3}L{x2},{y2}')

        d = ' '.join(d_list)
        path = _('path', None, AngleDiagram.STYLES.ROAD.PATH | dict(d=d))

        return _('g', [path])

    @cached_property
    def svg_roads(self):
        return _(
            'g',
            [
                self.get_svg_road(road, places)
                for road, places in self.roads.items()
            ],
        )

    @cached_property
    def svg(self) -> _:
        width, height = self.width_height
        padding = self.padding
        svg = _(
            'svg',
            [self.svg_roads, self.svg_places],
            dict(width=width + 2 * padding, height=height + 2 * padding),
        )
        return svg

    def write(self, path: pathlib.Path):
        self.svg.store(path)
        log.debug(f'Wrote {path}')
        os.startfile(path)

