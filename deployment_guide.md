# Hướng dẫn Triển khai DreamSketch lên Cloud

Tài liệu này hướng dẫn cách chạy ứng dụng bằng Docker và triển khai lên môi trường Cloud.

## 1. Chạy cục bộ với Docker (Local)

Trước khi đưa lên cloud, bạn có thể kiểm tra trên máy tính cá nhân.

**Yêu cầu:** Đã cài đặt [Docker Desktop](https://www.docker.com/products/docker-desktop/).

1.  **Tạo file .env:**
    Đảm bảo bạn có file `.env` chứa `API_KEY` (Google Gemini API Key) cùng cấp với file `docker-compose.yml`.

2.  **Build và chạy:**
    Mở terminal tại thư mục dự án và chạy lệnh:
    ```bash
    docker-compose up --build
    ```

3.  **Truy cập:**
    Mở trình duyệt và vào: `http://localhost:5000`

---

## 2. Triển khai lên Cloud

Dưới đây là 2 cách phổ biến và dễ dàng nhất để triển khai ứng dụng Docker: **Render** (Dễ nhất) và **Google Cloud Run** (Mạnh mẽ nhất).

### Lưu ý quan trọng về dữ liệu (Ảnh/Video)
Ứng dụng hiện tại lưu ảnh vào thư mục `results/` trên disk.
- **Trên Docker Local:** Ảnh sẽ được lưu lại nhờ cấu hình `volumes`.
- **Trên Cloud (Render/Cloud Run):** Các dịch vụ này thường là "Stateless". Khi server khởi động lại (hoặc sau một thời gian không dùng), **file ảnh cũ sẽ bị mất**. Để lưu vĩnh viễn, cần code thêm chức năng upload lên Google Drive hoặc AWS S3.

---

### Cách 1: Deploy lên Render (Miễn phí / Dễ dùng)

1.  Đẩy code của bạn lên **GitHub**.
2.  Tạo tài khoản tại [render.com](https://render.com/).
3.  Chọn **New +** -> **Web Service**.
4.  Kết nối với repository GitHub của bạn.
5.  Cấu hình:
    - **Runtime:** chọn **Docker**.
    - **Region:** Singapore (cho nhanh từ VN).
    - **Free Instance Type:** Chọn gói Free (lưu ý sẽ sleep sau 15p không dùng).
6.  **Environment Variables (Quan trọng):**
    - Nhấn **Add Environment Variable**.
    - Key: `API_KEY`
    - Value: `...` (Copy key Gemini của bạn vào đây).
7.  Nhấn **Create Web Service**.

Render sẽ tự động build Dockerfile và chạy web.

---

### Cách 2: Deploy lên Google Cloud Run

Cách này chuyên nghiệp hơn, server tự động scale (tắt khi không dùng, bật khi có khách).

**Yêu cầu:** Cài đặt [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) hoặc dùng Google Cloud Shell trên trình duyệt.

1.  **Đăng nhập & Setup Project:**
    ```bash
    gcloud auth login
    gcloud config set project [YOUR_PROJECT_ID]
    ```

2.  **Bật Artifact Registry & Cloud Run:**
    Vào Google Cloud Console bật API "Cloud Run" và "Artifact Registry".

3.  **Deploy bằng 1 lệnh:**
    Chạy lệnh sau tại thư mục code:
    ```bash
    gcloud run deploy dreamsketch --source . --region asia-southeast1 --allow-unauthenticated
    ```

4.  **Nhập biến môi trường (Lần đầu):**
    Quá trình chạy lệnh có thể hỏi hoặc bạn cần vào giao diện Cloud Run để thêm `API_KEY` vào phần **Security/Variables**.

---

### Kiểm tra Dockerfile (Dành cho Dev)

Docker file hiện tại sử dụng `python:3.9-slim` để tối ưu dung lượng.
- Port: `5000`
- Lệnh chạy: `python server.py`
