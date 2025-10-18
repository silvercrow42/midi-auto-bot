# build.py
import PyInstaller.__main__


def build_app():
    PyInstaller.__main__.run([
        'main.py',
        '--name=MidiAutoBot',
        '--windowed',
        '--onedir',  # 打包成文件夹 或使用 --onefile 打包成exe文件
        '--add-data=dist;dist',  # 包含前端构建文件
        '--add-data=assets;assets',  # 包含静态资源（如有）
        '--icon=favicon.ico',
        '--clean',
        '--noconfirm',
        '--uac-admin',  # 添加此参数请求管理员权限
    ])


if __name__ == '__main__':
    build_app()
