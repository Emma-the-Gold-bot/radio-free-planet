export async function loadSchema() {
  const res = await fetch('./data/layers.json');
  return res.json();
}
