from pydantic import BaseModel


class MinimalSource(BaseModel):
    pass


class UnansweredQuestion(BaseModel):
    pass


class AnsweredQuestion(BaseModel):
    pass


class RagDataset(BaseModel):
    pass


class MinimalSearchResult(BaseModel):
    pass


class MinimalAnswer(BaseModel):
    pass


class StudentSearchResults(BaseModel):
    pass


class StudentSearchResultsAndAnswer(BaseModel):
    pass


class Chunk(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int
    text: str
