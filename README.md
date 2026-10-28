# Elden Ring to MapGenie (FMG) Sync Tool

A standalone, zero-dependency Python tool to parse PC Elden Ring save files (`ER0000.sl2`), automatically extract completed world progress (Sites of Grace, Bosses, Weapons, Armor, Talismans, Sorceries, Incantations, Dungeons, Imp Seals, etc.), and generate standard JSON files ready for direct import into the **Free Map Genie (FMG)** Chrome extension.

---

## 🌟 Key Features

- **Automatic Save Detection**: Auto-detects local Steam save files at `%APPDATA%/EldenRing/<SteamID>/ER0000.sl2` or supports custom file drop.
- **Full 10 Character Slots**: Select any active character with stats (name, level, playtime, deaths).
- **High-Accuracy Flag & Item Verification**:
  - **Sites of Grace**: Exact activation event flags (190+ locations in The Lands Between).
  - **Bosses & Invasions**: Overworld, night roaming, dungeon bosses, and NPC invaders tracked via defeat flags and dropped unique gear.
  - **Equipment & Magic**: Weapons, Armor sets, Talismans, Sorceries (55+), Incantations, Cookbooks, and Ashes of War.
  - **Materials & Consumables**: Optional toggle for finite materials (Smithing stones, rare lilies) and consumables.
  - **Spatial Coordinate Mapping**: Automatically links overworld dungeon entrances, Evergaols, and Imp Seal statues to their cleared interior graces and bosses.
- **Smart Merge & Override**:
  - **Additive Mode**: Preserves 100% of your previous manual exploration notes (landmarks, custom pins, herbs) while adding newly discovered save data.
  - **Override Mode**: Preserves manual exploration notes, but overrides unique items (Graces, Bosses) strictly based on your current save reality to eliminate false positives.
  - **Diff Log**: Displays a detailed comparison log of what the old file misidentified and what the save added.
- **Both Maps Supported**:
  - **The Lands Between** (Base Game - Map ID `413`)
  - **Realm of Shadow** (DLC Shadow of the Erdtree - Map ID `638`)

---

## 🚀 Quick Start

### Option 1: Web Interface (Recommended)
Run `Chay_Tool_Sync.bat` (or `python elden_ring_fmg_sync.py --web`).
Your browser will open `http://127.0.0.1:8088`.

1. Click **Load Detected Save** or drag-and-drop your `ER0000.sl2`.
2. Select your character slot and target map.
3. *(Optional)* Drag-and-drop an existing FMG JSON file to combine your manual notes with auto-scan.
4. Click **Start Sync & Generate FMG File** ➔ Download the generated JSON.

---

### Option 2: Command Line (CLI)
```bash
# Sync character slot 0 for The Lands Between:
python elden_ring_fmg_sync.py --slot 0 --map 413 --output fmg_sync.json

# Merge with existing FMG JSON export (Additive union):
python elden_ring_fmg_sync.py --slot 0 --map 413 --merge "old_fmg_file.json" --merge-mode additive --output fmg_merged.json

# Merge with strict override for 100% verified unique items (Graces & Bosses):
python elden_ring_fmg_sync.py --slot 0 --map 413 --merge "old_fmg_file.json" --merge-mode override --output fmg_override.json
```

---

## 📥 How to Import into MapGenie

1. Open Google Chrome with the **Free Map Genie (FMG)** extension installed.
2. Click the **FMG icon** on the toolbar ➔ Open **Data Manager**.
3. Switch to the **Import** tab.
4. Drag-and-drop the generated JSON file into the Import area and confirm.
5. Reload the [MapGenie Elden Ring Map](https://mapgenie.io/elden-ring/maps/the-lands-between) — all your completed locations will be marked automatically!

---

## 📜 License
MIT License.
