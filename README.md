# BIMIT Plan Generation — How-To Guide Generator

Converts the BIMIT Plan Orientation meeting recording + transcript into a structured how-to guide with embedded screenshots.

## Output

**`how_to_bimit_plan_generation.md`** — The generated how-to guide (28 screenshot slots, full structured content).

## Quick Start — Fill In Screenshots

### Step 1: Get your Fireflies API key

1. Go to [app.fireflies.ai/integrations/custom/fireflies](https://app.fireflies.ai/integrations/custom/fireflies)
2. Copy your API key

### Step 2: Fetch the transcript and video URL

```bash
export FIREFLIES_API_KEY=your_api_key_here
python3 fetch_transcript.py
```

This outputs:
- `transcript_data.json` — Full transcript with timestamps
- `transcript.txt` — Human-readable transcript
- `key_moments.json` — Detected visual cue timestamps
- Prints the video URL for download

### Step 3: Download the video

```bash
# Replace URL with the one printed by fetch_transcript.py
curl -o BIMIT-Plan-Orientation_2026-02-18.mp4 "https://fireflies-video-url..."
```

Or place a locally downloaded copy named `BIMIT-Plan-Orientation_2026-02-18.mp4` in this directory.

### Step 4: Extract frames

```bash
python3 extract_frames.py --video BIMIT-Plan-Orientation_2026-02-18.mp4 --output images/
```

Extracts 28 frames at key teaching moments. Saves PNGs to `images/`.

### Step 5: Regenerate the document with screenshots

```bash
python3 generate_howto.py
```

The document now has inline screenshots instead of placeholder text.

---

## File Reference

| File | Purpose |
|------|---------|
| `how_to_bimit_plan_generation.md` | **Main output** — the how-to guide |
| `fetch_transcript.py` | Fetches transcript + video URL from Fireflies API |
| `extract_frames.py` | Extracts PNG frames from video at key timestamps |
| `generate_howto.py` | Generates the markdown document from frames |
| `images/` | Extracted frames (created by `extract_frames.py`) |

## Adding the Style Reference

When `how_to_manage_scanit.md` is available, place it in this directory and re-run `generate_howto.py`. The generator will align section structure and formatting to match.

## Screenshot Timestamp Reference

| Frame | Timestamp | Section |
|-------|-----------|---------|
| `01_architecture_overview` | 04:00 | Architecture |
| `02_data_flow_modules` | 05:00 | Architecture |
| `03_api_call_sequence` | 06:00 | Architecture |
| `04_module_relationship` | 07:00 | Architecture |
| `05_architecture_summary` | 07:30 | Architecture |
| `06_codebase_file_nav` | 08:00 | Code Structure |
| `07_route_area_plan_create` | 08:30 | Code Structure |
| `08_module_organization` | 09:00 | Code Structure |
| `09_code_entry_point` | 09:30 | Code Structure |
| `10_airtable_project_runs` | 17:00 | Airtable |
| `11_airtable_asset_storage` | 17:30 | Airtable |
| `12_airtable_status_tracking` | 18:00 | Airtable |
| `13_airtable_linked_records` | 18:30 | Airtable |
| `14_terminal_npm_run_test` | 27:00 | Dev Setup |
| `15_terminal_npm_run_dev` | 28:00 | Dev Setup |
| `16_terminal_powershell_vs_gitbash` | 29:00 | Dev Setup |
| `17_vscode_settings` | 30:00 | Dev Setup |
| `18_terminal_server_start` | 31:00 | Dev Setup |
| `19_postman_local_endpoint` | 32:00 | Postman |
| `20_postman_request_body` | 33:00 | Postman |
| `21_postman_successful_response` | 34:00 | Postman |
| `22_postman_error_debugging` | 35:00 | Postman |
| `23_env_file_setup` | 36:00 | Environment |
| `24_env_sample_vs_example` | 36:30 | Environment |
| `25_env_aws_keys` | 37:00 | Environment |
| `26_module5_structure` | 50:00 | Module 5 Ref |
| `27_module5_documentation` | 50:30 | Module 5 Ref |
| `28_module5_modular_arch` | 51:00 | Module 5 Ref |
