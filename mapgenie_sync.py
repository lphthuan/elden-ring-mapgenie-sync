"""
MapGenie Sync Engine
Matches Elden Ring parsed save data with MapGenie location markers and formats FMG JSON.
Supports:
1. Exact Event Flags (Sites of Grace, Bosses)
2. Strict Unique Item Matching (items appearing only once on the map)
3. Spatial Coordinate Mapping (Sacred Tears, Boss Drops, Grace Vicinity Pickups)
"""

import os
import json
import re
import math
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
            return {}, {}, {}, []

        locations = map_json.get('locations', [])

        boss_cats = {5699, 5710, 5711, 5697, 5700}
        all_item_cats = {
            5688, 5689, 5690, 5691, 5692, 5693, 5714, 5687,
            5676, 5672, 5673, 5674, 5725, 5726, 5677, 5727,
            6031, 6033, 6034, 6037, 6038, 6039,
            # Materials, consumables, tears, seeds
            5685, 6026, 5702, 6035, 6028, 6027, 6029, 5683, 5678, 5681
        }

        graces = {}   # norm_title -> list[loc]
        bosses = {}   # norm_title -> list[loc]
        items = {}    # norm_title -> list[loc]
        graces_list = []

        for loc in locations:
            cid = loc['category_id']
            t_norm = norm_title(loc['title'])
            if cid == 5658:
                graces.setdefault(t_norm, []).append(loc)
                graces_list.append(loc)
            elif cid in boss_cats:
                bosses.setdefault(t_norm, []).append(loc)
            elif cid in all_item_cats:
                items.setdefault(t_norm, []).append(loc)

        return graces, bosses, items, graces_list

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
                'strict_unique': True,       # Feature 1: Only mark items appearing once on this map
                'spatial_mapping': True,     # Feature 2: Spatial coordinate mapping for non-respawn pickups
                'include_storage': True
            }

        graces_idx, bosses_idx, items_idx, graces_list = self._index_map_locations(map_id)

        matched_location_ids = set()
        active_grace_titles = set()
        active_boss_titles = set()

        breakdown = {
            'graces': {'count': 0, 'samples': []},
            'bosses': {'count': 0, 'samples': []},
            'unique_items': {'count': 0, 'samples': []},
            'spatial_sacred_tears': {'count': 0, 'samples': []},
            'spatial_boss_drops': {'count': 0, 'samples': []},
            'spatial_grace_vicinity': {'count': 0, 'samples': []},
            'weapons': {'count': 0, 'samples': []},
            'armor': {'count': 0, 'samples': []},
            'talismans': {'count': 0, 'samples': []},
            'spells': {'count': 0, 'samples': []},
            'key_items': {'count': 0, 'samples': []},
            'ashes': {'count': 0, 'samples': []},
            'existing_merged': 0
        }

        is_flag_active = slot_data['is_flag_active']

        # 1. MATCH SITES OF GRACE (100% Event Flags via BST)
        if options.get('sync_graces', True):
            for g in self.graces_ref:
                if is_flag_active(g['flagId']):
                    name = g['name']
                    n_norm = norm_title(name)
                    locs = graces_idx.get(n_norm)
                    if not locs:
                        for alias in self.aliases.get('graces', {}).get(n_norm, []):
                            locs = graces_idx.get(alias)
                            if locs: break
                    if locs:
                        for l in locs:
                            matched_location_ids.add(l['id'])
                            active_grace_titles.add(n_norm)
                        breakdown['graces']['count'] += 1
                        if len(breakdown['graces']['samples']) < 8:
                            breakdown['graces']['samples'].append(name)

        # 2. MATCH BOSSES (100% Defeat Flags)
        if options.get('sync_bosses', True):
            for b in self.bosses_ref:
                if is_flag_active(b['defeatFlagId']):
                    name = b.get('name')
                    if not name: continue
                    n_norm = norm_title(name)
                    locs = bosses_idx.get(n_norm)
                    if not locs:
                        for alias in self.aliases.get('bosses', {}).get(n_norm, []):
                            locs = bosses_idx.get(alias)
                            if locs: break
                    if not locs:
                        calnum = clean_alnum(name)
                        for mg_t, mg_locs in bosses_idx.items():
                            if clean_alnum(mg_t) == calnum:
                                locs = mg_locs
                                break
                    if locs:
                        for l in locs:
                            matched_location_ids.add(l['id'])
                            active_boss_titles.add(n_norm)
                        breakdown['bosses']['count'] += 1
                        if len(breakdown['bosses']['samples']) < 8:
                            breakdown['bosses']['samples'].append(name)

        # 3. INVENTORY RESOLUTION & FEATURE 1: STRICT UNIQUE ITEM MATCHING
        common_pool = list(slot_data.get('common_items', []))
        key_pool = list(slot_data.get('key_items', []))
        if options.get('include_storage', True):
            common_pool.extend(slot_data.get('storage_common', []))
            key_pool.extend(slot_data.get('storage_key', []))

        # Build map of player items
        player_items = {} # norm_title -> {'cat': 'weapon'|'armor'|'talisman'|'spell'|'key'|'ash', 'raw_name': str}

        # Key items
        for item in key_pool:
            raw_id = item['id']
            clean_id = raw_id & 0x0FFFFFFF
            name = self.names['goods'].get(clean_id) or self.names['goods'].get(raw_id)
            if name:
                player_items[norm_title(name)] = {'cat': 'key', 'raw_name': name}

        # Common items
        for item in common_pool:
            raw_id = item['id']
            clean_id = raw_id & 0x0FFFFFFF
            w_base = clean_id - (clean_id % 100)

            w_name = self.names['weapons'].get(clean_id) or self.names['weapons'].get(w_base)
            a_name = self.names['armors'].get(clean_id)
            t_name = self.names['accessories'].get(clean_id)
            m_name = self.names['magic'].get(clean_id)
            g_name = self.names['goods'].get(clean_id)
            s_name = self.names['sword_arts'].get(clean_id)

            if w_name:
                player_items[norm_title(w_name)] = {'cat': 'weapon', 'raw_name': w_name}
            elif a_name:
                player_items[norm_title(a_name)] = {'cat': 'armor', 'raw_name': a_name}
            elif t_name:
                player_items[norm_title(t_name)] = {'cat': 'talisman', 'raw_name': t_name}
            elif m_name:
                player_items[norm_title(m_name)] = {'cat': 'spell', 'raw_name': m_name}
            elif s_name or g_name:
                player_items[norm_title(s_name or g_name)] = {'cat': 'ash', 'raw_name': s_name or g_name}

        # Match player items
        strict_unique = options.get('strict_unique', True)

        for n_norm, item_info in player_items.items():
            cat = item_info['cat']
            raw_name = item_info['raw_name']

            # Check category toggle
            if cat == 'weapon' and not options.get('sync_weapons', True): continue
            if cat == 'armor' and not options.get('sync_armor', True): continue
            if cat == 'talisman' and not options.get('sync_talismans', True): continue
            if cat == 'spell' and not options.get('sync_spells', True): continue
            if cat == 'key' and not options.get('sync_key_items', True): continue
            if cat == 'ash' and not options.get('sync_ashes', True): continue

            locs = items_idx.get(n_norm)
            if not locs:
                continue

            # In Strict Unique Mode: ONLY mark if item appears EXACTLY ONCE on this map!
            if strict_unique and len(locs) > 1:
                continue

            for l in locs:
                matched_location_ids.add(l['id'])

            if len(locs) == 1:
                breakdown['unique_items']['count'] += 1
                if len(breakdown['unique_items']['samples']) < 8:
                    breakdown['unique_items']['samples'].append(raw_name)

            # Also increment specific category
            cat_map = {
                'weapon': 'weapons', 'armor': 'armor', 'talisman': 'talismans',
                'spell': 'spells', 'key': 'key_items', 'ash': 'ashes'
            }
            target_key = cat_map.get(cat)
            if target_key:
                breakdown[target_key]['count'] += len(locs)
                if len(breakdown[target_key]['samples']) < 8:
                    breakdown[target_key]['samples'].append(raw_name)

        # 4. FEATURE 2 (CÁCH 2): SPATIAL COORDINATE MAPPING (Bản đồ hóa Event Flag theo Tọa độ Không Gian)
        if options.get('spatial_mapping', True) and graces_list:
            all_locs = self.maps_data.get(map_id, {}).get('locations', [])

            # A. Sacred Tears (Cat 5678): Proximity to activated Church Sites of Grace (< 0.003 deg, ~200m)
            tears = [l for l in all_locs if l.get('category_id') == 5678]
            for t in tears:
                if t['id'] in matched_location_ids: continue
                t_lat, t_lng = float(t['latitude']), float(t['longitude'])
                closest = min(graces_list, key=lambda g: (float(g['latitude']) - t_lat)**2 + (float(g['longitude']) - t_lng)**2)
                dist = math.sqrt((float(closest['latitude']) - t_lat)**2 + (float(closest['longitude']) - t_lng)**2)
                if dist < 0.003 and norm_title(closest['title']) in active_grace_titles:
                    matched_location_ids.add(t['id'])
                    breakdown['spatial_sacred_tears']['count'] += 1
                    if len(breakdown['spatial_sacred_tears']['samples']) < 6:
                        breakdown['spatial_sacred_tears']['samples'].append(f"{t['title']} ({closest['title']})")

            # B. Boss Drop Materials (Ancient Dragon Stones, Golden Seeds, Memory Stones)
            # Checked via Boss Defeat flags
            boss_reward_cats = {5685, 6026, 5683, 5725}
            for l in [l for l in all_locs if l.get('category_id') in boss_reward_cats]:
                if l['id'] in matched_location_ids: continue
                desc = norm_title(l.get('description', ''))
                for b_norm in active_boss_titles:
                    if b_norm in desc or any(w in desc for w in b_norm.split() if len(w) > 5):
                        matched_location_ids.add(l['id'])
                        breakdown['spatial_boss_drops']['count'] += 1
                        if len(breakdown['spatial_boss_drops']['samples']) < 6:
                            breakdown['spatial_boss_drops']['samples'].append(l['title'])
                        break

            # C. Grace Vicinity World Pickups: Lilies, Stones, Plants right next to an unlocked Grace (< 0.0012 deg, ~60m)
            material_cats = {5685, 6026, 5702, 6035, 6028, 6027, 6029, 5681}
            for l in [l for l in all_locs if l.get('category_id') in material_cats]:
                if l['id'] in matched_location_ids: continue
                t_norm = norm_title(l['title'])
                if t_norm in player_items:
                    l_lat, l_lng = float(l['latitude']), float(l['longitude'])
                    closest = min(graces_list, key=lambda g: (float(g['latitude']) - l_lat)**2 + (float(g['longitude']) - l_lng)**2)
                    dist = math.sqrt((float(closest['latitude']) - l_lat)**2 + (float(closest['longitude']) - l_lng)**2)
                    if dist < 0.0012 and norm_title(closest['title']) in active_grace_titles:
                        matched_location_ids.add(l['id'])
                        breakdown['spatial_grace_vicinity']['count'] += 1
                        if len(breakdown['spatial_grace_vicinity']['samples']) < 6:
                            breakdown['spatial_grace_vicinity']['samples'].append(l['title'])

        # 5. MERGE WITH EXISTING FMG EXPORT
        if existing_fmg_data:
            existing_locs = existing_fmg_data.get('data', {}).get('locationIds', [])
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
