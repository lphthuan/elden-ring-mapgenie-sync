import os
import sys
import argparse
import json

if sys.stdout:
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr:
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

curr_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, curr_dir)

from er_save_parser import EldenRingSave, find_default_save_path
from mapgenie_sync import MapGenieSyncEngine

def main():
    parser = argparse.ArgumentParser(description="Elden Ring Save to MapGenie (FMG) Sync Tool")
    parser.add_argument("--save", type=str, default=None, help="Đường dẫn file ER0000.sl2")
    parser.add_argument("--slot", type=int, default=0, help="Vị trí nhân vật (0 đến 9, mặc định 0)")
    parser.add_argument("--map", type=int, default=413, choices=[413, 638], help="Map ID: 413 (The Lands Between) hoặc 638 (Realm of Shadow)")
    parser.add_argument("--user", type=int, default=7764114, help="User ID MapGenie (mặc định 7764114)")
    parser.add_argument("--merge", type=str, default=None, help="File FMG JSON cũ để gộp dữ liệu")
    parser.add_argument("--merge-mode", type=str, choices=["additive", "override"], default="additive", help="Chế độ gộp: 'additive' (gộp bổ sung) hoặc 'override' (ghi đè 100% Grace & Boss)")
    parser.add_argument("--output", type=str, default=None, help="File JSON xuất ra")
    parser.add_argument("--no-materials", action="store_true", help="Vô hiệu hóa quét vật liệu (Materials: đá rèn, hoa hầm mộ, thảo mộc hiếm)")
    parser.add_argument("--no-consumables", action="store_true", help="Vô hiệu hóa quét vật phẩm dùng một lần (Consumables: Runes, Rune Arcs, Ammunition)")
    parser.add_argument("--no-strict-unique", action="store_true", help="Vô hiệu hóa Strict Unique Mode (quét cả vật phẩm rơi ở nhiều nơi)")
    parser.add_argument("--no-spatial", action="store_true", help="Vô hiệu hóa Spatial Mapping (không quét Sacred Tears theo Church Grace, Boss drop và Grace pickups)")
    parser.add_argument("--web", action="store_true", help="Chạy giao diện Web (mặc định nếu không truyền tham số)")
    parser.add_argument("--port", type=int, default=8088, help="Cổng Web server (mặc định 8088)")

    args = parser.parse_args()

    # If no CLI arguments provided, launch Web UI
    if len(sys.argv) == 1 or args.web:
        from web_app import run_server
        run_server(port=args.port, auto_open=True)
        return

    # CLI Mode
    save_path = args.save or find_default_save_path()
    if not save_path or not os.path.exists(save_path):
        print(f"Error: Không tìm thấy file save: {save_path}")
        sys.exit(1)

    print(f"Loading save: {save_path}")
    er = EldenRingSave(save_path)
    profiles = er.get_profiles()

    if args.slot < 0 or args.slot >= len(profiles) or not profiles[args.slot]['is_active']:
        print(f"Error: Slot {args.slot} không hợp lệ hoặc đang trống!")
        sys.exit(1)

    slot_info = profiles[args.slot]
    print(f"Selected: Slot {args.slot} ('{slot_info['name']}', Level {slot_info['level']}, Playtime: {slot_info['playtime_str']})")

    slot_data = er.parse_slot(args.slot)
    engine = MapGenieSyncEngine()

    existing_fmg = None
    if args.merge and os.path.exists(args.merge):
        print(f"Merging with: {args.merge}")
        with open(args.merge, 'r', encoding='utf-8') as f:
            existing_fmg = json.load(f)

    options = {
        'sync_graces': True,
        'sync_bosses': True,
        'sync_weapons': True,
        'sync_armor': True,
        'sync_talismans': True,
        'sync_spells': True,
        'sync_key_items': True,
        'sync_ashes': True,
        'sync_materials': not args.no_materials,
        'sync_consumables': not args.no_consumables,
        'strict_unique': not args.no_strict_unique,
        'spatial_mapping': not args.no_spatial,
        'merge_mode': args.merge_mode,
        'include_storage': True
    }

    res = engine.sync_slot(
        slot_data,
        map_id=args.map,
        user_id=args.user,
        options=options,
        existing_fmg_data=existing_fmg
    )

    print("\n" + "=" * 50)
    print(f"SYNC RESULT: {res['character_name']} (Lvl {res['level']})")
    print(f"Map: {res['map_name']} (ID {res['map_id']})")
    print(f"Total Locations Marked: {res['total_locations_found']}")
    print("-" * 50)
    for k, v in res['breakdown'].items():
        if isinstance(v, dict):
            print(f"  - {k.capitalize()}: {v['count']}")
        else:
            print(f"  - {k}: {v}")
    print("=" * 50)

    out_file = args.output
    if not out_file:
        out_file = f"fmg_game_111_map_{args.map}_user_{args.user}_sync.json"

    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(res['fmg_json'], f, indent=2)

    print(f"\n[OK] Xuất file thành công: {os.path.abspath(out_file)}")
    print("Hãy mở FMG Extension -> Data Manager -> Import file này vào MapGenie!")

if __name__ == '__main__':
    main()
