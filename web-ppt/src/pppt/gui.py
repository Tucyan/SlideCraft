import sys
import json
import os
import PySimpleGUI as sg
from pppt import JsonToPptxExporter


def validate_json(json_str):
    try:
        json.loads(json_str)
        return True, ""
    except json.JSONDecodeError as e:
        return False, str(e)


def main():
    sg.theme("LightBlue")

    layout = [
        [sg.Text("JSON转PPTX工具", font=("Microsoft YaHei", 16), text_color="#1a1a1a")],
        [sg.Text("将AI生成的JSON内容粘贴到下方文本框中:", font=("Microsoft YaHei", 10))],
        [sg.Multiline(key="-JSON_INPUT-", font=("Consolas", 10), size=(80, 20), autoscroll=True)],
        [sg.Button("验证JSON", button_color=("#4CAF50", "#ffffff")), sg.Button("清空", button_color=("#f44336", "#ffffff"))],
        [sg.Text(key="-STATUS-", font=("Microsoft YaHei", 10), text_color="#666666")],
        [sg.HorizontalSeparator()],
        [sg.Text("输出设置:", font=("Microsoft YaHei", 10))],
        [sg.Text("文件名:"), sg.Input(key="-FILENAME-", default_text="output.pptx", size=(40, 1)), sg.Text(".pptx")],
        [sg.FolderBrowse("选择保存位置", key="-FOLDER-", target="-FOLDER-"), sg.Input(key="-FOLDER-", size=(40, 1), readonly=True)],
        [sg.Button("生成PPTX", button_color=("#2196F3", "#ffffff"), size=(15, 1), disabled=True), sg.Button("退出", button_color=("#9E9E9E", "#ffffff"))],
        [sg.Text(key="-PROGRESS-", font=("Microsoft YaHei", 10), text_color="#2196F3")],
    ]

    window = sg.Window("Web PPT - JSON转PPTX工具", layout, finalize=True)

    json_valid = False

    while True:
        event, values = window.read()

        if event in (None, "退出"):
            break

        elif event == "验证JSON":
            json_str = values["-JSON_INPUT-"].strip()
            if not json_str:
                window["-STATUS-"].update("请输入JSON内容！", text_color="#f44336")
                json_valid = False
            else:
                is_valid, error_msg = validate_json(json_str)
                if is_valid:
                    window["-STATUS-"].update("✓ JSON格式正确", text_color="#4CAF50")
                    json_valid = True
                    window["生成PPTX"].update(disabled=False)
                else:
                    window["-STATUS-"].update(f"✗ JSON格式错误: {error_msg}", text_color="#f44336")
                    json_valid = False
                    window["生成PPTX"].update(disabled=True)

        elif event == "清空":
            window["-JSON_INPUT-"].update("")
            window["-STATUS-"].update("")
            window["-PROGRESS-"].update("")
            json_valid = False
            window["生成PPTX"].update(disabled=True)

        elif event == "生成PPTX":
            json_str = values["-JSON_INPUT-"].strip()
            filename = values["-FILENAME-"].strip()
            folder = values["-FOLDER-"].strip()

            if not folder:
                folder = os.getcwd()

            if not filename.endswith(".pptx"):
                filename += ".pptx"

            output_path = os.path.join(folder, filename)

            try:
                window["-PROGRESS-"].update("正在生成PPTX...")
                window.refresh()

                doc = json.loads(json_str)
                exporter = JsonToPptxExporter(doc, output_path)
                exporter.run()

                window["-PROGRESS-"].update(f"✓ 生成成功！保存至: {output_path}", text_color="#4CAF50")

            except Exception as e:
                window["-PROGRESS-"].update(f"✗ 生成失败: {str(e)}", text_color="#f44336")

    window.close()


if __name__ == "__main__":
    main()
