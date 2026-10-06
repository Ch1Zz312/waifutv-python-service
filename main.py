from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from anime_parsers_ru import KodikParser
import uvicorn

app = FastAPI()

# Разрешаем CORS для всех (для теста)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализируем парсер один раз
parser = KodikParser()

@app.get("/")
def health_check():
    return {"status": "ok", "service": "waifutv-python-service"}

@app.get("/video")
async def get_video(
    shikimori_id: str = Query(..., description="ID аниме в Shikimori"),
    episode: int = Query(1, description="Номер серии"),
    quality: int = Query(720, description="Качество видео")
):
    """
    Получает ссылку на видео с Kodik через anime_parsers_ru.
    """
    try:
        # Получаем токен
        token = parser.get_token()
        
        # Получаем ссылки на видео
        # Метод parse_video_by_shikimori_id возвращает словарь с качествами
        video_info = parser.parse_video_by_shikimori_id(
            shikimori_id=shikimori_id,
            episode=episode,
            token=token
        )
        
        if not video_info:
            raise HTTPException(status_code=404, detail="Видео не найдено")
        
        # video_info имеет структуру:
        # {'360': 'url1', '480': 'url2', '720': 'url3'}
        # Или {'link': 'url', 'quality': 720} в зависимости от версии
        
        # Приводим к единому формату
        url = None
        qualities = {}
        
        if isinstance(video_info, dict):
            # Если это словарь с качествами
            if '720' in video_info:
                url = video_info.get(str(quality)) or video_info.get('720')
                qualities = video_info
            # Если это словарь с одной ссылкой
            elif 'link' in video_info:
                url = video_info['link']
                qualities = {str(video_info.get('quality', 720)): url}
        
        if not url:
            raise HTTPException(status_code=404, detail="Ссылка не найдена")
        
        return {
            "url": url,
            "qualities": qualities,
            "source": "kodik",
            "quality": quality
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)