import subprocess
import os

def convert_doc_to_docx(input_doc_path:str):
    """
    使用 LibreOffice 将 .doc 文件转换为 .docx。
    :param input_doc_path: 输入 .doc 文件路径
    :return: 输出 .docx 文件路径
    """
    # 生成输出路径（替换扩展名为 .docx）
    output_docx_path = os.path.splitext(input_doc_path)[0] + '.docx'
    
    # 构建命令
    command = [
        "soffice",
        '--headless',  # 无界面模式
        '--convert-to', 'docx',
        input_doc_path,
        '--outdir', os.path.dirname(output_docx_path)  # 输出到同一目录
    ]
    
    try:
        # 执行命令
        subprocess.run(command, check=True, capture_output=True, text=True)
        # LibreOffice 会生成同名 .docx 文件，我们重命名如果需要
        generated_file = os.path.join(os.path.dirname(output_docx_path), os.path.basename(output_docx_path))
        if os.path.exists(generated_file):
            print(f"转换成功：{generated_file}")
        else:
            print("转换失败：未找到输出文件")
        return generated_file
    except subprocess.CalledProcessError as e:
        print(f"转换失败：{e.stderr}")
        return None