import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import re

class HeThongKhoBasa:
    def __init__(self):
        print("🤖 Bot Quản Lý đang khởi động và kết nối với Google Sheet...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
        self.client = gspread.authorize(creds)
        self.doc = self.client.open("KHO_THUY_SAN_BASA")
        self.ton_kho_sheet = self.doc.worksheet("TON_KHO")
        self.log_sheet = self.doc.worksheet("NHAT_KY_NHAP_XUAT")
        print("✅ Bot đã sẵn sàng nhận lệnh!\n" + "="*40)

    def thuc_thi_lenh(self, cau_lenh):
        cau_lenh_lower = cau_lenh.lower()
        
        # 1. Xác định hành động (Nhập hay Xuất)
        hinh_thuc = ""
        if "nhập" in cau_lenh_lower:
            hinh_thuc = "NHAP"
        elif "xuất" in cau_lenh_lower:
            hinh_thuc = "XUAT"
        else:
            return "❌ Bot không hiểu lệnh. Bạn cần có chữ 'Nhập' hoặc 'Xuất'."

        # 2. Tìm số lượng (lấy con số trong câu lệnh)
        so_luong_tim_thay = re.findall(r'\d+', cau_lenh)
        if not so_luong_tim_thay:
            return "❌ Bot không thấy số lượng trong câu lệnh."
        so_luong = float(so_luong_tim_thay[0])

        # 3. Kéo dữ liệu từ Sheet về để tìm tên vật tư
        danh_sach_vt = self.ton_kho_sheet.get_all_records()
        vat_tu_match = None
        chi_so_dong = 1 # Dòng 1 là tiêu đề
        
        for row in danh_sach_vt:
            chi_so_dong += 1
            ten_vt = str(row.get('Tên Mặt Hàng', '')).lower()
            ma_vt = str(row.get('Mã VT', '')).lower()
            
            # Nếu tên vật tư (hoặc 1 phần tên) xuất hiện trong câu lệnh
            if ten_vt in cau_lenh_lower or (ma_vt != "" and ma_vt in cau_lenh_lower):
                vat_tu_match = row
                break

        # Thử tìm theo từ khóa lỏng hơn nếu tìm chính xác không ra
        if not vat_tu_match:
            for row in danh_sach_vt:
                ten_vt = str(row.get('Tên Mặt Hàng', '')).lower()
                # Ví dụ gõ "bao tay rồng" thì tìm "bao tay dragon"
                if "dragon" in cau_lenh_lower and "dragon" in ten_vt:
                    vat_tu_match = row; break
                elif "hướng dương" in cau_lenh_lower and "hướng dương" in ten_vt:
                    vat_tu_match = row; break
                elif "clorin" in cau_lenh_lower and "clorin" in ten_vt:
                    vat_tu_match = row; break

        if not vat_tu_match:
            return f"❌ Bot không tìm thấy mặt hàng nào phù hợp với câu lệnh: '{cau_lenh}'"

        # 4. Bắt đầu tính toán xuất/nhập
        ton_dau = float(vat_tu_match['Tồn Đầu'])
        tong_nhap = float(vat_tu_match['Tổng Nhập'])
        tong_xuat = float(vat_tu_match['Tổng Xuất'])
        ton_toi_thieu = float(vat_tu_match['Tồn Tối Thiểu'])
        ton_cuoi_hien_tai = ton_dau + tong_nhap - tong_xuat

        if hinh_thuc == "NHAP":
            tong_nhap += so_luong
            ton_cuoi_moi = ton_dau + tong_nhap - tong_xuat
        else: # XUAT
            if ton_cuoi_hien_tai < so_luong:
                return f"⚠️ TỪ CHỐI XUẤT: Trong kho chỉ còn {ton_cuoi_hien_tai} {vat_tu_match['ĐVT']} {vat_tu_match['Tên Mặt Hàng']}."
            tong_xuat += so_luong
            ton_cuoi_moi = ton_dau + tong_nhap - tong_xuat

        trang_thai = "CẢNH BÁO TỒN THẤP" if ton_cuoi_moi <= ton_toi_thieu else "AN TOÀN"

        # 5. Cập nhật lên Google Sheet (Sheet TON_KHO)
        # Cột: 7(Nhập), 8(Xuất), 9(Tồn Cuối), 11(Cảnh Báo)
        self.ton_kho_sheet.update_cell(chi_so_dong, 7, tong_nhap)
        self.ton_kho_sheet.update_cell(chi_so_dong, 8, tong_xuat)
        self.ton_kho_sheet.update_cell(chi_so_dong, 9, ton_cuoi_moi)
        self.ton_kho_sheet.update_cell(chi_so_dong, 11, trang_thai)

        # 6. Ghi vào Sổ Nhật Ký (Sheet NHAT_KY_NHAP_XUAT)
        thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.log_sheet.append_row([
            thoi_gian, hinh_thuc, vat_tu_match['Mã VT'], vat_tu_match['Tên Mặt Hàng'],
            vat_tu_match['Danh Mục'], so_luong, vat_tu_match['ĐVT'], 
            "Người dùng qua lệnh", "Thủ Kho Bot", cau_lenh
        ])

        return f"✅ Đã {hinh_thuc} {so_luong} {vat_tu_match['ĐVT']} [{vat_tu_match['Tên Mặt Hàng']}]. Tồn cuối mới: {ton_cuoi_moi}"

# ==========================================
# PHẦN CHẠY THỬ NGHIỆM
# ==========================================
if __name__ == "__main__":
    bot = HeThongKhoBasa()
    
    while True:
        lenh = input("\n📝 Nhập lệnh của bạn (hoặc gõ 'thoat' để tắt): ")
        if lenh.lower() == 'thoat':
            break
        
        ket_qua = bot.thuc_thi_lenh(lenh)
        print(ket_qua)