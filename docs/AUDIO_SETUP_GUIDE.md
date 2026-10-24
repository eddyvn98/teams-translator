# Hướng dẫn cấu hình âm thanh 2 chiều (Zero-Intrusive Audio Guide)

> **Mục tiêu**: 
> 1. Vừa xem transcript & dịch trực tiếp từ cuộc họp Teams.
> 2. Vừa nói tiếng Việt ở điện thoại $\rightarrow$ máy tính phát tiếng Anh vào micro Teams.
> 3. Chính bạn vẫn tự nghe thấy câu tiếng Anh phát ra (Audio Monitor).
> 4. **Quan trọng nhất**: Khi tắt app, máy tính **không bao giờ bị câm loa hay điếc mic** (giữ nguyên 100% loa & mic mặc định).

---

## 1. Nguyên tắc cốt lõi: "Zero-Intrusive" (Không can thiệp Loa hệ thống)

* **Loa (Speaker) của máy & Teams**: **TUYỆT ĐỐI GIỮ NGUYÊN là Loa / Tai nghe thật của bạn**.
  - Không bao giờ đổi Loa của hệ điều hành hay Loa của Teams sang Cáp ảo.
  - Web App (`run_web.py`) thu âm cuộc họp bằng tính năng **Share Tab Teams** (kèm Share Tab Audio) của Chrome/Edge. Trình duyệt tự nhân bản luồng âm thanh số cho app dịch, tai bạn vẫn nghe cuộc họp bình thường 100%.
* **Microphone của Teams**: Sử dụng **Microphone Gộp (Hybrid / Aggregate Mic)** kết hợp giữa **Micro thật** và **Cáp ảo**.

---

## 2. Hướng dẫn cấu hình trên macOS

### Bước 1: Cài đặt Driver âm thanh ảo BlackHole 2ch (Chỉ làm 1 lần)
Mở Terminal trên Mac và chạy:
```bash
brew install blackhole-2ch
```
*(Hoặc tải gói cài đặt `.pkg` trực tiếp từ [existential.audio/blackhole](https://existential.audio/blackhole/)).*

Sau khi cài đặt xong, bạn có thể khởi động lại CoreAudio để nhận ngay thiết bị:
```bash
sudo killall coreaudiod
```

---

### Bước 2: Tạo Micro Gộp (Aggregate Device) trong Audio MIDI Setup
Ứng dụng **Audio MIDI Setup** có sẵn 100% trên mọi máy Mac:
1. Nhấn `Cmd + Space`, gõ `Audio MIDI Setup` và nhấn Enter (hoặc mở từ `Finder` > `Applications` > `Utilities` > `Audio MIDI Setup.app`).
2. Ở góc dưới bên trái cửa sổ, bấm vào dấu **`+`** $\rightarrow$ chọn **Create Aggregate Device**.
3. Đổi tên thiết bị mới tạo thành: **`Teams Hybrid Mic`**.
4. Ở bảng danh sách thiết bị bên phải, tích chọn 2 mục sau:
   - ✅ **Micrô MacBook Pro** (hoặc Micro tai nghe AirPods / USB của bạn).
   - ✅ **BlackHole 2ch**.
   *(Lưu ý: Đảm bảo ô **Drift Correction** được tích ở dòng BlackHole 2ch).*

---

### Bước 3: Cấu hình trong Microsoft Teams (hoặc Chrome)
1. Mở Microsoft Teams > **Cài đặt (Settings)** > **Thiết bị (Devices)**:
   * **Speaker (Loa)**: Giữ nguyên **`Loa MacBook Pro`** (hoặc Tai nghe của bạn).
   * **Microphone**: Chọn **`Teams Hybrid Mic`** (thiết bị vừa tạo ở Bước 2).
2. **Hoàn tất!**
   * Khi bạn nói bằng mic laptop $\rightarrow$ Teams nghe thấy bình thường.
   * Khi điện thoại bạn gửi câu tiếng Anh về $\rightarrow$ Web App phát song song vào `BlackHole 2ch` (Teams nghe thấy) và `Loa MacBook Pro` (bạn tự nghe thấy).
   * **Khi tắt app hoàn toàn**: Bạn vẫn nói chuyện trong Teams và nghe nhạc bình thường, không bao giờ phải đổi lại thiết bị.

---

## 3. Hướng dẫn cấu hình trên Windows

### Bước 1: Cài đặt VB-CABLE Virtual Audio Device
Tải driver miễn phí tại [vb-audio.com/Cable](https://vb-audio.com/Cable/) (giải nén file zip, chuột phải `VBCABLE_Setup_x64.exe` chọn *Run as administrator* và Restart máy).
Windows sẽ có thêm 2 thiết bị:
* Playback: `CABLE Input (VB-Audio Virtual Cable)`
* Recording: `CABLE Output (VB-Audio Virtual Cable)`

---

### Bước 2: Chọn 1 trong 2 phương án bên dưới

#### Phương án A: Dùng VoiceMeeter (Gộp Mic 1 lần dùng mãi mãi - Khuyên dùng)
1. Tải **VoiceMeeter** (miễn phí) từ [vb-audio.com/Voicemeeter](https://vb-audio.com/Voicemeeter/).
2. Mở VoiceMeeter:
   * **Hardware Input 1**: Chọn Microphone thật của bạn (chọn chuẩn `MME` hoặc `WDM`).
   * **Hardware Input 2**: Chọn `CABLE Output (VB-Audio)`.
   * Bật nút **`B`** (hoặc `B1`) ở cả 2 cột Input để đẩy âm thanh vào cổng ra ảo `VoiceMeeter Output`.
3. Trong Microsoft Teams:
   * **Speaker (Loa)**: Giữ nguyên **Loa/Tai nghe thật của bạn**.
   * **Microphone**: Chọn **`VoiceMeeter Output (VB-Audio VoiceMeeter VAIO)`**.
4. **Kết quả**: Cả mic thật của bạn và tiếng Anh từ điện thoại đều chạy thẳng vào Teams. Khi tắt app, mic thật vẫn luôn thông suốt vào Teams, không bị ảnh hưởng.

---

#### Phương án B: Dùng tính năng "Listen to this device" của Windows
Nếu bạn không muốn cài thêm VoiceMeeter:
1. Nhấn `Win + R`, gõ `mmsys.cpl` và nhấn Enter để mở **Sound Control Panel**.
2. **Tab Playback (Phát lại)**:
   * Đảm bảo **Loa / Tai nghe thật của bạn** đang là **Default Device**.
3. **Tab Recording (Thu âm)**:
   * Chuột phải vào **`CABLE Output`** $\rightarrow$ chọn **Properties**.
   * Chuyển sang tab **Listen**.
   * Tích vào ô: **`☑ Listen to this device`**.
   * Tại mục *Playback through this device*, chọn **Loa / Tai nghe thật của bạn**.
   * Bấm **Apply** $\rightarrow$ **OK**.
4. Trong Microsoft Teams:
   * **Speaker (Loa)**: Chọn **Loa / Tai nghe thật của bạn**.
   * **Microphone**: Khi họp phiên dịch thì chọn **`CABLE Output`**. Khi kết thúc cuộc họp, chọn lại Micro thật của máy.

---

## 4. Khắc phục sự cố trên Windows nếu bị kẹt loa từ phiên bản cũ

Nếu trước đó bạn từng chạy các script cũ (`setup_audio_monitor.ps1`, `nghe_loa_va_dich.bat`) và bị kẹt thiết bị:
1. Chạy file **`khoi_phuc_loa.bat`** trong thư mục gốc của repo để tự động xóa registry ghi đè và đặt lại thiết bị mặc định.
2. Hoặc nhấn `Win + R`, gõ `mmsys.cpl`, chuột phải vào Loa thật của bạn chọn **Set as Default Device**.

---

## 5. Sử dụng Tai nghe Bluetooth có Mic (AirPods, Sony, v.v.)

### Cách 1: Dùng tai nghe để NGHE (Khuyên dùng nhất ⭐)
* **Speaker trong Teams**: Chọn Tai nghe Bluetooth của bạn.
* **Microphone trong Teams**: Vẫn chọn **`Teams Hybrid Mic`** (trên Mac) hoặc **`VoiceMeeter / CABLE Output`** (trên Win).
* **Lợi ích**: Giữ nguyên âm thanh Hi-Fi Stereo / AAC chất lượng cao nhất cho tai nghe, không bị giảm chất lượng xuống chế độ mono đàm thoại của Bluetooth.

### Cách 2: Muốn dùng Mic của tai nghe Bluetooth để nói chuyện từ xa
* **Trên Mac**: Mở **Audio MIDI Setup** $\rightarrow$ bấm vào `Teams Hybrid Mic` $\rightarrow$ tích chọn thêm tên Tai nghe Bluetooth của bạn $\rightarrow$ tích ô **Drift Correction** (Hiệu chỉnh trôi).
* **Trên Win**: Trong VoiceMeeter, chuyển `Hardware Input 1` sang Mic của Tai nghe Bluetooth.
