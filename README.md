# LSB_steganography
此项目是二次开发的项目，源项目来源 https://github.com/RobinDavid/LSB-Steganography
本项目继承了源项目的所有功能，并可直接隐写数据至png图片；从png图片中提取base64加密数据并保存，或者提取base64加密数据并执行。适用于CTF或者渗透测试的小工具

## 安装
-----
```bash
pip install -r requirements.txt
# 可发布为EXE文件使用，也可直接使用源码
# 发布为EXE文件
python -m PyInstaller -F LSB_image_steganography.py
```

## 使用
-----

```bash
LSB_image_steganography.py
使用 python -m PyInstaller -F LSB_image_steganography.py 发布EXE后，名字可自定义
自定义名字后，命令中使用自定义的名字来启动脚本
通过有意限制，-f 和 -d 参数不能同时使用

Usage:
  LSB_image_steganography.py encode -i <input> -o <output> [-f <file>] [-d <data>]
  LSB_image_steganography.py decode -i <input> -o <output>
  LSB_image_steganography.py run -i <input>

Options:
  -h, --help                Show this help
  --version                 Show the version
  -f,--file=<file>          File to hide
  -d,--data=<data>          写入数据，用""包起来
  -i,--in=<input>           Input image (carrier)
  -o,--out=<output>         Output image (or extracted file)
  run                       配合 -i 参数对隐写在图片中的数据进行提取、base64解密、最后运行代码 -i不可省
```
Python module
-------------

Text encoding:

```python
#encoding
steg = LSBSteg(cv2.imread("my_image.png"))
img_encoded = steg.encode_text("my message")
cv2.imwrite("my_new_image.png", img_encoded)

#decoding
im = cv2.imread("my_new_image.png")
steg = LSBSteg(im)
print("Text value:",steg.decode_text())
```

Image steganography:

```python
#encoding
steg = LSBSteg(cv2.imread("carrier.png")
new_im = steg.encode_image(cv2.imread("secret_image.jpg"))
cv2.imwrite("new_image.png", new_im)

#decoding
steg = LSBSteg("new_image.png")
orig_im = steg.decode_image()
cv.SaveImage("recovered.png", orig_im)
```

Binary steganography:

```python
#encoding
steg = LSBSteg(cv2.imread("carrier.png"))
data = open("my_data.bin", "rb").read()
new_img = steg.encode_binary(data)
cv2.imwrite("new_image.png", new_img)

#decoding
steg = LSBSteg(cv2.imread("new_image.png"))
binary = steg.decode_binary()
with open("recovered.bin", "rb") as f:
    f.write(data)
    
```







