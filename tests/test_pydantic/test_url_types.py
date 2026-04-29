from pydantic import BaseModel, HttpUrl
from sqlmodel import Field, Session, SQLModel, create_engine, select

from typing import ClassVar

from pydantic import ConfigDict

from sqlmodel._compat import SQLModelConfig

def test_httpurl_stored_via_base_model_inheritance(clear_sqlmodel) -> None:
    class Product(BaseModel):
        url: HttpUrl

    class StoredProduct(Product, SQLModel, table=True):
        id: int = Field(primary_key=True, default=None)

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        session.add(StoredProduct(id=1, url="https://example.com"))
        session.commit()
        result = session.exec(select(StoredProduct)).all()

    assert len(result) == 1
    assert str(result[0].url) == "https://example.com"


def test_httpurl_add_all_frozen_inheritance(clear_sqlmodel) -> None:

    class Product(BaseModel):
        model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

        id: int
        url: HttpUrl
        image_url: HttpUrl

    class StoredProduct(Product, SQLModel, table=True):
        model_config: ClassVar[SQLModelConfig] = SQLModelConfig(table=True)

        id: int = Field(primary_key=True)

        @classmethod
        def from_product(cls, p: Product) -> "StoredProduct":
            return cls(**dict(p))

    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    products = [
        StoredProduct.from_product(
            Product(
                id=i,
                url=f"https://example.com/product/{i}",
                image_url=f"https://example.com/image/{i}.webp",
            )
        )
        for i in range(5)
    ]

    with Session(engine) as session:
        session.add_all(products)
        session.commit()
        result = session.exec(select(StoredProduct)).all()

    assert len(result) == 5
    assert all(str(p.url).startswith("https://example.com/product/") for p in result)
    assert all(str(p.image_url).startswith("https://example.com/image/") for p in result)
