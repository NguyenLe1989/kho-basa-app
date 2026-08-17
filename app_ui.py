import streamlit as st
import pandas as pd
from bot_quan_ly import HeThongKhoBasa

# 1. CẤU HÌNH TRANG WEB
st.set_page_config(page_title="Quản Lý Kho Thủy Sản Basa", page_icon="🐟", layout="wide")

# 2. KHỞI TẠO KẾT NỐI VỚI BOT (Chỉ chạy 1 lần để không bị chậm)
@st.cache_resource
def load_bot():
    return HeThongKhoBasa()

bot = load_bot()

# 3. HỆ THỐNG TÀI KHOẢN (Phân quyền)
if "db_users" not in st.session_state:
    st.session_state.db_users = {
        "admin": {"pass": "123", "role": "Admin", "name": "Giám Đốc"},
        "thukho": {"pass": "123", "role": "Editor", "name": "Thủ Kho Chính"},
        "fillet": {"pass": "123", "role": "Viewer", "name": "Tổ Trưởng Fillet"},
        "codien": {"pass": "123", "role": "Viewer", "name": "Tổ Trưởng Cơ Điện"}
    }

# 4. GIAO DIỆN ĐĂNG NHẬP
def login_screen():
    st.markdown("<h1 style='text-align: center; color: #1E90FF;'>🐟 HỆ THỐNG KHO THỦY SẢN BASA</h1>", unsafe_allow_html=True)
    st.write("---")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.info("💡 Tài khoản test: admin/123, thukho/123, fillet/123")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submit = st.form_submit_button("Đăng nhập", use_container_width=True)

            if submit:
                if username in st.session_state.db_users and st.session_state.db_users[username]["pass"] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_info = st.session_state.db_users[username]
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    login_screen()
    st.stop() # Chặn không cho xem bên dưới nếu chưa đăng nhập

# 5. GIAO DIỆN CHÍNH (SAU KHI ĐĂNG NHẬP)
user = st.session_state.user_info

# Sidebar (Cột bên trái)
with st.sidebar:
    st.success(f"👤 Chào mừng, **{user['name']}**")
    st.write(f"🔑 Quyền hạn: **{user['role']}**")
    st.write("---")
    if st.button("Đăng xuất", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

st.title(f"🏢 BẢNG ĐIỀU KHIỂN - {user['role'].upper()}")

# Tải dữ liệu kho hiện tại để hiển thị
records = bot.ton_kho_sheet.get_all_records()
df_ton_kho = pd.DataFrame(records)

# ===============================================
# A. DÀNH CHO ADMIN (Giám Đốc) - Xem toàn cảnh
# ===============================================
if user["role"] == "Admin":
    st.subheader("📊 TỔNG QUAN TỒN KHO")
    
    # Lọc ra các mặt hàng sắp hết
    df_canh_bao = df_ton_kho[df_ton_kho["Cảnh Báo"] == "CẢNH BÁO TỒN THẤP"]
    if not df_canh_bao.empty:
        st.error(f"⚠️ Có {len(df_canh_bao)} mặt hàng đang ở mức TỒN THẤP cần nhập thêm!")
        st.dataframe(df_canh_bao[["Mã VT", "Tên Mặt Hàng", "Tồn Cuối", "Tồn Tối Thiểu"]], use_container_width=True)
    else:
        st.success("✅ Toàn bộ vật tư trong kho đều ở mức an toàn.")
        
    st.write("---")
    st.write("**BẢNG KÊ CHI TIẾT TẤT CẢ VẬT TƯ:**")
    st.dataframe(df_ton_kho, use_container_width=True)

# ===============================================
# B. DÀNH CHO EDITOR (Thủ Kho) - Thao tác với Agent
# ===============================================
elif user["role"] == "Editor":
    tab1, tab2 = st.tabs(["🤖 Ra lệnh cho Agent (Nhập/Xuất)", "📦 Bảng Tồn Kho"])
    
    with tab1:
        st.info("💡 Bạn hãy gõ lệnh tự nhiên. Ví dụ: 'Nhập 100 yếm 1m' hoặc 'Xuất 5 dao lạng da 20'. Agent sẽ tự tìm mã và cập nhật sổ sách.")
        cau_lenh = st.text_input("📝 Gõ lệnh của bạn vào đây:")
        if st.button("Thực thi lệnh", type="primary"):
            if cau_lenh:
                with st.spinner("🤖 Agent đang xử lý..."):
                    ket_qua = bot.thuc_thi_lenh(cau_lenh)
                if "✅" in ket_qua:
                    st.success(ket_qua)
                else:
                    st.error(ket_qua)
            else:
                st.warning("Vui lòng nhập câu lệnh.")
                
    with tab2:
        st.dataframe(df_ton_kho, use_container_width=True)

# ===============================================
# C. DÀNH CHO VIEWER (Tổ Trưởng/Nhân Viên) - Chỉ tra cứu
# ===============================================
elif user["role"] == "Viewer":
    st.subheader("🔍 TRA CỨU VẬT TƯ")
    search = st.text_input("Nhập tên vật tư bạn muốn tìm (VD: Băng keo, Ủng...):")
    
    if search:
        # Lọc dữ liệu theo chữ nhân viên gõ
        df_tim_kiem = df_ton_kho[df_ton_kho["Tên Mặt Hàng"].str.contains(search, case=False, na=False)]
        st.write(f"Tìm thấy {len(df_tim_kiem)} kết quả:")
        st.dataframe(df_tim_kiem[["Tên Mặt Hàng", "ĐVT", "Tồn Cuối"]], use_container_width=True)
    else:
        st.write("Toàn bộ danh sách (Chỉ xem):")
        st.dataframe(df_ton_kho[["Mã VT", "Tên Mặt Hàng", "ĐVT", "Tồn Cuối"]], use_container_width=True)