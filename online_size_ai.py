"""通过 DashScope 的 Qwen API 生成普通或尺码问答。"""

from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

import config_data as config
from file_history_store import get_history
from size_recommendation import SIZE_GUIDE


def stream_answer(question: str, session_id: str, use_size_guide: bool = False):
    """调用 Qwen 流式回答，并在完整回答后写入会话历史。"""
    history = get_history(session_id)
    if use_size_guide:
        guide = SIZE_GUIDE.read_text(encoding="utf-8")
        system_content = (
            "你是尺码推荐助手。只依据下面的尺码表回答。回答只能包含匹配的尺码、对应区间，"
            "以及无法匹配或区间重叠的说明。表中没有宽松度、合身度或版型信息，"
            "因此禁止给出这类选择建议，也不要编造唯一尺码。\n尺码表：\n" + guide
        )
    else:
        system_content = "你是智能客服。请用中文简洁、准确地回答用户问题。"
    messages = [
        SystemMessage(content=system_content),
        *history.messages,
        HumanMessage(content=question),
    ]
    model = ChatTongyi(model=config.chat_model_name)
    chunks = []
    for response in model.stream(messages):
        content = response.content
        if isinstance(content, str) and content:
            chunks.append(content)
            yield content
    if not chunks:
        raise RuntimeError("DashScope 没有返回回答")
    history.add_messages(
        [HumanMessage(content=question), AIMessage(content="".join(chunks))]
    )


def stream_size_answer(question: str, session_id: str):
    yield from stream_answer(question, session_id, use_size_guide=True)
