# build.py
import PyInstaller.__main__
import os
import shutil

build_target_name = 'MidiAutoBot'


def copy_to_target(dir_path):
    if os.path.exists(dir_path):
        target_path = os.path.join('dist', build_target_name, dir_path)
        if os.path.exists(target_path):
            shutil.rmtree(target_path)
        shutil.copytree(dir_path, target_path)


def build_app():
    PyInstaller.__main__.run([
        'backend/main.py',
        '--name=' + build_target_name,
        '--windowed',
        '--onedir',  # 打包成文件夹 或使用 --onefile 打包成exe文件
        '--add-data=dist/html;dist',  # 包含前端构建文件
        '--add-data=assets;assets',  # 包含静态资源（如有）
        '--icon=favicon.ico',
        '--clean',
        '--noconfirm',
        '--uac-admin',  # 添加此参数请求管理员权限
    ])
    # 复制 midis 文件夹到目标目录
    copy_to_target('midis')
    # 复制 config 文件夹到目标目录
    copy_to_target('config')
    # 复制 db 文件夹到目标目录
    copy_to_target('db')


if __name__ == '__main__':
    build_app()
