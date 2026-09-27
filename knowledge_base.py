"""
知识库基础流程

"""
import os
import config_data as config
import hashlib
from langchain_chroma import Chroma
from langchain_community.embeddings import  DashScopeEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from datetime import datetime

def check_md5(md5_str:str):
    #检查传入的md5字符串是否已经被处理过了
    #return False表示未处理过, return True表示已处理过
    if not os.path.exists(config.md5_path):
        #代表不存在
        open(config.md5_path, "w" ,encoding="utf-8").close()
        return False
    else:
        for line in open(config.md5_path, "r" ,encoding="utf-8").readlines():
            line = line.strip()     #处理字符前后的空格和回车
            if line == md5_str:
                return True
        return False



def save_md5(md5_str:str):
    #将传入的md5字符串记录到文件内保存
    with open(config.md5_path, "a" ,encoding="utf-8") as f:
        f.write(md5_str + "\n")



def get_string_md5(input_str:str , encoding="utf-8"):
    #将传入的字符串转换为md5值

    #将字符串转化为bytes字节数据
    input_str = input_str.encode(encoding)

    #创建md5对象
    md5_obj = hashlib.md5()       #得到md5对象
    md5_obj.update(input_str)     #更新内容
    return md5_obj.hexdigest()     #返回得到更新的md5的十六进制字符串




class KnonledgeBaseService(object):
    def __init__(self):
        #如果文件夹不存在则创建，存在则忽略
        os.makedirs(config.persist_directory, exist_ok=True)
        self.chroma = Chroma(
            collection_name=config.collection_name ,       #数据库表名
            embedding_function=DashScopeEmbeddings(model="text-embedding-v4"),
            persist_directory=config.persist_directory    #数据库本地存储文件夹

        )   #向量存储对象
        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size = config.chunk_size,   #分割后的段最大长度
            chunk_overlap = config.chunk_overlap,  #分割后段落之间的重叠部分
            separators = config.separators,     #自然段落划分的符号
            length_function = len     #计算长度的函数
        )  #分段器对象

    def upload_by_str(self,data, filename):
        #将传入的字符串进行吸纳功利化,传入向量数据库
        #得到传入字符串的MD5
        md5_hex = get_string_md5(data)

        if check_md5(md5_hex):
            print("文件已处理过，不再处理")
            return "文件已处理过，不再处理"

        if len(data) > config.max_split_chae_number:
            knowledge_chunks : list[str] = self.spliter.split_text(data)
        else:
            knowledge_chunks : list[str] = [data]

        metadata = {
            "source": filename,
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator" : "牵挂"
        }

        self.chroma.add_texts(
            knowledge_chunks,
            metadata=[metadata for _ in knowledge_chunks]

        )

        #
        save_md5(md5_hex)

        return  "上传成功"







if __name__ == "__main__":
    service = KnonledgeBaseService()
    r = service.upload_by_str("周杰伦","test.file")
    print(r)

