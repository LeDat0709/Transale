#!/bin/bash

echo "================================================="
echo "🚀 SCRIPT CÀI ĐẶT LIBRE TRANSLATE TRÊN VPS UBUNTU 🚀"
echo "================================================="

# Cập nhật hệ thống
echo "1. Đang cập nhật hệ thống..."
sudo apt-get update && sudo apt-get upgrade -y

# Kiểm tra xem Docker đã cài chưa
if ! command -v docker &> /dev/null
then
    echo "2. Đang cài đặt Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "Docker đã được cài đặt! Vui lòng logout và login lại để nhận quyền docker."
else
    echo "2. Docker đã được cài đặt, bỏ qua bước cài Docker."
fi

# Chạy container LibreTranslate
echo "3. Đang tải và khởi chạy mô hình LibreTranslate (Quá trình này có thể mất vài phút tùy tốc độ mạng VPS)..."
# Chạy ở cổng 5000, tải sẵn model tiếng Anh và tiếng Đức
sudo docker run -d \
  --name libretranslate \
  -ti --rm \
  -p 5000:5000 \
  libretranslate/libretranslate \
  --load-only en,de

echo "================================================="
echo "✅ HOÀN TẤT!"
echo "LibreTranslate đang chạy ngầm trên cổng 5000."
echo "Bạn có thể kiểm tra bằng lệnh: docker logs -f libretranslate"
echo "Bây giờ bạn có thể chạy script Python: python3 sheet_translator.py"
echo "================================================="
