from __future__ import annotations

GENRE_NORMALIZATION_MAP: dict[str, str] = {
    # Alternative / Indie
    "alt": "alternative",
    "alt-rock": "alternative",
    "alt rock": "alternative",
    "alternative rock": "alternative",
    "indie rock": "indie",
    "indie pop": "indie",
    "indiepop": "indie",
    "indietronica": "indie",

    # Electronic
    "electronic music": "electronic",
    "electronica": "electronic",
    "electro": "electronic",
    "idm": "electronic",
    "beats": "electronic",
    "downtempo": "electronic",
    "chillout": "electronic",
    "chill out": "electronic",
    "trip-hop": "electronic",
    "trip hop": "electronic",
    "synthwave": "electronic",
    "synth": "electronic",
    "glitch": "electronic",
    "breakbeat": "electronic",

    # House / Techno / Club
    "house": "house",
    "deep house": "house",
    "tech house": "house",
    "techno": "techno",
    "minimal": "techno",
    "minimal techno": "techno",
    "trance": "trance",
    "drum and bass": "dnb",
    "drum & bass": "dnb",
    "d&b": "dnb",
    "jungle": "dnb",
    "dubstep": "dubstep",
    "garage": "garage",
    "uk garage": "garage",
    "grime": "grime",
    "bass": "bass",
    "bass music": "bass",
    "new beat": "electronic",
    "ebm": "industrial",
    "industrial": "industrial",

    # Ambient / Drone
    "ambient": "ambient",
    "drone": "ambient",
    "new age": "ambient",
    "meditative": "ambient",
    "space music": "ambient",

    # Hip-hop / R&B
    "hip hop": "hip-hop",
    "hiphop": "hip-hop",
    "hip-hop": "hip-hop",
    "rap": "hip-hop",
    "r&b": "soul",
    "rnb": "soul",
    "rhythm and blues": "soul",
    "neo-soul": "soul",
    "neo soul": "soul",

    # Jazz
    "jazz": "jazz",
    "free jazz": "jazz",
    "nu jazz": "jazz",
    "smooth jazz": "jazz",
    "avant-garde jazz": "jazz",
    "bebop": "jazz",
    "fusion": "jazz",

    # Soul / Funk / Disco
    "soul": "soul",
    "funk": "funk",
    "classic disco": "disco",
    "disco": "disco",
    "boogie": "disco",
    "nu-disco": "disco",

    # Rock
    "rock": "rock",
    "classic rock": "rock",
    "hard rock": "rock",
    "psychedelic": "rock",
    "psych": "rock",
    "garage rock": "rock",
    "post-rock": "rock",
    "post rock": "rock",
    "prog": "rock",
    "progressive rock": "rock",
    "stoner": "rock",
    "punk": "punk",
    "post-punk": "punk",
    "post punk": "punk",
    "new wave": "punk",
    "hardcore": "punk",

    # Metal
    "metal": "metal",
    "heavy metal": "metal",
    "death metal": "metal",
    "black metal": "metal",
    "doom": "metal",
    "sludge": "metal",

    # World / Reggae / Latin
    "world": "world",
    "world music": "world",
    "afrobeat": "world",
    "afrobeats": "world",
    "latin": "latin",
    "cumbia": "latin",
    "salsa": "latin",
    "reggaeton": "latin",
    "bossa nova": "latin",
    "reggae": "reggae",
    "dub": "reggae",
    "dancehall": "reggae",
    "ska": "reggae",
    "kuduro": "world",
    "batida": "world",

    # Folk / Country / Americana
    "folk": "folk",
    "folk rock": "folk",
    "acoustic": "folk",
    "singer-songwriter": "folk",
    "country": "country",
    "bluegrass": "country",
    "americana": "country",

    # Classical
    "classical music": "classical",
    "classical": "classical",
    "contemporary classical": "classical",
    "orchestral": "classical",
    "opera": "classical",
    "chamber": "classical",

    # Blues / Gospel
    "blues": "blues",
    "gospel": "blues",
    "delta blues": "blues",

    # Experimental / Noise
    "experimental": "experimental",
    "noise": "experimental",
    "avant-garde": "experimental",
    "sound art": "experimental",
    "musique concrète": "experimental",

    # Talk / News / Public Radio
    "news/talk": "talk",
    "public radio": "talk",
    "spoken word": "talk",
    "talk": "talk",
    "news": "talk",
    "podcast": "talk",
    "comedy": "talk",
    "discussion": "talk",

    # Eclectic / Freeform / Variety
    "eclectic": "eclectic",
    "freeform": "freeform",
    "variety": "variety",
    "various": "variety",
    "variety mix": "eclectic",
    "mixed": "eclectic",
    "community": "eclectic",
    "college": "eclectic",
}


def normalize_genre(raw_genre: str | None) -> tuple[str, str]:
    if not raw_genre:
        return "unknown", "unknown"
    raw = raw_genre.strip()
    if not raw:
        return "unknown", "unknown"
    normalized = GENRE_NORMALIZATION_MAP.get(raw.lower(), raw.lower())
    return normalized, raw
