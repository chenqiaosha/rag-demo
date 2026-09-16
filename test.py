print("=== 脚本开始运行 ===")

from rag_core import get_vectorstore

print("=== 导入成功 ===")

vectorstore = get_vectorstore()
print("=== 拿到 vectorstore ===")

collection = vectorstore._collection
print("=== 拿到 collection ===")

all_data = collection.get(include=["metadatas"])
print("总向量数:", len(all_data["ids"]))

for i, metadata in enumerate(all_data["metadatas"][:10]):
    print(i, "->", metadata)

print("=== 脚本结束 ===")