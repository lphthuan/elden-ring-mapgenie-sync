"""
Elden Ring Save Parser (ER0000.sl2)
Extracts character slots, stats, inventory, and event flags.
"""

import os
import glob
import struct
import json

PC_MAGIC = b'BND4'
HEADER_SIZE = 0x2FC
SLOTS_START = 0x300
SLOT_SIZE = 0x280010
SLOT_CHECKSUM = 0x10
SLOT_COUNT = 10
USER_DATA_10_START = SLOTS_START + SLOT_SIZE * SLOT_COUNT # 0x19003A0
EVENT_FLAGS_LEN = 0x1BF99F

class BinaryReader:
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def seek(self, pos: int):
        self.pos = pos

    def skip(self, n: int):
        self.pos += n

    def u8(self) -> int:
        v = self.data[self.pos]
        self.pos += 1
        return v

    def u32(self) -> int:
        v = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return v

    def u64(self) -> int:
        v = struct.unpack_from('<Q', self.data, self.pos)[0]
        self.pos += 8
        return v

    def bytes(self, n: int) -> bytes:
        b = self.data[self.pos:self.pos + n]
        self.pos += n
        return b


def find_default_save_path() -> str | None:
    """Finds Steam Elden Ring save file automatically on Windows."""
    appdata = os.environ.get('APPDATA', '')
    if not appdata:
        return None
    er_dir = os.path.join(appdata, 'EldenRing')
    if not os.path.exists(er_dir):
        return None
    saves = glob.glob(os.path.join(er_dir, '**', 'ER0000.sl2'), recursive=True)
    if saves:
        # Return most recently modified save file
        saves.sort(key=lambda s: os.path.getmtime(s), reverse=True)
        return saves[0]
    return None


class EldenRingSave:
    def __init__(self, file_path_or_bytes: str | bytes, bst_path: str | None = None):
        if isinstance(file_path_or_bytes, str):
            self.file_path = file_path_or_bytes
            with open(file_path_or_bytes, 'rb') as f:
                self.buf = f.read()
        else:
            self.file_path = "memory"
            self.buf = file_path_or_bytes

        if len(self.buf) < USER_DATA_10_START + 0x100:
            raise ValueError(f"Save file too small: {len(self.buf)} bytes")

        if self.buf[:4] != PC_MAGIC:
            raise ValueError("Invalid Elden Ring save file magic (expected 'BND4')")

        self.bst = self._load_bst(bst_path)

    def _load_bst(self, bst_path: str | None) -> dict[int, int]:
        bst = {}
        if not bst_path:
            # Look in standard locations relative to this script
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = [
                os.path.join(curr_dir, 'data', 'eventflag-bst.txt'),
                os.path.join(curr_dir, 'eventflag-bst.txt'),
                os.path.join(curr_dir, '..', 'DataTemp', 'eventflag-bst.txt')
            ]
            for c in candidates:
                if os.path.exists(c):
                    bst_path = c
                    break

        if bst_path and os.path.exists(bst_path):
            with open(bst_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ',' in line:
                        k, v = line.split(',')
                        bst[int(k)] = int(v)
        return bst

    def get_profiles(self) -> list[dict]:
        """Reads UserData10 to list all 10 slots and their summary."""
        r = BinaryReader(self.buf)
        ud10_pos = USER_DATA_10_START + SLOT_CHECKSUM
        r.seek(ud10_pos)

        # UserData10 header
        r.u32() # version
        r.u64() # steam_id
        r.skip(0x140) # settings

        # MenuSystemSaveLoad
        r.skip(4)
        menu_size = r.u32()
        r.skip(menu_size)

        active_slots_mask = [r.u8() != 0 for _ in range(10)]

        # Seconds played
        seconds_played = []
        PROFILE_LEN = 0x24C
        PROFILE_SECONDS_OFFSET = 0x26
        for i in range(10):
            start = r.pos
            r.seek(start + PROFILE_SECONDS_OFFSET)
            seconds_played.append(r.u32())
            r.seek(start + PROFILE_LEN)

        profiles = []
        for i in range(10):
            is_active = active_slots_mask[i]
            if not is_active:
                profiles.append({
                    'slot_index': i,
                    'is_active': False,
                    'name': f"Slot {i+1} (Trống)",
                    'level': 0,
                    'seconds_played': 0,
                    'playtime_str': '0h 0m',
                    'deaths': 0
                })
                continue

            # Read slot info
            name, level, deaths = self._read_slot_summary(i)
            sec = seconds_played[i] if i < len(seconds_played) else 0
            hours = sec // 3600
            mins = (sec % 3600) // 60

            profiles.append({
                'slot_index': i,
                'is_active': True,
                'name': name or f"Slot {i+1}",
                'level': level,
                'seconds_played': sec,
                'playtime_str': f"{hours}h {mins}m",
                'deaths': deaths
            })
        return profiles

    def _read_slot_summary(self, slot_idx: int) -> tuple[str, int, int]:
        try:
            r = BinaryReader(self.buf)
            slot_offset = SLOTS_START + SLOT_SIZE * slot_idx + SLOT_CHECKSUM
            r.seek(slot_offset)
            version = r.u32()
            r.skip(4 + 8 + 0x10)

            gaitem_count = 0x13fe if version <= 81 else 0x1400
            for _ in range(gaitem_count):
                handle = r.u32()
                r.u32()
                if handle != 0:
                    masked = (handle & 0xf0000000)
                    if masked != 0xc0000000:
                        r.skip(8)
                    if masked == 0x80000000:
                        r.skip(5)

            pgd_start = r.pos
            r.seek(pgd_start + 0x60)
            level = r.u32()
            r.seek(pgd_start + 0x94)
            name = r.bytes(32).decode('utf-16le', errors='ignore').split('\0')[0]

            # Deaths
            r.seek(pgd_start + 0x1B0)
            r.skip(13 * 16 + 0x58 + 0x1C + 0x58 + 88)
            r.skip(4 + 0xA80 * 12 + 4 + 0x180 * 12 + 8)
            r.skip(14 * 8 + 4 + 10 * 8 + 4 + 6 * 8 + 8 + 24)
            proj_count = r.u32()
            r.skip(proj_count * 8 + 0x9C + 12 + 0x12F)
            r.skip(4 + 0x780 * 12 + 4 + 0x80 * 12 + 8 + 256)
            reg_count = r.u32()
            r.skip(reg_count * 4 + 0x28 + 1 + 0x44 + 8 + 4)
            menu_prof_size = r.u32()
            r.skip(menu_prof_size + 0x34 + 8 + 7000 * 16 + 4)
            tut_size = r.u32()
            tut_count = r.u32()
            if tut_count != 0:
                r.skip(tut_size - 4)
            r.skip(3)
            deaths = r.u32()
            return name, level, deaths
        except Exception:
            return f"Slot {slot_idx+1}", 0, 0

    def parse_slot(self, slot_idx: int) -> dict:
        """Fully parses a character slot (stats, inventories, event flags)."""
        r = BinaryReader(self.buf)
        slot_offset = SLOTS_START + SLOT_SIZE * slot_idx + SLOT_CHECKSUM
        r.seek(slot_offset)

        version = r.u32()
        r.skip(4 + 8 + 0x10)

        # GaItem mapping
        gaitem_map = {}
        gaitem_count = 0x13fe if version <= 81 else 0x1400
        for _ in range(gaitem_count):
            handle = r.u32()
            item_id = r.u32()
            if handle != 0:
                gaitem_map[handle] = item_id
                masked = (handle & 0xf0000000)
                if masked != 0xc0000000:
                    r.skip(8)
                if masked == 0x80000000:
                    r.skip(5)

        pgd_start = r.pos
        # PlayerGameData
        r.seek(pgd_start + 0x60)
        level = r.u32()
        runes = r.u32()
        r.seek(pgd_start + 0x94)
        name = r.bytes(32).decode('utf-16le', errors='ignore').split('\0')[0]

        r.seek(pgd_start + 0x1B0)
        r.skip(13 * 16 + 0x58 + 0x1C + 0x58 + 88)

        # Common Held Inventory
        common_count = r.u32()
        common_items = []
        for i in range(0xA80):
            handle = r.u32()
            qty = r.u32()
            acq_idx = r.u32()
            if i < common_count and handle != 0:
                raw_id = gaitem_map.get(handle, handle)
                common_items.append({'handle': handle, 'id': raw_id, 'qty': qty})

        # Key Held Inventory
        key_count = r.u32()
        key_items = []
        for i in range(0x180):
            handle = r.u32()
            qty = r.u32()
            acq_idx = r.u32()
            if i < key_count and handle != 0:
                raw_id = gaitem_map.get(handle, handle)
                key_items.append({'handle': handle, 'id': raw_id, 'qty': qty})

        # Skip to Storage box
        r.skip(8 + 14 * 8 + 4 + 10 * 8 + 4 + 6 * 8 + 8 + 24)
        proj_count = r.u32()
        r.skip(proj_count * 8 + 0x9C + 12 + 0x12F)

        # Storage Common
        storage_common_count = r.u32()
        storage_common = []
        for i in range(0x780):
            handle = r.u32()
            qty = r.u32()
            acq_idx = r.u32()
            if i < storage_common_count and handle != 0:
                raw_id = gaitem_map.get(handle, handle)
                storage_common.append({'handle': handle, 'id': raw_id, 'qty': qty})

        # Storage Key
        storage_key_count = r.u32()
        storage_key = []
        for i in range(0x80):
            handle = r.u32()
            qty = r.u32()
            acq_idx = r.u32()
            if i < storage_key_count and handle != 0:
                raw_id = gaitem_map.get(handle, handle)
                storage_key.append({'handle': handle, 'id': raw_id, 'qty': qty})

        # Skip to Event Flags
        r.skip(8 + 256)
        reg_count = r.u32()
        r.skip(reg_count * 4 + 0x28 + 1 + 0x44 + 8 + 4)
        menu_prof_size = r.u32()
        r.skip(menu_prof_size + 0x34 + 8 + 7000 * 16 + 4)
        tut_size = r.u32()
        tut_count = r.u32()
        if tut_count != 0:
            r.skip(tut_size - 4)
        r.skip(3)
        deaths = r.u32()
        r.skip(4 + 1 + 4)
        last_rested_grace = r.u32()
        r.skip(1 + 4 + 4)

        raw_flags = r.bytes(EVENT_FLAGS_LEN)

        def is_flag_active(flag_id: int) -> bool:
            block = flag_id // 1000
            if block not in self.bst:
                return False
            mult = self.bst[block]
            index = flag_id % 1000
            byte_offset = mult * 125 + (index // 8)
            bit_pos = 7 - (index % 8)
            if byte_offset >= len(raw_flags):
                return False
            return (raw_flags[byte_offset] & (1 << bit_pos)) != 0

        return {
            'slot_index': slot_idx,
            'name': name,
            'level': level,
            'runes': runes,
            'deaths': deaths,
            'last_rested_grace': last_rested_grace,
            'common_items': common_items,
            'key_items': key_items,
            'storage_common': storage_common,
            'storage_key': storage_key,
            'is_flag_active': is_flag_active
        }
