
import streamlit as st
import requests
import json

# --- Cấu hình trang và các hằng số ---
st.set_page_config(page_title="Smart OCR Chatbot", layout="wide")

GATEWAY_API_URL = "http://103.78.3.50:8888/v1/ocr"

# --- Các hàm xử lý logic ---

def call_api(prompt_text):
    """Hàm này xử lý việc hiển thị tin nhắn và gọi API."""
    file = st.session_state.get("uploaded_file")
    if not file:
        st.warning("Vui lòng tải lên tài liệu trước khi gửi yêu cầu.")
        return

    prompt_to_display = prompt_text if prompt_text else "Trích xuất tất cả thông tin trong tài liệu."
    print(prompt_to_display)
    st.session_state.messages.append({"role": "user", "content": prompt_to_display})
    
    st.session_state.messages.append({"role": "assistant", "content": "..."})
    st.session_state.api_call_triggered = True
    st.rerun()

def perform_api_call():
    """Hàm này thực hiện cuộc gọi API thực tế."""
    last_user_message = st.session_state.messages[-2]["content"]
    prompt_for_api = "" if last_user_message == "Trích xuất tất cả thông tin trong tài liệu." else last_user_message
    
    file = st.session_state.get("uploaded_file")
    if not file:
        st.session_state.messages[-1] = {"role": "assistant", "content": "Lỗi: Không tìm thấy file để gửi. Vui lòng tải lại file."}
        return

    try:
        # Gửi đi một file duy nhất, nhưng API Gateway vẫn nhận dưới dạng danh sách
        files_to_send = [("files", (file.name, file.getvalue(), file.type))]
        data_payload = {"prompt": prompt_for_api}

        response = requests.post(GATEWAY_API_URL, files=files_to_send, data=data_payload, timeout=300)
        response.raise_for_status()
        response_data = response.json()
        
        if "choices" in response_data and response_data["choices"]:
            bot_response_content = response_data["choices"][0]["message"]["content"]
            st.session_state.messages[-1] = {"role": "assistant", "content": bot_response_content}
        else:
            error_content = f"Lỗi: Phản hồi không hợp lệ. {response_data}"
            st.session_state.messages[-1] = {"role": "assistant", "content": error_content}

    except requests.exceptions.RequestException as e:
        error_content = f"Lỗi kết nối đến API Gateway: {e}"
        st.session_state.messages[-1] = {"role": "assistant", "content": error_content}
    
    st.session_state.api_call_triggered = False

def handle_file_upload():
    """Callback được gọi mỗi khi người dùng thay đổi lựa chọn file."""
    new_file = st.session_state.get("file_uploader_widget")
    
    if new_file:
        st.session_state.uploaded_file = new_file
        # Reset lại cuộc hội thoại để bắt đầu với ngữ cảnh mới
        st.session_state.messages = [
            {"role": "assistant", "content": f"Đã nhận file mới: **{new_file.name}**. Bạn muốn trích xuất thông tin gì?"}
        ]
    else:
        # Nếu người dùng xóa file
        if "uploaded_file" in st.session_state:
            del st.session_state["uploaded_file"]
        st.session_state.messages = [
            {"role": "assistant", "content": "Chào bạn! Vui lòng tải lên tài liệu và đặt câu hỏi để tôi có thể giúp bạn."}
        ]


# --- Giao diện người dùng ---

st.title("🤖 Smart OCR Chatbot")
st.caption("Powered")

# Khởi tạo session state
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Chào bạn! Vui lòng tải lên tài liệu và đặt câu hỏi để tôi có thể giúp bạn."}]
if "api_call_triggered" not in st.session_state:
    st.session_state.api_call_triggered = False
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None

# Sidebar cho việc tải file
with st.sidebar:
    st.header("📁 Tải lên tài liệu")
    st.file_uploader(
        "Chọn một file (Ảnh/PDF)",
        type=["png", "jpg", "jpeg", "pdf"],
        accept_multiple_files=False, # **FIX**: Chỉ cho phép 1 file
        key="file_uploader_widget",
        on_change=handle_file_upload
    )
    
    if st.session_state.uploaded_file:
        st.success(f"Đã chọn: {st.session_state.uploaded_file.name}")
        if st.button("Trích xuất tất cả thông tin", use_container_width=True):
            call_api("")

# Hiển thị các tin nhắn đã có
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["content"] == "...":
            st.spinner("AI đang phân tích...")
        elif isinstance(msg["content"], str) and msg["content"].strip().startswith('{'):
            try:
                st.json(json.loads(msg["content"]))
            except json.JSONDecodeError:
                st.markdown(msg["content"])
        else:
            st.markdown(msg["content"])

# Ô chat input cho các câu hỏi tùy chỉnh
if user_prompt_input := st.chat_input("Nhập các trường cần trích xuất..."):
    call_api(user_prompt_input)

# Logic để thực hiện cuộc gọi API sau khi rerun
if st.session_state.api_call_triggered:
    perform_api_call()
    st.rerun()