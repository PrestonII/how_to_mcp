#!/usr/bin/env python3
"""
fetch_transcript.py - Fetch meeting transcript from Fireflies.ai API.

Retrieves the BIMIT Plan Orientation transcript and optionally the video URL.
Requires a Fireflies API key set as FIREFLIES_API_KEY environment variable.

Usage:
    export FIREFLIES_API_KEY=your_api_key_here
    python3 fetch_transcript.py
    python3 fetch_transcript.py --search "BIMIT Plan Orientation"
    python3 fetch_transcript.py --id <transcript_id>
"""

import argparse
import json
import os
import sys
from datetime import datetime, date

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)


FIREFLIES_API_URL = "https://api.fireflies.ai/graphql"


def get_api_key() -> str:
    key = os.environ.get("FIREFLIES_API_KEY", "")
    if not key:
        print("ERROR: FIREFLIES_API_KEY environment variable not set.")
        print("\nTo set it:")
        print("  export FIREFLIES_API_KEY=your_api_key_here")
        print("\nGet your API key from: https://app.fireflies.ai/integrations/custom/fireflies")
        sys.exit(1)
    return key


def graphql_request(query: str, variables: dict = None) -> dict:
    """Execute a GraphQL request against the Fireflies API."""
    api_key = get_api_key()
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {"query": query}
    if variables:
        payload["variables"] = variables

    response = requests.post(FIREFLIES_API_URL, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "errors" in data:
        print(f"GraphQL errors: {json.dumps(data['errors'], indent=2)}")
        sys.exit(1)

    return data.get("data", {})


def list_transcripts(from_date: str = None, to_date: str = None, limit: int = 20) -> list:
    """List available transcripts, optionally filtered by date."""
    query = """
    query GetTranscripts($limit: Int, $fromDate: String, $toDate: String) {
        transcripts(limit: $limit, fromDate: $fromDate, toDate: $toDate) {
            id
            title
            date
            duration
            participants {
                name
                email
            }
        }
    }
    """
    variables = {"limit": limit}
    if from_date:
        variables["fromDate"] = from_date
    if to_date:
        variables["toDate"] = to_date

    data = graphql_request(query, variables)
    return data.get("transcripts", [])


def search_transcripts(query_str: str, limit: int = 10) -> list:
    """Search transcripts by keyword."""
    query = """
    query SearchTranscripts($query: String!, $limit: Int) {
        transcripts(search: $query, limit: $limit) {
            id
            title
            date
            duration
            video_url
        }
    }
    """
    data = graphql_request(query, {"query": query_str, "limit": limit})
    return data.get("transcripts", [])


def get_transcript_details(transcript_id: str) -> dict:
    """Get full transcript details including sentences, video URL, and summary."""
    query = """
    query GetTranscriptDetails($id: String!) {
        transcript(id: $id) {
            id
            title
            date
            duration
            video_url
            transcript_url
            summary {
                keywords
                action_items
                outline
                overview
                bullet_gist
                short_summary
                meeting_type
            }
            sentences {
                index
                speaker_name
                start_time
                end_time
                text
                raw_text
            }
            participants {
                name
                email
            }
        }
    }
    """
    data = graphql_request(query, {"id": transcript_id})
    return data.get("transcript", {})


def format_time(ms: int) -> str:
    """Convert milliseconds to MM:SS format."""
    total_seconds = ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"


def extract_key_moments(sentences: list) -> list:
    """
    Parse transcript sentences to identify timestamps where presenter
    is showing something on screen (visual cue phrases).
    """
    visual_cues = [
        "let me show you",
        "let me pull up",
        "let me open",
        "if you look at",
        "look at",
        "go to",
        "here you can see",
        "you can see here",
        "i'm going to go to",
        "navigate to",
        "open up",
        "pull up",
        "switch to",
        "i'll show you",
        "if i go to",
        "if we look at",
        "this is the",
        "here's the",
        "you'll see",
        "can you see",
    ]

    key_moments = []
    for sentence in sentences:
        text_lower = sentence.get("text", "").lower()
        for cue in visual_cues:
            if cue in text_lower:
                start_ms = sentence.get("start_time", 0)
                # Add 1.5s offset for screen to update
                capture_ms = start_ms + 1500
                key_moments.append({
                    "timestamp_ms": start_ms,
                    "capture_ms": capture_ms,
                    "capture_sec": capture_ms / 1000,
                    "time_display": format_time(start_ms),
                    "speaker": sentence.get("speaker_name", "Unknown"),
                    "text": sentence.get("text", ""),
                    "cue_phrase": cue,
                })
                break

    return key_moments


def save_transcript_text(transcript: dict, output_file: str = "transcript.txt"):
    """Save formatted transcript to a text file."""
    sentences = transcript.get("sentences", [])
    with open(output_file, "w") as f:
        f.write(f"# {transcript.get('title', 'Meeting Transcript')}\n")
        f.write(f"Date: {transcript.get('date', 'Unknown')}\n")
        f.write(f"Duration: {transcript.get('duration', 0) // 60} minutes\n\n")
        f.write("=" * 60 + "\n\n")

        for sentence in sentences:
            ts = format_time(sentence.get("start_time", 0))
            speaker = sentence.get("speaker_name", "Unknown")
            text = sentence.get("text", "")
            f.write(f"[{ts}] {speaker}: {text}\n")

    print(f"Transcript saved: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch meeting transcript from Fireflies.ai API"
    )
    parser.add_argument(
        "--search", "-s",
        default="BIMIT Plan Orientation",
        help="Search term to find the meeting (default: 'BIMIT Plan Orientation')"
    )
    parser.add_argument(
        "--id", "-i",
        help="Direct transcript ID to fetch"
    )
    parser.add_argument(
        "--from-date",
        default="2026-02-18",
        help="Filter transcripts from this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--to-date",
        default="2026-02-19",
        help="Filter transcripts to this date (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--output", "-o",
        default="transcript_data.json",
        help="Output file for transcript data"
    )
    parser.add_argument(
        "--list-only", "-l",
        action="store_true",
        help="Only list transcripts, don't fetch full details"
    )
    args = parser.parse_args()

    if args.id:
        print(f"Fetching transcript by ID: {args.id}")
        transcript = get_transcript_details(args.id)
    else:
        print(f"Searching for: '{args.search}'")
        transcripts = list_transcripts(
            from_date=args.from_date,
            to_date=args.to_date,
            limit=20
        )

        if not transcripts:
            print("No transcripts found for the given date range.")
            print("Trying broader search...")
            transcripts = search_transcripts(args.search)

        if not transcripts:
            print(f"No transcripts found matching '{args.search}'")
            sys.exit(1)

        print(f"\nFound {len(transcripts)} transcript(s):\n")
        for i, t in enumerate(transcripts):
            print(f"  [{i}] {t.get('title', 'Untitled')}")
            print(f"       ID: {t.get('id')}")
            print(f"       Date: {t.get('date')}")
            if t.get("video_url"):
                print(f"       Video: {t.get('video_url')}")
            print()

        if args.list_only:
            return

        # Auto-select BIMIT match or first result
        selected = None
        for t in transcripts:
            title = t.get("title", "").lower()
            if "bimit" in title or "plan orientation" in title:
                selected = t
                break
        if not selected:
            selected = transcripts[0]

        print(f"Selected: {selected.get('title')} (ID: {selected.get('id')})")
        transcript = get_transcript_details(selected["id"])

    if not transcript:
        print("ERROR: Could not fetch transcript details.")
        sys.exit(1)

    # Save full data as JSON
    with open(args.output, "w") as f:
        json.dump(transcript, f, indent=2)
    print(f"\nFull transcript data saved: {args.output}")

    # Save readable text version
    save_transcript_text(transcript, "transcript.txt")

    # Extract and save key visual moments
    sentences = transcript.get("sentences", [])
    if sentences:
        key_moments = extract_key_moments(sentences)
        with open("key_moments.json", "w") as f:
            json.dump(key_moments, f, indent=2)
        print(f"Key visual moments identified: {len(key_moments)}")
        print("Saved to: key_moments.json")

        print("\nTop key moments for frame extraction:")
        for m in key_moments[:10]:
            print(f"  [{m['time_display']}] {m['speaker']}: \"{m['text'][:80]}...\"")

    # Print video URL if available
    video_url = transcript.get("video_url")
    if video_url:
        print(f"\nVideo URL: {video_url}")
        print("You can download the video with:")
        print(f"  curl -o BIMIT-Plan-Orientation_2026-02-18.mp4 \"{video_url}\"")
        print("  # or: wget -O BIMIT-Plan-Orientation_2026-02-18.mp4 \"{video_url}\"")


if __name__ == "__main__":
    main()
