import math
import os
import pathlib
import random
from functools import cache, cached_property

from reportlab.graphics import renderPM
from svglib.svglib import svg2rlg
from utils import Log, _

from utils_future import BBox, LatLng

log = Log('AngleDiagramRender')

COLOR_CACHE = {}


def get_color(x):
    if x not in COLOR_CACHE:
        h = random.randint(0, 240)
        COLOR_CACHE[x] = f'hsla({h}, 100%, 25%, 0.5)'
    return COLOR_CACHE[x]


FONT_FAMILY = "P22 Johnston Underground"
FONT_SIZE = 16


class AngleDiagramRender:
    class STYLES:
        TITLE = dict(
            font_family=FONT_FAMILY, fill="gray", text_anchor="middle"
        )

        class PLACE:
            CIRCLE = dict(r=9, fill='white', stroke='grey', stroke_width=6)
            TEXT = dict(
                text_anchor='start',
                dominant_baseline='middle',
                font_size=FONT_SIZE,
                font_family=FONT_FAMILY,
            )

        class ROAD:
            PATH = dict(stroke_width=12, fill='none')

            LABEL = dict(font_size=FONT_SIZE * 2 / 3, font_family=FONT_FAMILY)

    @cached_property
    def norm_places(self) -> dict[str, LatLng]:
        places = self.places
        place_keys = sorted(places.keys())
        n_places = len(places)
        MIN_D = 0.2
        ALPHA = 0.01
        MAX_ITERS = 1_000
        for iter in range(MAX_ITERS):
            if iter % 100 == 0:
                log.debug(f'{iter=}')
            no_changes = True
            for i1 in range(n_places):
                lat1, lng1 = places[place_keys[i1]].to_tuple()
                slat, slng = 0, 0
                for i2 in range(n_places):
                    if i1 == i2:
                        continue
                    latlng2 = places[place_keys[i2]]
                    lat2, lng2 = latlng2.to_tuple()
                    dlat, dlng = lat2 - lat1, lng2 - lng1
                    d = math.sqrt(dlat**2 + dlng**2)
                    if d < MIN_D:
                        slat -= dlat * ALPHA
                        slng -= dlng * ALPHA
                if slat != 0 or slng != 0:
                    no_changes = False
                    places[place_keys[i1]] = LatLng(lat1 + slat, lng1 + slng)

            if no_changes:
                break

        return places

    @cached_property
    def bbox(self) -> BBox:
        return BBox.fromLatLngList(self.norm_places.values())

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
                    AngleDiagramRender.STYLES.PLACE.CIRCLE | dict(cx=x, cy=y),
                ),
                _(
                    'text',
                    str(place),
                    AngleDiagramRender.STYLES.PLACE.TEXT
                    | dict(
                        x=x
                        + AngleDiagramRender.STYLES.PLACE.TEXT['font_size'],
                        y=y,
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
                for place, latlng in self.norm_places.items()
            ],
        )

    @cache
    def get_svg_road(self, road: str, places: tuple[str]) -> _:
        d_list = []
        n = len(places)
        labels = []
        for i in range(n - 1):
            latlng1 = self.norm_places[places[i]]
            latlng2 = self.norm_places[places[i + 1]]
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

                label = _(
                    'text',
                    str(road),
                    AngleDiagramRender.STYLES.ROAD.LABEL | dict(x=x3, y=y3),
                )
                labels.append(label)

                d_list.append(f'M{x1},{y1}L{x3},{y3}L{x2},{y2}')

        d = ' '.join(d_list)
        stroke = get_color(road)
        path = _(
            'path',
            None,
            AngleDiagramRender.STYLES.ROAD.PATH | dict(d=d, stroke=stroke),
        )

        return _('g', [path] + labels)

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
    def svg_titles(self) -> _:
        width, height = self.width_height
        padding = self.padding
        return _(
            'g',
            [
                _(
                    'text',
                    self.title,
                    AngleDiagramRender.STYLES.TITLE
                    | dict(
                        x=width / 2 + padding,
                        y=padding * 1.5,
                        font_size=FONT_SIZE * 8,
                    ),
                ),
                _(
                    'text',
                    self.sub_title,
                    AngleDiagramRender.STYLES.TITLE
                    | dict(
                        x=width / 2 + padding,
                        y=padding * 2.5,
                        font_size=FONT_SIZE * 4,
                    ),
                ),
                _(
                    'text',
                    self.footer,
                    AngleDiagramRender.STYLES.TITLE
                    | dict(
                        x=width / 2 + padding,
                        y=height + padding * 3,
                        font_size=FONT_SIZE * 4.5,
                    ),
                ),
            ],
        )

    @cached_property
    def svg(self) -> _:
        width, height = self.width_height
        padding = self.padding
        svg = _(
            'svg',
            [self.svg_roads, self.svg_places, self.svg_titles],
            dict(width=width + 2 * padding, height=height + 4 * padding),
        )
        return svg

    def write(self, path: pathlib.Path):
        self.svg.store(path)
        log.debug(f'Wrote {path}')
        png_path = path.with_suffix('.png')

        drawing = svg2rlg(path)
        renderPM.drawToFile(drawing, png_path, fmt="PNG", dpi=300)
        log.info(f'Wrote {png_path}')

        os.startfile(png_path)
