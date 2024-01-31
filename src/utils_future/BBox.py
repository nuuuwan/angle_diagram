from dataclasses import dataclass
from functools import cached_property

from utils_future.LatLng import LatLng


@dataclass
class BBox:
    min: LatLng
    max: LatLng

    @cached_property
    def min_lat(self) -> float:
        return self.min.lat

    @cached_property
    def min_lng(self) -> float:
        return self.min.lng

    @cached_property
    def max_lat(self) -> float:
        return self.max.lat

    @cached_property
    def max_lng(self) -> float:
        return self.max.lng

    @cached_property
    def lat_span(self) -> float:
        return self.max_lat - self.min_lat

    @cached_property
    def lng_span(self) -> float:
        return self.max_lng - self.min_lng

    @staticmethod
    def fromLatLngList(latLngList: list[LatLng]):
        latList = [latLng.lat for latLng in latLngList]
        lngList = [latLng.lng for latLng in latLngList]
        return BBox(
            min=LatLng(min(latList), min(lngList)),
            max=LatLng(max(latList), max(lngList)),
        )

    def get_transformer(
        self, width_height: tuple[float, float], padding: float
    ) -> callable:
        def transformer(latLng: LatLng) -> tuple[float, float]:
            lat, lng = latLng.lat, latLng.lng

            plat = (lat - self.min_lat) / self.lat_span
            plng = (lng - self.min_lng) / self.lng_span

            width, height = width_height
            x = padding + plng * (width - 2 * padding)
            y = padding + (1 - plat) * (height - 2 * padding)
            return x, y

        return transformer
