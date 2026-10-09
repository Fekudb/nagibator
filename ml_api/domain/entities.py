from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)
    gender: str = Field(..., pattern="^(male|female)$")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    gender: str


class PredictionRequest(BaseModel):
    text: str = Field(..., min_length=1)
    user_id: int | None = None


class PredictionResponse(BaseModel):
    label: str
    score: float


class HealthResponse(BaseModel):
    status: str


class RecentPrediction(BaseModel):
    text: str
    label: str
    score: float
    created_at: str


class GenderStats(BaseModel):
    gender: str
    total: int
    toxic_count: int
    toxic_percent: float


class StatsResponse(BaseModel):
    total_checks: int
    toxic_count: int
    neutral_count: int
    toxic_percent: float
    avg_toxic_score: float
    recent: list[RecentPrediction]
    by_gender: list[GenderStats]


class ArticleResponse(BaseModel):
    id: int
    title: str
    summary: str
    author: str
    created_at: str


class CommentRequest(BaseModel):
    article_id: int
    text: str = Field(..., min_length=1)
    user_id: int


class CommentResponse(BaseModel):
    id: int
    article_id: int
    user_id: int
    username: str
    text: str
    created_at: str
