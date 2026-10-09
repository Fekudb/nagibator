from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db.database import (
    authenticate_user,
    create_user,
    get_article,
    get_articles,
    get_comments,
    get_stats,
    init_db,
    save_comment,
    save_prediction,
)
from domain.entities import (
    ArticleResponse,
    CommentRequest,
    CommentResponse,
    HealthResponse,
    LoginRequest,
    PredictionRequest,
    PredictionResponse,
    RegisterRequest,
    StatsResponse,
    UserResponse,
)
from ml.predictor import Predictor

predictor = None


@asynccontextmanager
async def lifespan(app):
    global predictor
    init_db()
    predictor = Predictor()
    yield


app = FastAPI(title="Toxic Comment Detector", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/register", response_model=UserResponse)
def register(request: RegisterRequest):
    user = create_user(request.username, request.password, request.gender)
    if user is None:
        raise HTTPException(status_code=409, detail="Пользователь с таким именем уже существует")
    return UserResponse(**user)


@app.post("/login", response_model=UserResponse)
def login(request: LoginRequest):
    user = authenticate_user(request.username, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    return UserResponse(**user)


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    if not request.text.strip():
        raise HTTPException(
            status_code=400,
            detail="Field 'text' is required and must be a non-empty string",
        )
    try:
        label, score = predictor.predict(request.text)
        save_prediction(request.text, label, score, request.user_id)
        return PredictionResponse(label=label, score=score)
    except Exception:
        raise HTTPException(status_code=500, detail="Model prediction failed")


@app.get("/stats", response_model=StatsResponse)
def stats():
    return StatsResponse(**get_stats())


@app.get("/articles", response_model=list[ArticleResponse])
def articles():
    return [ArticleResponse(**a) for a in get_articles()]


@app.get("/articles/{article_id}", response_model=ArticleResponse)
def article(article_id: int):
    a = get_article(article_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    return ArticleResponse(**a)


@app.post("/articles/{article_id}/comments", response_model=CommentResponse)
def add_comment(article_id: int, request: CommentRequest):
    if get_article(article_id) is None:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Комментарий не может быть пустым")
    label, score = predictor.predict(request.text)
    save_prediction(request.text, label, score, request.user_id)
    if label == "toxic":
        raise HTTPException(
            status_code=403,
            detail="Комментарий содержит токсичный контент и не может быть опубликован",
        )
    comment = save_comment(article_id, request.user_id, request.text)
    return CommentResponse(**comment)


@app.get("/articles/{article_id}/comments", response_model=list[CommentResponse])
def list_comments(article_id: int):
    if get_article(article_id) is None:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    return [CommentResponse(**c) for c in get_comments(article_id)]


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")
