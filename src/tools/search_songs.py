from __future__ import annotations

from pydantic import BaseModel, Field


class SongSearchResult(BaseModel):
    """A single song returned from the vector database."""

    title: str = Field(description="Song title")
    artist: str = Field(description="Artist / performer name")
    album: str = Field(default="", description="Album name (if available)")
    genre: str = Field(default="", description="Genre tag")
    score: float = Field(default=0.0, description="Similarity score from vector search")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class SongSearchResponse(BaseModel):
    """Wrapper for a list of search results."""

    results: list[SongSearchResult] = Field(default_factory=list)
    total: int = Field(default=0, description="Total number of matches")


async def search_songs_from_vector_db(
    query: str,
    top_k: int = 10,
) -> SongSearchResponse:
    from asyncio import sleep

    await sleep(1)

    # Mock data for development/testing
    mock_results = [
        SongSearchResult(
            title="Chasing Summer",
            artist="The Sunsets",
            album="Endless Days",
            genre="Pop",
            score=0.947,
            metadata={"year": 2020, "mood": "upbeat, sunny"},
        ),
        SongSearchResult(
            title="Rainy Morning Blues",
            artist="Jodie Lane",
            album="Skyline Sketches",
            genre="Blues",
            score=0.914,
            metadata={"year": 2018, "mood": "melancholic, relaxed"},
        ),
        SongSearchResult(
            title="Heartbeat Drive",
            artist="Neon Arrows",
            album="Night Runner",
            genre="Synthwave",
            score=0.872,
            metadata={"year": 2023, "mood": "energetic, driving"},
        ),
    ]
    return SongSearchResponse(results=mock_results[:top_k], total=3)
