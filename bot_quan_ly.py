import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import streamlit as st
import re

class HeThongKhoBasa:
    def __init__(self):
        print("🤖 Bot Quản Lý đang khởi động...")
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Tự động lấy key từ Streamlit Secrets khi chạy online
        if hasattr(st, "secrets") and "gcp_service_account" in st.secrets:
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dict(st.secrets["gcp_service_account"]), scope)
        else:
            creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
            
        self.client = gspread.authorize(creds)
        self.doc = self.client.open("KHO_THUY_SAN_BASA")
        self.ton_kho_sheet = self.doc.worksheet("TON_KHO")
        self.log_sheet = self.doc.worksheet("NHAT_KY_NHAP_XUAT")
        print("✅ Bot đã sẵn sàng nhận lệnh!\n" + "="*40)

    def thuc_thi_lenh(self, cau_lenh):
        cau_lenh_lower = cau_lenh.lower()
        
        hinh_thuc = ""
        if "nhập" in cau_lenh_lower:
            hinh_thuc = "NHAP"
        elif "xuất" in cau_lenh_lower:
            hinh_thuc = "XUAT"
        else:
            return "❌ Bot không hiểu lệnh. Bạn cần có chữ 'Nhập' hoặc 'Xuất'."

        so_luong_tim_thay = re.findall(r'\d+', cau_lenh)
        if not so_luong_tim_thay:
            return "❌ Bot không thấy số lượng trong câu lệnh."
        so_luong = float(so_luong_tim_thay[0])

        danh_sach_vt = self.ton_kho_sheet.get_all_records()
        vat_tu_match = None
        chi_so_dong = 1
        
        for row in danh_sach_vt:
            chi_so_dong += 1
            ten_vt = str(row.get('Tên Mặt Hàng', '')).lower()
            ma_vt = str(row.get('Mã VT', '')).lower()
            
            if ten_vt in cau_lenh_lower or (ma_vt != "" and ma_vt in cau_lenh_lower):
                vat_tu_match = row
                break

        if not vat_tu_match:
            for row in danh_sach_vt:
                ten_vt = str(row.get('Tên Mặt Hàng', '')).lower()
                if "dragon" in cau_lenh_lower and "dragon" in ten_vt:
                    vat_tu_match = row; break
                elif "hướng dương" in cau_lenh_lower and "hướng dương" in ten_vt:
                    vat_tu_match = row; break
                elif "clorin" in cau_lenh_lower and "clorin" in ten_vt:
                    vat_tu_match = row; break

        if not vat_tu_match:
            return f"❌ Bot không tìm thấy mặt hàng nào phù hợp với câu lệnh: '{cau_lenh}'"

        ton_dau = float(vat_tu_match['Tồn Đầu'])
        tong_nhap = float(vat_tu_match['Tổng Nhập'])
        tong_xuat = float(vat_tu_match['Tổng Xuất'])
        ton_toi_thieu = float(vat_tu_match['Tồn Tối Thiểu'])
        ton_cuoi_hien_tai = ton_dau + tong_nhap - tong_xuat

        if hinh_thuc == "NHAP":
            tong_nhap += so_luong
            ton_cuoi_moi = ton_dau + tong_nhap - tong_xuat
        else:
            if ton_cuoi_hien_tai < so_luong:
                return f"⚠️ TỪ CHỐI XUẤT: Trong kho chỉ còn {ton_cuoi_hien_tai} {vat_tu_match['ĐVT']} {vat_tu_match['Tên Mặt Hàng']}."
            tong_xuat += so_luong
            ton_cuoi_moi = ton_dau + tong_nhap - tong_xuat

        trang_thai = "CẢNH BÁO TỒN THẤP" if ton_cuoi_moi <= ton_toi_thieu else "AN TOÀN"

        self.ton_kho_sheet.update_cell(chi_so_dong, 7, tong_nhap)
        self.ton_kho_sheet.update_cell(chi_so_dong, 8, tong_xuat)
        self.ton_kho_sheet.update_cell(chi_so_dong, 9, ton_cuoi_moi)
        self.ton_kho_sheet.update_cell(chi_so_dong, 11, trang_thai)

        thoi_gian = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.log_sheet.append_row([
            thoi_gian, hinh_thuc, vat_tu_match['Mã VT'], vat_tu_match['Tên Mặt Hàng'],
            vat_tu_match['Danh Mục'], so_luong, vat_tu_match['ĐVT'], 
            "Người dùng qua Web", "Thủ Kho Bot", cau_lenh
        ])

        return f"✅ Đã {hinh_thuc} {so_luong} {vat_tu_match['ĐVT']} [{vat_tu_match['Tên Mặt Hàng']}]. Tồn cuối mới: {ton_cuoi_moi}"