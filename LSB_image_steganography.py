#!/usr/bin/env python
# coding:UTF-8
"""LSB_image_steganography.py
使用 python -m PyInstaller -F LSB_image_steganography.py 发布EXE后，名字可自定义
自定义名字后，命令中使用自定义的名字来启动脚本

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
"""


from PIL import Image
import numpy as np
import docopt
import sys
import base64


class SteganographyException(Exception):
    pass


class LSBSteg():
    def __init__(self, im):
        self.image = im
        self.height, self.width, self.nbchannels = im.shape
        self.size = self.width * self.height

        self.maskONEValues = [1, 2, 4, 8, 16, 32, 64, 128]
        # Mask used to put one ex:1->00000001, 2->00000010 .. associated with OR bitwise
        self.maskONE = self.maskONEValues.pop(0)  # Will be used to do bitwise operations

        self.maskZEROValues = [254, 253, 251, 247, 239, 223, 191, 127]
        # Mak used to put zero ex:254->11111110, 253->11111101 .. associated with AND bitwise
        self.maskZERO = self.maskZEROValues.pop(0)

        self.curwidth = 0  # Current width position
        self.curheight = 0  # Current height position
        self.curchan = 0  # Current channel position

    def put_binary_value(self, bits):  # Put the bits in the image
        for c in bits:
            val = list(self.image[self.curheight, self.curwidth])  # Get the pixel value as a list
            if int(c) == 1:
                val[self.curchan] = int(val[self.curchan]) | self.maskONE  # OR with maskONE
            else:
                val[self.curchan] = int(val[self.curchan]) & self.maskZERO  # AND with maskZERO

            self.image[self.curheight, self.curwidth] = tuple(val)
            self.next_slot()  # Move "cursor" to the next space

    def next_slot(self):  # Move to the next slot were information can be taken or put
        if self.curchan == self.nbchannels - 1:  # Next Space is the following channel
            self.curchan = 0
            if self.curwidth == self.width - 1:  # Or the first channel of the next pixel of the same line
                self.curwidth = 0
                if self.curheight == self.height - 1:  # Or the first channel of the first pixel of the next line
                    self.curheight = 0
                    if self.maskONE == 128:  # Mask 1000000, so the last mask
                        raise SteganographyException("No available slot remaining (image filled)")
                    else:  # Or instead of using the first bit start using the second and so on..
                        self.maskONE = self.maskONEValues.pop(0)
                        self.maskZERO = self.maskZEROValues.pop(0)
                else:
                    self.curheight += 1
            else:
                self.curwidth += 1
        else:
            self.curchan += 1

    def read_bit(self):  # Read a single bit int the image
        val = self.image[self.curheight, self.curwidth][self.curchan]
        val = int(val) & self.maskONE
        self.next_slot()
        if val > 0:
            return "1"
        else:
            return "0"

    def read_byte(self):
        return self.read_bits(8)

    def read_bits(self, nb):  # Read the given number of bits
        bits = ""
        for i in range(nb):
            bits += self.read_bit()
        return bits

    def byteValue(self, val):
        return self.binary_value(val, 8)

    def binary_value(self, val, bitsize):  # Return the binary value of an int as a byte
        binval = bin(val)[2:]
        if len(binval) > bitsize:
            raise SteganographyException("binary value larger than the expected size")
        while len(binval) < bitsize:
            binval = "0" + binval
        return binval

    def encode_text(self, txt):
        l = len(txt)
        binl = self.binary_value(l, 16)  # Length coded on 2 bytes so the text size can be up to 65536 bytes long
        self.put_binary_value(binl)  # Put text length coded on 4 bytes
        for char in txt:  # And put all the chars
            c = ord(char)
            self.put_binary_value(self.byteValue(c))
        return self.image

    def decode_text(self):
        ls = self.read_bits(16)  # Read the text size in bytes
        l = int(ls, 2)
        i = 0
        unhideTxt = ""
        while i < l:  # Read all bytes of the text
            tmp = self.read_byte()  # So one byte
            i += 1
            unhideTxt += chr(int(tmp, 2))  # Every chars concatenated to str
        return unhideTxt

    def encode_image(self, imtohide):
        w = imtohide.width
        h = imtohide.height
        if self.width * self.height * self.nbchannels < w * h * imtohide.channels:
            raise SteganographyException("Carrier image not big enough to hold all the datas to steganography")
        binw = self.binary_value(w, 16)  # Width coded on to byte so width up to 65536
        binh = self.binary_value(h, 16)
        self.put_binary_value(binw)  # Put width
        self.put_binary_value(binh)  # Put height
        for h in range(imtohide.height):  # Iterate the hole image to put every pixel values
            for w in range(imtohide.width):
                for chan in range(imtohide.channels):
                    val = imtohide[h, w][chan]
                    self.put_binary_value(self.byteValue(int(val)))
        return self.image

    def decode_image(self):
        width = int(self.read_bits(16), 2)  # Read 16bits and convert it in int
        height = int(self.read_bits(16), 2)
        unhideimg = np.zeros((height, width, 3), np.uint8)  # Create an image in which we will put all the pixels read
        for h in range(height):
            for w in range(width):
                for chan in range(unhideimg.shape[2]):
                    val = list(unhideimg[h, w])
                    val[chan] = int(self.read_byte(), 2)  # Read the value
                    unhideimg[h, w] = tuple(val)
        return unhideimg

    def encode_binary(self, data):
        l = len(data)
        if self.width * self.height * self.nbchannels < l + 64:
            raise SteganographyException("Carrier image not big enough to hold all the datas to steganography")
        self.put_binary_value(self.binary_value(l, 64))
        for byte in data:
            byte = byte if isinstance(byte, int) else ord(byte)  # Compat py2/py3
            self.put_binary_value(self.byteValue(byte))
        return self.image

    def decode_binary(self):
        l = int(self.read_bits(64), 2)
        output = b""
        for i in range(l):
            output += bytearray([int(self.read_byte(), 2)])
        return output


def main():
    try:
        args = docopt.docopt(__doc__, version="0.4")
    except docopt.DocoptExit as e:
        print(e)
        sys.exit(1)

    in_f = args["--in"]
    out_f = args.get("--out", None)

    if not in_f:
        print("Error: Missing required argument: -i <input>")
        print("Usage:")
        print("  LSB_image_steganography.py encode -i <input> -o <output> [-f <file>] [-d <data>]")
        print("  LSB_image_steganography.py decode -i <input> -o <output>")
        print("  LSB_image_steganography.py run -i <input>")
        sys.exit(1)

    try:
        # 使用 Pillow 读取图片
        try:
            pil_img = Image.open(in_f)
            pil_img = pil_img.convert('RGB')  # 确保是 RGB 格式
        except Exception as e:
            raise SteganographyException(f"Failed to load input image: {in_f}. Error: {str(e)}")

        # 转为 numpy 数组供 LSBSteg 使用
        in_img = np.array(pil_img)
    except Exception as e:
        print(f"Error loading image: {e}")
        sys.exit(1)

    steg = LSBSteg(in_img)
    lossy_formats = ["jpeg", "jpg"]

    if args['encode']:
        if not out_f:
            print("Error: Missing required argument: -o <output>")
            sys.exit(1)

        # 确保输出文件有 .png 扩展名
        if "." not in out_f:
            out_f = out_f + ".png"

        out_f_parts = out_f.rsplit(".", 1)
        if len(out_f_parts) == 2:
            base_name, out_ext = out_f_parts
            if out_ext.lower() in lossy_formats:
                out_f = base_name + ".png"
                print("Output file changed to PNG:", out_f)

        # 检查是否同时提供了 -f 和 -d 参数
        if args["--file"] and args["--data"]:
            print("Error: Cannot use both -f and -d options at the same time")
            sys.exit(1)

        # 检查是否至少提供了一个参数
        if not args["--file"] and not args["--data"]:
            print("Error: Must provide either -f (file) or -d (data) option")
            sys.exit(1)

        # 根据参数选择数据来源
        if args["--data"]:
            data = args["--data"].encode('utf-8')  # 直接获取命令行输入的文本数据并转为字节
            print(f"Encoding text data: {args['--data'][:50]}{'...' if len(args['--data']) > 50 else ''}")
        else:
            try:
                data = open(args["--file"], "rb").read()
                print(f"Encoding file: {args['--file']} ({len(data)} bytes)")
            except FileNotFoundError:
                print(f"Error: File not found: {args['--file']}")
                sys.exit(1)

        try:
            res = steg.encode_binary(data)

            # 使用 Pillow 保存图片
            result_img = Image.fromarray(res, 'RGB')
            result_img.save(out_f, 'PNG')
            print(f"Successfully encoded to {out_f}")
        except SteganographyException as e:
            print(f"Error: {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Error saving image: {e}")
            sys.exit(1)

    elif args["decode"]:
        if not out_f:
            print("Error: Missing required argument: -o <output>")
            sys.exit(1)

        try:
            raw = steg.decode_binary()
            with open(out_f, "wb") as f:
                f.write(raw)
            print(f"Successfully decoded to {out_f} ({len(raw)} bytes)")
        except Exception as e:
            print(f"Error decoding: {e}")
            sys.exit(1)

    elif args["run"]:
        try:
            print("Extracting and decoding data from image...")
            raw = steg.decode_binary()

            # Base64 解码
            try:
                decoded_data = base64.b64decode(raw).decode('utf-8')
                print(f"Successfully decoded base64 data ({len(decoded_data)} bytes)")
                print("-" * 50)
                print("Executing code...")
                print("-" * 50)

                # 执行解码后的 Python 代码
                exec(decoded_data)

            except Exception as e:
                print(f"Error decoding base64 data: {e}")
                print("Raw data extracted:", raw[:100], "...")
                sys.exit(1)

        except Exception as e:
            print(f"Error extracting or executing data: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
