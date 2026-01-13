import flet as ft
import requests
import sqlite3

AREA_URL = "http://www.jma.go.jp/bosai/common/const/area.json"
FORECAST_URL = "https://www.jma.go.jp/bosai/forecast/data/forecast/{}.json"



def weather_icon(text: str) -> str:
    if "晴" in text:
        return "☀️"
    if "くもり" in text or "曇" in text:
        return "☁️"
    if "雨" in text:
        return "🌧️"
    if "雪" in text:
        return "❄️"
    return "🌈"



def init_db():
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS areas (
        area_code TEXT PRIMARY KEY,
        area_name TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS forecasts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_code TEXT,
        date TEXT,
        weather TEXT,
        max_temp INTEGER,
        min_temp INTEGER
    )
    """)

    conn.commit()
    conn.close()



def save_forecast(area_code, area_name, data_list):
    conn = sqlite3.connect("weather.db")
    cur = conn.cursor()

    cur.execute(
        "INSERT OR IGNORE INTO areas VALUES (?, ?)",
        (area_code, area_name)
    )

    for d in data_list:
        cur.execute("""
        INSERT INTO forecasts (area_code, date, weather, max_temp, min_temp)
        VALUES (?, ?, ?, ?, ?)
        """, (
            area_code,
            d["date"],
            d["weather"],
            d["max"],
            d["min"]
        ))

    conn.commit()
    conn.close()



def main(page: ft.Page):
    init_db()  

    page.title = "天気予報アプリ"
    page.window_width = 900
    page.window_height = 600

    area_data = requests.get(AREA_URL).json()
    offices = area_data["offices"]

    area_list = [
        {"code": code, "name": info["name"]}
        for code, info in offices.items()
    ]

    forecast_column = ft.Column(
        controls=[ft.Text("地域を選択してください", size=20)],
        scroll=ft.ScrollMode.AUTO,
        expand=True,
    )

    def show_forecast(area_code, area_name):
        forecast_column.controls.clear()
        forecast_column.controls.append(
            ft.Text(f"{area_name} の天気予報", size=22, weight=ft.FontWeight.BOLD)
        )

        data = requests.get(FORECAST_URL.format(area_code)).json()
        time_series = data[0]["timeSeries"]

        weather_series = time_series[0]
        dates = weather_series["timeDefines"]
        weathers = weather_series["areas"][0]["weathers"]

        temp_series = time_series[1]
        temps_max = temp_series["areas"][0].get("tempsMax", [])
        temps_min = temp_series["areas"][0].get("tempsMin", [])

        save_data = []

        for i in range(len(dates)):
            date = dates[i][:10]
            weather = weathers[i]
            icon = weather_icon(weather)

            max_t = int(temps_max[i]) if i < len(temps_max) else None
            min_t = int(temps_min[i]) if i < len(temps_min) else None

            save_data.append({
                "date": date,
                "weather": weather,
                "max": max_t,
                "min": min_t,
            })

            forecast_column.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Text(
                            f"{date} {icon}\n"
                            f"{weather}\n"
                            f"最高 {max_t}℃ / 最低 {min_t}℃",
                            size=14,
                        ),
                    )
                )
            )

        save_forecast(area_code, area_name, save_data)
        page.update()

    
    area_list_view = ft.ListView(width=260, spacing=2, padding=10)

    for area in area_list:
        area_list_view.controls.append(
            ft.ListTile(
                title=ft.Text(area["name"]),
                on_click=lambda e, a=area: show_forecast(a["code"], a["name"]),
            )
        )

    page.add(
        ft.Row(
            controls=[
                ft.Container(content=area_list_view, bgcolor=ft.Colors.BLUE_GREY_50),
                ft.VerticalDivider(width=1),
                ft.Container(content=forecast_column, expand=True, padding=20),
            ],
            expand=True,
        )
    )


ft.app(target=main)
