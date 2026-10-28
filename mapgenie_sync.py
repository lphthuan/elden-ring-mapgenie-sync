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
    s = re.sub(r'^\[.*?\]\s*', '', s)
    s = re.sub(r'\s+', ' ', s)
    return s

def clean_alnum(s: str) -> str:
    return re.sub(r'[^a-z0-9]', '', s.lower())

# MapGenie 1-time Event Flag Categories
GRACE_CATS = {5658}
BOSS_CATS = {5699, 5710, 5711, 5697, 5700}
WEAPON_CATS = {5688, 5690}
ARMOR_CATS = {5689}
TALISMAN_CATS = {5691}
SPELL_CATS = {5692, 5693}
KEY_ITEM_CATS = {5673, 5676, 5672, 5674, 5675, 5725, 5726, 6031, 6032, 6033, 6034, 6037, 6038, 6039, 5721, 5728, 11316, 11317}
ASH_CATS = {5714, 5687}
MATERIAL_CATS = {5722, 5723, 5685, 6026, 5702, 6035, 6027, 6028, 6029, 5703, 5709}
CONSUMABLE_CATS = {5681, 5712, 5724, 5682, 5680, 5677, 5678, 5679, 5683, 5684, 5707, 5727, 5686}
LOCATION_EVENT_CATS = {5667, 6040, 5665, 5664, 5660}

ALL_ITEM_CATS = (
    WEAPON_CATS | ARMOR_CATS | TALISMAN_CATS | SPELL_CATS |
    KEY_ITEM_CATS | ASH_CATS | MATERIAL_CATS | CONSUMABLE_CATS | LOCATION_EVENT_CATS
)

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
                            clean_name = re.sub(r'^\[.*?\]\s*', '', parts[1]).strip()
                            self.names[key][int(parts[0])] = clean_name

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

        graces = {}   # norm_title -> list[loc]
        bosses = {}   # norm_title -> list[loc]
        items = {}    # norm_title -> list[loc]
        graces_list = []

        for loc in locations:
            cid = loc['category_id']
            t_norm = norm_title(loc['title'])
            if cid in GRACE_CATS:
                graces.setdefault(t_norm, []).append(loc)
                graces_list.append(loc)
            elif cid in BOSS_CATS:
                bosses.setdefault(t_norm, []).append(loc)
            elif cid in ALL_ITEM_CATS:
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
                'sync_materials': True,      # New: Materials (Stones, Gloveworts, rare flora)
                'sync_consumables': True,    # New: Consumables (Runes, Rune Arcs, Ammunition)
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
            'weapons': {'count': 0, 'samples': []},
            'armor': {'count': 0, 'samples': []},
            'talismans': {'count': 0, 'samples': []},
            'spells': {'count': 0, 'samples': []},
            'key_items': {'count': 0, 'samples': []},
            'ashes': {'count': 0, 'samples': []},
            'materials': {'count': 0, 'samples': []},
            'consumables': {'count': 0, 'samples': []},
            'unique_items': {'count': 0, 'samples': []},
            'spatial_sacred_tears': {'count': 0, 'samples': []},
            'spatial_boss_drops': {'count': 0, 'samples': []},
            'spatial_grace_vicinity': {'count': 0, 'samples': []},
            'spatial_invasions': {'count': 0, 'samples': []},
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

        player_items = {} # norm_title -> raw_name

        # Pool all held and storage items across all item types
        all_pool = common_pool + key_pool
        for item in all_pool:
            raw_id = item['id']
            clean_id = raw_id & 0x0FFFFFFF
            w_base = clean_id - (clean_id % 100)

            for key in ('weapons', 'armors', 'accessories', 'magic', 'sword_arts', 'goods'):
                name = self.names[key].get(clean_id) or self.names[key].get(raw_id)
                if not name and key == 'weapons':
                    name = self.names['weapons'].get(w_base)
                if name:
                    player_items[norm_title(name)] = name

        # Match player items with MapGenie locations
        strict_unique = options.get('strict_unique', True)

        for n_norm, locs in items_idx.items():
            raw_name = player_items.get(n_norm)
            if not raw_name:
                n_alnum = clean_alnum(n_norm)
                for p_norm, p_raw in player_items.items():
                    if clean_alnum(p_norm) == n_alnum:
                        raw_name = p_raw
                        break
            if not raw_name:
                continue

            # In Strict Unique Mode: ONLY mark if item appears EXACTLY ONCE on this map!
            if strict_unique and len(locs) > 1:
                continue

            for l in locs:
                cid = l['category_id']
                cat_key = None
                opt_key = None

                if cid in WEAPON_CATS:
                    cat_key, opt_key = 'weapons', 'sync_weapons'
                elif cid in ARMOR_CATS:
                    cat_key, opt_key = 'armor', 'sync_armor'
                elif cid in TALISMAN_CATS:
                    cat_key, opt_key = 'talismans', 'sync_talismans'
                elif cid in SPELL_CATS:
                    cat_key, opt_key = 'spells', 'sync_spells'
                elif cid in KEY_ITEM_CATS:
                    cat_key, opt_key = 'key_items', 'sync_key_items'
                elif cid in ASH_CATS:
                    cat_key, opt_key = 'ashes', 'sync_ashes'
                elif cid in MATERIAL_CATS:
                    cat_key, opt_key = 'materials', 'sync_materials'
                elif cid in CONSUMABLE_CATS:
                    cat_key, opt_key = 'consumables', 'sync_consumables'

                if not cat_key or not options.get(opt_key, True):
                    continue

                matched_location_ids.add(l['id'])
                breakdown[cat_key]['count'] += 1
                if len(breakdown[cat_key]['samples']) < 8:
                    breakdown[cat_key]['samples'].append(raw_name)

                if len(locs) == 1:
                    breakdown['unique_items']['count'] += 1
                    if len(breakdown['unique_items']['samples']) < 8:
                        breakdown['unique_items']['samples'].append(raw_name)

        # 4. FEATURE 2 (CÁCH 2): SPATIAL COORDINATE MAPPING (Bản đồ hóa Event Flag theo Tọa độ Không Gian)
        if options.get('spatial_mapping', True):
            all_locs = self.maps_data.get(map_id, {}).get('locations', [])

            # A. Sacred Tears (Cat 5678): Proximity to activated Church Sites of Grace (< 0.003 deg, ~200m)
            if options.get('sync_consumables', True) and graces_list:
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

            # B. Boss Drop Materials & Rewards (Ancient Dragon Stones, Seeds, Memory Stones)
            boss_reward_cats = {5685, 6026, 5683, 5725, 5722, 5723}
            for l in [l for l in all_locs if l.get('category_id') in boss_reward_cats]:
                if l['id'] in matched_location_ids: continue
                cid = l['category_id']
                if cid in MATERIAL_CATS and not options.get('sync_materials', True): continue
                if cid in CONSUMABLE_CATS and not options.get('sync_consumables', True): continue
                if cid in KEY_ITEM_CATS and not options.get('sync_key_items', True): continue

                desc = norm_title(l.get('description', ''))
                for b_norm in active_boss_titles:
                    if b_norm in desc or any(w in desc for w in b_norm.split() if len(w) > 5):
                        matched_location_ids.add(l['id'])
                        breakdown['spatial_boss_drops']['count'] += 1
                        if len(breakdown['spatial_boss_drops']['samples']) < 6:
                            breakdown['spatial_boss_drops']['samples'].append(l['title'])
                        break

            # C. Grace Vicinity World Pickups: Materials & Consumables (< 0.0012 deg, ~60m)
            if graces_list:
                vicinity_cats = set()
                if options.get('sync_materials', True):
                    vicinity_cats.update(MATERIAL_CATS)
                if options.get('sync_consumables', True):
                    vicinity_cats.update(CONSUMABLE_CATS)

                for l in [l for l in all_locs if l.get('category_id') in vicinity_cats]:
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

            # D. Spatial Invasions & Unique Enemy Drops: (< 0.0015 deg, ~70m)
            if options.get('sync_bosses', True):
                invader_cats = {5697, 5700}
                invaders = [l for l in all_locs if l.get('category_id') in invader_cats and l['id'] not in matched_location_ids]
                matched_items = [l for l in all_locs if l['id'] in matched_location_ids and l.get('category_id') in (WEAPON_CATS | TALISMAN_CATS | SPELL_CATS | ASH_CATS | KEY_ITEM_CATS)]
                for inv in invaders:
                    i_lat, i_lng = float(inv['latitude']), float(inv['longitude'])
                    for itm in matched_items:
                        dist = math.sqrt((float(itm['latitude']) - i_lat)**2 + (float(itm['longitude']) - i_lng)**2)
                        if dist < 0.0015:
                            matched_location_ids.add(inv['id'])
                            breakdown['spatial_invasions']['count'] += 1
                            breakdown['bosses']['count'] += 1
                            if len(breakdown['spatial_invasions']['samples']) < 6:
                                breakdown['spatial_invasions']['samples'].append(f"{inv['title']} (from {itm['title']})")
                            break

            # E. Dungeons with Unlocked Entrance Grace (< 0.002 deg, ~100m)
            active_grace_locs = [l for l in all_locs if l.get('category_id') == 5658 and norm_title(l['title']) in active_grace_titles]
            for d in [l for l in all_locs if l.get('category_id') == 5655 and l['id'] not in matched_location_ids]:
                d_lat, d_lng = float(d['latitude']), float(d['longitude'])
                for g in active_grace_locs:
                    dist = math.sqrt((float(g['latitude']) - d_lat)**2 + (float(g['longitude']) - d_lng)**2)
                    if dist < 0.002:
                        matched_location_ids.add(d['id'])
                        breakdown['graces']['count'] += 1
                        break

            # F. Evergaols with Defeated Boss (< 0.0012 deg, ~60m)
            if options.get('sync_bosses', True):
                active_boss_locs = [l for l in all_locs if l.get('category_id') in BOSS_CATS and norm_title(l['title']) in active_boss_titles]
                for eg in [l for l in all_locs if l.get('category_id') == 5660 and l['id'] not in matched_location_ids]:
                    e_lat, e_lng = float(eg['latitude']), float(eg['longitude'])
                    for b in active_boss_locs:
                        dist = math.sqrt((float(b['latitude']) - e_lat)**2 + (float(b['longitude']) - e_lng)**2)
                        if dist < 0.0012:
                            matched_location_ids.add(eg['id'])
                            breakdown['bosses']['count'] += 1
                            break

            # G. Imp Seal Statues Opened (proximity to cleared items/graces < 0.0008 deg, ~40m)
            locs_by_id = {l['id']: l for l in all_locs}
            matched_current = [locs_by_id[mid] for mid in matched_location_ids if mid in locs_by_id]
            for imp in [l for l in all_locs if l.get('category_id') == 5667 and l['id'] not in matched_location_ids]:
                i_lat, i_lng = float(imp['latitude']), float(imp['longitude'])
                for ml in matched_current:
                    dist = math.sqrt((float(ml['latitude']) - i_lat)**2 + (float(ml['longitude']) - i_lng)**2)
                    if dist < 0.0008:
                        matched_location_ids.add(imp['id'])
                        breakdown['key_items']['count'] += 1
                        break

            # H. Multi-occurrence Keys, Pots, Bottles & Equipment in Grace Vicinity (< 0.0015 deg, ~75m)
            multi_vicinity_cats = (WEAPON_CATS | KEY_ITEM_CATS | TALISMAN_CATS | ASH_CATS)
            for l in [l for l in all_locs if l.get('category_id') in multi_vicinity_cats and l['id'] not in matched_location_ids]:
                t_norm = norm_title(l['title'])
                if t_norm in player_items:
                    l_lat, l_lng = float(l['latitude']), float(l['longitude'])
                    for g in active_grace_locs:
                        dist = math.sqrt((float(g['latitude']) - l_lat)**2 + (float(g['longitude']) - l_lng)**2)
                        if dist < 0.0015:
                            matched_location_ids.add(l['id'])
                            breakdown['unique_items']['count'] += 1
                            break

            # I. Margit's Talisman Pouch (166509) if Margit is defeated
            if is_flag_active(10000850) and 166509 in locs_by_id:
                matched_location_ids.add(166509)
                breakdown['talismans']['count'] += 1

        # 5. SMART MERGE WITH EXISTING FMG EXPORT & DIFF LOG
        diff_log = None
        if existing_fmg_data:
            existing_locs = set(existing_fmg_data.get('data', {}).get('locationIds', []))
            merge_mode = options.get('merge_mode', 'additive') # 'additive' or 'override'
            all_locs_dict = {l['id']: l for l in self.maps_data.get(map_id, {}).get('locations', [])}
            verified_strict_cats = GRACE_CATS | BOSS_CATS

            # Detect false positives in old manual file:
            # Graces or Bosses marked in old manual file, but NOT active/defeated in this save!
            false_positives = []
            for lid in sorted(list(existing_locs)):
                l = all_locs_dict.get(lid)
                if l and l.get('category_id') in verified_strict_cats:
                    if lid not in matched_location_ids:
                        cat_label = 'Grace' if l.get('category_id') in GRACE_CATS else 'Boss'
                        false_positives.append({
                            'id': lid,
                            'title': l.get('title'),
                            'category': cat_label,
                            'reason': 'Chưa kích hoạt trong file save' if cat_label == 'Grace' else 'Chưa bị tiêu diệt trong file save'
                        })

            # Detect items newly added from save:
            newly_added_ids = matched_location_ids - existing_locs
            newly_added_samples = [all_locs_dict[lid]['title'] for lid in list(newly_added_ids)[:12] if lid in all_locs_dict]

            if merge_mode == 'override':
                # Overwrite verified strict categories (Graces & Bosses) with current save reality
                kept_existing = set()
                for lid in existing_locs:
                    l = all_locs_dict.get(lid)
                    if l and l.get('category_id') in verified_strict_cats:
                        if lid in matched_location_ids:
                            kept_existing.add(lid)
                    else:
                        kept_existing.add(lid)

                matched_location_ids.update(kept_existing)
                breakdown['existing_merged'] = {
                    'count': len(kept_existing),
                    'samples': [f"Giữ {len(kept_existing)} điểm từ file cũ (chế độ ghi đè {merge_mode})"]
                }
            else:
                # Additive: preserve all old manual markings + add all newly detected save locations
                matched_location_ids.update(existing_locs)
                breakdown['existing_merged'] = {
                    'count': len(existing_locs),
                    'samples': [f"Gộp {len(existing_locs)} điểm từ file cũ (chế độ gộp bổ sung)"]
                }

            diff_log = {
                'mode': merge_mode,
                'old_count': len(existing_locs),
                'overridden_count': len(false_positives),
                'overridden_items': false_positives,
                'added_count': len(newly_added_ids),
                'added_samples': newly_added_samples
            }

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
            'diff_log': diff_log,
            'fmg_json': fmg_payload
        }
