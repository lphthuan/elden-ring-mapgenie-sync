# HƯỚNG DẪN SỬ DỤNG CÔNG CỤ ĐỒNG BỘ ELDEN RING ➔ MAPGENIE (FMG)

Công cụ độc lập giúp tự động giải mã file save của Elden Ring PC (`ER0000.sl2`), nhận diện toàn bộ các vị trí đã khám phá và xuất ra file JSON chuẩn để **Import** trực tiếp vào extension **Free Map Genie (FMG)** trên Chrome.

---

## 🌟 CÁC TÍNH NĂNG CHÍNH

1. **Tự động tìm kiếm file save Steam**:
   - Tự động nhận diện đường dẫn save Steam tại `%APPDATA%\EldenRing\<SteamID>\ER0000.sl2`.
   - Hỗ trợ kéo thả hoặc chọn file save từ bất kỳ thư mục nào trên máy tính.
2. **Hỗ trợ đầy đủ 10 Slot nhân vật**:
   - Hiển thị tên nhân vật, cấp độ (Level), thời gian chơi (Playtime), số lần tử trận (Deaths).
3. **Độ chính xác cao & Phân loại chi tiết**:
   - **Sites of Grace (Điểm ân điển)**: Quét chính xác theo cờ kích hoạt event của game.
   - **Bosses & Great Enemies (Trùm & Kẻ địch)**: Quét trùm chính, trùm phụ thế giới, trùm đêm.
   - **Vũ khí, Giáp, Bùa hộ mệnh, Phép thuật, Sách nấu ăn, Tro tàn chiến tranh**.
   - **Vật liệu nâng cấp (Materials)**: Đá rèn, Hoa hầm mộ, Thảo mộc hiếm (tùy chọn bật/tắt riêng).
   - **Vật phẩm dùng 1 lần (Consumables)**: Hạt vàng (Golden Runes), Cung lửa, Bình gỉ (tùy chọn bật/tắt riêng).
   - **Hòm đồ (Storage Box)**: Quét cả vật phẩm cất trong rương tại Grace.
4. **Động cơ Nhận diện Không gian Thông minh (Smart Spatial Engine)**:
   - **Cửa Hầm ngục (Dungeons)**: Tự động đánh dấu lối vào hầm ngục khi Điểm Ân Điển bên trong đã mở.
   - **Ngục tù vĩnh hằng (Evergaols)**: Tự động đánh dấu khi trùm bên trong bị hạ gục.
   - **Tượng ấn Yêu tinh (Imp Seal Statues)**: Đánh dấu tượng dùng Stonesword Key khi đã lấy đồ/Grace sau tượng.
   - **Kẻ xâm lăng (NPC Invasions) & Quái Tinh Anh**: Đánh dấu khi sở hữu vũ khí/bùa rơi độc nhất tại vị trí đó (Reduvia, Vyke's Spear, Rivers of Blood, v.v.).
   - **Túi bùa Margit (Talisman Pouch)**: Đánh dấu chuẩn xác khi Margit đã bị tiêu diệt.
5. **Tính năng Smart Merge & Override (Gộp file FMG cũ)**:
   - **Gộp Bổ Sung (Additive Union - Mặc định)**: Giữ 100% tất cả các điểm đánh dấu tỉ mỉ bằng tay (Landmarks, NPCs, ghi chú thế giới, hoa cỏ) + Bổ sung tất cả các điểm mới tự động phát hiện từ Save game.
   - **Ghi Đè Độc Nhất (Strict Override)**: Giữ các điểm khám phá nhỏ, nhưng riêng với Điểm Ân Điển (Grace) và Trùm (Boss) sẽ ghi đè 100% theo đúng tiến trình thực tế của file save.
6. **Hỗ trợ cả 2 bản đồ**:
   - **The Lands Between** (Bản đồ game gốc - Map ID `413`).
   - **Realm of Shadow** (DLC Shadow of the Erdtree - Map ID `638`).

---

## 🚀 CÁCH SỬ DỤNG (CỰC KỲ ĐƠN GIẢN)

### Cách 1: Sử dụng Giao diện Web (Khuyên dùng)
1. Nhấp đúp vào file **`Chay_Sync_Save_EldenRing.bat`** (ở thư mục gốc) hoặc file **`run_web_ui.bat`** (trong thư mục `EldenRing_SaveSync`).
2. Trình duyệt Chrome sẽ tự động mở trang giao diện: `http://127.0.0.1:8088`.
3. Nhấp nút **"Nạp File Này"** (công cụ tự phát hiện save Steam) hoặc kéo thả file `ER0000.sl2` vào trang web.
4. Bấm chọn **Nhân vật** bạn muốn đồng bộ (ví dụ: Slot 1: Thune - Level 99).
5. *(Tùy chọn)* Kéo thả file **FMG JSON cũ** đã đánh dấu bằng tay vào khung **"Kết Hợp Với File FMG Cũ"** và chọn chế độ:
   - **Gộp Bổ Sung**: Giữ nguyên toàn bộ điểm cũ + thêm điểm mới.
   - **Ghi Đè Độc Nhất**: Cập nhật lại Grace và Boss theo đúng file save.
6. Chọn bản đồ (**The Lands Between** hoặc **Realm of Shadow**).
7. Bấm nút **"⚡ Bắt Đầu Quét & Tạo File FMG"**.
8. Bấm **"📥 Tải File JSON Cho FMG"** để lưu file import về máy.

---

### Cách 2: Sử dụng dòng lệnh (CLI)
Mở PowerShell hoặc CMD trong thư mục `EldenRing_SaveSync`:
```bash
# Quét tự động save Steam, xuất cho bản đồ The Lands Between:
python elden_ring_fmg_sync.py --slot 0 --map 413 --user 7764114 --output fmg_import_ready.json

# Quét và gộp bổ sung (Additive) với file FMG cũ:
python elden_ring_fmg_sync.py --slot 0 --map 413 --user 7764114 --merge "data/manual_fmg_user_marked.json" --merge-mode additive --output fmg_merged.json

# Quét và ghi đè độc nhất (Override) Grace/Boss theo file save:
python elden_ring_fmg_sync.py --slot 0 --map 413 --user 7764114 --merge "data/manual_fmg_user_marked.json" --merge-mode override --output fmg_merged_override.json
```

---

## 📥 HƯỚNG DẪN IMPORT VÀO MAPGENIE (FMG)

1. Mở trình duyệt Chrome có cài extension **Free Map Genie (FMG)**.
2. Bấm vào icon **FMG** trên thanh công cụ tiện ích ➔ Chọn **Data Manager** (hoặc mở trực tiếp file `dataManager.html` của extension).
3. Tại giao diện Data Manager:
   - Chuyển sang thẻ **Import**.
   - Kéo thả file JSON vừa tạo (`fmg_import_ready_map413.json` hoặc file vừa tải về) vào khung Import.
   - Nhấn nút xác nhận Import.
4. Mở lại bản đồ [MapGenie Elden Ring](https://mapgenie.io/elden-ring/maps/the-lands-between) và nhấn **F5 (Reload)**.
5. Toàn bộ các Điểm ân điển, Trùm và Vật phẩm mà nhân vật của bạn đã nhặt sẽ tự động được tích dấu hoàn thành trên bản đồ!
