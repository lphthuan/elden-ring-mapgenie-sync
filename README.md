# Elden Ring ➔ MapGenie Sync Tool ⚔️

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078d7.svg)](https://microsoft.com/windows)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Release](https://img.shields.io/badge/Release-v1.1.0-gold.svg)](https://github.com/lphthuan/elden-ring-mapgenie-sync/releases/latest)

> **Công cụ tự động đọc file save game *Elden Ring* PC (`ER0000.sl2`) và xuất file JSON đồng bộ trực tiếp lên bản đồ tương tác MapGenie (thông qua extension Free Map Genie - FMG).**

Không còn phải ngồi tích tay hàng trăm Điểm ân điển (Grace), Boss, Vũ khí, Bùa hộ mệnh hay Sách nấu ăn trên bản đồ! Chỉ với **1 cú nhấp chuột**, toàn bộ hành trình của nhân vật sẽ được đánh dấu đầy đủ lên bản đồ MapGenie.

---

## ✨ TÍNH NĂNG NỔI BẬT

* ⚡ **Không cần cài đặt phức tạp (Zero-Dependency)**: Chạy hoàn toàn bằng Python có sẵn trên máy, không cần chạy `pip install` bất kỳ thư viện ngoài nào.
* 🔍 **Tự động nhận diện Save Steam**: Tự động phát hiện vị trí file save `%APPDATA%\EldenRing\<SteamID>\ER0000.sl2` của bạn mà không cần đi tìm thủ công. Hỗ trợ cả kéo thả (Drag & Drop) file save tùy ý.
* 👤 **Hỗ trợ đầy đủ 10 Slot nhân vật**: Hiển thị chi tiết Tên, Cấp độ (Level), Thời gian chơi (Playtime) và Số lần tử trận (Deaths).
* 🎯 **Độ chính xác cực cao (99%+)**:
  * 🌟 **Điểm Ân Điển (Sites of Grace)**: Nhận diện chính xác 100% các grace đã kích hoạt thông qua Event Flags.
  * ⚔️ **Trùm & Kẻ địch lớn (Bosses)**: Tự động đối soát cờ tiêu diệt (defeat flags) của hơn 200 boss lớn nhỏ.
  * 🗡️ **Vũ khí & Khiên (Weapons & Shields)**: Tra cứu toàn bộ bảng ID vật phẩm trong túi và trang bị.
  * 🛡️ **Áo giáp & Nón (Armor Sets)**: Tự động đánh dấu vị trí các bộ giáp đã nhặt.
  * 💍 **Bùa Hộ Mệnh (Talismans)**: Quét toàn bộ bùa hộ mệnh đang sở hữu.
  * ✨ **Phép thuật & Lời nguyện (Sorceries & Incantations)**.
  * 📜 **Vật phẩm chính, Sách nấu ăn & Bản đồ (Key Items, Cookbooks, Maps)**.
  * 🌪️ **Tro tàn chiến tranh & Tro gọi hồn (Ashes of War & Spirit Ashes)**.
  * 📦 **Quét cả Hòm Đồ (Storage Box)**: Quét cả những món đồ bạn đang cất trong rương tại Grace.
* 🎯 **Tính năng Nhận diện Nâng cao (Smart Detection Engine)**:
  * 🎯 **Chế độ Quét Vật Phẩm Độc Nhất (Strict Unique Mode - 100% Chính xác)**: Nhận diện vật phẩm chỉ xuất hiện đúng 1 lần duy nhất trên bản đồ (1,346 vật phẩm tại The Lands Between, 434 vật phẩm tại DLC). Ngăn ngừa hoàn toàn việc tích nhầm các vật phẩm rải rác ở nhiều tọa độ khác nhau (hoa Lily, đá Smithing rơi phổ thông, thức ăn).
  * 🌐 **Ánh xạ Không gian & Vùng Lân Cận (Spatial Proximity Mapping - Cách 2)**:
    * 🍷 **Bình Giọt Lệ (Sacred Tears)**: Tự động đánh dấu tại các Nhà Thờ khi Điểm Ân Điển bên trong đã được kích hoạt (khoảng cách < 200m).
    * 🏆 **Vật phẩm Thưởng Sau Khi Hạ Boss**: Tự động đánh dấu Đá Cổ Đại, Hạt Giống Vàng, Bùa Nhớ khi Boss tương ứng bị tiêu diệt.
    * ✨ **Vệt Sáng Quanh Grace**: Tự động đánh dấu các tài nguyên nhặt ngay sát Điểm Ân Điển đã kích hoạt (< 60m) khi người chơi sở hữu vật phẩm trong túi đồ.
* 🗺️ **Hỗ trợ cả 2 Bản đồ**:
  * **The Lands Between** (Bản đồ game gốc - Map ID `413` - 5,700+ địa điểm).
  * **Realm of Shadow** (DLC Shadow of the Erdtree - Map ID `638` - 1,800+ địa điểm).
* 🔄 **Chế độ Gộp (Merge)**: Cho phép kết hợp dữ liệu save mới với file xuất FMG cũ để không bao giờ bị mất các ghi chú hoặc đánh dấu thủ công trước đó.
* 🎨 **Giao diện Web Dark-Fantasy**: Giao diện mang đậm chất Elden Ring (vàng kim, đá phiến, hiệu ứng ánh sáng Grace), responsive và mượt mà trên Chrome/Edge/Brave.

---

## 🚀 HƯỚNG DẪN SỬ DỤNG NHANH (3 BƯỚC)

### Bước 1: Khởi động công cụ
* Tải bản phát hành mới nhất tại mục [Releases](https://github.com/lphthuan/elden-ring-mapgenie-sync/releases/latest) và giải nén.
* Nhấp đúp vào file **`Chay_Tool_Sync.bat`** (hoặc `run.bat`).
* Trình duyệt web sẽ tự động mở giao diện tại địa chỉ: `http://127.0.0.1:8088`.

### Bước 2: Quét file Save
1. Nhấp nút **"Nạp File Này"** (công cụ tự phát hiện save Steam của bạn) hoặc kéo thả file `ER0000.sl2` vào khung.
2. Nhấp chuột để chọn **Nhân vật** bạn muốn đồng bộ (ví dụ: *Slot 1: Thune - Level 99*).
3. Chọn bản đồ cần quét:
   * **The Lands Between** (Game gốc)
   * **Realm of Shadow** (DLC)
4. Tích chọn các mục vật phẩm muốn đánh dấu (Grace, Boss, Vũ khí, Bùa, v.v.).
5. Nhấn **"⚡ Bắt Đầu Quét & Tạo File FMG"** ➔ Nhấn **"📥 Tải File JSON Cho FMG"** để lưu file import về máy tính.

### Bước 3: Nhập (Import) vào Extension Free Map Genie
1. Mở Chrome (hoặc Edge/Brave) đã cài tiện ích **Free Map Genie (FMG)**.
2. Bấm vào icon FMG trên thanh công cụ tiện ích ➔ Chọn **Data Manager**.
3. Chuyển sang thẻ **Import**.
4. Kéo thả file JSON vừa tải về ở Bước 2 vào khung Import ➔ Nhấn xác nhận.
5. Mở lại bản đồ [MapGenie The Lands Between](https://mapgenie.io/elden-ring/maps/the-lands-between) và nhấn **F5** để tải lại trang.
6. 🎉 **Toàn bộ vị trí vật phẩm đã nhặt và boss đã hạ sẽ tự động được đánh dấu hoàn thành trên bản đồ!**

---

## 💻 SỬ DỤNG DÒNG LỆNH (CLI)

Dành cho người dùng thích tự động hóa qua terminal:

```bash
# Quét tự động save Steam mặc định và xuất file cho bản đồ The Lands Between
python elden_ring_fmg_sync.py --slot 0 --map 413 --user 7764114 --output fmg_import.json

# Quét file save tùy chọn
python elden_ring_fmg_sync.py --save "C:\path\to\ER0000.sl2" --slot 0 --map 413

# Quét và gộp (merge) với file FMG JSON cũ
python elden_ring_fmg_sync.py --slot 0 --map 413 --merge "old_fmg_export.json" --output fmg_merged.json

# Quét cho bản đồ DLC Shadow of the Erdtree
python elden_ring_fmg_sync.py --slot 0 --map 638 --output fmg_dlc.json

# Khởi chạy giao diện Web server
python elden_ring_fmg_sync.py --web --port 8088
```

### Các tham số CLI:
| Tham số | Ý nghĩa | Mặc định |
| :--- | :--- | :--- |
| `--save` | Đường dẫn tới file `ER0000.sl2` | Tự động dò save Steam |
| `--slot` | Vị trí nhân vật (`0` đến `9`) | `0` (Slot đầu tiên) |
| `--map` | Map ID MapGenie: `413` (Gốc) hoặc `638` (DLC) | `413` |
| `--user` | MapGenie User ID | `7764114` |
| `--merge` | File JSON FMG cũ để gộp thêm | Không gộp |
| `--output` | Đường dẫn file JSON xuất ra | Tự động đặt tên theo Map & User |
| `--no-strict-unique` | Tắt Strict Unique Mode (quét cả item rơi nhiều nơi) | Mặc định bật (chỉ quét item độc nhất) |
| `--no-spatial` | Tắt Spatial Mapping (Tear nhà thờ, thưởng boss, vùng Grace) | Mặc định bật |
| `--web` | Chạy ở chế độ giao diện Web | Bật nếu không truyền cờ khác |
| `--port` | Cổng HTTP Server cho giao diện Web | `8088` |

---

## 📂 CẤU TRÚC THƯ MỤC

```text
elden-ring-mapgenie-sync/
├── data/                         # Cơ sở dữ liệu MapGenie & Bảng tra cứu Game Param
│   ├── clean_graces.json         # Danh mục 419 Sites of Grace & Event Flag IDs
│   ├── clean_bosses.json         # Danh mục 212 Bosses & Defeat Flag IDs
│   ├── eventflag-bst.txt         # Bảng cây nhị phân giải mã cờ Event Flags
│   ├── map_413_data.json         # Database đầy đủ MapGenie: The Lands Between
│   ├── map_638_data.json         # Database đầy đủ MapGenie: Realm of Shadow (DLC)
│   ├── EquipParam*.txt           # Bảng tra cứu tên vũ khí, giáp, bùa, phép thuật
│   └── aliases.json              # Từ điển chuẩn hóa tên gọi giữa game và MapGenie
├── web/
│   └── index.html                # Giao diện Web dark-fantasy
├── er_save_parser.py             # Parser nhị phân giải mã file save ER0000.sl2
├── mapgenie_sync.py              # Engine đối soát và sinh JSON chuẩn FMG v2
├── web_app.py                    # Máy chủ Web siêu nhẹ (chuẩn Python http.server)
├── elden_ring_fmg_sync.py        # File thực thi dòng lệnh & khởi chạy Web
├── Chay_Tool_Sync.bat            # Phím tắt nhấp đúp chạy nhanh trên Windows
├── run.bat                       # Phím tắt ngắn gọn
├── LICENSE                       # Giấy phép nguồn mở MIT
└── README.md                     # Tài liệu hướng dẫn sử dụng
```

---

## ⚙️ NGUYÊN LÝ HOẠT ĐỘNG (DÀNH CHO DEV)

1. **Cấu trúc File Save Elden Ring (`ER0000.sl2`)**:
   * File đóng gói dạng container BND4 (magic `BND4` tại `0x00`).
   * Chứa 10 Slot nhân vật (`0x300` + stride `0x280010` mỗi slot).
   * Vùng `UserData10` tại offset `0x19003A0` lưu trữ thông tin active profile, thời gian chơi, Steam ID.
2. **Giải mã Kho đồ (Inventory & Storage)**:
   * Đọc bảng GaItem (bảng băm liên kết `handle:u32 ➔ item_id:u32`).
   * Phân giải túi đồ thường (`0xA80` slot), túi đồ nhiệm vụ (`0x180` slot) và hòm đồ tại Grace.
   * Lọc và loại bỏ bitmask cấp độ cường hóa vũ khí (`raw_id - (raw_id % 100)`).
3. **Giải mã Cờ Sự Kiện (Event Flags Decoding)**:
   * Vùng dữ liệu cờ `0x1BF99F` byte được lập chỉ mục thông qua thuật toán FromSoftware Event Flag Binary Search Tree (`eventflag-bst.txt`):
     ```python
     mult = EVENT_FLAG_BST[flag_id // 1000]
     index = flag_id % 1000
     byte_offset = mult * 125 + (index // 8)
     bit_pos = 7 - (index % 8)
     is_active = (raw_flags[byte_offset] & (1 << bit_pos)) != 0
     ```
4. **Đối soát & Tạo cấu trúc FMG v2**:
   * Chuẩn hóa ký tự và tên gọi theo từ điển `aliases.json`.
   * Tạo payload JSON khớp 100% schema Zod validation của extension Free Map Genie (FMG):
     ```json
     {
       "version": 2,
       "gameId": 111,
       "mapId": 413,
       "userId": 7764114,
       "data": {
         "locationIds": [163925, 163926, ...]
       }
     }
     ```

---

## 🤝 LỜI CẢM ƠN & THAM KHẢO

Dự án này sử dụng và kế thừa các nghiên cứu xuất sắc từ cộng đồng mã nguồn mở:
* [EthanShoeDev/elden-ring-compass](https://github.com/EthanShoeDev/elden-ring-compass): Tham khảo cấu trúc parser save TypeScript và bảng cây nhị phân Event Flags.
* [soulsmods/Paramdex](https://github.com/soulsmods/Paramdex): Tham khảo bảng danh mục tên vật phẩm và tham số Elden Ring.
* [Free Map Genie (FMG)](https://github.com/fmg-project): Tiện ích mở rộng bản đồ tương tác trên Chrome.
* [MapGenie.io](https://mapgenie.io/elden-ring): Bản đồ tương tác tuyệt vời dành cho Elden Ring.

---

## 📄 BẢN QUYỀN (LICENSE)

Dự án được phát hành theo giấy phép [MIT License](LICENSE). Tự do sử dụng, chỉnh sửa và chia sẻ cho cộng đồng người chơi Elden Ring!
