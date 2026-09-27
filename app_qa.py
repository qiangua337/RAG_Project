from uuid import uuid4

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

from file_history_store import get_history
from online_size_ai import stream_answer, stream_size_answer
from size_recommendation import recommend_size

# 标题
st.title("智能客服")
st.divider()    # 分隔符
st.caption("普通问题由 Qwen 在线回答；尺码问题默认使用本地尺码表，可在侧栏切换为 Qwen。")

use_online_size_ai = st.sidebar.toggle(
    "用 Qwen API 分析尺码",
    help="开启后会将你的提问、会话历史和《尺码推荐.txt》内容发送至阿里云 DashScope 的 qwen3-max API。",
)

if "message" not in st.session_state:
    st.session_state["message"] = [{"role": "assistant", "content": "你好，有什么可以帮助你?"}]

if "session_id" not in st.session_state:
    st.session_state["session_id"] = uuid4().hex

# 渲染历史对话
for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

# 在页面最下方提供用户输入栏
prompt = st.chat_input("请输入你的问题")

if prompt:
    previous_messages = list(st.session_state["message"])
    # 在页面输出用户的提问
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        try:
            local_answer = recommend_size(prompt, previous_messages)
            if local_answer is not None:
                if use_online_size_ai:
                    with st.spinner("Qwen 思考中..."):
                        answer = st.write_stream(
                            stream_size_answer(prompt, st.session_state["session_id"])
                        )
                else:
                    answer = local_answer
                    st.write(answer)
                    get_history(st.session_state["session_id"]).add_messages(
                        [HumanMessage(content=prompt), AIMessage(content=answer)]
                    )
            else:
                with st.spinner("Qwen 思考中..."):
                    answer = st.write_stream(
                        stream_answer(prompt, st.session_state["session_id"])
                    )
        except Exception as exc:
            if "dashscope.aliyuncs.com" in str(exc) and "WinError 10013" in str(exc):
                st.error("当前运行环境无法连接 DashScope。尺码问题可根据本地尺码表回答；其他问题需要允许访问外网的运行环境。")
            else:
                st.error(f"回答失败：{exc}")
        else:
            st.session_state["message"].append(
                {"role": "assistant", "content": answer}
            )
