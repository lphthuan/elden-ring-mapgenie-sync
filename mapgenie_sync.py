"""
MapGenie Sync Engine
Matches Elden Ring parsed save data with MapGenie location markers and formats FMG JSON.
"""

import os
import json
import re
from typing import Any

def norm_title(s: str) -> str:
    if not s:
        return ''
    s = s.lower().strip()
    s = s.replace("’", "'").replace("`", "'")
    s = re.sub(r'^(ash of war:\s*)', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def clean_alnum(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', s.lower())

class MapGenieSyncEngine:
    def __init__(self, data_dir: str | None = None):
        if not data_dir:
            curr = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(curr, 'data')
        self.data_dir = data_dir

        self.maps_data = {}
        self.names = {}
        self.aliases = {'graces': {}, 'bosses': {}}
        self.graces_ref = []
        self.bosses_ref = []

        self._load_all_data()

    def _load_all_data(self):
        # 1. MapGenie map data
        for mid in (413, 638):
            p = os.path.join(self.data_dir, f'map_{mid}_data.json')
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    self.maps_data[mid] = json.load(f)

        # 2. Param names
        param_files = {
            'goods': 'EquipParamGoods.txt',
            'weapons': 'EquipParamWeapon.txt',
            'armors': 'EquipParamProtector.txt',
            'accessories': 'EquipParamAccessory.txt',
            'magic': 'Magic.txt',
            'sword_arts': 'SwordArtsParam.txt'
        }
        for key, fname in param_files.items():
            self.names[key] = {}
            p = os.path.join(self.data_dir, fname)
            if os.path.exists(p):
                with open(p, 'r', encoding='utf-8') as f:
                    for line in f:
                        parts = line.strip().split(' ', 1)
                        if len(parts) == 2 and parts[0].isdigit():
                            self.names[key][int(parts[0])] = parts[1]

        # 3. Reference graces & bosses
        g_path = os.path.join(self.data_dir, 'clean_graces.json')
        if os.path.exists(g_path):
            with open(g_path, 'r', encoding='utf-8') as f:
                self.graces_ref = json.load(f)

        b_path = os.path.join(self.data_dir, 'clean_bosses.json')
        if os.path.exists(b_path):
            with open(b_path, 'r', encoding='utf-8') as f:
                self.bosses_ref = json.load(f)

        # 4. Aliases
        a_path = os.path.join(self.data_dir, 'aliases.json')
        if os.path.exists(a_path):
            with open(a_path, 'r', encoding='utf-8') as f:
                self.aliases = json.load(f)

    def _index_map_locations(self, map_id: int):
        map_json = self.maps_data.get(map_id)
        if not map_json:
            return {}, {}, {}

        locations = map_json.get('locations', [])

        boss_cats = {5699, 5710, 5711, 5697, 5700}
        item_cats = {
            5688, 5689, 5690, 5691, 5692, 5693, 5714, 5687,
            5676, 5672, 5673, 5674, 5725, 5726, 5677, 5727,
            6031, 6033, 6034, 6037, 6038, 6039
        }

        graces = {}   # norm_title -> list[loc]
        bosses = {}   # norm_title -> list[loc]
        items = {}    # norm_title -> list[loc]

        for loc in locations:
            cid = loc['category_id']
            t_norm = norm_title(loc['title'])
            if cid == 5658:
                graces.setdefault(t_norm, []).append(loc)
            elif cid in boss_cats:
                bosses.setdefault(t_norm, []).append(loc)
            elif cid in item_cats:
                items.setdefault(t_norm, []).append(loc)

        return graces, bosses, items

    def sync_slot(
        self,
        slot_data: dict,
        map_id: int = 413,
        user_id: int = 7764114,
        options: dict[str, bool] | None = None,
        existing_fmg_data: dict | None = None
    ) -> dict[str, Any]:
        """
        Executes matching between parsed slot data and MapGenie map markers.
        Returns the FMG export payload and statistical breakdown.
        """
        if options is None:
            options = {
                'sync_graces': True,
                'sync_bosses': True,
                'sync_weapons': True,
                'sync_armor': True,
                'sync_talismans': True,
                'sync_spells': True,
                'sync_key_items': True,
                'sync_ashes': True,
                'include_storage': True
            }

        graces_idx, bosses_idx, items_idx = self._index_map_locations(map_id)

        matched_location_ids = set()
        breakdown = {
            'graces': {'count': 0, 'samples': []},
            'bosses': {'count': 0, 'samples': []},
            'weapons': {'count': 0, 'samples': []},
            'armor': {'count': 0, 'samples': []},
            'talismans': {'count': 0, 'samples': []},
            'spells': {'count': 0, 'samples': []},
            'key_items': {'count': 0, 'samples': []},
            'ashes': {'count': 0, 'samples': []},
            'existing_merged': 0
        }

        is_flag_active = slot_data['is_flag_active']

        # 1. MATCH SITES OF GRACE
        if options.get('sync_graces', True):
            for g in self.graces_ref:
                if is_flag_active(g['flagId']):
                    name = g['name']
                    n_norm = norm_title(name)
                    # Check exact norm
                    locs = graces_idx.get(n_norm)
                    if not locs:
                        # Check aliases
                        for alias in self.aliases.get('graces', {}).get(n_norm, []):
                            locs = graces_idx.get(alias)
                            if locs:
                                break
                    if locs:
                        for l in locs:
                            matched_location_ids.add(l['id'])
                        breakdown['graces']['count'] += 1
                        if len(breakdown['graces']['samples']) < 8:
                            breakdown['graces']['samples'].append(name)

        # 2. MATCH BOSSES
        if options.get('sync_bosses', True):
            for b in self.bosses_ref:
                if is_flag_active(b['defeatFlagId']):
                    name = b.get('name')
                    if not name:
                        continue
                    n_norm = norm_title(name)
                    locs = bosses_idx.get(n_norm)
                    if not locs:
                        # Check aliases
                        for alias in self.aliases.get('bosses', {}).get(n_norm, []):
                            locs = bosses_idx.get(alias)
                            if locs:
                                break
                    if not locs:
                        # Alphanumeric fallback match
                        calnum = clean_alnum(name)
                        for mg_t, mg_locs in bosses_idx.items():
                            if clean_alnum(mg_t) == calnum:
                                locs = mg_locs
                                break
                    if locs:
                        for l in locs:
                            matched_location_ids.add(l['id'])
                        breakdown['bosses']['count'] += 1
                        if len(breakdown['bosses']['samples']) < 8:
                            breakdown['bosses']['samples'].append(name)

        # 3. MATCH INVENTORIES
        # Combine held items and optionally storage box
        common_pool = list(slot_data.get('common_items', []))
        key_pool = list(slot_data.get('key_items', []))
        if options.get('include_storage', True):
            common_pool.extend(slot_data.get('storage_common', []))
            key_pool.extend(slot_data.get('storage_key', []))

        # Key items
        if options.get('sync_key_items', True):
            for item in key_pool:
                raw_id = item['id']
                clean_id = raw_id & 0x0FFFFFFF
                name = self.names['goods'].get(clean_id) or self.names['goods'].get(raw_id)
                if name:
                    n_norm = norm_title(name)
                    locs = items_idx.get(n_norm)
                    if locs:
                        for l in locs:
                            matched_location_ids.add(l['id'])
                        breakdown['key_items']['count'] += 1
                        if len(breakdown['key_items']['samples']) < 8:
                            breakdown['key_items']['samples'].append(name)

        # Common items (Weapons, Armors, Talismans, Spells, Ashes)
        for item in common_pool:
            raw_id = item['id']
            clean_id = raw_id & 0x0FFFFFFF
            w_base = clean_id - (clean_id % 100)

            # Determine item category
            w_name = self.names['weapons'].get(clean_id) or self.names['weapons'].get(w_base)
            a_name = self.names['armors'].get(clean_id)
            t_name = self.names['accessories'].get(clean_id)
            m_name = self.names['magic'].get(clean_id)
            g_name = self.names['goods'].get(clean_id)
            s_name = self.names['sword_arts'].get(clean_id)

            if w_name and options.get('sync_weapons', True):
                n_norm = norm_title(w_name)
                locs = items_idx.get(n_norm)
                if locs:
                    for l in locs:
                        matched_location_ids.add(l['id'])
                    breakdown['weapons']['count'] += 1
                    if len(breakdown['weapons']['samples']) < 8:
                        breakdown['weapons']['samples'].append(w_name)

            elif a_name and options.get('sync_armor', True):
                n_norm = norm_title(a_name)
                locs = items_idx.get(n_norm)
                if locs:
                    for l in locs:
                        matched_location_ids.add(l['id'])
                    breakdown['armor']['count'] += 1
                    if len(breakdown['armor']['samples']) < 8:
                        breakdown['armor']['samples'].append(a_name)

            elif t_name and options.get('sync_talismans', True):
                n_norm = norm_title(t_name)
                locs = items_idx.get(n_norm)
                if locs:
                    for l in locs:
                        matched_location_ids.add(l['id'])
                    breakdown['talismans']['count'] += 1
                    if len(breakdown['talismans']['samples']) < 8:
                        breakdown['talismans']['samples'].append(t_name)

            elif m_name and options.get('sync_spells', True):
                n_norm = norm_title(m_name)
                locs = items_idx.get(n_norm)
                if locs:
                    for l in locs:
                        matched_location_ids.add(l['id'])
                    breakdown['spells']['count'] += 1
                    if len(breakdown['spells']['samples']) < 8:
                        breakdown['spells']['samples'].append(m_name)

            elif (s_name or g_name) and options.get('sync_ashes', True):
                candidate = s_name or g_name
                n_norm = norm_title(candidate)
                locs = items_idx.get(n_norm)
                if locs:
                    for l in locs:
                        matched_location_ids.add(l['id'])
                    breakdown['ashes']['count'] += 1
                    if len(breakdown['ashes']['samples']) < 8:
                        breakdown['ashes']['samples'].append(candidate)

        # 4. MERGE WITH EXISTING FMG EXPORT
        if existing_fmg_data:
            existing_locs = existing_fmg_data.get('data', {}).get('locationIds', [])
            before_count = len(matched_location_ids)
            matched_location_ids.update(existing_locs)
            breakdown['existing_merged'] = len(existing_locs)

        # Build final FMG JSON payload
        sorted_locations = sorted(list(matched_location_ids))
        fmg_payload = {
            "version": 2,
            "gameId": 111,
            "mapId": map_id,
            "userId": user_id,
            "data": {
                "locationIds": sorted_locations,
                "categoryIds": existing_fmg_data.get('data', {}).get('categoryIds', []) if existing_fmg_data else [],
                "notes": existing_fmg_data.get('data', {}).get('notes', []) if existing_fmg_data else [],
                "presets": existing_fmg_data.get('data', {}).get('presets', []) if existing_fmg_data else [],
                "presetOrder": existing_fmg_data.get('data', {}).get('presetOrder', []) if existing_fmg_data else [],
                "visibleCategoriesIds": existing_fmg_data.get('data', {}).get('visibleCategoriesIds', []) if existing_fmg_data else []
            }
        }

        return {
            'character_name': slot_data.get('name'),
            'level': slot_data.get('level'),
            'map_id': map_id,
            'map_name': "The Lands Between" if map_id == 413 else "Realm of Shadow",
            'total_locations_found': len(sorted_locations),
            'breakdown': breakdown,
            'fmg_json': fmg_payload
        }
