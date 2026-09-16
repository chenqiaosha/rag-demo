import os
from fastapi import FastAPI,UploadFile,File,HTTPException,Query
from pydantic import BaseModel
from rag_core import index_pdf,get_vectorstore,ask_question
from db import save_message,get_history

app = FastAPI(title="RAG知识库问答API")
vectorstore = None

class QuestionRequest(BaseModel):
    question:str
    session_id:str="default"
    
@app.get("/health")#.get 注册get路由
def health():
    return {"status":"ok"}

@app.post("/upload")
async def upload_pdf(file:UploadFile = File(...)):
    global vectorstore
    os.makedirs("data",exist_ok = True)
    file_path = f"data/{file.filename}"
    with open(file_path,"wb") as f:
        content = await file.read()
        f.write(content)        
        
    try:
        chunk_count = index_pdf(file_path)
        vectorstore = get_vectorstore()
        return {"message":f"索引成功，共{chunk_count}个片段","filename":file.filename}
    except Exception as e:
        raise HTTPException(status_code= 500,detail = str(e))
    
@app.get("/files")
def list_files():
    data_dir = "data"
    if not os.path.exists(data_dir):
        return {"files": []}
    files = [f for f in os.listdir(data_dir) if f.endswith(".pdf")]
    return {"files": files}
    
@app.post("/chat")
def chat(req:QuestionRequest):
    global vectorstore
    if vectorstore is None:
        vectorstore = get_vectorstore()
    try:
        save_message(req.session_id,"user",req.question)
        answer,sources = ask_question(req.question,vectorstore)
        save_message(req.session_id,"assistant",answer,",".join(sources))   
        return {"answer":answer,"sources":sources}
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))

@app.get("/history/{session_id}")
def history(session_id:str):
    return get_history(session_id)



@app.delete("/delete")
def delete_document(filename: str = Query(..., description="要删除的文件名")):
    import time
    try:
        vectorstore = get_vectorstore()
        collection = vectorstore._collection

        # 1. 查出所有向量
        all_data = collection.get(include=["metadatas"])

        # 2. 过滤出 source 里包含该文件名的向量 id
        ids_to_delete = []
        for i, metadata in enumerate(all_data["metadatas"]):
            if metadata and filename in metadata.get("source", ""):
                ids_to_delete.append(all_data["ids"][i])

        # 3. 按 id 删除向量
        if ids_to_delete:
            collection.delete(ids=ids_to_delete)

        # 4. 等待句柄释放
        time.sleep(0.5)

        # 5. 尝试删除本地 PDF，被占用就跳过，不报错
        file_path = f"data/{filename}"
        file_deleted = False
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                file_deleted = True
            except PermissionError:
                file_deleted = False

        msg = f"成功删除 {filename}，共清理 {len(ids_to_delete)} 个向量片段"
        if not file_deleted and os.path.exists(file_path):
            msg += "。注意：PDF 文件被占用，未删除，请关闭占用程序后手动删除"

        return {"message": msg}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))