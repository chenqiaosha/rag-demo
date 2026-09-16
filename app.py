import streamlit as st
import requests
import uuid

API_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="PDF知识库问答", layout="wide")
st.title("知识库问答")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]
if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("上传文档")
    st.caption(f"会话id:{st.session_state.session_id}")
    
    uploaded_file = st.file_uploader("选择PDF文件", type=["pdf"])
    if uploaded_file and st.button("索引文档"):
        with st.spinner("正在索引..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
            resp = requests.post(f"{API_URL}/upload", files=files)
            if resp.status_code == 200:
                st.success(resp.json()["message"])
            else:
                st.error(f"失败:{resp.text}")

    st.markdown("---")

    st.header("删除文档")

    # 从后端拉取已有文件列表
    try:
        resp = requests.get(f"{API_URL}/files")
        file_list = resp.json().get("files", []) if resp.status_code == 200 else []
    except Exception:
        file_list = []

    if file_list:
        delete_filename = st.selectbox("选择要删除的文件", file_list)
        if st.button("删除文档"):
            resp = requests.delete(f"{API_URL}/delete", params={"filename": delete_filename})
            if resp.status_code == 200:
                st.success(resp.json()["message"])
                st.rerun()
            else:
                st.error(f"删除失败: {resp.text}")
    else:
        st.info("暂无可删除的文件")

    st.markdown("---")

    st.header("对话历史")
    if st.button("从数据库加载历史记录"):
        resp = requests.get(f"{API_URL}/history/{st.session_state.session_id}")
        if resp.status_code == 200:
            history_data = resp.json()
            st.session_state.messages = []
            for item in history_data:
                st.session_state.messages.append({
                    "role": item["role"],
                    "content": item["content"]
                })
            st.rerun()
        else:
            st.error("加载历史失败")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("输入你的问题..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)
        
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            resp = requests.post(
                f"{API_URL}/chat",
                json={"question": prompt, "session_id": st.session_state.session_id}
            )
            if resp.status_code == 200:
                data = resp.json()
                st.write(data["answer"])
                if data.get("sources"):
                    st.caption(f"来源:{','.join(data['sources'])}")
                st.session_state.messages.append(
                    {"role": "assistant", "content": data["answer"]}
                )
            else:
                st.error(f"出错:{resp.text}")