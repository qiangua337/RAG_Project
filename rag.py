# rag.py
from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory

from file_history_store import get_history
from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_core.documents import Document



def print_prompt(prompt):
    print("="*20)
    print(prompt.to_string())
    print("="*20)
    return prompt


class RagService(object):
    def __init__(self):
        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=config.embedding_model_name)
        )

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "以我提供的已知参考资料为主，简洁和专业的回答用户问题。参考资料:{context}。"),
                MessagesPlaceholder(variable_name="history"),
                ("user", "请回答用户提问: {input}")
            ]
        )

        self.chat_model = ChatTongyi(model=config.chat_model_name)
        self.chain = self.__get_chain()

    def __get_chain(self):
        retriever = self.vector_service.get_retriever()

        def format_document(docs: list[Document]):
            if not docs:
                return "无相关参考资料"
            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段: {doc.page_content}\n文档元数据: {doc.metadata}\n\n"
            return formatted_str

        chain = (
            {
                "input": itemgetter("input"),
                "history": itemgetter("history"),
                "context": itemgetter("input") | retriever | format_document
            }
            | self.prompt_template
            | print_prompt
            | self.chat_model
            | StrOutputParser()
        )

        return RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history"
        )

    def ask(self, question: str, session_id: str = "default") -> str:
        return self.chain.invoke(
            {"input": question},
            config={"configurable": {"session_id": session_id}},
        )


if __name__ == '__main__':
    service = RagService()
    session_id = input("今天是什么天气：").strip() or "default"
    while True:
        question = input("问题（输入 exit 结束）：").strip()
        if question.lower() == "exit":
            break
        if question:
            print(service.ask(question, session_id))
