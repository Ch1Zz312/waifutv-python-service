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
        # 1. Ищем аниме по shikimori_id
        search_results = parser.search_by_id(id=shikimori_id, id_type="shikimori", limit=10)
        
        if not search_results:
            raise HTTPException(status_code=404, detail="Аниме не найдено в базе Kodik")
        
        # 2. Берём первый результат (там может быть несколько озвучек)
        anime_data = search_results[0]
        kodik_link = anime_data.get("link")
        
        if not kodik_link:
            raise HTTPException(status_code=404, detail="Ссылка на плеер не найдена")
        
        # 3. Получаем прямую ссылку на видео из ссылки плеера
        # Метод get_mp4_link возвращает ссылку на видеофайл
        video_url = parser.get_mp4_link(kodik_link, seria_num=episode)
        
        if not video_url:
            raise HTTPException(status_code=404, detail="Не удалось получить ссылку на видео")
        
        return {
            "url": video_url,
            "qualities": {},
            "source": "kodik",
            "quality": quality
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка парсинга: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)