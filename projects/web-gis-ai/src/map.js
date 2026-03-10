export function createMap() {
  const map = new maplibregl.Map({
    container: 'map',
    style: 'https://demotiles.maplibre.org/style.json',
    center: [-121.5, 38.6],
    zoom: 8
  });

  map.addControl(new maplibregl.NavigationControl(), 'top-right');
  return map;
}
