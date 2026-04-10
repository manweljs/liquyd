from liquyd import BaseDocument, Property


class PlaygroundLog(BaseDocument):
    id: str = Property("keyword", primary_key=True)
    project_name: str = Property("keyword")
    endpoint_path: str = Property("keyword")
    status_code: int | None = Property("integer", nullable=True)
    method: str | None = Property("keyword", nullable=True)

    class Meta:
        index = "liquyd_playground_logs"


class PlaygroundUser(BaseDocument):
    username: str = Property("keyword", primary_key=True)
    full_name: str = Property("text")
    avatar_url: str | None = Property("keyword", nullable=True)

    # products: list['PlaygroundProduct'] = disini apa ???

    class Meta:
        index = "liquyd_playground_users"


class PlaygroundProduct(BaseDocument):
    product_id: str = Property("keyword", primary_key=True)
    name: str = Property("text")
    sku: str | None = Property("keyword", nullable=True)

    class Meta:
        index = "liquyd_playground_products"


class PlaygroundStore(BaseDocument):
    id: str = Property("keyword", primary_key=True)
    name: str = Property("text")
    location: str | None = Property("text", nullable=True)

    class Meta:
        index = "liquyd_playground_stores"
