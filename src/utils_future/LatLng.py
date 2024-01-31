from dataclasses import dataclass


@dataclass
class LatLng:
    lat: float
    lng: float

    def __hash__(self) -> int:
        return hash((self.lat, self.lng))

    def to_tuple(self) -> dict:
        return [LatLng.norm(self.lat), LatLng.norm(self.lng)]

    @staticmethod
    def from_tuple(t: [float, float]) -> 'LatLng':
        return LatLng(lat=t[0], lng=t[1])

    @staticmethod
    def norm(x: float) -> float:
        return round(x, 4)
