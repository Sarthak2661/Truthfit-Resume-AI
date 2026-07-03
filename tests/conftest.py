from io import BytesIO


class NamedBytesIO(BytesIO):
    def __init__(self, data: bytes, name: str):
        super().__init__(data)
        self.name = name


class FakePdfPage:
    def __init__(self, text: str):
        self.text = text

    def extract_text(self):
        return self.text


class FakePdfReader:
    def __init__(self, uploaded_file):
        self.pages = [
            FakePdfPage("First PDF page"),
            FakePdfPage("Second PDF page"),
        ]


def make_upload(data: bytes, name: str) -> NamedBytesIO:
    return NamedBytesIO(data, name)
