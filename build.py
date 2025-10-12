# build.py
import PyInstaller.__main__


def build_app():
    PyInstaller.__main__.run([
        'main.py',
        '--name=AutoPlayer',
        '--windowed',
        '--onefile',
        '--add-data=dist;dist',  # Vue3 构建文件
        '--icon=favicon.ico',
        '--clean',
        '--noconfirm'
    ])


if __name__ == '__main__':
    build_app()
