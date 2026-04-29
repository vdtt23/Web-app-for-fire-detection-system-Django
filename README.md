# 🔥 Fire Detection System (Django + Contiki-NG)

Hệ thống phát hiện cháy theo thời gian thực sử dụng mô phỏng mạng cảm biến và web dashboard.

---

## 🚀 Technologies

* **Contiki-NG** – mô phỏng sensor network
* **UDP / RPL** – truyền dữ liệu giữa các node
* **Serial Socket (TCP)** – bridge sang backend
* **Django** – xử lý dữ liệu & API
* **Chart.js + AJAX** – hiển thị realtime

---

## ✨ Features

* 📡 Thu thập dữ liệu: Temperature, Smoke, Humidity
* 🔄 Dashboard realtime (không cần reload)
* 📊 Biểu đồ sensor realtime
* 🚨 Cảnh báo FIRE / WARNING
* 🔌 Tự động reconnect khi mất socket
* 🧹 Giới hạn database tránh phình to

---

## 🏗️ System Architecture

```text
Sensor Nodes → UDP → Border Router → Serial Socket (TCP) → Django → Web (HTTP)
```

---

## ⚙️ Setup Instructions

### 1. Clone project

```bash
git clone https://github.com/vdtt23/Web-app-for-fire-detection-system-Django.git
cd Web-app-for-fire-detection-system-Django
```

---

### 2. Create virtual environment

```bash
python -m venv venv
```

#### Windows

```bash
venv\Scripts\activate
```

#### Ubuntu

```bash
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Create `.env`

Tạo file `.env` ở root project:

```env
SOCKET_HOST=127.0.0.1
SOCKET_PORT=60001
```

---

### 5. Run database

```bash
python manage.py migrate
```

---

## ▶️ Run Project

### 1. Start Django server

```bash
python manage.py runserver 0.0.0.0:8000
```

---

### 2. Start socket listener

```bash
python manage.py read_socket
```

---

### 3. Start Cooja simulation

* Mở Cooja
* Bật **Serial Socket Server (port 60001)**

---

## 🌐 Access

* Dashboard:

```text
http://localhost:8000/dashboard/
```

* Alerts:

```text
http://localhost:8000/alerts/
```

---

## 📡 API Endpoints

* `/api/nodes/` → dữ liệu sensor realtime
* `/api/alerts/` → danh sách cảnh báo

---

## 🚨 Status Logic

```python
if temp > 60 and smoke > 80:
    FIRE
elif temp > 40 or smoke > 50:
    WARNING
else:
    SAFE
```

---

## ⚠️ Notes

* Không commit `.env`, `venv`, `db.sqlite3`
* Đảm bảo port `60001` đang mở
* Nếu dùng ngrok → thêm domain vào `ALLOWED_HOSTS`

---

## 🧪 Demo

* Realtime update mỗi ~2s
* Auto reconnect socket
* Fire alert detection

---

## 🔮 Future Improvements

* WebSocket realtime (thay polling)
* MQTT integration (chuẩn IoT)
* Deploy production (Gunicorn + Nginx)
* UI nâng cao (animation, alert popup)

---

## 📚 References

Simulation được xây dựng dựa trên:

* [https://github.com/vytrannguyenthao/Simulating-the-fire-detection-system-in-Contiki.git](https://github.com/vytrannguyenthao/Simulating-the-fire-detection-system-in-Contiki.git)

Modifications:

* Tích hợp với Django backend
* Xây dựng hệ thống realtime dashboard
* Thêm logic phát hiện cháy và cảnh báo

---

## 👤 Author

GitHub: [https://github.com/vdtt23](https://github.com/vdtt23)
