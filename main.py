import os
import requests
from flask import Flask, request, jsonify
from pdf2image import convert_from_bytes
import io
import base64

app = Flask(__name__)

# 这是一个简单的接口，钉钉会向这个地址发送请求
@app.route('/convert', methods=['POST'])
def convert_pdf():
    try:
        # 1. 从钉钉获取 PDF 文件的下载链接
        data = request.json
        pdf_url = data.get('file_url')
        
        if not pdf_url:
            return jsonify({"success": False, "message": "没有收到文件链接"}), 400

        # 2. 下载 PDF 文件
        print(f"正在下载: {pdf_url}")
        response = requests.get(pdf_url)
        if response.status_code != 200:
            return jsonify({"success": False, "message": "下载文件失败"}), 400

        # 3. 将 PDF 转换为图片
        # 注意：这里我们只转换第一页作为演示，或者合并所有页
        # 为了生成"长图"，我们需要把每一页拼起来，这里简化处理：返回第一页的高清图
        # 如果需要真正的长图拼接，代码会复杂很多，这里先实现单页转换
        images = convert_from_bytes(response.content, dpi=200)
        
        if not images:
            return jsonify({"success": False, "message": "PDF内容为空"}), 400

        # 4. 将图片转换为 Base64 格式 (这样钉钉可以直接显示，不用额外上传图床)
        # 取第一页
        img_byte_arr = io.BytesIO()
        images[0].save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        # 编码为 base64
        img_base64 = base64.b64encode(img_byte_arr).decode('utf-8')
        
        # 5. 返回结果给钉钉
        # 钉钉多维表支持直接显示 base64 图片，或者你可以上传到阿里云OSS后返回URL
        # 这里我们返回 base64 数据，并在钉钉里通过公式处理显示
        return jsonify({
            "success": True, 
            "image_data": f"data:image/png;base64,{img_base64}",
            "message": "转换成功"
        })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/')
def hello():
    return "PDF转换服务正在运行！"

# 这里的 port 是 Render 平台要求的
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
