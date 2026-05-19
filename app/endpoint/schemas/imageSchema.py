from sqlmodel import SQLModel


class ImageCreate(SQLModel):
    path_256x256:   str
    path_512x512:   str


class ImageShow(SQLModel):
    path_256x256:   str
    path_512x512:   str


class ImagePatch(SQLModel):
    path_256x256:   str | None = None
    path_512x512:   str | None = None
