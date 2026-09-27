"""
基于Streamlit的文件完成web网页上传
当web网页元素发生变化,则代码会重新运行一遍
"""

import streamlit as st
from knowledge_base import KnonledgeBaseService
import time

#添加网页标题
st.title("知识库更新服务")

uploader_file = st.file_uploader(
    "请上传TXT文件",
    type=["txt", "pdf", "docx"],
    accept_multiple_files=False  # 是否接受多文件上传
)

service = KnonledgeBaseService
if "service" not in st.session_state:
    st.session_state["service"] = KnonledgeBaseService()


if uploader_file is not None:
    #提取文本信息
    file_name = uploader_file.name
    file_type = uploader_file.type
    file_size = uploader_file.size / 1024  # 文件大小单位为KB

    st.subheader(f"文件名:{file_name}")
    st.write(f"格式:{file_type} |大小:{file_size : .2f}KB")

    #getvalue -> bytes ->decode("utf-8")
    text = uploader_file.getvalue().decode("utf-8")

    with st.spinner("上传中..."):
        time.sleep(1)
        result = st.session_state["service"].upload_by_str(text , file_name)
        st.write(result)

