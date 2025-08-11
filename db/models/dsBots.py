from sqlmodel import Field, SQLModel

class DsBot(SQLModel, table=True):
  id: int | None = Field(default=None, primary_key=True)
  name: str
  token: str