import re
import utils
import decimal
import codecs
import warnings
import filters
from utils import PdfStreamError
from utils import readNonWhitespace, skipOverComment
from utils import u_, RC4_encrypt


ObjectPrefix = '/<[tf(n%'
NumberSigns = '+-'
IndirectPattern = re.compile(r"[+-]?(\d+)\s+(\d+)\s+R[^a-zA-Z]")


def readObject(stream, pdf):
    tok = stream.read(1)
    stream.seek(-1, 1) # reset to start
    idx = ObjectPrefix.find(tok)
    if idx == 0:
        # name object
        return NameObject.readFromStream(stream, pdf)
    elif idx == 1:
        # hexadecimal string OR dictionary
        peek = stream.read(2)
        stream.seek(-2, 1) # reset to start
        if peek == '<<':
            return DictionaryObject.readFromStream(stream, pdf)
        else:
            return readHexStringFromStream(stream)
    elif idx == 2:
        # array object
        return ArrayObject.readFromStream(stream, pdf)
    elif idx == 3 or idx == 4:
        # boolean object
        return BooleanObject.readFromStream(stream)
    elif idx == 5:
        # string object
        return readStringFromStream(stream)
    elif idx == 6:
        # null object
        return NullObject.readFromStream(stream)
    elif idx == 7:
        # comment
        while tok not in ('\r', '\n'):
            tok = stream.read(1)
            # Prevents an infinite loop by raising an error if the stream is at
            # the EOF
            if len(tok) <= 0:
                raise PdfStreamError("File ended unexpectedly.")
        tok = readNonWhitespace(stream)
        stream.seek(-1, 1)
        return readObject(stream, pdf)
    else:
        # number object OR indirect reference
        peek = stream.read(20)
        stream.seek(-len(peek), 1) # reset to start
        if IndirectPattern.match(peek) != None:
            return IndirectObject.readFromStream(stream, pdf)
        else:
            return NumberObject.readFromStream(stream)


class PdfObject(object):
    def getObject(self):
        """Resolves indirect references."""
        return self


class NullObject(PdfObject):
    def writeToStream(self, stream, encryption_key):
        stream.write("null")

    def readFromStream(stream):
        nulltxt = stream.read(4)
        if nulltxt != "null":
            raise utils.PdfReadError("Could not read Null object")
        return NullObject()
    readFromStream = staticmethod(readFromStream)


class BooleanObject(PdfObject):
    def __init__(self, value):
        self.value = value

    def writeToStream(self, stream, encryption_key):
        if self.value:
            stream.write("true")
        else:
            stream.write("false")

    def readFromStream(stream):
        word = stream.read(4)
        if word == "true":
            return BooleanObject(True)
        elif word == "fals":
            stream.read(1)
            return BooleanObject(False)
        else:
            raise utils.PdfReadError('Could not read Boolean object')
    readFromStream = staticmethod(readFromStream)


class ArrayObject(list, PdfObject):
    def writeToStream(self, stream, encryption_key):
        stream.write("[")
        for data in self:
            stream.write(" ")
            data.writeToStream(stream, encryption_key)
        stream.write(" ]")

    def readFromStream(stream, pdf):
        arr = ArrayObject()
        tmp = stream.read(1)
        if tmp != "[":
            raise utils.PdfReadError("Could not read array")
        while True:
            # skip leading whitespace
            tok = stream.read(1)
            while tok.isspace():
                tok = stream.read(1)
            stream.seek(-1, 1)
            # check for array ending
            peekahead = stream.read(1)
            if peekahead == "]":
                break
            stream.seek(-1, 1)
            # read and append obj
            arr.append(readObject(stream, pdf))
        return arr
    readFromStream = staticmethod(readFromStream)


class IndirectObject(PdfObject):
    def __init__(self, idnum, generation, pdf):
        self.idnum = idnum
        self.generation = generation
        self.pdf = pdf

    def getObject(self):
        return self.pdf.getObject(self).getObject()

    def __repr__(self):
        return "IndirectObject(%r, %r)" % (self.idnum, self.generation)

    def __eq__(self, other):
        return (
            other != None and
            isinstance(other, IndirectObject) and
            self.idnum == other.idnum and
            self.generation == other.generation and
            self.pdf is other.pdf
            )

    def __ne__(self, other):
        return not self.__eq__(other)

    def writeToStream(self, stream, encryption_key):
        stream.write("%s %s R" % (self.idnum, self.generation))

    def readFromStream(stream, pdf):
        idnum = ""
        while True:
            tok = stream.read(1)
            if not tok:
                # stream has truncated prematurely
                raise PdfStreamError("Stream has ended unexpectedly")
            if tok.isspace():
                break
            idnum += tok
        generation = ""
        while True:
            tok = stream.read(1)
            if not tok:
                # stream has truncated prematurely
                raise PdfStreamError("Stream has ended unexpectedly")
            if tok.isspace():
                if not generation:
                    continue
                break
            generation += tok
        r = readNonWhitespace(stream)
        if r != "R":
            raise utils.PdfReadError("Error reading indirect object reference at byte %s" % utils.hexStr(stream.tell()))
        return IndirectObject(int(idnum), int(generation), pdf)
    readFromStream = staticmethod(readFromStream)


class FloatObject(decimal.Decimal, PdfObject):
    def __new__(cls, value="0", context=None):
        try:
            return decimal.Decimal.__new__(cls, value, context)
        except:
            return decimal.Decimal.__new__(cls, str(value))

    def __repr__(self):
        if self == self.to_integral():
            return str(self.quantize(decimal.Decimal(1)))
        else:
            # Standard formatting adds useless extraneous zeros.
            o = "%.5f" % self
            # Remove the zeros.
            while o and o[-1] == '0':
                o = o[:-1]
            return o

    def as_numeric(self):
        return float(repr(self))

    def writeToStream(self, stream, encryption_key):
        stream.write(repr(self))


class NumberObject(int, PdfObject):
    NumberPattern = re.compile('[^+-.0-9]')
    ByteDot = "."

    def __new__(cls, value):
        val = int(value)
        try:
            return int.__new__(cls, val)
        except OverflowError:
            return int.__new__(cls, 0)

    def as_numeric(self):
        return int(repr(self))

    def writeToStream(self, stream, encryption_key):
        stream.write(repr(self))

    def readFromStream(stream):
        num = utils.readUntilRegex(stream, NumberObject.NumberPattern)
        if num.find(NumberObject.ByteDot) != -1:
            return FloatObject(num)
        else:
            return NumberObject(num)
    readFromStream = staticmethod(readFromStream)


##
# Given a string (either a "str" or "unicode"), create a ByteStringObject or a
# TextStringObject to represent the string.
def createStringObject(string):
    if isinstance(string, utils.string_type):
        return TextStringObject(string)
    elif isinstance(string, utils.bytes_type):
        try:
            if string.startswith(codecs.BOM_UTF16_BE):
                retval = TextStringObject(string.decode("utf-16"))
                retval.autodetect_utf16 = True
                return retval
            else:
                # This is probably a big performance hit here, but we need to
                # convert string objects into the text/unicode-aware version if
                # possible... and the only way to check if that's possible is
                # to try.  Some strings are strings, some are just byte arrays.
                retval = TextStringObject(decode_pdfdocencoding(string))
                retval.autodetect_pdfdocencoding = True
                return retval
        except UnicodeDecodeError:
            return ByteStringObject(string)
    else:
        raise TypeError("createStringObject should have str or unicode arg")


def readHexStringFromStream(stream):
    stream.read(1)
    txt = ""
    x = ""
    while True:
        tok = readNonWhitespace(stream)
        if not tok:
            # stream has truncated prematurely
            raise PdfStreamError("Stream has ended unexpectedly")
        if tok == ">":
            break
        x += tok
        if len(x) == 2:
            txt += chr(int(x, base=16))
            x = ""
    if len(x) == 1:
        x += "0"
    if len(x) == 2:
        txt += chr(int(x, base=16))
    return createStringObject(txt)


def readStringFromStream(stream):
    tok = stream.read(1)
    parens = 1
    txt = ""
    while True:
        tok = stream.read(1)
        if not tok:
            # stream has truncated prematurely
            raise PdfStreamError("Stream has ended unexpectedly")
        if tok == "(":
            parens += 1
        elif tok == ")":
            parens -= 1
            if parens == 0:
                break
        elif tok == "\\":
            tok = stream.read(1)
            ESCAPE_DICT = {"n" : "\n",
                           "r" : "\r",
                           "t" : "\t",
                           "b" : "\b",
                           "f" : "\f",
                           "c" : "\c",
                           "(" : "(",
                           ")" : ")",
                           #"/" : "/",
                           "\\" : "\\",
                           " " : " ",
                           "/" : "/",
                           "%" : "%",
                           "<" : "<",
                           ">" : ">",
                           "[" : "[",
                           "]" : "]",
                           "#" : "#",
                           "_" : "_",
                           "&" : "&",
                           '$' : '$',
                           }
            try:
                tok = ESCAPE_DICT[tok]
            except KeyError:
                if tok.isdigit():
                    # "The number ddd may consist of one, two, or three
                    # octal digits; high-order overflow shall be ignored.
                    # Three octal digits shall be used, with leading zeros
                    # as needed, if the next character of the string is also
                    # a digit." (PDF reference 7.3.4.2, p 16)
                    for i in range(2):
                        ntok = stream.read(1)
                        if ntok.isdigit():
                            tok += ntok
                        else:
                            break
                    tok = chr(int(tok, base=8))
                elif tok in "\n\r":
                    # This case is  hit when a backslash followed by a line
                    # break occurs.  If it's a multi-char EOL, consume the
                    # second character:
                    tok = stream.read(1)
                    if not tok in "\n\r":
                        stream.seek(-1, 1)
                    # Then don't add anything to the actual string, since this
                    # line break was escaped:
                    tok = ''
                else:
                    raise utils.PdfReadError(r"Unexpected escaped string: %s" % tok)
        txt += tok
    return createStringObject(txt)


##
# Represents a string object where the text encoding could not be determined.
# This occurs quite often, as the PDF spec doesn't provide an alternate way to
# represent strings -- for example, the encryption data stored in files (like
# /O) is clearly not text, but is still stored in a "String" object.
class ByteStringObject(utils.bytes_type, PdfObject):

    ##
    # For compatibility with TextStringObject.original_bytes.  This method
    # returns self.
    original_bytes = property(lambda self: self)

    def writeToStream(self, stream, encryption_key):
        bytearr = self
        if encryption_key:
            bytearr = RC4_encrypt(encryption_key, bytearr)
        stream.write("<")
        stream.write(utils.hexencode(bytearr))
        stream.write(">")


##
# Represents a string object that has been decoded into a real unicode string.
# If read from a PDF document, this string appeared to match the
# PDFDocEncoding, or contained a UTF-16BE BOM mark to cause UTF-16 decoding to
# occur.
class TextStringObject(utils.string_type, PdfObject):
    autodetect_pdfdocencoding = False
    autodetect_utf16 = False

    ##
    # It is occasionally possible that a text string object gets created where
    # a byte string object was expected due to the autodetection mechanism --
    # if that occurs, this "original_bytes" property can be used to
    # back-calculate what the original encoded bytes were.
    original_bytes = property(lambda self: self.get_original_bytes())

    def get_original_bytes(self):
        # We're a text string object, but the library is trying to get our raw
        # bytes.  This can happen if we auto-detected this string as text, but
        # we were wrong.  It's pretty common.  Return the original bytes that
        # would have been used to create this object, based upon the autodetect
        # method.
        if self.autodetect_utf16:
            return codecs.BOM_UTF16_BE + self.encode("utf-16be")
        elif self.autodetect_pdfdocencoding:
            return encode_pdfdocencoding(self)
        else:
            raise Exception("no information about original bytes")

    def writeToStream(self, stream, encryption_key):
        # Try to write the string out as a PDFDocEncoding encoded string.  It's
        # nicer to look at in the PDF file.  Sadly, we take a performance hit
        # here for trying...
        try:
            bytearr = encode_pdfdocencoding(self)
        except UnicodeEncodeError:
            bytearr = codecs.BOM_UTF16_BE + self.encode("utf-16be")
        if encryption_key:
            bytearr = RC4_encrypt(encryption_key, bytearr)
            obj = ByteStringObject(bytearr)
            obj.writeToStream(stream, None)
        else:
            stream.write("(")
            for c in bytearr:
                if not c.isalnum() and c != ' ':
                    stream.write("\\%03o" % ord(c))
                else:
                    stream.write(c)
            stream.write(")")


class NameObject(str, PdfObject):
    delimiterPattern = re.compile(r"\s+|[\(\)<>\[\]{}/%]")
    surfix = "/"

    def writeToStream(self, stream, encryption_key):
        stream.write(self)

    def readFromStream(stream, pdf):
        debug = False
        if debug: print((stream.tell()))
        name = stream.read(1)
        if name != NameObject.surfix:
            raise utils.PdfReadError("name read error")
        name += utils.readUntilRegex(stream, NameObject.delimiterPattern,
            ignore_eof=True)
        if debug: print(name)
        try:
            return NameObject(name.decode('utf-8'))
        except (UnicodeEncodeError, UnicodeDecodeError) as e:
            # Name objects should represent irregular characters
            # with a '#' followed by the symbol's hex number
            if not pdf.strict:
                warnings.warn("Illegal character in Name Object", utils.PdfReadWarning)
                return NameObject(name)
            else:
                raise utils.PdfReadError("Illegal character in Name Object")

    readFromStream = staticmethod(readFromStream)


class DictionaryObject(dict, PdfObject):
    def raw_get(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        if not isinstance(key, PdfObject):
            raise ValueError("key must be PdfObject")
        if not isinstance(value, PdfObject):
            raise ValueError("value must be PdfObject")
        return dict.__setitem__(self, key, value)

    def setdefault(self, key, value=None):
        if not isinstance(key, PdfObject):
            raise ValueError("key must be PdfObject")
        if not isinstance(value, PdfObject):
            raise ValueError("value must be PdfObject")
        return dict.setdefault(self, key, value)

    # def __getitem__(self, key):
    #     return dict.__getitem__(self, key).getObject()

    ##
    # Retrieves XMP (Extensible Metadata Platform) data relevant to the
    # this object, if available.
    # <p>
    # Stability: Added in v1.12, will exist for all future v1.x releases.
    # @return Returns a {@link #xmp.XmpInformation XmlInformation} instance
    # that can be used to access XMP metadata from the document.  Can also
    # return None if no metadata was found on the document root.
    def getXmpMetadata(self):
        metadata = self.get("/Metadata", None)
        if metadata == None:
            return None
        metadata = metadata.getObject()
        import xmp
        if not isinstance(metadata, xmp.XmpInformation):
            metadata = xmp.XmpInformation(metadata)
            self[NameObject("/Metadata")] = metadata
        return metadata

    ##
    # Read-only property that accesses the {@link
    # #DictionaryObject.getXmpData getXmpData} function.
    # <p>
    # Stability: Added in v1.12, will exist for all future v1.x releases.
    xmpMetadata = property(lambda self: self.getXmpMetadata(), None, None)

    def writeToStream(self, stream, encryption_key):
        stream.write("<<\n")
        for key, value in list(self.items()):
            key.writeToStream(stream, encryption_key)
            stream.write(" ")
            value.writeToStream(stream, encryption_key)
            stream.write("\n")
        stream.write(">>")

    def readFromStream(stream, pdf):
        debug = False
        tmp = stream.read(2)
        if tmp != "<<":
            raise utils.PdfReadError("Dictionary read error at byte %s: stream must begin with '<<'" % utils.hexStr(stream.tell()))
        data = {}
        while True:
            tok = readNonWhitespace(stream)
            if tok == '\x00':
                continue
            elif tok == '%':
                stream.seek(-1, 1)
                skipOverComment(stream)
                continue
            if not tok:
                # stream has truncated prematurely
                raise PdfStreamError("Stream has ended unexpectedly")

            if debug: print(("Tok:", tok))
            if tok == ">":
                stream.read(1)
                break
            stream.seek(-1, 1)
            key = readObject(stream, pdf)
            tok = readNonWhitespace(stream)
            stream.seek(-1, 1)
            value = readObject(stream, pdf)
            if not data.get(key):
                data[key] = value
            elif pdf.strict:
                # multiple definitions of key not permitted
                raise utils.PdfReadError("Multiple definitions in dictionary at byte %s for key %s" \
                                           % (utils.hexStr(stream.tell()), key))
            else:
                warnings.warn("Multiple definitions in dictionary at byte %s for key %s" \
                                           % (utils.hexStr(stream.tell()), key), utils.PdfReadWarning)

        pos = stream.tell()
        s = readNonWhitespace(stream)
        if s == 's' and stream.read(5) == 'tream':
            eol = stream.read(1)
            # odd PDF file output has spaces after 'stream' keyword but before EOL.
            # patch provided by Danial Sandler
            while eol == ' ':
                eol = stream.read(1)
            assert eol in ("\n", "\r")
            if eol == "\r":
                # read \n after
                if stream.read(1)  != '\n':
                    stream.seek(-1, 1)
            # this is a stream object, not a dictionary
            assert "/Length" in data
            length = data["/Length"]
            if debug: print(data)
            if isinstance(length, IndirectObject):
                t = stream.tell()
                length = pdf.getObject(length)
                stream.seek(t, 0)
            data["__streamdata__"] = stream.read(length)
            if debug: print("here")
            #if debug: print(binascii.hexlify(data["__streamdata__"]))
            e = readNonWhitespace(stream)
            ndstream = stream.read(8)
            if (e + ndstream) != "endstream":
                # (sigh) - the odd PDF file has a length that is too long, so
                # we need to read backwards to find the "endstream" ending.
                # ReportLab (unknown version) generates files with this bug,
                # and Python users into PDF files tend to be our audience.
                # we need to do this to correct the streamdata and chop off
                # an extra character.
                pos = stream.tell()
                stream.seek(-10, 1)
                end = stream.read(9)
                if end == "endstream":
                    # we found it by looking back one character further.
                    data["__streamdata__"] = data["__streamdata__"][:-1]
                else:
                    stream.seek(pos, 0)
                    raise utils.PdfReadError("Unable to find 'endstream' marker after stream at byte %s." % utils.hexStr(stream.tell()))
        else:
            stream.seek(pos, 0)
        if "__streamdata__" in data:
            return StreamObject.initializeFromDictionary(data)
        else:
            retval = DictionaryObject()
            retval.update(data)
            return retval
    readFromStream = staticmethod(readFromStream)


class TreeObject(DictionaryObject):
    def __init__(self):
        DictionaryObject.__init__(self)

    def hasChildren(self):
        return '/First' in self

    def __iter__(self):
        return self.children()

    def children(self):
        if not self.hasChildren():
            raise StopIteration

        child = self['/First']
        while True:
            yield child
            if child == self['/Last']:
                raise StopIteration
            child = child['/Next']

    def addChild(self, child, pdf):
        childObj = child.getObject()
        child = pdf.getReference(childObj)
        assert isinstance(child, IndirectObject)

        if '/First' not in self:
            self[NameObject('/First')] = child
            self[NameObject('/Count')] = NumberObject(0)
            prev = None
        else:
            prev = self['/Last']

        self[NameObject('/Last')] = child
        self[NameObject('/Count')] = NumberObject(self[NameObject('/Count')] + 1)

        if prev:
            prevRef = pdf.getReference(prev)
            assert isinstance(prevRef, IndirectObject)
            childObj[NameObject('/Prev')] = prevRef
            prev[NameObject('/Next')] = child

        parentRef = pdf.getReference(self)
        assert isinstance(parentRef, IndirectObject)
        childObj[NameObject('/Parent')] = parentRef

    def removeChild(self, child):
        childObj = child.getObject()

        if NameObject('/Parent') not in childObj:
            raise ValueError("Removed child does not appear to be a tree item")
        elif childObj[NameObject('/Parent')] != self:
            raise ValueError("Removed child is not a member of this tree")

        found = False
        prevRef = None
        prev = None
        curRef = self[NameObject('/First')]
        cur = curRef.getObject()
        lastRef = self[NameObject('/Last')]
        last = lastRef.getObject()
        while cur != None:
            if cur == childObj:
                if prev == None:
                    if NameObject('/Next') in cur:
                        # Removing first tree node
                        nextRef = cur[NameObject('/Next')]
                        next = nextRef.getObject()
                        del next[NameObject('/Prev')]
                        self[NameObject('/First')] = nextRef
                        self[NameObject('/Count')] = self[NameObject('/Count')] - 1

                    else:
                        # Removing only tree node
                        assert self[NameObject('/Count')] == 1
                        del self[NameObject('/Count')]
                        del self[NameObject('/First')]
                        if NameObject('/Last') in self:
                            del self[NameObject('/Last')]
                else:
                    if NameObject('/Next') in cur:
                        # Removing middle tree node
                        nextRef = cur[NameObject('/Next')]
                        next = nextRef.getObject()
                        next[NameObject('/Prev')] = prevRef
                        prev[NameObject('/Next')] = nextRef
                        self[NameObject('/Count')] = self[NameObject('/Count')] - 1
                    else:
                        # Removing last tree node
                        assert cur == last
                        del prev[NameObject('/Next')]
                        self[NameObject('/Last')] = prevRef
                        self[NameObject('/Count')] = self[NameObject('/Count')] - 1
                found = True
                break

            prevRef = curRef
            prev = cur
            if NameObject('/Next') in cur:
                curRef = cur[NameObject('/Next')]
                cur = curRef.getObject()
            else:
                curRef = None
                cur = None

        if not found:
            raise ValueError("Removal couldn't find item in tree")

        del childObj[NameObject('/Parent')]
        if NameObject('/Next') in childObj:
            del childObj[NameObject('/Next')]
        if NameObject('/Prev') in childObj:
            del childObj[NameObject('/Prev')]

    def emptyTree(self):
        for child in self:
            childObj = child.getObject()
            del childObj[NameObject('/Parent')]
            if NameObject('/Next') in childObj:
                del childObj[NameObject('/Next')]
            if NameObject('/Prev') in childObj:
                del childObj[NameObject('/Prev')]

        if NameObject('/Count') in self:
            del self[NameObject('/Count')]
        if NameObject('/First') in self:
            del self[NameObject('/First')]
        if NameObject('/Last') in self:
            del self[NameObject('/Last')]


class StreamObject(DictionaryObject):
    def __init__(self):
        self._data = None
        self.decodedSelf = None

    def writeToStream(self, stream, encryption_key):
        self[NameObject("/Length")] = NumberObject(len(self._data))
        DictionaryObject.writeToStream(self, stream, encryption_key)
        del self["/Length"]
        stream.write("\nstream\n")
        data = self._data
        if encryption_key:
            data = RC4_encrypt(encryption_key, data)
        stream.write(data)
        stream.write("\nendstream")

    def initializeFromDictionary(data):
        if "/Filter" in data:
            retval = EncodedStreamObject()
        else:
            retval = DecodedStreamObject()
        retval._data = data["__streamdata__"]
        del data["__streamdata__"]
        del data["/Length"]
        retval.update(data)
        return retval
    initializeFromDictionary = staticmethod(initializeFromDictionary)

    def flateEncode(self):
        if "/Filter" in self:
            f = self["/Filter"]
            if isinstance(f, ArrayObject):
                f.insert(0, NameObject("/FlateDecode"))
            else:
                newf = ArrayObject()
                newf.append(NameObject("/FlateDecode"))
                newf.append(f)
                f = newf
        else:
            f = NameObject("/FlateDecode")
        retval = EncodedStreamObject()
        retval[NameObject("/Filter")] = f
        retval._data = filters.FlateDecode.encode(self._data)
        return retval


class DecodedStreamObject(StreamObject):
    def getData(self):
        return self._data

    def setData(self, data):
        self._data = data


class EncodedStreamObject(StreamObject):
    def __init__(self):
        self.decodedSelf = None

    def getData(self):
        if self.decodedSelf:
            # cached version of decoded object
            return self.decodedSelf.getData()
        else:
            # create decoded object
            decoded = DecodedStreamObject()

            decoded._data = filters.decodeStreamData(self)
            for key, value in list(self.items()):
                if not key in ("/Length", "/Filter", "/DecodeParms"):
                    decoded[key] = value
            self.decodedSelf = decoded
            return decoded._data

    def setData(self, data):
        raise utils.PdfReadError("Creating EncodedStreamObject is not currently supported")



def encode_pdfdocencoding(unicode_string):
    retval = ''
    for c in unicode_string:
        try:
            retval += chr(_pdfDocEncoding_rev[c])
        except KeyError:
            raise UnicodeEncodeError("pdfdocencoding", c, -1, -1,
                    "does not exist in translation table")
    return retval


def decode_pdfdocencoding(byte_array):
    retval = u_('')
    for b in byte_array:
        c = _pdfDocEncoding[ord(b)]
        if c == u_('\u0000'):
            raise UnicodeDecodeError("pdfdocencoding", b, -1, -1,
                    "does not exist in translation table")
        retval += c
    return retval

_pdfDocEncoding = (
  u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'),
  u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'),
  u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'), u_('\u0000'),
  u_('\u02d8'), u_('\u02c7'), u_('\u02c6'), u_('\u02d9'), u_('\u02dd'), u_('\u02db'), u_('\u02da'), u_('\u02dc'),
  u_('\u0020'), u_('\u0021'), u_('\u0022'), u_('\u0023'), u_('\u0024'), u_('\u0025'), u_('\u0026'), u_('\u0027'),
  u_('\u0028'), u_('\u0029'), u_('\u002a'), u_('\u002b'), u_('\u002c'), u_('\u002d'), u_('\u002e'), u_('\u002f'),
  u_('\u0030'), u_('\u0031'), u_('\u0032'), u_('\u0033'), u_('\u0034'), u_('\u0035'), u_('\u0036'), u_('\u0037'),
  u_('\u0038'), u_('\u0039'), u_('\u003a'), u_('\u003b'), u_('\u003c'), u_('\u003d'), u_('\u003e'), u_('\u003f'),
  u_('\u0040'), u_('\u0041'), u_('\u0042'), u_('\u0043'), u_('\u0044'), u_('\u0045'), u_('\u0046'), u_('\u0047'),
  u_('\u0048'), u_('\u0049'), u_('\u004a'), u_('\u004b'), u_('\u004c'), u_('\u004d'), u_('\u004e'), u_('\u004f'),
  u_('\u0050'), u_('\u0051'), u_('\u0052'), u_('\u0053'), u_('\u0054'), u_('\u0055'), u_('\u0056'), u_('\u0057'),
  u_('\u0058'), u_('\u0059'), u_('\u005a'), u_('\u005b'), u_('\u005c'), u_('\u005d'), u_('\u005e'), u_('\u005f'),
  u_('\u0060'), u_('\u0061'), u_('\u0062'), u_('\u0063'), u_('\u0064'), u_('\u0065'), u_('\u0066'), u_('\u0067'),
  u_('\u0068'), u_('\u0069'), u_('\u006a'), u_('\u006b'), u_('\u006c'), u_('\u006d'), u_('\u006e'), u_('\u006f'),
  u_('\u0070'), u_('\u0071'), u_('\u0072'), u_('\u0073'), u_('\u0074'), u_('\u0075'), u_('\u0076'), u_('\u0077'),
  u_('\u0078'), u_('\u0079'), u_('\u007a'), u_('\u007b'), u_('\u007c'), u_('\u007d'), u_('\u007e'), u_('\u0000'),
  u_('\u2022'), u_('\u2020'), u_('\u2021'), u_('\u2026'), u_('\u2014'), u_('\u2013'), u_('\u0192'), u_('\u2044'),
  u_('\u2039'), u_('\u203a'), u_('\u2212'), u_('\u2030'), u_('\u201e'), u_('\u201c'), u_('\u201d'), u_('\u2018'),
  u_('\u2019'), u_('\u201a'), u_('\u2122'), u_('\ufb01'), u_('\ufb02'), u_('\u0141'), u_('\u0152'), u_('\u0160'),
  u_('\u0178'), u_('\u017d'), u_('\u0131'), u_('\u0142'), u_('\u0153'), u_('\u0161'), u_('\u017e'), u_('\u0000'),
  u_('\u20ac'), u_('\u00a1'), u_('\u00a2'), u_('\u00a3'), u_('\u00a4'), u_('\u00a5'), u_('\u00a6'), u_('\u00a7'),
  u_('\u00a8'), u_('\u00a9'), u_('\u00aa'), u_('\u00ab'), u_('\u00ac'), u_('\u0000'), u_('\u00ae'), u_('\u00af'),
  u_('\u00b0'), u_('\u00b1'), u_('\u00b2'), u_('\u00b3'), u_('\u00b4'), u_('\u00b5'), u_('\u00b6'), u_('\u00b7'),
  u_('\u00b8'), u_('\u00b9'), u_('\u00ba'), u_('\u00bb'), u_('\u00bc'), u_('\u00bd'), u_('\u00be'), u_('\u00bf'),
  u_('\u00c0'), u_('\u00c1'), u_('\u00c2'), u_('\u00c3'), u_('\u00c4'), u_('\u00c5'), u_('\u00c6'), u_('\u00c7'),
  u_('\u00c8'), u_('\u00c9'), u_('\u00ca'), u_('\u00cb'), u_('\u00cc'), u_('\u00cd'), u_('\u00ce'), u_('\u00cf'),
  u_('\u00d0'), u_('\u00d1'), u_('\u00d2'), u_('\u00d3'), u_('\u00d4'), u_('\u00d5'), u_('\u00d6'), u_('\u00d7'),
  u_('\u00d8'), u_('\u00d9'), u_('\u00da'), u_('\u00db'), u_('\u00dc'), u_('\u00dd'), u_('\u00de'), u_('\u00df'),
  u_('\u00e0'), u_('\u00e1'), u_('\u00e2'), u_('\u00e3'), u_('\u00e4'), u_('\u00e5'), u_('\u00e6'), u_('\u00e7'),
  u_('\u00e8'), u_('\u00e9'), u_('\u00ea'), u_('\u00eb'), u_('\u00ec'), u_('\u00ed'), u_('\u00ee'), u_('\u00ef'),
  u_('\u00f0'), u_('\u00f1'), u_('\u00f2'), u_('\u00f3'), u_('\u00f4'), u_('\u00f5'), u_('\u00f6'), u_('\u00f7'),
  u_('\u00f8'), u_('\u00f9'), u_('\u00fa'), u_('\u00fb'), u_('\u00fc'), u_('\u00fd'), u_('\u00fe'), u_('\u00ff')
)

assert len(_pdfDocEncoding) == 256

_pdfDocEncoding_rev = {}
for i in range(256):
    char = _pdfDocEncoding[i]
    if char == u_("\u0000"):
        continue
    assert char not in _pdfDocEncoding_rev
    _pdfDocEncoding_rev[char] = i
