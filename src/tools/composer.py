"""
Composition tool stubs.

Each function represents one stage in the music-creation pipeline.
The LLM-driven implementations in composer_agent.py call these helpers,
but you can also replace the bodies here with real music-generation API
calls (e.g. Suno, Udio, MusicGen, MIDI generation libraries, etc.).
"""

from __future__ import annotations


def write_lyrics(
    theme: str,
    genre: str,
    mood: str,
    structure: str,
    user_request: str,
) -> str:
    """Generate song lyrics.

    Args:
        theme: Core theme or story of the song.
        genre: Music genre (e.g. pop, rock, jazz).
        mood: Emotional mood (e.g. melancholic, upbeat, romantic).
        structure: Song structure (e.g. verse-chorus-verse-chorus-bridge-chorus).
        user_request: Original user request for extra context.

    Returns:
        The full lyrics as a plain text string.

    TODO: replace with a call to a lyrics-generation API or a fine-tuned
          model if you want specialised lyric output.
    """
    raise NotImplementedError("Implement or delegate to LLM in composer_agent.py")


def create_arrangement(
    lyrics: str,
    genre: str,
    mood: str,
    instruments: list[str],
    key: str,
    tempo: str,
) -> str:
    """Design the musical arrangement.

    Args:
        lyrics: The finished lyrics produced in the previous step.
        genre: Music genre.
        mood: Emotional mood.
        instruments: List of instruments to use.
        key: Musical key (e.g. C major, A minor).
        tempo: Tempo description (e.g. slow 70 BPM, upbeat 120 BPM).

    Returns:
        A textual description of the arrangement (chord progressions,
        instrumentation layers, dynamics, etc.).

    TODO: replace with calls to a chord-generation or arrangement API
          (e.g. send to a DAW automation script, call HookTheory API, etc.).
    """
    raise NotImplementedError("Implement or delegate to LLM in composer_agent.py")


def compose_melody(
    lyrics: str,
    arrangement: str,
    key: str,
    tempo: str,
    genre: str,
) -> str:
    """Compose the melodic line.

    Args:
        lyrics: The finished lyrics.
        arrangement: The arrangement description from the previous step.
        key: Musical key.
        tempo: Tempo description.
        genre: Music genre.

    Returns:
        A textual (and/or ABC-notation / lilypond) description of the melody.

    TODO: replace with a real melody-generation model (e.g. MusicGen,
          Magenta, custom MIDI generator) that produces actual note data.
    """
    raise NotImplementedError("Implement or delegate to LLM in composer_agent.py")


def produce_full_song(
    title: str,
    lyrics: str,
    arrangement: str,
    melody: str,
    genre: str,
    mood: str,
) -> str:
    """Assemble and present the complete song.

    Args:
        title: Song title.
        lyrics: Finished lyrics.
        arrangement: Arrangement description.
        melody: Melody description.
        genre: Music genre.
        mood: Emotional mood.

    Returns:
        A formatted summary presenting the complete composition.

    TODO: replace with an audio-rendering pipeline (e.g. feed MIDI + stems
          into a DAW, call a text-to-music API like Suno/Udio, etc.) that
          returns a URL or binary audio file.
    """
    raise NotImplementedError("Implement or delegate to LLM in composer_agent.py")
